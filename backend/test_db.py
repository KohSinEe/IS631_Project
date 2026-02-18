import psycopg2

# Update these with your actual credentials
DB_HOST = "localhost"
DB_NAME = "fridge_db"
DB_USER = "postgres"
DB_PASSWORD = "rupa"  # <-- replace this
DB_PORT = 5432

try:
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT
    )
    print("✅ Connected successfully to PostgreSQL!")
    conn.close()
except Exception as e:
    print("❌ Connection failed:", e)
