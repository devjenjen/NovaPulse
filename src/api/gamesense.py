import requests
from src.core.constants import APP_NAME, logger
from src.api.gg_engine import get_base_url

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
