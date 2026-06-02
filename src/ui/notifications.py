from src.core.constants import SOUNDS_DIR, APP_NAME, logger

try:
    from windows_toasts import InteractableWindowsToaster, Toast, ToastButton
    WIN_TOASTS_AVAILABLE = True
except ImportError:
    WIN_TOASTS_AVAILABLE = False

import os
import time

try:
    os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
    import pygame
    pygame.mixer.init()
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

def is_dnd_active() -> bool:
    """Check if a fullscreen app is active (Game/DND mode)."""
    try:
        import ctypes
        from ctypes import wintypes
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        if not hwnd or hwnd in (user32.GetDesktopWindow(), user32.GetShellWindow()): 
            return False
        
        rect = wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        
        screen_width = user32.GetSystemMetrics(0)
        screen_height = user32.GetSystemMetrics(1)
        
        return (rect.right - rect.left == screen_width and rect.bottom - rect.top == screen_height)
    except Exception as e:
        logger.error(f"DND check error: {e}")
        return False

def play_sound(filename: str, dnd_enabled: bool = False) -> None:
    if not filename or filename.lower() == "none":
        return
        
    if dnd_enabled and is_dnd_active():
        logger.info("DND mode active (fullscreen detected): suppressing audio")
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
            
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.music.load(str(sound_path))
                pygame.mixer.music.play()
                return
            except Exception as e:
                logger.error(f"pygame playback failed: {e}")
        
        # Fallback to winsound for wav
        if str(sound_path).lower().endswith('.wav'):
            import winsound
            winsound.PlaySound(str(sound_path), winsound.SND_FILENAME | winsound.SND_ASYNC)
    except Exception as e:
        logger.error(f"Failed to play sound {filename}: {e}")

def send_notification(title: str, message: str, snooze_callback=None) -> None:
    """Send a Windows toast notification; falls back to MessageBox if windows-toasts is missing."""
    if WIN_TOASTS_AVAILABLE:
        try:
            toaster = InteractableWindowsToaster(APP_NAME)
            new_toast = Toast()
            new_toast.text_fields = [title, message]
            if snooze_callback:
                button = ToastButton("In 30 Minuten nochmal erinnern", arguments="snooze")
                new_toast.AddAction(button)
                def on_activated(args):
                    if getattr(args, 'arguments', None) == "snooze":
                        snooze_callback()
                new_toast.on_activated = on_activated
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
