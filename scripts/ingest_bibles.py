import json
import os
import requests
import sys
from urllib.parse import urlparse

# Add parent directory to path to import services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.upload_service import UploadService

def convert_github_url_to_raw(url: str) -> str:
    """Converts a GitHub blob URL to a raw URL."""
    if "github.com" in url and "/blob/" in url:
        return url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
    if "github.com" in url and "/tree/" in url:
         # The user provided /tree/ in the example URLs for files, which is technically for dirs but sometimes used for files in UI copy-paste?
         # Actually, looking at the user's JSON: "https://github.com/.../tree/master/json/es_rvr.json"
         # "tree" is usually for directories. If it's a file, it's usually "blob".
         # However, if I change 'tree' to 'raw' (or blob to raw) and domain, it might work.
         # Let's try replacing "github.com" -> "raw.githubusercontent.com" and removing "/tree/" or "/blob/".
         return url.replace("github.com", "raw.githubusercontent.com").replace("/tree/", "/")
    return url

def parse_filename(filename: str) -> dict:
    """
    Parses 'es_rvr.json' into {language: 'es', version: 'rvr', label: 'Reina Valera' (inferred?)}
    User said: { language: 'es', version: rvr, label: 'Reina valera' }
    
    Mapping logic:
    es_rvr -> lang: es, ver: rvr
    fi_finnish -> lang: fi, ver: finnish
    pt_aa -> lang: pt, ver: aa
    ...
    
    I will infer label from version or filename for now, maybe map known ones.
    """
    base = filename.replace(".json", "")
    parts = base.split("_")
    
    if len(parts) >= 2:
        lang = parts[0]
        ver = "_".join(parts[1:])
    else:
        lang = "unknown"
        ver = base

    # Simple label mapping based on the file list provided
    labels = {
        "es_rvr": "Reina Valera",
        "fi_finnish": "Finnish Bible",
        "fi_pr": "Finnish Pyhä Raamattu",
        "fr_apee": "French Epée",
        "ko_ko": "Korean",
        "pt_aa": "Almeida Atualizada",
        "pt_acf": "Almeida Corrigida Fiel",
        "pt_nvi": "Nova Versão Internacional",
        "ro_cornilescu": "Cornilescu",
        "ru_synodal": "Russian Synodal",
        "vi_vietnamese": "Vietnamese",
        "zh_cuv": "Chinese Union Version",
        "zh_ncv": "Chinese New Version"
    }
    
    label = labels.get(base, f"{lang.upper()} {ver.upper()}")
    
    return {
        "language": lang,
        "version": ver,
        "label": label
    }

def main():
    bibles_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bibles.json")
    
    try:
        with open(bibles_path, "r") as f:
            urls = json.load(f)
    except FileNotFoundError:
        print(f"Error: {bibles_path} not found.")
        return

    print("Starting ingestion script...")
    uploader = UploadService()
    print("UploadService initialized. Connecting to DB...")

    # Quick hack: Fetch a valid user ID (e.g., the owner) to assign these files to.
    try:
        rs = uploader.db.execute("SELECT id FROM user LIMIT 1")
        if not rs.rows:
            print("No users found in DB. Cannot upload without a valid userId.")
            return
        user_id = rs.rows[0][0] # Assuming first column is ID
        print(f"Uploading as User ID: {user_id}")
    except Exception as e:
        print(f"DB Error fetching user: {e}")
        import traceback
        traceback.print_exc()
        return

    for url in urls:
        if "index.json" in url:
            continue # Skip index
            
        raw_url = convert_github_url_to_raw(url)
        filename = raw_url.split("/")[-1]
        
        # Parse metadata first to get source_id
        meta = parse_filename(filename)
        source_id = f"bible_{meta['language']}_{meta['version']}"
        source = "bible_import"

        # Check if already exists in DB
        try:
             # Basic check to see if we can skip download
             rs = uploader.db.execute("SELECT id FROM files WHERE sourceId = ? AND userId = ?", [source_id, user_id])
             if rs.rows:
                 print(f"Skipping {filename} (already ingested).")
                 continue
        except Exception as e:
            print(f"Error checking DB for existence: {e}")

        print(f"Processing {filename} from {raw_url}...")
        
        try:
            # Download content with timeout
            resp = requests.get(raw_url, timeout=30)
            if resp.status_code != 200:
                print(f"Failed to download {raw_url}: {resp.status_code}")
                continue
                
            file_content = resp.content # bytes
            
            # Additional metadata structure requested: { language, version, label }
            # Plus context: reference="bible"
            
            metadata = {
                "language": meta["language"],
                "version": meta["version"],
                "label": meta["label"],
                "type": "bible_version"
            }
            


            # Upload
            result = uploader.upload_file(
                file_input=file_content,
                filename=filename,
                user_id=user_id,
                metadata=metadata,
                source_id=source_id, # Unique Source ID
                source="bible_import" # Custom source column
            )
            
            print(f"Successfully uploaded {filename}: ID={result.get('id')}, Status={result.get('status')}")
            
        except Exception as e:
            print(f"Error uploading {filename}: {e}")

if __name__ == "__main__":
    main()
