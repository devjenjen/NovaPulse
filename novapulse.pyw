"""
NovaPulse – SteelSeries GG Battery Monitor
===========================================
Monitors SteelSeries headset battery levels via the GG Engine API and sends
Windows toast notifications for low headset battery and fully charged spare.

Requirements:
    pip install requests windows-toasts pystray pillow customtkinter

GitHub: https://github.com/devjenjen/NovaPulse
"""

import json
import logging
import os
import socket
import sqlite3
import sys
import threading
import time
import traceback
import winreg
from contextlib import contextmanager
from logging.handlers import RotatingFileHandler
from pathlib import Path

import requests
import urllib3

try:
    from windows_toasts import WindowsToaster, ToastText1
    WIN_TOASTS_AVAILABLE = True
except ImportError:
    WIN_TOASTS_AVAILABLE = False

try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False

# SteelSeries GG uses a self-signed cert on localhost – no security risk.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# ── Constants ──────────────────────────────────────────────────────────────────

APP_NAME    = "NovaPulse"
VERSION     = "0.1.0"
APP_DIR     = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "NovaPulse"
CONFIG_FILE = APP_DIR / "config.json"
LOG_FILE    = APP_DIR / "novapulse.log"
CRASH_LOG   = APP_DIR / "crash.log"
DB_FILE     = APP_DIR / "history.db"
SOUNDS_DIR  = APP_DIR / "sounds"
CORE_PROPS  = (
    Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData"))
    / "SteelSeries" / "SteelSeries Engine 3" / "coreProps.json"
)
CORE_PROPS_GG = (
    Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData"))
    / "SteelSeries" / "GG" / "apps" / "engine" / "coreProps.json"
)
GITHUB_RELEASES_URL = "https://api.github.com/repos/devjenjen/NovaPulse/releases/latest"

APP_DIR.mkdir(parents=True, exist_ok=True)
SOUNDS_DIR.mkdir(parents=True, exist_ok=True)

# ── i18n ───────────────────────────────────────────────────────────────────────

