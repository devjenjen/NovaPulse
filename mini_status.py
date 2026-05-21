import customtkinter as ctk

class MiniStatusWindow(ctk.CTkToplevel):
    def __init__(self, master=None, headset_pct: int = 0, charger_pct: int = 0, charging_status: str = "", **kwargs):
        super().__init__(master, **kwargs)
        
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.geometry("300x120")
        
        # Position at bottom right, near tray
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = screen_width - 320
        y = screen_height - 180
        self.geometry(f"+{x}+{y}")
        
        # Auto-hide on focus out
        self.bind("<FocusOut>", lambda e: self.withdraw())
        
        # UI
        self.configure(fg_color="#0f172a")
        
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(10, 5))
        ctk.CTkLabel(header, text="NovaPulse", font=("Segoe UI", 14, "bold"), text_color="#ffffff").pack(side="left")
        ctk.CTkButton(header, text="×", width=24, height=24, fg_color="transparent", hover_color="#ef4444", command=self.withdraw).pack(side="right")
        
        # Battery Displays
        self.batt_frame = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=10)
        self.batt_frame.pack(fill="x", padx=10, pady=5)
        
        self.headset_lbl = None
        self.charger_lbl = None
        
        self.update_battery(headset_pct, charger_pct, charging_status)

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

    def show(self):
        self.deiconify()
        self.focus_force()
