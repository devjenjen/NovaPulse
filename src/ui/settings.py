import os
import threading
import tkinter as tk
import json

from src.core.constants import APP_NAME, VERSION, SOUNDS_DIR, CONFIG_FILE, logger
from src.core.i18n import t
from src.core.autostart import enable_autostart, disable_autostart, is_autostart_enabled
from src.core.utils import get_reload_event
from src.ui.notifications import send_notification
from src.monitor.database import get_battery_health_estimate

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False

def _center_window(win) -> None:
    win.update_idletasks()
    w = win.winfo_reqwidth()
    h = win.winfo_reqheight()
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    win.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

def test_low_battery() -> None:
    send_notification(t("test_low_title"), t("test_low_msg"))

def test_charger_full() -> None:
    send_notification(t("test_full_title"), t("test_full_msg"))

def test_critical_battery() -> None:
    from src.core.config import load_config
    cfg = load_config()
    send_notification(t("test_critical_title", pct=cfg["critical_threshold"]), t("test_critical_msg"))

def _open_settings_gui_legacy(current_config: dict) -> None:
    import tkinter.ttk as ttk
    def _run():
        root = tk.Tk()
        root.title(t("gui_title"))
        root.resizable(False, False)
        lbl = ttk.Label(root, text="Settings (legacy mode – install customtkinter for the full UI)")
        lbl.pack(padx=20, pady=20)
        ttk.Button(root, text="Close", command=root.destroy).pack(pady=(0, 20))
        _center_window(root)
        root.mainloop()
    threading.Thread(target=_run, daemon=True).start()

