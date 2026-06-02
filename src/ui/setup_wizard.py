import json
from src.core.constants import CONFIG_FILE, logger
from src.core.i18n import _STRINGS
from src.api.gg_engine import find_transmitter_id

def _ask_language_and_save_cli() -> None:
    prompt = _STRINGS["en"]["lang_prompt"]
    try:
        choice = input(prompt).strip()
    except Exception:
        choice = "1"
    lang = "de" if choice == "2" else "en"
    
    # We must load defaults here dynamically to avoid circular import if config.py imports this
    from src.core.config import DEFAULT_CONFIG
    config = DEFAULT_CONFIG.copy()
    config["language"] = lang
    CONFIG_FILE.write_text(json.dumps(config, indent=4), encoding="utf-8")
    print(f"[INFO] Language set to '{lang}'. Config saved: {CONFIG_FILE}")

def run_setup_wizard() -> None:
    try:
        import customtkinter as ctk
        CTK_AVAILABLE = True
    except ImportError:
        CTK_AVAILABLE = False
        
    if not CTK_AVAILABLE:
        _ask_language_and_save_cli()
        return

    from src.core.config import DEFAULT_CONFIG
    from src.ui.settings import _center_window

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    root = ctk.CTk()
    root.title("NovaPulse Setup")
    root.geometry("500x350")
    root.resizable(False, False)
    _center_window(root)
    
    config = DEFAULT_CONFIG.copy()
    f1 = ctk.CTkFrame(root, fg_color="transparent")
    ctk.CTkLabel(f1, text="Welcome to NovaPulse", font=("Segoe UI", 24, "bold")).pack(pady=(40, 20))
    ctk.CTkLabel(f1, text="Please select your language / Bitte Sprache wählen:").pack(pady=10)
    
    lang_var = ctk.StringVar(value="en")
    ctk.CTkSegmentedButton(f1, values=["en", "de"], variable=lang_var).pack(pady=10)
    
    f2 = ctk.CTkFrame(root, fg_color="transparent")
    ctk.CTkLabel(f2, text="Locating SteelSeries GG Engine...", font=("Segoe UI", 18, "bold")).pack(pady=(60, 20))
    status_lbl = ctk.CTkLabel(f2, text="Searching...", text_color="#f59e0b")
    status_lbl.pack(pady=10)
    
    progress = ctk.CTkProgressBar(f2, mode="indeterminate", width=300)
    progress.pack(pady=20)
    next_btn = ctk.CTkButton(f2, text="Finish Setup", state="disabled", command=root.destroy)
    next_btn.pack(pady=20)
    
    def search_engine():
        progress.start()
        def _check():
            tx_id = find_transmitter_id()
            progress.stop()
            progress.configure(mode="determinate")
            progress.set(1.0)
            if tx_id is not None:
                status_lbl.configure(text="✅ Engine & Transmitter found!", text_color="#10b981")
            else:
                status_lbl.configure(text="⚠️ Engine found, but no transmitter detected.\nMake sure your headset is connected.", text_color="#f59e0b")
            next_btn.configure(state="normal")
            CONFIG_FILE.write_text(json.dumps(config, indent=4), encoding="utf-8")
            logger.info("Setup wizard completed.")
        root.after(1500, _check)
        
    def next_to_2():
        config["language"] = lang_var.get()
        f1.pack_forget()
        f2.pack(fill="both", expand=True)
        search_engine()
        
    ctk.CTkButton(f1, text="Next", command=next_to_2).pack(pady=30)
    f1.pack(fill="both", expand=True)
    root.mainloop()
