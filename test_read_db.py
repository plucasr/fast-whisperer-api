#!/usr/bin/env python3
"""
Test script to read resources from the Turso database.
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
    print("Turso Database - Read Resources Test")
    print("=" * 60)
    
    if not url or not auth_token:
        print("❌ Error: Database credentials not set in .env file")
        return
    
    try:
        # Connect to database
        print(f"📡 Connecting to database...")
        conn = libsql_client.create_client_sync(url=url, auth_token=auth_token)
        print("✅ Connected successfully!")
        print()
        
        # Count total records
        print("📊 Checking total records...")
        count_result = conn.execute("SELECT COUNT(*) FROM theological_resources")
        total_count = count_result.rows[0][0] if count_result.rows else 0
        print(f"Total records in database: {total_count}")
        print()
        
        if total_count == 0:
            print("⚠️  No resources found in the database.")
            print("Run the agent to discover and catalog resources first.")
            return
        
        # Read first two resources
        print("🔍 Fetching first 2 resources...")
        print("-" * 60)
        
        result = conn.execute("""
            SELECT id, name, download_url, size, type, license, 
                   discovered_at, processed 
            FROM theological_resources 
            WHERE name = 'SF_2009-01-20_GRC_GREEKM_(MODERN GREEK).xml'
        """)
        
        if not result.rows:
            print("⚠️  No resources found.")
            return
        
        for i, row in enumerate(result.rows, 1):
            resource_id, name, download_url, size, res_type, license, discovered_at, processed = row
            
            print(f"\n📖 Resource #{i}")
            print(f"   ID:             {resource_id}")
            print(f"   Name:           {name}")
            print(f"   Download URL:   {download_url}")
            print(f"   Size:           {size if size else 'Unknown'} bytes")
            print(f"   Type:           {res_type if res_type else 'Unknown'}")
            print(f"   License:        {license if license else 'Unknown'}")
            print(f"   Discovered:     {discovered_at}")
            print(f"   Processed:      {'Yes' if processed else 'No'}")
            print("-" * 60)
        
        print(f"\n✅ Successfully read {len(result.rows)} resource(s)")
        
        # Show sample query for all resources
        print("\n💡 To view all resources, run:")
        print("   SELECT * FROM theological_resources;")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"Error type: {type(e).__name__}")

if __name__ == "__main__":
    main()
