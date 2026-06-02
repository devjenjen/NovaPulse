import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import threading
import time
import traceback
from src.core.constants import APP_NAME, VERSION, CONFIG_FILE, CRASH_LOG, DB_FILE, logger, crash_logger
from src.core.config import load_config
from src.core.autostart import is_autostart_enabled
from src.core.updater import check_for_updates
from src.core.utils import acquire_instance_lock
from src.api.gg_engine import get_base_url
from src.api.gamesense import register_gamesense, trigger_hardware_alert
from src.monitor.database import init_db
from src.monitor.battery_monitor import monitor_loop, get_current_data
from src.ui.tray import TrayApp, TRAY_AVAILABLE
from src.ui.notifications import WIN_TOASTS_AVAILABLE
from src.ui.settings import test_low_battery, test_charger_full, open_settings_gui

try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False

_mini_status_running = False

def toggle_mini_status():
    global _mini_status_running
    try:
        import customtkinter as ctk
        from src.ui.mini_status import MiniStatusWindow
    except ImportError:
        return
        
    if _mini_status_running:
        return
    _mini_status_running = True
    
    try:
        root = ctk.CTk()
        root.withdraw()
        
        def on_close():
            global _mini_status_running
            _mini_status_running = False
            root.destroy()
            
        def fetch_data():
            # h, c, s
            return get_current_data()
            
        h, c, s = fetch_data()

        win = MiniStatusWindow(root, db_file=DB_FILE, headset_pct=h, 
                               charger_pct=c, charging_status=s,
                               refresh_callback=fetch_data)
        win.protocol("WM_DELETE_WINDOW", on_close)
        win.show()
        root.mainloop()
    except Exception as e:
        logger.error(f"Failed to show mini status: {e}")
        _mini_status_running = False

def main() -> None:
    if not acquire_instance_lock():
        print("[WARNING] Another instance is already running. Exiting.")
        sys.exit(0)

    config = load_config()
    init_db()

    logger.info("=" * 52)
    logger.info(f"{APP_NAME} v{VERSION} started")
    logger.info(f"  Language           : {config.get('language', 'en')}")
    logger.info(f"  Config             : {CONFIG_FILE}")
    logger.info(f"  GG API URL         : {get_base_url()}")
    logger.info(f"  Headset warning at : <= {config['low_threshold']}%")
    logger.info(f"  Charger notify at  : =  {config['full_level']}%")
    logger.info(f"  Poll interval      : {config['poll_interval']}s")
    logger.info(f"  windows-toasts     : {'available' if WIN_TOASTS_AVAILABLE else 'NOT installed'}")
    logger.info(f"  pystray            : {'available' if TRAY_AVAILABLE else 'NOT installed'}")
    logger.info(f"  Autostart          : {'enabled' if is_autostart_enabled() else 'disabled'}")
    logger.info("=" * 52)

    if KEYBOARD_AVAILABLE and config.get("hotkey"):
        try:
            keyboard.add_hotkey(config["hotkey"], toggle_mini_status)
            logger.info(f"Registered global hotkey: {config['hotkey']}")
        except Exception as e:
            logger.error(f"Failed to register hotkey: {e}")

    tray = TrayApp()
    t_thread = threading.Thread(target=monitor_loop, args=(config, tray), daemon=True)
    register_gamesense()
    check_for_updates(config)
    t_thread.start()
    tray.run()

    if not TRAY_AVAILABLE:
        t_thread.join()

if __name__ == "__main__":
    args = sys.argv[1:]

    if "--test-low" in args:
        test_low_battery()
        sys.exit(0)
    if "--test-full" in args:
        test_charger_full()
        sys.exit(0)
    if "--test-hardware" in args:
        register_gamesense()
        trigger_hardware_alert(12)
        sys.exit(0)
    if "--settings" in args:
        config = load_config()
        open_settings_gui(config)
        while threading.active_count() > 1:
            time.sleep(0.1)
        sys.exit(0)

    try:
        main()
    except Exception:
        msg = traceback.format_exc()
        crash_logger.error("Unhandled exception:\n" + msg)
        logger.error(f"Fatal error – details in: {CRASH_LOG}")
        sys.exit(1)