_STRINGS = {
    "en": {
        "gui_title":            "NovaPulse Settings",
        "headset_low_title":    "Headset battery low: {pct}%",
        "headset_low_msg":      "Your headset has only {pct}% battery left.\nPlease swap or charge the battery soon.",
        "charger_full_title":   "Spare battery fully charged",
        "charger_full_msg":     "The battery in the charger dock is at 100%.\nYou can now swap it into your headset.",
        "autostart_on":         "Autostart enabled. App will start with Windows.",
        "autostart_off":        "Autostart disabled.",
        "tray_status_offline":  "Device offline – standby",
        "tray_menu_settings":   "Settings",
        "tray_menu_autostart":  "{check} Start with Windows",
        "tray_menu_config":     "Open config.json",
        "tray_menu_log":        "Open log file",
        "tray_menu_quit":       "Quit",
        "tray_tooltip":         "Headset: {h}%  |  Charger: {c}%",
        "test_low_title":       "Headset battery low: 20%  [TEST]",
        "test_low_msg":         "TEST: This is what the low-battery alert looks like.",
        "test_full_title":      "Spare battery fully charged  [TEST]",
        "test_full_msg":        "TEST: This is what the charger notification looks like.",
        "lang_prompt":          "Choose language / Sprache wählen:\n  1 – English\n  2 – Deutsch\n> ",
        "gui_save":             "Save & Close",
        "gui_cancel":           "Cancel",
        "gui_restart_required": "Restart required to apply changes",
        "gui_language":         "Language",
        "gui_poll_interval":    "Poll interval (seconds)",
        "gui_autostart":        "Start with Windows",
        "gui_auto_update":      "Check for updates on startup",
        "gui_low_threshold":      "Tier 1 warning threshold (%)",
        "gui_low_note":           "Recommended: 25  (GG API step value)",
        "gui_critical_threshold": "Tier 2 warning threshold (%)",
        "gui_critical_note":      "Recommended: 12  (last step before 0%)",
        "gui_full_level":         "Charger full notification at (%)",
        "gui_test_low":           "Test Tier 1",
        "gui_test_critical":      "Test Tier 2",
        "gui_test_full":          "Test Charger",
        "gui_sounds_info":        "FUN OPTION - completely optional!\n\nDrop any .wav file into the sounds folder and enter its filename below.\nLeave blank = Windows default beep    |    type 'none' = silence.",
        "gui_sound_tier1":        "Sound for Tier 1 alert (25%)",
        "gui_sound_tier2":        "Sound for Tier 2 alert (12%)",
        "gui_sound_charger":      "Sound when charger is full",
        "gui_open_sounds_folder": "Open sounds folder",
        "gui_startup_grace":      "Startup grace period (seconds)",
        "gui_standby_fast":       "Standby fast-retry interval (s)",
        "gui_standby_count":      "Standby fast-retry count",
        "gui_standby_slow":       "Standby slow-retry interval (s)",
        "gui_hardware_alert":     "Hardware OLED Alert (on base station)",
    },
    "de": {
        "gui_title":            "NovaPulse Einstellungen",
        "headset_low_title":    "Headset-Akku schwach: {pct}%",
        "headset_low_msg":      "Dein Headset hat nur noch {pct}% Akku.\nBitte bald tauschen oder laden.",
        "charger_full_title":   "Ersatzakku vollständig geladen",
        "charger_full_msg":     "Der Akku in der Ladestation ist bei 100%.\nDu kannst ihn jetzt ins Headset einlegen.",
        "autostart_on":         "Autostart aktiviert. App startet mit Windows.",
        "autostart_off":        "Autostart deaktiviert.",
        "tray_status_offline":  "Gerät offline – Standby",
        "tray_menu_settings":   "Einstellungen",
        "tray_menu_autostart":  "{check} Mit Windows starten",
        "tray_menu_config":     "config.json öffnen",
        "tray_menu_log":        "Log-Datei öffnen",
        "tray_menu_quit":       "Beenden",
        "tray_tooltip":         "Headset: {h}%  |  Ladegerät: {c}%",
        "test_low_title":       "Headset-Akku schwach: 20%  [TEST]",
        "test_low_msg":         "TEST: So sieht die Niedrig-Akku-Meldung aus.",
        "test_full_title":      "Ersatzakku vollständig geladen  [TEST]",
        "test_full_msg":        "TEST: So sieht die Ladegerät-Benachrichtigung aus.",
        "lang_prompt":          "Choose language / Sprache wählen:\n  1 – English\n  2 – Deutsch\n> ",
        "gui_save":             "Speichern & Schließen",
        "gui_cancel":           "Abbrechen",
        "gui_restart_required": "Neustart erforderlich zum Anwenden",
        "gui_language":         "Sprache",
        "gui_poll_interval":    "Abfrageintervall (Sekunden)",
        "gui_autostart":        "Mit Windows starten",
        "gui_auto_update":      "Beim Start auf Updates prüfen",
        "gui_low_threshold":      "Stufe 1 Warnschwelle (%)",
        "gui_low_note":           "Empfohlen: 25  (GG-API-Stufe)",
        "gui_critical_threshold": "Stufe 2 Warnschwelle (%)",
        "gui_critical_note":      "Empfohlen: 12  (letzte Stufe vor 0%)",
        "gui_full_level":         "Ladegerät-Benachrichtigung bei (%)",
        "gui_test_low":           "Test Stufe 1",
        "gui_test_critical":      "Test Stufe 2",
        "gui_test_full":          "Test Ladegerät",
        "gui_sounds_info":        "FUN OPTION - vollkommen optional!\n\nLege eine .wav-Datei in den Sound-Ordner und trage den Dateinamen unten ein.\nLeer lassen = Windows-Standardton    |    'none' eingeben = kein Ton.",
        "gui_sound_tier1":        "Sound für Stufe 1 (25%)",
        "gui_sound_tier2":        "Sound für Stufe 2 (12%)",
        "gui_sound_charger":      "Sound wenn Ladegerät voll",
        "gui_open_sounds_folder": "Sound-Ordner öffnen",
        "gui_startup_grace":      "Wartezeit bei Start (Sekunden)",
        "gui_standby_fast":       "Standby Schnell-Retry (s)",
        "gui_standby_count":      "Standby Schnell-Retry Anzahl",
        "gui_standby_slow":       "Standby Langsam-Retry (s)",
        "gui_hardware_alert":     "Hardware OLED Alert (auf Basisstation)",
    },
}

def t(key: str, **kwargs) -> str:
    """Return a translated string for the active language."""
    lang = _cfg_lang()
    text = _STRINGS.get(lang, _STRINGS["en"]).get(key, key)
    return text.format(**kwargs) if kwargs else text

def _cfg_lang() -> str:
    """Read language from config, fallback to 'en'."""
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        return data.get("language", "en")
    except Exception:
        return "en"


# ── Default config ─────────────────────────────────────────────────────────────

