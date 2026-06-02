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
        conn.execute("CREATE INDEX IF NOT EXISTS idx_battery_log_timestamp ON battery_log (timestamp)")

def log_battery(headset: int, charger: int) -> None:
    """Log current battery percentages to the database."""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("INSERT INTO battery_log (headset_pct, charger_pct) VALUES (?, ?)", 
                         (headset, charger))
    except Exception as e:
        logger.error(f"Failed to log battery to DB: {e}")

def get_time_remaining_estimate(current_pct: int) -> str:
    """Returns estimated time remaining as a string."""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.execute("""
                SELECT timestamp, headset_pct 
                FROM battery_log 
                ORDER BY timestamp DESC 
                LIMIT 60
            """)
            rows = cursor.fetchall()
            
            if len(rows) < 10:
                return "Berechnung kalibriert sich noch..."
            
            valid_points = [rows[0]]
            for r in rows[1:]:
                if r[1] >= valid_points[-1][1]:
                    valid_points.append(r)
                else:
                    break
                    
            if len(valid_points) < 10:
                return "Berechnung kalibriert sich noch..."
                
            from datetime import datetime
            t_new = datetime.strptime(valid_points[0][0], "%Y-%m-%d %H:%M:%S")
            t_old = datetime.strptime(valid_points[-1][0], "%Y-%m-%d %H:%M:%S")
            
            diff_pct = valid_points[-1][1] - valid_points[0][1]
            diff_sec = (t_new - t_old).total_seconds()
            
            if diff_pct <= 0 or diff_sec <= 0:
                return "Berechnung kalibriert sich noch..."
                
            sec_per_pct = diff_sec / diff_pct
            
            remaining_sec = sec_per_pct * current_pct
            hours = int(remaining_sec // 3600)
            mins = int((remaining_sec % 3600) // 60)
            
            return f"Noch ca. {hours} Stunden und {mins} Minuten verbleibend"
    except Exception as e:
        logger.error(f"Failed to calculate time remaining: {e}")
        return "Berechnung kalibriert sich noch..."

def get_battery_health_estimate() -> str:
    """Returns an estimate of battery health."""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.execute("""
                SELECT timestamp, headset_pct 
                FROM battery_log 
                WHERE timestamp >= date('now', '-30 days')
                ORDER BY timestamp ASC
            """)
            rows = cursor.fetchall()
            
            if len(rows) < 100:
                return "Nicht genug Daten"
                
            from datetime import datetime
            total_sec = 0
            total_pct_drop = 0
            
            for i in range(1, len(rows)):
                t_prev = datetime.strptime(rows[i-1][0], "%Y-%m-%d %H:%M:%S")
                t_curr = datetime.strptime(rows[i][0], "%Y-%m-%d %H:%M:%S")
                
                pct_prev = rows[i-1][1]
                pct_curr = rows[i][1]
                
                if pct_curr < pct_prev:
                    diff_sec = (t_curr - t_prev).total_seconds()
                    if diff_sec > 0 and diff_sec < 7200:
                        total_sec += diff_sec
                        total_pct_drop += (pct_prev - pct_curr)
                        
            if total_pct_drop < 50:
                return "Nicht genug Daten"
                
            sec_per_pct = total_sec / total_pct_drop
            full_runtime_hours = (sec_per_pct * 100) / 3600
            
            return f"Geschätzte max. Laufzeit: {full_runtime_hours:.1f} Stunden"
    except Exception as e:
        logger.error(f"Failed to calculate battery health: {e}")
        return "Fehler bei der Berechnung"
