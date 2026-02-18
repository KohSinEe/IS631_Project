import psycopg2

DB_HOST = "localhost"
DB_NAME = "fridge_db"
DB_USER = "postgres"
DB_PASS = "rupa"  # change this
DB_PORT = 5432

def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT
    )

def create_inventory_table():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id SERIAL PRIMARY KEY,
            item_name TEXT UNIQUE,
            quantity NUMERIC,
            storage_type TEXT,
            expiry_days INT
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

def add_item(item_name, quantity, storage_type, expiry_days):
    conn = get_connection()
    cur = conn.cursor()
    # Check if item already exists
    cur.execute("SELECT id FROM inventory WHERE item_name = %s", (item_name,))
    if cur.fetchone():
        cur.execute("""
            UPDATE inventory
            SET quantity = %s, storage_type = %s, expiry_days = %s
            WHERE item_name = %s
        """, (quantity, storage_type, expiry_days, item_name))
    else:
        cur.execute("""
            INSERT INTO inventory (item_name, quantity, storage_type, expiry_days)
            VALUES (%s, %s, %s, %s)
        """, (item_name, quantity, storage_type, expiry_days))
    conn.commit()
    cur.close()
    conn.close()
