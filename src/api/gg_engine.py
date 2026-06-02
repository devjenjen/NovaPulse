import json
import requests
import urllib3
from src.core.constants import CORE_PROPS, CORE_PROPS_GG, logger

# The local GG Engine uses a self-signed certificate.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
        if addr and ("127.0.0.1" in addr or "localhost" in addr):
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
