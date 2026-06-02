import customtkinter as ctk
import sqlite3
from datetime import datetime, timedelta, timezone
import tkinter as tk
from src.monitor.database import get_time_remaining_estimate

class MiniStatusWindow(ctk.CTkToplevel):
    def __init__(self, master=None, db_file=None, headset_pct: int = 0, charger_pct: int = 0, charging_status: str = "", refresh_callback=None, **kwargs):
        super().__init__(master, **kwargs)
        
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.geometry("340x280")
        
        self.db_file = db_file
        self.time_range = "12h"
        self.history_data = []
        self.refresh_callback = refresh_callback

        # Position at bottom right, near tray
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = screen_width - 360
        y = screen_height - 340
        self.geometry(f"+{x}+{y}")
        
        # Auto-hide on focus out
        self.bind("<FocusOut>", lambda e: self.master.destroy())
        
        # UI
        self.configure(fg_color="#0f172a")
        
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(10, 5))
        ctk.CTkLabel(header, text="NovaPulse", font=("Segoe UI", 14, "bold"), text_color="#ffffff").pack(side="left")
        ctk.CTkButton(header, text="×", width=24, height=24, fg_color="transparent", hover_color="#ef4444", command=self.master.destroy).pack(side="right")
        
        # Battery Displays
        self.batt_frame = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=10)
        self.batt_frame.pack(fill="x", padx=10, pady=5)
        
        self.headset_lbl = None
        self.charger_lbl = None
        
        self.est_lbl = ctk.CTkLabel(self.batt_frame, text="", font=("Segoe UI", 11, "italic"), text_color="#94a3b8")
        self.est_lbl.pack(fill="x", padx=10, pady=(0, 5))
        
        self.update_battery(headset_pct, charger_pct, charging_status)

        # Graph Controls
        ctrl_frame = ctk.CTkFrame(self, fg_color="transparent")
        ctrl_frame.pack(fill="x", padx=10, pady=(10, 0))
        ctk.CTkLabel(ctrl_frame, text="History", font=("Segoe UI", 12, "bold"), text_color="#ffffff").pack(side="left")
        
        self.range_var = ctk.StringVar(value="12h")
        self.range_btn = ctk.CTkSegmentedButton(ctrl_frame, values=["12h", "24h", "7d"], variable=self.range_var, command=self._on_range_change, width=120)
        self.range_btn.pack(side="right")
        
        # Graph Canvas
        self.graph_cv = tk.Canvas(self, height=100, bg="#1e293b", highlightthickness=0)
        self.graph_cv.pack(fill="both", expand=True, padx=10, pady=(5, 10))
        self.graph_cv.bind("<Configure>", lambda e: self.draw_graph())
        
        if self.db_file:
            self.load_graph_data()
            
        # Start auto-refresh
        self._schedule_refresh()

    def _schedule_refresh(self):
        """Schedule the next UI refresh."""
        self.after(60000, self.refresh)

    def refresh(self):
        """Update battery levels and graph data from callback or global state."""
        if self.refresh_callback:
            h, c, s = self.refresh_callback()
            self.update_battery(h, c, s)
        
        self.load_graph_data()
        self._schedule_refresh()

    def _on_range_change(self, value):
        self.time_range = value
        self.load_graph_data()

    def load_graph_data(self):
        if not self.db_file: return
        
        hours = 12 if self.time_range == "12h" else 24 if self.time_range == "24h" else 24 * 7
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT timestamp, headset_pct, charger_pct FROM battery_log WHERE timestamp >= ? ORDER BY timestamp ASC",
                    (cutoff.strftime("%Y-%m-%d %H:%M:%S"),)
                )
                self.history_data = cursor.fetchall()
            self.draw_graph()
        except Exception as e:
            print(f"Graph load error: {e}")

    def draw_graph(self):
        self.graph_cv.delete("all")
        if not self.history_data:
            self.graph_cv.create_text(self.graph_cv.winfo_width()/2, 50, text="No data available", fill="#7f8c8d")
            return
            
        w = self.graph_cv.winfo_width()
        h = self.graph_cv.winfo_height()
        if w < 10 or h < 10: return
        
        # Determine time range
        t0 = datetime.strptime(self.history_data[0][0], "%Y-%m-%d %H:%M:%S").timestamp()
        t1 = datetime.strptime(self.history_data[-1][0], "%Y-%m-%d %H:%M:%S").timestamp()
        dt = max(t1 - t0, 1)
        
        # Draw background grid lines (25%, 50%, 75%)
        for y_pct in [25, 50, 75]:
            y_pos = h - (y_pct / 100) * h
            self.graph_cv.create_line(0, y_pos, w, y_pos, fill="#374151", dash=(2, 4))
            
        # Extract points
        headset_pts = []
        charger_pts = []
        for row in self.history_data:
            ts = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S").timestamp()
            x = ((ts - t0) / dt) * w
            headset_pts.extend([x, h - (row[1] / 100) * h])
            charger_pts.extend([x, h - (row[2] / 100) * h])
            
        # Draw lines
        if len(headset_pts) >= 4:
            self.graph_cv.create_line(headset_pts, fill="#27ae60", width=2, smooth=False)
            self.graph_cv.create_line(charger_pts, fill="#3b82f6", width=2, smooth=False)

    def _add_or_update_row(self, label_text, pct, status, is_headset):
        color = "#27ae60" if pct > 20 else "#e74c3c"
        if pct == 0 and status == "UNKNOWN_OR_HEADSET_NOT_CONNECTED":
            color = "#7f8c8d"
            val_text = "Offline"
        else:
            val_text = f"{pct}% {'⚡' if status == 'CHARGING' else ''}".strip()
            
        if is_headset:
            if not self.headset_lbl:
                row = ctk.CTkFrame(self.batt_frame, fg_color="transparent")
                row.pack(fill="x", padx=10, pady=(5, 2))
                ctk.CTkLabel(row, text=label_text, font=("Segoe UI", 12), text_color="#e5e7eb").pack(side="left")
                self.headset_lbl = ctk.CTkLabel(row, text=val_text, font=("Segoe UI", 12, "bold"), text_color=color)
                self.headset_lbl.pack(side="right")
            else:
                self.headset_lbl.configure(text=val_text, text_color=color)
        else:
            if not self.charger_lbl:
                row = ctk.CTkFrame(self.batt_frame, fg_color="transparent")
                row.pack(fill="x", padx=10, pady=(2, 5))
                ctk.CTkLabel(row, text=label_text, font=("Segoe UI", 12), text_color="#e5e7eb").pack(side="left")
                self.charger_lbl = ctk.CTkLabel(row, text=val_text, font=("Segoe UI", 12, "bold"), text_color=color)
                self.charger_lbl.pack(side="right")
            else:
                self.charger_lbl.configure(text=val_text, text_color=color)

    def update_battery(self, headset_pct: int, charger_pct: int, charging_status: str):
        self._add_or_update_row("Headset", headset_pct, charging_status, True)
        self._add_or_update_row("Charger", charger_pct, "", False)
        
        # Update estimate
        if headset_pct == 0 and charging_status == "UNKNOWN_OR_HEADSET_NOT_CONNECTED":
            est = ""
        else:
            est = get_time_remaining_estimate(headset_pct)
            
        if hasattr(self, 'est_lbl'):
            self.est_lbl.configure(text=est)

    def show(self):
        self.deiconify()
        self.focus_force()