DEFAULT_CONFIG = {
    "language":           "en",   # "en" or "de"
    "poll_interval":       60,    # seconds between battery checks
    "low_threshold":       25,    # warn when headset battery <= this (%)
    "critical_threshold":  12,    # critical alert threshold (%)
    "full_level":         100,    # notify when charger reaches this (%)
    "startup_grace":       10,    # wait on first launch for GG to boot
    "standby_retry_fast":  15,    # fast retry interval after going offline
    "standby_fast_count":   8,    # how many fast retries before slowing down
    "standby_retry_slow": 300,    # slow retry interval
    "auto_check_updates":  True,  # check GitHub Releases API on startup
    "hardware_alert":      True,  # trigger GameSense OLED alert
}


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        _ask_language_and_save()
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        config = DEFAULT_CONFIG.copy()
        config.update(data)
        if config.keys() != data.keys():
            CONFIG_FILE.write_text(json.dumps(config, indent=4), encoding="utf-8")
        return config
    except json.JSONDecodeError as e:
        print(f"[ERROR] Corrupt config.json ({e}) – using defaults")
        return DEFAULT_CONFIG.copy()
    except Exception as e:
        print(f"[WARNING] Could not read config.json ({e}) – using defaults")
        return DEFAULT_CONFIG.copy()


def _ask_language_and_save() -> None:
    """Prompt the user once on first launch to choose a language."""
    prompt = _STRINGS["en"]["lang_prompt"]
    try:
        choice = input(prompt).strip()
    except Exception:
        choice = "1"
    lang = "de" if choice == "2" else "en"
    config = DEFAULT_CONFIG.copy()
    config["language"] = lang
    CONFIG_FILE.write_text(json.dumps(config, indent=4), encoding="utf-8")
    print(f"[INFO] Language set to '{lang}'. Config saved: {CONFIG_FILE}")


# ── Logging ────────────────────────────────────────────────────────────────────

def _make_rotating_handler(path: Path) -> RotatingFileHandler:
    h = RotatingFileHandler(path, maxBytes=1_048_576, backupCount=2, encoding="utf-8")
    h.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)-8s %(message)s",
                                     datefmt="%Y-%m-%d %H:%M:%S"))
    return h


logger = logging.getLogger("novapulse")
logger.setLevel(logging.DEBUG)
logger.addHandler(_make_rotating_handler(LOG_FILE))
logger.addHandler(logging.StreamHandler(sys.stdout))

crash_logger = logging.getLogger("novapulse.crash")
crash_logger.setLevel(logging.ERROR)
crash_logger.addHandler(_make_rotating_handler(CRASH_LOG))


# ── Single-instance guard ──────────────────────────────────────────────────────
# A bound socket acts as a lightweight mutex – no files or admin rights needed.

_LOCK_PORT   = 47893
_lock_socket = None
_reload_event = threading.Event()

def _acquire_instance_lock() -> bool:
    global _lock_socket
    try:
        _lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _lock_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
        _lock_socket.bind(("127.0.0.1", _LOCK_PORT))
        return True
    except OSError:
        return False


# ── Autostart ──────────────────────────────────────────────────────────────────

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


# ── GG Engine API ──────────────────────────────────────────────────────────────

def _get_engine_data() -> dict | None:
    for p in [CORE_PROPS_GG, CORE_PROPS]:
        if p.exists():
            try:
                return json.loads(p.read_text())
            except Exception as e:
                logger.warning(f"Could not read {p}: {e}")
    return None


def get_base_url(use_https: bool = True) -> str:
    data = _get_engine_data()
    if data:
        key = "encryptedAddress" if use_https else "address"
        addr = data.get(key)
        if addr:
            proto = "https" if use_https else "http"
            return f"{proto}://{addr}"
    return "https://127.0.0.1:52640" if use_https else "http://127.0.0.1:52639"


def find_transmitter_id() -> int | None:
    """Dynamically find the transmitter device ID – avoids hardcoded IDs."""
    try:
        r = requests.get(f"{get_base_url()}/devices", verify=False, timeout=5,
                         headers={"Content-Type": "application/json"})
        r.raise_for_status()
        devices = r.json().get("devices", [])
        # Primary: match by known device name pattern
        for d in devices:
            if "nova_pro_wireless_tx" in d.get("name", "").lower():
                logger.info(f"Found transmitter: id={d['id']}  name={d['name']}")
                return d["id"]
        # Fallback: first connected type-3 device
        for d in devices:
            if d.get("connected") and d.get("type") == 3:
                logger.info(f"Fallback transmitter: id={d['id']}  name={d['name']}")
                return d["id"]
    except Exception as e:
        logger.debug(f"Device discovery failed: {e}")
    return None


# ── GameSense OLED ─────────────────────────────────────────────────────────────

def _get_gs_url() -> str:
    return get_base_url().replace("https://", "http://")


