import os
import libsql_experimental as libsql
from dotenv import load_dotenv

load_dotenv()

# Setup Sync Connection for now (LangGraph nodes are sync for simplicity usually, or we can make them async)
# LibSQL experimental supports both.
url = os.getenv("TURSO_DATABASE_URL")
auth_token = os.getenv("TURSO_AUTH_TOKEN")

if not url:
    print("Warning: TURSO_DATABASE_URL not set")

conn = None

def get_db_connection():
    global conn
    if conn is None and url:
        conn = libsql.connect(database=url, auth_token=auth_token)
        # Create table if not exists
        conn.execute("""
            CREATE TABLE IF NOT EXISTS theological_resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                download_url TEXT NOT NULL UNIQUE,
                size INTEGER,
                type TEXT,
                license TEXT,
                discovered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                processed BOOLEAN DEFAULT 0
            )
        """)
        conn.commit()
    return conn

def save_resource(resource: dict):
    """
    Saves a discovered resource to the database.
    Resource dict: {name, download_url, size, type, path}
    """
    try:
        db = get_db_connection()
        if not db:
            print("DB Connection failed")
            return
            
        db.execute(
            """
            INSERT OR IGNORE INTO theological_resources (name, download_url, size, type)
            VALUES (?, ?, ?, ?)
            """,
            (resource['name'], resource['download_url'], resource['size'], resource['type'])
        )
        db.commit()
        print(f"Saved {resource['name']} to DB")
    except Exception as e:
        print(f"Error saving to DB: {e}")
