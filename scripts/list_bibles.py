import os
import sys
import json
import libsql_client
from dotenv import load_dotenv

# Add parent directory to path to import config/tools if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

TURSO_URL = os.getenv("TURSO_DATABASE_URL")
TURSO_TOKEN = os.getenv("TURSO_AUTH_TOKEN")

def list_bibles():
    if not TURSO_URL:
        print("Error: TURSO_DATABASE_URL not set in .env")
        return

    try:
        db = libsql_client.create_client_sync(url=TURSO_URL, auth_token=TURSO_TOKEN)
        
        # Query for files marked as bible imports
        # We can filter by source='bible_import'
        rs = db.execute("SELECT id, title, sourceId, metadata, createdAt FROM files WHERE source = 'bible_import' ORDER BY createdAt DESC")
        
        from prettytable import PrettyTable
        table = PrettyTable()
        table.field_names = ["Language", "Version", "Label", "Source ID", "File ID"]
        table.align = "l"

        count = 0
        for row in rs.rows:
            # row structure depends on driver, usually tuple or object. 
            # based on previous script usage: row[0] is id, etc.
            # Columns selected: id, title, sourceId, metadata, createdAt
            file_id = row[0]
            # title = row[1] 
            source_id = row[2]
            metadata_str = row[3]
            
            lang = "?"
            ver = "?"
            label = "?"
            
            if metadata_str:
                try:
                    meta = json.loads(metadata_str)
                    lang = meta.get("language", "?")
                    ver = meta.get("version", "?")
                    label = meta.get("label", row[1]) # Fallback to title
                except json.JSONDecodeError:
                    pass
            
            table.add_row([lang, ver, label, source_id, file_id])
            count += 1
            
        print(f"\nFound {count} Bible(s) in database:\n")
        print(table)
        
    except Exception as e:
        print(f"Error querying database: {e}")

if __name__ == "__main__":
    # Check if prettytable is installed, if not, simple print
    try:
        import prettytable
    except ImportError:
        print("Installing prettytable...")
        os.system(f"{sys.executable} -m pip install prettytable")
        import prettytable
        
    list_bibles()
