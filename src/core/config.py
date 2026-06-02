import json
from src.core.constants import CONFIG_FILE, logger

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
    "hotkey":      "ctrl+shift+b",# global hotkey for mini status
}

_INT_KEYS = {
    "poll_interval", "low_threshold", "critical_threshold", "full_level",
    "startup_grace", "standby_retry_fast", "standby_fast_count", "standby_retry_slow",
}

def load_config() -> dict:
    if not CONFIG_FILE.exists():
        # Import here to avoid circular dependencies
        from src.ui.setup_wizard import run_setup_wizard
        run_setup_wizard()
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        config = DEFAULT_CONFIG.copy()
        config.update(data)
        for key in _INT_KEYS:
            try:
                config[key] = int(config[key])
            except (TypeError, ValueError):
                config[key] = DEFAULT_CONFIG[key]
        if config.keys() != data.keys():
            CONFIG_FILE.write_text(json.dumps(config, indent=4), encoding="utf-8")
        return config
    except json.JSONDecodeError as e:
        logger.error(f"Corrupt config.json ({e}) – using defaults")
        return DEFAULT_CONFIG.copy()
    except Exception as e:
        logger.warning(f"Could not read config.json ({e}) – using defaults")
        return DEFAULT_CONFIG.copy()
