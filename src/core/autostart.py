import sys
import winreg
from pathlib import Path
from contextlib import contextmanager
from src.core.constants import APP_NAME, logger

_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"

@contextmanager
def _reg_key(access: int):
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, access)
    try:
        yield key
    finally:
        winreg.CloseKey(key)

def _exe_path() -> Path:
    return Path(sys.executable) if getattr(sys, "frozen", False) else Path(sys.argv[0]).resolve()

def is_autostart_enabled() -> bool:
    try:
        with _reg_key(winreg.KEY_READ) as key:
            winreg.QueryValueEx(key, APP_NAME)
        return True
    except FileNotFoundError:
        return False

def enable_autostart() -> None:
    try:
        with _reg_key(winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, f'"{_exe_path()}"')
        logger.info("Autostart enabled")
    except Exception as e:
        logger.error(f"Could not enable autostart: {e}")

def disable_autostart() -> None:
    try:
        with _reg_key(winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, APP_NAME)
        logger.info("Autostart disabled")
    except FileNotFoundError:
        pass
    except Exception as e:
        logger.error(f"Could not disable autostart: {e}")
