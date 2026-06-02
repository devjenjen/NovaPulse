import os
import sqlite3
import pytest
from pathlib import Path

# Add project root to sys.path to allow relative imports in tests
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.monitor import database
import src.core.constants

def test_init_db_creates_table(tmp_path):
    # Override DB_FILE for testing
    test_db = tmp_path / "test_history.db"
    
    # We must patch the constant inside the database module
    database.DB_FILE = test_db
    
    if not hasattr(database, 'init_db'):
        pytest.fail("init_db not implemented")
        
    database.init_db()
    
    assert test_db.exists()
    
    with sqlite3.connect(test_db) as conn:
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='battery_log'")
        assert cursor.fetchone() is not None

def test_log_battery_inserts_data(tmp_path):
    test_db = tmp_path / "test_history.db"
    database.DB_FILE = test_db
    
    if not hasattr(database, 'log_battery'):
        pytest.fail("log_battery not implemented")
        
    database.init_db()
    database.log_battery(85, 100)
    
    with sqlite3.connect(test_db) as conn:
        cursor = conn.execute("SELECT headset_pct, charger_pct FROM battery_log")
        row = cursor.fetchone()
        assert row is not None
        assert row == (85, 100)
