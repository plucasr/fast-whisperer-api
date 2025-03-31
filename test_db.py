#!/usr/bin/env python3
"""
Test script to verify Turso database connectivity and basic operations.
"""
import os
import libsql_client
from dotenv import load_dotenv

def main():
    # Load environment variables
    load_dotenv()
    
    url = os.getenv("TURSO_DATABASE_URL")
    auth_token = os.getenv("TURSO_AUTH_TOKEN")
    
    print("=" * 60)
    print("Turso Database Connection Test")
    print("=" * 60)
    
    # Verify environment variables
    if not url:
        print("❌ Error: TURSO_DATABASE_URL not set in .env file")
        return
    
    if not auth_token:
        print("❌ Error: TURSO_AUTH_TOKEN not set in .env file")
        return
    
    print(f"✓ Database URL: {url}")
    print(f"✓ Auth Token: ...{auth_token[-10:] if auth_token else 'None'}")
    print()
    
    try:
        print("📡 Attempting to connect to Turso database...")
        conn = libsql_client.create_client_sync(url=url, auth_token=auth_token)
        print("✅ Connection successful!")
        print()
        
        # Test 1: Create table
        print("🔧 Test 1: Creating table if not exists...")
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
        print("✅ Table created/verified successfully!")
        print()
        
        # Test 2: Insert a test record
        print("📝 Test 2: Inserting a test record...")
        test_resource = {
            'name': 'Test Bible Lexicon',
            'download_url': 'https://example.com/test-lexicon.json',
            'size': 1024,
            'type': 'json'
        }
        
        conn.execute(
            """
            INSERT OR IGNORE INTO theological_resources (name, download_url, size, type)
            VALUES (?, ?, ?, ?)
            """,
            (test_resource['name'], test_resource['download_url'], 
             test_resource['size'], test_resource['type'])
        )
        print(f"✅ Test record inserted: {test_resource['name']}")
        print()
        
        # Test 3: Query the record
        print("🔍 Test 3: Querying records...")
        result = conn.execute("SELECT * FROM theological_resources WHERE name = ?", 
                            (test_resource['name'],))
        
        if result.rows:
            print(f"✅ Found {len(result.rows)} record(s):")
            for row in result.rows:
                print(f"   - ID: {row[0]}, Name: {row[1]}, URL: {row[2]}")
        else:
            print("⚠️  No records found (might have been skipped due to IGNORE)")
        print()
        
        # Test 4: Count all records
        print("📊 Test 4: Counting all records in table...")
        count_result = conn.execute("SELECT COUNT(*) FROM theological_resources")
        total_count = count_result.rows[0][0] if count_result.rows else 0
        print(f"✅ Total records in database: {total_count}")
        print()
        
        print("=" * 60)
        print("🎉 All tests passed successfully!")
        print("=" * 60)
        
    except libsql_client.LibsqlError as e:
        print(f"❌ Database Error: {e}")
        print("\nTroubleshooting:")
        print("1. Verify your TURSO_DATABASE_URL starts with 'libsql://' or 'https://'")
        print("2. Check if your TURSO_AUTH_TOKEN is valid and not expired")
        print("3. Ensure your Turso database is active and not suspended")
        print("4. Try generating a new auth token from Turso dashboard")
        
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        print(f"Error type: {type(e).__name__}")

if __name__ == "__main__":
    main()
