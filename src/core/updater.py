import requests
from src.core.constants import VERSION, GITHUB_RELEASES_URL, logger

def check_for_updates(config: dict) -> None:
    if not config.get("auto_check_updates", True):
        return
    try:
        logger.info("Checking for updates...")
        r = requests.get(GITHUB_RELEASES_URL, timeout=3)
        r.raise_for_status()
        latest = r.json().get("tag_name", "")
        if latest and latest != f"v{VERSION}":
            logger.info(f"Update available: {latest} (Current: v{VERSION})")
            
            # Local import to avoid circular dependency
            from src.ui.notifications import send_notification
            send_notification(f"Update Available: {latest}", f"NovaPulse {latest} is available on GitHub.")
    except Exception as e:
        logger.debug(f"Update check failed: {e}")
