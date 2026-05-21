import os
import sqlite3
import pytest
import importlib.util
from pathlib import Path

# Import novapulse.pyw
spec = importlib.util.spec_from_file_location("novapulse", "novapulse.pyw")
novapulse = importlib.util.module_from_spec(spec)
spec.loader.exec_module(novapulse)

def test_init_db_creates_table(tmp_path):
    # Override DB_FILE for testing
    test_db = tmp_path / "test_history.db"
    novapulse.DB_FILE = test_db
    
    # Check if init_db exists
    if not hasattr(novapulse, 'init_db'):
        pytest.fail("init_db not implemented")
        
    novapulse.init_db()
    
    assert test_db.exists()
    
    with sqlite3.connect(test_db) as conn:
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='battery_log'")
        assert cursor.fetchone() is not None

def test_log_battery_inserts_data(tmp_path):
    test_db = tmp_path / "test_history.db"
    novapulse.DB_FILE = test_db
    
    if not hasattr(novapulse, 'log_battery'):
        pytest.fail("log_battery not implemented")
        
    novapulse.init_db()
    novapulse.log_battery(85, 100)
    
    with sqlite3.connect(test_db) as conn:
        cursor = conn.execute("SELECT headset_pct, charger_pct FROM battery_log")
        row = cursor.fetchone()
        assert row is not None
        assert row == (85, 100)