def register_gamesense() -> None:
    try:
        requests.post(f"{_get_gs_url()}/register_game", json={
            "game": "NOVAPULSE",
            "game_display_name": APP_NAME,
            "developer": "devjenjen"
        }, timeout=2)

        # 2. Bind OLED Event
        blink_frame_on = {
            "has-text": True,
            "lines": [
                {"has-text": True, "prefix": "!!! SWAP AKKU !!!", "bold": True},
                {"has-text": True, "prefix": "Headset: ", "context-frame-key": "pct", "suffix": "%"}
            ],
            "length-millis": 800
        }
        blink_frame_off = {
            "has-text": True,
            "lines": [{"has-text": False}, {"has-text": False}],
            "length-millis": 400
        }

        requests.post(f"{_get_gs_url()}/bind_game_event", json={
            "game": "NOVAPULSE",
            "event": "BATTERY_CRITICAL",
            "min_value": 0,
            "max_value": 100,
            "icon_id": 15,
            "handlers": [{
                "device-type": "screened",
                "zone": "one",
                "mode": "screen",
                "datas": [
                    blink_frame_on, blink_frame_off,
                    blink_frame_on, blink_frame_off,
                    blink_frame_on
                ]
            }]
        }, timeout=2)
    except Exception as e:
        logger.debug(f"GameSense registration failed: {e}")


def trigger_hardware_alert(pct: int) -> None:
    try:
        requests.post(f"{_get_gs_url()}/game_event", json={
            "game": "NOVAPULSE",
            "event": "BATTERY_CRITICAL",
            "data": {
                "value": pct,
                "frame": {"pct": str(pct)}
            }
        }, timeout=2)
        logger.info(f"Hardware alert sent to OLED: {pct}%")
    except Exception as e:
        logger.debug(f"Hardware alert failed: {e}")


def read_battery(tx_id: int) -> dict | None:
    """Fetch current battery status from the GG Engine API."""
    try:
        r = requests.post(
            f"{get_base_url()}/device/{tx_id}/function/read_battery_status",
            verify=False, timeout=5,
            headers={"Content-Type": "application/json"},
            json={},
        )
        r.raise_for_status()
        data = json.loads(r.json()["function_data"])
        return {
            "headset_pct": data["headset_battery_level"]["level"],
            "charger_pct": data["charger_battery_level"]["level"],
            "charging":    data["charging_status"]["chargingStatus"],
        }
    except requests.exceptions.ConnectionError:
        return None
    except KeyError as e:
        logger.error(f"Unexpected API response – missing key: {e}")
        return None
    except Exception as e:
        logger.error(f"Read error: {e}")
        return None


# ── Notifications ──────────────────────────────────────────────────────────────

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


def _check_for_updates(config: dict) -> None:
    if not config.get("auto_check_updates", True):
        return
    try:
        logger.info("Checking for updates...")
        r = requests.get(GITHUB_RELEASES_URL, timeout=3)
        r.raise_for_status()
        latest = r.json().get("tag_name", "")
        if latest and latest != f"v{VERSION}":
            logger.info(f"Update available: {latest} (Current: v{VERSION})")
            send_notification(f"Update Available: {latest}", f"NovaPulse {latest} is available on GitHub.")
    except Exception as e:
        logger.debug(f"Update check failed: {e}")


# ── Tray icon ──────────────────────────────────────────────────────────────────

_COLOR_GREEN  = "#27ae60"
_COLOR_YELLOW = "#f39c12"
_COLOR_RED    = "#e74c3c"
_COLOR_GREY   = "#7f8c8d"

def _battery_color(pct: int, offline: bool = False) -> str:
    if offline:  return _COLOR_GREY
    if pct <= 20: return _COLOR_RED
    if pct <= 60: return _COLOR_YELLOW
    return _COLOR_GREEN

def _hex_to_rgba(hex_color: str, alpha: int = 255) -> tuple:
    h = hex_color.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), alpha)


def _create_tray_icon(color: str = _COLOR_GREY) -> "Image.Image":
    """
    Draw a headset-shaped tray icon at 256x256px.
    Color signals battery status: green > 60%, yellow 21-60%, red <= 20%, grey = offline.
    Hover the tray icon to see exact battery percentages.
    """
    size = 256
    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    s    = size / 64
    rim  = _hex_to_rgba(color, 255)
    fill = _hex_to_rgba(color, 80)
    rad  = int(4 * s)
    lw   = max(2, int(2 * s))

    # Headband arc – thick stroke built from stacked 1px arcs
    cx, cy = int(32 * s), int(30 * s)
    arc_r  = int(18 * s)
    for offset in range(max(1, int(5 * s))):
        ri = arc_r - offset
        draw.arc([cx - ri, cy - ri, cx + ri, cy + ri], start=180, end=0, fill=rim, width=1)

    # Ear cups (left and right)
    for x1, y1, x2, y2 in [(int(7*s), int(28*s), int(18*s), int(44*s)),
                             (int(46*s), int(28*s), int(57*s), int(44*s))]:
        draw.rounded_rectangle([x1, y1, x2, y2], radius=rad, fill=fill, outline=rim, width=lw)

    return img