def _open_settings_gui_ctk(current_config: dict) -> None:
    BG      = "#0f172a"
    CARD    = "#1e293b"
    ACCENT  = "#7c3aed"
    ACCENT2 = "#1d4ed8"
    FG      = "#e5e7eb"
    MUTED   = "#6b7280"
    ENTRY   = "#111827"
    BORDER  = "#374151"
    DANGER  = "#ef4444"
    WARN    = "#f59e0b"
    OK      = "#10b981"
    cfg = current_config.copy()

    def _run():
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        root = ctk.CTk()
        root.title(t("gui_title"))
        root.resizable(False, False)
        root.configure(fg_color=BG)

        hdr = tk.Canvas(root, height=54, bd=0, highlightthickness=0)
        hdr.pack(fill="x")
        def _draw_header(event=None):
            w = hdr.winfo_width() or 480
            r1, g1, b1 = 0x1d, 0x4e, 0xd8
            r2, g2, b2 = 0x7c, 0x3a, 0xed
            for i in range(w):
                frac = i / max(w - 1, 1)
                r = int(r1 + (r2 - r1) * frac)
                g = int(g1 + (g2 - g1) * frac)
                b = int(b1 + (b2 - b1) * frac)
                hdr.create_line(i, 0, i, 54, fill=f"#{r:02x}{g:02x}{b:02x}")
            hdr.create_text(20, 27, anchor="w", text=f"  {APP_NAME}", fill="#ffffff", font=("Segoe UI", 15, "bold"))
            hdr.create_text(460, 27, anchor="e", text=f"v{VERSION}", fill="#c4b5fd", font=("Segoe UI", 9))
        hdr.bind("<Configure>", _draw_header)

        tabview = ctk.CTkTabview(root, fg_color=BG, segmented_button_fg_color=CARD, segmented_button_selected_color=ACCENT, segmented_button_selected_hover_color=ACCENT, segmented_button_unselected_color=CARD, segmented_button_unselected_hover_color=BORDER, text_color=FG, text_color_disabled=MUTED)
        tabview.pack(fill="both", expand=True, padx=0, pady=0)
        TAB_GENERAL  = "General"
        TAB_ALERTS   = "Alerts"
        TAB_SOUNDS   = "Sounds ✨"
        TAB_ADVANCED = "Advanced"
        tabview.add(TAB_GENERAL)
        tabview.add(TAB_ALERTS)
        tabview.add(TAB_SOUNDS)
        tabview.add(TAB_ADVANCED)
        f_gen = tabview.tab(TAB_GENERAL)
        f_al  = tabview.tab(TAB_ALERTS)
        f_snd = tabview.tab(TAB_SOUNDS)
        f_adv = tabview.tab(TAB_ADVANCED)

        def _create_card(parent, title: str):
            card = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=12)
            card.pack(fill="x", padx=20, pady=(0, 16))
            ctk.CTkLabel(card, text=title.upper(), text_color=ACCENT, font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=16, pady=(12, 8))
            return card
        def _create_row(parent, label: str):
            row = ctk.CTkFrame(parent, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=(0, 12))
            ctk.CTkLabel(row, text=label, text_color=FG).pack(side="left")
            return row

        c_lang = _create_card(f_gen, t("gui_language"))
        r_lang = _create_row(c_lang, t("gui_language"))
        lang_var = tk.StringVar(value=cfg.get("language", "en"))
        ctk.CTkSegmentedButton(r_lang, values=["en", "de"], variable=lang_var, selected_color=ACCENT2, selected_hover_color=ACCENT2, unselected_color=ENTRY, unselected_hover_color=BORDER).pack(side="right")

        c_app = _create_card(f_gen, "App Behaviour")
        r_poll = _create_row(c_app, t("gui_poll_interval"))
        poll_var = tk.IntVar(value=cfg.get("poll_interval", 60))
        ctk.CTkEntry(r_poll, textvariable=poll_var, width=60, fg_color=ENTRY, border_color=BORDER).pack(side="right")
        r_auto = _create_row(c_app, t("gui_autostart"))
        auto_var = tk.BooleanVar(value=is_autostart_enabled())
        ctk.CTkSwitch(r_auto, text="", variable=auto_var, progress_color=OK, button_color=FG, button_hover_color="#ffffff").pack(side="right")
        r_upd = _create_row(c_app, t("gui_auto_update"))
        upd_var = tk.BooleanVar(value=cfg.get("auto_check_updates", True))
        ctk.CTkSwitch(r_upd, text="", variable=upd_var, progress_color=OK, button_color=FG, button_hover_color="#ffffff").pack(side="right")
        r_dnd = _create_row(c_app, "DND Mode (Mute on Fullscreen)")
        dnd_var = tk.BooleanVar(value=cfg.get("dnd_mode", True))
        ctk.CTkSwitch(r_dnd, text="", variable=dnd_var, progress_color=OK, button_color=FG, button_hover_color="#ffffff").pack(side="right")

        c_health = _create_card(f_gen, "Battery Analytics")
        r_health = _create_row(c_health, "Battery Health")
        health_text = get_battery_health_estimate()
        ctk.CTkLabel(r_health, text=health_text, text_color=OK, font=("Segoe UI", 11, "bold")).pack(side="right")

        c_headset = _create_card(f_al, "Headset Alerts")
        r_t1 = _create_row(c_headset, t("gui_low_threshold"))
        t1_var = tk.IntVar(value=cfg.get("low_threshold", 25))
        ctk.CTkEntry(r_t1, textvariable=t1_var, width=60, fg_color=ENTRY, border_color=BORDER).pack(side="right")
        ctk.CTkLabel(c_headset, text=t("gui_low_note"), text_color=MUTED, font=("Segoe UI", 9)).pack(anchor="w", padx=16, pady=(0, 12))
        r_t2 = _create_row(c_headset, t("gui_critical_threshold"))
        t2_var = tk.IntVar(value=cfg.get("critical_threshold", 12))
        ctk.CTkEntry(r_t2, textvariable=t2_var, width=60, fg_color=ENTRY, border_color=BORDER).pack(side="right")
        ctk.CTkLabel(c_headset, text=t("gui_critical_note"), text_color=MUTED, font=("Segoe UI", 9)).pack(anchor="w", padx=16, pady=(0, 12))

        diag_frame = ctk.CTkFrame(c_headset, fg_color="transparent")
        diag_frame.pack(fill="x", padx=16, pady=(0, 12))
        diag_cv = tk.Canvas(diag_frame, height=40, bg=CARD, highlightthickness=0)
        diag_cv.pack(fill="x")
        def _draw_diagram(event=None):
            diag_cv.delete("all")
            w = diag_cv.winfo_width() or 400
            steps = [0, 12, 25, 37, 50, 62, 75, 87, 100]
            diag_cv.create_line(20, 20, w-20, 20, fill=BORDER, width=2)
            for s in steps:
                x = 20 + (s / 100) * (w - 40)
                color = OK if s > 25 else (WARN if s > 12 else DANGER)
                diag_cv.create_oval(x-4, 16, x+4, 24, fill=color, outline=BG)
                if s in [0, 25, 50, 75, 100]:
                    diag_cv.create_text(x, 32, text=f"{s}%", fill=MUTED, font=("Segoe UI", 7))
        diag_cv.bind("<Configure>", _draw_diagram)

        c_charger = _create_card(f_al, "Charger Alert")
        r_full = _create_row(c_charger, t("gui_full_level"))
        full_var = tk.IntVar(value=cfg.get("full_level", 100))
        ctk.CTkEntry(r_full, textvariable=full_var, width=60, fg_color=ENTRY, border_color=BORDER).pack(side="right")

        c_test = _create_card(f_al, "Test Notifications")
        r_test = ctk.CTkFrame(c_test, fg_color="transparent")
        r_test.pack(fill="x", padx=16, pady=(0, 12))
        ctk.CTkButton(r_test, text=t("gui_test_low"), width=100, height=28, fg_color=CARD, border_width=1, border_color=BORDER, command=test_low_battery).pack(side="left", padx=(0, 8))
        ctk.CTkButton(r_test, text=t("gui_test_critical"), width=100, height=28, fg_color=CARD, border_width=1, border_color=BORDER, command=test_critical_battery).pack(side="left", padx=(0, 8))
        ctk.CTkButton(r_test, text=t("gui_test_full"), width=100, height=28, fg_color=CARD, border_width=1, border_color=BORDER, command=test_charger_full).pack(side="left")

        ctk.CTkLabel(f_snd, text=t("gui_sounds_info"), text_color=MUTED, font=("Segoe UI", 10), justify="left").pack(fill="x", padx=24, pady=16)
        c_sound = _create_card(f_snd, "Sound Settings")
        r_s1 = _create_row(c_sound, t("gui_sound_tier1"))
        s1_var = tk.StringVar(value=cfg.get("sound_tier1", ""))
        ctk.CTkEntry(r_s1, textvariable=s1_var, width=180, fg_color=ENTRY, border_color=BORDER).pack(side="right")
        r_s2 = _create_row(c_sound, t("gui_sound_tier2"))
        s2_var = tk.StringVar(value=cfg.get("sound_tier2", ""))
        ctk.CTkEntry(r_s2, textvariable=s2_var, width=180, fg_color=ENTRY, border_color=BORDER).pack(side="right")
        r_s3 = _create_row(c_sound, t("gui_sound_charger"))
        s3_var = tk.StringVar(value=cfg.get("sound_charger_full", ""))
        ctk.CTkEntry(r_s3, textvariable=s3_var, width=180, fg_color=ENTRY, border_color=BORDER).pack(side="right")
        def _open_snd_dir(): os.startfile(str(SOUNDS_DIR))
        ctk.CTkButton(c_sound, text=t("gui_open_sounds_folder"), fg_color=CARD, border_width=1, border_color=BORDER, command=_open_snd_dir).pack(padx=16, pady=(0, 16))

        c_engine = _create_card(f_adv, "Engine Connectivity")
        r_grace = _create_row(c_engine, t("gui_startup_grace"))
        grace_var = tk.IntVar(value=cfg.get("startup_grace", 10))
        ctk.CTkEntry(r_grace, textvariable=grace_var, width=60, fg_color=ENTRY, border_color=BORDER).pack(side="right")
        r_f_int = _create_row(c_engine, t("gui_standby_fast"))
        f_int_var = tk.IntVar(value=cfg.get("standby_retry_fast", 15))
        ctk.CTkEntry(r_f_int, textvariable=f_int_var, width=60, fg_color=ENTRY, border_color=BORDER).pack(side="right")
        r_f_cnt = _create_row(c_engine, t("gui_standby_count"))
        f_cnt_var = tk.IntVar(value=cfg.get("standby_fast_count", 8))
        ctk.CTkEntry(r_f_cnt, textvariable=f_cnt_var, width=60, fg_color=ENTRY, border_color=BORDER).pack(side="right")
        r_s_int = _create_row(c_engine, t("gui_standby_slow"))
        s_int_var = tk.IntVar(value=cfg.get("standby_retry_slow", 300))
        ctk.CTkEntry(r_s_int, textvariable=s_int_var, width=60, fg_color=ENTRY, border_color=BORDER).pack(side="right")
        r_hk = _create_row(c_engine, "Global Hotkey")
        hk_var = tk.StringVar(value=cfg.get("hotkey", "ctrl+shift+b"))
        ctk.CTkEntry(r_hk, textvariable=hk_var, width=100, fg_color=ENTRY, border_color=BORDER).pack(side="right")
        c_hw = _create_card(f_adv, "Hardware Features")
        r_hw = _create_row(c_hw, t("gui_hardware_alert"))
        hw_var = tk.BooleanVar(value=cfg.get("hardware_alert", True))
        ctk.CTkSwitch(r_hw, text="", variable=hw_var, progress_color=OK, button_color=FG, button_hover_color="#ffffff").pack(side="right")

        footer = ctk.CTkFrame(root, fg_color=BG, corner_radius=0)
        footer.pack(fill="x", padx=20, pady=(4, 16))
        ctk.CTkLabel(footer, text=t("gui_restart_required"), text_color=MUTED, font=("Segoe UI", 10)).pack(side="left")

        def _save():
            cfg["language"]           = lang_var.get()
            cfg["poll_interval"]      = max(5, poll_var.get())
            cfg["auto_check_updates"] = upd_var.get()
            cfg["dnd_mode"]           = dnd_var.get()
            cfg["low_threshold"]      = max(1, min(99, t1_var.get()))
            cfg["critical_threshold"] = max(1, min(cfg["low_threshold"]-1, t2_var.get()))
            cfg["full_level"]         = max(1, min(100, full_var.get()))
            cfg["sound_tier1"]        = s1_var.get().strip()
            cfg["sound_tier2"]        = s2_var.get().strip()
            cfg["sound_charger_full"] = s3_var.get().strip()
            cfg["startup_grace"]      = max(0, grace_var.get())
            cfg["standby_retry_fast"] = max(1, f_int_var.get())
            cfg["standby_fast_count"] = max(0, f_cnt_var.get())
            cfg["standby_retry_slow"] = max(1, s_int_var.get())
            cfg["hotkey"]             = hk_var.get().strip()
            cfg["hardware_alert"]     = hw_var.get()

            if auto_var.get(): enable_autostart()
            else: disable_autostart()

            try:
                CONFIG_FILE.write_text(json.dumps(cfg, indent=4), encoding="utf-8")
                logger.info(f"Config saved via GUI: {CONFIG_FILE}")
                get_reload_event().set()
            except Exception as e:
                logger.error(f"Failed to save config: {e}")
            root.destroy()

        ctk.CTkButton(footer, text=t("gui_save"), fg_color=ACCENT, hover_color="#6a4aad", font=("Segoe UI", 10, "bold"), command=_save).pack(side="right", padx=(8, 0))
        ctk.CTkButton(footer, text=t("gui_cancel"), fg_color=CARD, hover_color=BORDER, text_color=FG, border_width=1, border_color=BORDER, command=root.destroy).pack(side="right")

        root.update_idletasks()
        root.geometry("480x600")
        _center_window(root)
        root.mainloop()

    threading.Thread(target=_run, daemon=True).start()

def open_settings_gui(current_config: dict) -> None:
    if CTK_AVAILABLE:
        _open_settings_gui_ctk(current_config)
    else:
        logger.warning("customtkinter not found – using legacy settings GUI")
        _open_settings_gui_legacy(current_config)
