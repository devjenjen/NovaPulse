from src.core.constants import SOUNDS_DIR, APP_NAME, logger

try:
    from windows_toasts import WindowsToaster, ToastText1
    WIN_TOASTS_AVAILABLE = True
except ImportError:
    WIN_TOASTS_AVAILABLE = False

def play_sound(filename: str) -> None:
    if not filename or filename.lower() == "none":
        return
    try:
        sound_path = (SOUNDS_DIR / filename).resolve()
        # Prevent path traversal
        if not sound_path.is_relative_to(SOUNDS_DIR.resolve()):
            logger.error(f"Invalid sound path (traversal attempt?): {filename}")
            return
        if not sound_path.exists():
            logger.warning(f"Sound file not found: {sound_path}")
            return
            
        import winsound
        winsound.PlaySound(str(sound_path), winsound.SND_FILENAME | winsound.SND_ASYNC)
    except Exception as e:
        logger.error(f"Failed to play sound {filename}: {e}")

def send_notification(title: str, message: str) -> None:
    """Send a Windows toast notification; falls back to MessageBox if windows-toasts is missing."""
    if WIN_TOASTS_AVAILABLE:
        try:
            toaster = WindowsToaster(APP_NAME)
            new_toast = ToastText1()
            new_toast.SetBody(f"{title}\n{message}")
            toaster.show_toast(new_toast)
            logger.info(f"Notification sent via windows-toasts: {title}")
            return
        except Exception as e:
            logger.error(f"windows-toasts error: {e}")
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, message, title, 0x40)
    except Exception as e:
        logger.error(f"Fallback notification error: {e}")
