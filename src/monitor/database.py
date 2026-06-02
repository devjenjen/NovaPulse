import sqlite3
from src.core.constants import DB_FILE, logger

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
