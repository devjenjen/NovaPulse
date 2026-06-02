import os
try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False

from src.core.constants import APP_NAME, VERSION, CONFIG_FILE, LOG_FILE, logger
from src.core.i18n import t
from src.core.autostart import is_autostart_enabled, enable_autostart, disable_autostart
from src.ui.notifications import send_notification
from src.core.config import load_config

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
    if not TRAY_AVAILABLE: return None
    size = 256
    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    s    = size / 64
    rim  = _hex_to_rgba(color, 255)
    fill = _hex_to_rgba(color, 80)
    rad  = int(4 * s)
    lw   = max(2, int(2 * s))

    cx, cy = int(32 * s), int(30 * s)
    arc_r  = int(18 * s)
    for offset in range(max(1, int(5 * s))):
        ri = arc_r - offset
        draw.arc([cx - ri, cy - ri, cx + ri, cy + ri], start=180, end=0, fill=rim, width=1)

    for x1, y1, x2, y2 in [(int(7*s), int(28*s), int(18*s), int(44*s)),
                             (int(46*s), int(28*s), int(57*s), int(44*s))]:
        draw.rounded_rectangle([x1, y1, x2, y2], radius=rad, fill=fill, outline=rim, width=lw)

    return img


from src.monitor.database import get_time_remaining_estimate

class TrayApp:
    def __init__(self):
        self._status  = "Starting..."
        self._icon    = None

    def set_status(self, headset: int, charger: int, charging: str) -> None:
        is_offline = (headset == 0 and charging == "UNKNOWN_OR_HEADSET_NOT_CONNECTED")
        charge_mark  = " ⚡" if charging == "CHARGING" else ""
        
        if is_offline:
            self._status = f"Headset:  Offline\nCharger:  {charger}%"
            if self._icon:
                self._icon.icon  = _create_tray_icon(_battery_color(0, offline=True))
                self._icon.title = f"Headset: Offline  |  Charger: {charger}%"
        else:
            est = get_time_remaining_estimate(headset)
            self._status = f"Headset:  {headset}%{charge_mark}\nCharger:  {charger}%\n\n{est}"
            if self._icon:
                self._icon.icon  = _create_tray_icon(_battery_color(headset))
                self._icon.title = f"{t('tray_tooltip', h=headset, c=charger)}\n{est}"

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
        from src.ui.settings import open_settings_gui
        config = load_config()
        open_settings_gui(config)

    def _quit(self, icon, item) -> None:
        logger.info("Quit via tray menu.")
        icon.stop()

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
        self._icon.run()