class TrayApp:
    """System tray icon with right-click context menu."""

    def __init__(self):
        self._status  = "Starting..."
        self._icon    = None

    def set_status(self, headset: int, charger: int, charging: str) -> None:
        charge_mark  = " ⚡" if charging == "CHARGING" else ""
        self._status = f"Headset:  {headset}%{charge_mark}\nCharger:  {charger}%"
        if self._icon:
            self._icon.icon  = _create_tray_icon(_battery_color(headset))
            self._icon.title = t("tray_tooltip", h=headset, c=charger)

    def set_standby(self) -> None:
        self._status = t("tray_status_offline")
        if self._icon:
            self._icon.icon  = _create_tray_icon(_COLOR_GREY)
            self._icon.title = self._status

    def _toggle_autostart(self, icon, item) -> None:
        if is_autostart_enabled():
            disable_autostart()
            send_notification(APP_NAME, t("autostart_off"))
        else:
            enable_autostart()
            send_notification(APP_NAME, t("autostart_on"))

    def _open_config(self, icon, item) -> None:
        os.startfile(str(CONFIG_FILE))

    def _open_log(self, icon, item) -> None:
        os.startfile(str(LOG_FILE))

    def _on_settings(self, icon=None, item=None) -> None:
        config = load_config()
        open_settings_gui(config)

    def _quit(self, icon, item) -> None:
        logger.info("Quit via tray menu.")
        icon.stop()
        os._exit(0)

    def run(self) -> None:
        if not TRAY_AVAILABLE:
            logger.warning("pystray/Pillow not installed – tray disabled.")
            return

        menu = pystray.Menu(
            pystray.MenuItem(f"{APP_NAME}  v{VERSION}", None, enabled=False),
            pystray.MenuItem(lambda _: self._status, None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(lambda _: t("tray_menu_settings"), self._on_settings, default=True),
            pystray.MenuItem(
                lambda _: t("tray_menu_autostart", check="✓" if is_autostart_enabled() else "✗"),
                self._toggle_autostart,
            ),
            pystray.MenuItem(lambda _: t("tray_menu_config"), self._open_config),
            pystray.MenuItem(lambda _: t("tray_menu_log"),    self._open_log),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(lambda _: t("tray_menu_quit"), self._quit),
        )
        self._icon = pystray.Icon(
            APP_NAME, 
            icon=_create_tray_icon(_COLOR_GREY), 
            title=APP_NAME, 
            menu=menu
        )
        # Handle double-click/activation on the icon itself
        self._icon.run()


# ── Battery state machine ──────────────────────────────────────────────────────

class BatteryMonitor:
    """Tracks battery state across poll cycles to prevent duplicate notifications."""

    def __init__(self, config: dict):
        self.config                = config
        self.low_threshold         = config["low_threshold"]
        self.critical_threshold    = config["critical_threshold"]
        self.full_level            = config["full_level"]
        self.headset_low_notified  = False
        self.charger_full_notified = False
        self.last_charger_pct: int | None = None

    def reload_config(self, config: dict) -> None:
        self.config             = config
        self.low_threshold      = config["low_threshold"]
        self.critical_threshold = config["critical_threshold"]
        self.full_level         = config["full_level"]

    def update(self, data: dict) -> None:
        headset = data["headset_pct"]
        charger = data["charger_pct"]

        if headset <= self.low_threshold and not self.headset_low_notified:
            send_notification(
                t("headset_low_title", pct=headset),
                t("headset_low_msg",   pct=headset),
            )
            # Play appropriate sound
            if headset <= self.critical_threshold:
                play_sound(self.config.get("sound_tier2", ""))
            else:
                play_sound(self.config.get("sound_tier1", ""))

            if headset <= 12: # Standard critical threshold for hardware alert
                trigger_hardware_alert(headset)
            self.headset_low_notified = True
            logger.warning(f"Headset battery low: {headset}%")

        if headset > self.low_threshold + 5:
            self.headset_low_notified = False

        if (
            charger >= self.full_level
            and self.last_charger_pct is not None
            and self.last_charger_pct < self.full_level
            and not self.charger_full_notified
        ):
            send_notification(t("charger_full_title"), t("charger_full_msg"))
            play_sound(self.config.get("sound_charger_full", ""))
            self.charger_full_notified = True
            logger.info("Charger battery reached 100%")

        if charger < self.full_level - 5:
            self.charger_full_notified = False

        self.last_charger_pct = charger


# ── Main loop ──────────────────────────────────────────────────────────────────

def monitor_loop(config: dict, tray: TrayApp) -> None:
    startup_grace      = config["startup_grace"]
    standby_retry_fast = config["standby_retry_fast"]
    standby_retry_slow = config["standby_retry_slow"]
    standby_fast_count = config["standby_fast_count"]

    logger.info(f"Waiting {startup_grace}s for SteelSeries GG to become ready...")
    time.sleep(startup_grace)

    monitor       = BatteryMonitor(config)
    tx_id         = find_transmitter_id()
    gg_was_down   = False
    offline_count = 0

    while True:
        if _reload_event.is_set():
            _reload_event.clear()
            config.update(load_config())
            monitor.reload_config(config)

        if tx_id is None:
            tx_id = find_transmitter_id()

        data = read_battery(tx_id) if tx_id is not None else None

        if data is None:
            if not gg_was_down:
                logger.warning("SteelSeries GG not reachable – entering standby...")
                gg_was_down = True
            offline_count += 1
            tx_id = None
            tray.set_standby()
            sleep_time = standby_retry_fast if offline_count <= standby_fast_count else standby_retry_slow
            _reload_event.wait(sleep_time)
        else:
            if gg_was_down:
                logger.info(f"GG reconnected after {offline_count} retries – resuming polling")
                gg_was_down   = False
                offline_count = 0

            # GG reports headset_pct=0 + UNKNOWN status when headset is powered off, not truly empty.
            if data["headset_pct"] == 0 and data["charging"] == "UNKNOWN_OR_HEADSET_NOT_CONNECTED":
                logger.debug("Headset not connected or powered off – skipping update")
                tray.set_status(data["headset_pct"], data["charger_pct"], data["charging"])
                _reload_event.wait(config["poll_interval"])
                continue

            logger.info(
                f"Headset: {data['headset_pct']:3d}%  |  "
                f"Charger: {data['charger_pct']:3d}%  |  "
                f"Status: {data['charging']}"
            )
            tray.set_status(data["headset_pct"], data["charger_pct"], data["charging"])
            monitor.update(data)
            log_battery(data["headset_pct"], data["charger_pct"])
            _reload_event.wait(config["poll_interval"])


# ── Test helpers ───────────────────────────────────────────────────────────────

def test_low_battery() -> None:
    send_notification(t("test_low_title"), t("test_low_msg"))

def test_charger_full() -> None:
    send_notification(t("test_full_title"), t("test_full_msg"))


# ── Settings GUI ───────────────────────────────────────────────────────────────

def _center_window(win) -> None:
    """Center a tkinter/CTk window on the primary screen."""
    win.update_idletasks()
    w = win.winfo_reqwidth()
    h = win.winfo_reqheight()
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    win.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")


def _open_settings_gui_legacy(current_config: dict) -> None:
    """Legacy tkinter/ttk settings window. Used as fallback if customtkinter is unavailable."""
    import tkinter as tk
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
    """customtkinter settings window – dark navy/purple theme."""
    import tkinter as tk
    import customtkinter as ctk

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

        # ── Gradient header ────────────────────────────────────────────
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
            hdr.create_text(20, 27, anchor="w", text=f"  {APP_NAME}",
                            fill="#ffffff", font=("Segoe UI", 15, "bold"))
            hdr.create_text(460, 27, anchor="e", text=f"v{VERSION}",
                            fill="#c4b5fd", font=("Segoe UI", 9))

        hdr.bind("<Configure>", _draw_header)

        # ── Tabview ────────────────────────────────────────────────────
        tabview = ctk.CTkTabview(
            root,
            fg_color=BG,
            segmented_button_fg_color=CARD,
            segmented_button_selected_color=ACCENT,
            segmented_button_selected_hover_color=ACCENT,
            segmented_button_unselected_color=CARD,
            segmented_button_unselected_hover_color=BORDER,
            text_color=FG,
            text_color_disabled=MUTED,
        )
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

        # ── Tab content ────────────────────────────────────────────────
        def _create_card(parent, title: str):
            card = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=12)
            card.pack(fill="x", padx=20, pady=(0, 16))
            ctk.CTkLabel(card, text=title.upper(), text_color=ACCENT, 
                         font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=16, pady=(12, 8))
            return card

        def _create_row(parent, label: str):
            row = ctk.CTkFrame(parent, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=(0, 12))
            ctk.CTkLabel(row, text=label, text_color=FG).pack(side="left")
            return row

        # ── Tab: General ──
        # Card 1: Localization
        c_lang = _create_card(f_gen, t("gui_language"))
        r_lang = _create_row(c_lang, t("gui_language"))
        lang_var = tk.StringVar(value=cfg.get("language", "en"))
        lang_menu = ctk.CTkSegmentedButton(
            r_lang, values=["en", "de"], variable=lang_var,
            selected_color=ACCENT2, selected_hover_color=ACCENT2,
            unselected_color=ENTRY, unselected_hover_color=BORDER,
        )
        lang_menu.pack(side="right")

        # Card 2: App Behaviour
        c_app = _create_card(f_gen, "App Behaviour")
        
        # Poll Interval
        r_poll = _create_row(c_app, t("gui_poll_interval"))
        poll_var = tk.IntVar(value=cfg.get("poll_interval", 60))
        poll_spin = ctk.CTkEntry(r_poll, textvariable=poll_var, width=60, 
                                 fg_color=ENTRY, border_color=BORDER)
        poll_spin.pack(side="right")

        # Autostart
        r_auto = _create_row(c_app, t("gui_autostart"))
        auto_var = tk.BooleanVar(value=is_autostart_enabled())
        auto_switch = ctk.CTkSwitch(
            r_auto, text="", variable=auto_var,
            progress_color=OK, button_color=FG, button_hover_color="#ffffff"
        )
        auto_switch.pack(side="right")

        # Update Check
        r_upd = _create_row(c_app, t("gui_auto_update"))
        upd_var = tk.BooleanVar(value=cfg.get("auto_check_updates", True))
        upd_switch = ctk.CTkSwitch(
            r_upd, text="", variable=upd_var,
            progress_color=OK, button_color=FG, button_hover_color="#ffffff"
        )
        upd_switch.pack(side="right")

        # ── Tab: Alerts ──
        # Card 1: Headset Alerts
        c_headset = _create_card(f_al, "Headset Alerts")
        
        # Tier 1
        r_t1 = _create_row(c_headset, t("gui_low_threshold"))
        t1_var = tk.IntVar(value=cfg.get("low_threshold", 25))
        t1_spin = ctk.CTkEntry(r_t1, textvariable=t1_var, width=60, fg_color=ENTRY, border_color=BORDER)
        t1_spin.pack(side="right")
        ctk.CTkLabel(c_headset, text=t("gui_low_note"), text_color=MUTED, font=("Segoe UI", 9)).pack(anchor="w", padx=16, pady=(0, 12))

        # Tier 2
        r_t2 = _create_row(c_headset, t("gui_critical_threshold"))
        t2_var = tk.IntVar(value=cfg.get("critical_threshold", 12))
        t2_spin = ctk.CTkEntry(r_t2, textvariable=t2_var, width=60, fg_color=ENTRY, border_color=BORDER)
        t2_spin.pack(side="right")
        ctk.CTkLabel(c_headset, text=t("gui_critical_note"), text_color=MUTED, font=("Segoe UI", 9)).pack(anchor="w", padx=16, pady=(0, 12))

        # GG API Visual Diagram
        diag_frame = ctk.CTkFrame(c_headset, fg_color="transparent")
        diag_frame.pack(fill="x", padx=16, pady=(0, 12))
        diag_cv = tk.Canvas(diag_frame, height=40, bg=CARD, highlightthickness=0)
        diag_cv.pack(fill="x")

        def _draw_diagram(event=None):
            diag_cv.delete("all")
            w = diag_cv.winfo_width() or 400
            steps = [0, 12, 25, 37, 50, 62, 75, 87, 100]
            # Draw base line
            diag_cv.create_line(20, 20, w-20, 20, fill=BORDER, width=2)
            for s in steps:
                x = 20 + (s / 100) * (w - 40)
                color = OK if s > 25 else (WARN if s > 12 else DANGER)
                diag_cv.create_oval(x-4, 16, x+4, 24, fill=color, outline=BG)
                if s in [0, 25, 50, 75, 100]:
                    diag_cv.create_text(x, 32, text=f"{s}%", fill=MUTED, font=("Segoe UI", 7))
        
        diag_cv.bind("<Configure>", _draw_diagram)

        # Card 2: Charger Alert
        c_charger = _create_card(f_al, "Charger Alert")
        r_full = _create_row(c_charger, t("gui_full_level"))
        full_var = tk.IntVar(value=cfg.get("full_level", 100))
        full_spin = ctk.CTkEntry(r_full, textvariable=full_var, width=60, fg_color=ENTRY, border_color=BORDER)
        full_spin.pack(side="right")

        # Card 3: Test Notifications
        c_test = _create_card(f_al, "Test Notifications")
        r_test = ctk.CTkFrame(c_test, fg_color="transparent")
        r_test.pack(fill="x", padx=16, pady=(0, 12))
        
        ctk.CTkButton(r_test, text=t("gui_test_low"), width=100, height=28, fg_color=CARD, border_width=1, border_color=BORDER, command=test_low_battery).pack(side="left", padx=(0, 8))
        # (Using custom test helper for Tier 2 since it's not a top-level function yet)
        def test_critical(): send_notification(t("test_critical_title"), t("test_critical_msg"))
        ctk.CTkButton(r_test, text=t("gui_test_critical"), width=100, height=28, fg_color=CARD, border_width=1, border_color=BORDER, command=test_critical).pack(side="left", padx=(0, 8))
        ctk.CTkButton(r_test, text=t("gui_test_full"), width=100, height=28, fg_color=CARD, border_width=1, border_color=BORDER, command=test_charger_full).pack(side="left")

        # ── Tab: Sounds ──
        # Info Note
        ctk.CTkLabel(f_snd, text=t("gui_sounds_info"), text_color=MUTED, 
                     font=("Segoe UI", 10), justify="left").pack(fill="x", padx=24, pady=16)

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

        # ── Tab: Advanced ──
        # Card 1: Engine Connectivity
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

        # Card 2: Hardware
        c_hw = _create_card(f_adv, "Hardware Features")
        r_hw = _create_row(c_hw, t("gui_hardware_alert"))
        hw_var = tk.BooleanVar(value=cfg.get("hardware_alert", True))
        ctk.CTkSwitch(r_hw, text="", variable=hw_var, progress_color=OK, button_color=FG, button_hover_color="#ffffff").pack(side="right")

        # ── Footer ─────────────────────────────────────────────────────
        footer = ctk.CTkFrame(root, fg_color=BG, corner_radius=0)
        footer.pack(fill="x", padx=20, pady=(4, 16))

        ctk.CTkLabel(
            footer,
            text=t("gui_restart_required"),
            text_color=MUTED,
            font=("Segoe UI", 10),
        ).pack(side="left")

        def _save():
            # 1. Update config dict with GUI values
            cfg["language"]           = lang_var.get()
            cfg["poll_interval"]      = max(5, poll_var.get())
            cfg["auto_check_updates"] = upd_var.get()
            
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
            cfg["hardware_alert"]     = hw_var.get()

            # 2. Handle Autostart
            if auto_var.get(): enable_autostart()
            else: disable_autostart()

            # 3. Write to file
            try:
                CONFIG_FILE.write_text(json.dumps(cfg, indent=4), encoding="utf-8")
                logger.info(f"Config saved via GUI: {CONFIG_FILE}")
                _reload_event.set()
            except Exception as e:
                logger.error(f"Failed to save config: {e}")
            
            root.destroy()

        ctk.CTkButton(
            footer, text=t("gui_save"),
            fg_color=ACCENT, hover_color="#6a4aad",
            font=("Segoe UI", 10, "bold"),
            command=_save,
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            footer, text=t("gui_cancel"),
            fg_color=CARD, hover_color=BORDER,
            text_color=FG, border_width=1, border_color=BORDER,
            command=root.destroy,
        ).pack(side="right")

        root.update_idletasks()
        # Optimized height based on content
        win_w = 480
        win_h = 600
        root.geometry(f"{win_w}x{win_h}")
        _center_window(root)
        root.mainloop()

    threading.Thread(target=_run, daemon=True).start()


def open_settings_gui(current_config: dict) -> None:
    """Open the Settings window. Uses customtkinter if available, falls back to legacy ttk."""
    if CTK_AVAILABLE:
        _open_settings_gui_ctk(current_config)
    else:
        logger.warning("customtkinter not found – using legacy settings GUI")
        _open_settings_gui_legacy(current_config)


def init_db() -> None:
    """Initialize the battery history database."""
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS battery_log (
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                headset_pct INTEGER,
                charger_pct INTEGER
            )
        """)

def log_battery(headset: int, charger: int) -> None:
    """Log current battery percentages to the database."""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("INSERT INTO battery_log (headset_pct, charger_pct) VALUES (?, ?)", 
                         (headset, charger))
    except Exception as e:
        logger.error(f"Failed to log battery to DB: {e}")

# ── Entry point ────────────────────────────────────────────────────────────────

def main() -> None:
    if not _acquire_instance_lock():
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

    tray = TrayApp()
    t_thread = threading.Thread(target=monitor_loop, args=(config, tray), daemon=True)
    register_gamesense()
    _check_for_updates(config)
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
        # Keep process alive while the GUI daemon thread runs
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
