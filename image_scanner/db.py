# db.py
import sqlite3
from datetime import datetime

DB_FILE = "inventory.db"

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    return conn

def create_table():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        food_name TEXT,
        quantity REAL,
        unit TEXT,
        purchase_date TEXT,
        expiry_date TEXT,
        image_path TEXT
    )
    """)
    conn.commit()
    conn.close()

def add_item(food_name, quantity, unit, purchase_date, expiry_date, image_path=None):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    INSERT INTO inventory (food_name, quantity, unit, purchase_date, expiry_date, image_path)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (food_name, quantity, unit, purchase_date.strftime("%Y-%m-%d"),
          expiry_date.strftime("%Y-%m-%d"), image_path))
    conn.commit()
    conn.close()

def get_inventory():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, food_name, quantity, unit, purchase_date, expiry_date FROM inventory ORDER BY purchase_date DESC")
    rows = c.fetchall()
    conn.close()
    return rows