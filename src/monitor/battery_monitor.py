import time
from src.core.constants import logger
from src.core.config import load_config
from src.core.i18n import t
from src.api.gg_engine import find_transmitter_id, read_battery
from src.api.gamesense import trigger_hardware_alert
from src.ui.notifications import send_notification, play_sound
from src.monitor.database import log_battery
from src.core.utils import get_reload_event

# Global state for hotkey
_current_headset = 0
_current_charger = 0
_current_status = ""

def get_current_data():
    return _current_headset, _current_charger, _current_status

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

def monitor_loop(config: dict, tray) -> None:
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
    
    _reload_event = get_reload_event()

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

            global _current_headset, _current_charger, _current_status
            _current_headset = data["headset_pct"]
            _current_charger = data["charger_pct"]
            _current_status = data["charging"]

            logger.info(
                f"Headset: {data['headset_pct']:3d}%  |  "
                f"Charger: {data['charger_pct']:3d}%  |  "
                f"Status: {data['charging']}"
            )
            tray.set_status(data["headset_pct"], data["charger_pct"], data["charging"])
            monitor.update(data)
            log_battery(data["headset_pct"], data["charger_pct"])
            _reload_event.wait(config["poll_interval"])
