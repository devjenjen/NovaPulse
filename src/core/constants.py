import os
from pathlib import Path
import logging
import sys
from logging.handlers import RotatingFileHandler

APP_NAME    = "NovaPulse"
VERSION     = "0.2.0"
APP_DIR     = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "NovaPulse"
CONFIG_FILE = APP_DIR / "config.json"
LOG_FILE    = APP_DIR / "novapulse.log"
CRASH_LOG   = APP_DIR / "crash.log"
DB_FILE     = APP_DIR / "history.db"
SOUNDS_DIR  = APP_DIR / "sounds"
CORE_PROPS  = Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData")) / "SteelSeries" / "SteelSeries Engine 3" / "coreProps.json"
CORE_PROPS_GG = Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData")) / "SteelSeries" / "GG" / "apps" / "engine" / "coreProps.json"
GITHUB_RELEASES_URL = "https://api.github.com/repos/devjenjen/NovaPulse/releases/latest"

APP_DIR.mkdir(parents=True, exist_ok=True)
SOUNDS_DIR.mkdir(parents=True, exist_ok=True)

def _make_rotating_handler(path: Path) -> RotatingFileHandler:
    h = RotatingFileHandler(path, maxBytes=1_048_576, backupCount=2, encoding="utf-8")
    h.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)-8s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
    return h

logger = logging.getLogger("novapulse")
logger.setLevel(logging.DEBUG)
logger.addHandler(_make_rotating_handler(LOG_FILE))
logger.addHandler(logging.StreamHandler(sys.stdout))

crash_logger = logging.getLogger("novapulse.crash")
crash_logger.setLevel(logging.ERROR)
crash_logger.addHandler(_make_rotating_handler(CRASH_LOG))
