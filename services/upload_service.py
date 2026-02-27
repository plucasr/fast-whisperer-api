import os
import io
import json
import time
from typing import Optional, List, Dict, Any, Union
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
import libsql_client

# Load environment variables
load_dotenv()

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

# DB Configuration
TURSO_URL = os.getenv("TURSO_DATABASE_URL")
TURSO_TOKEN = os.getenv("TURSO_AUTH_TOKEN")

class UploadService:
    def __init__(self):
        self.db = libsql_client.create_client_sync(url=TURSO_URL, auth_token=TURSO_TOKEN)

    def upload_file(
        self, 
        file_input: Union[str, bytes, io.BytesIO], 
        filename: str, 
        user_id: str, 
        metadata: Optional[Dict[str, Any]] = None,
        source_id: Optional[str] = None,
        source: str = "transcription"
    ) -> Dict[str, Any]:
        """
        Main entry point for uploading a file. 
        Replicates the logic from uploadRoute.ts.
        
        Args:
            file_input: Path to file (str), bytes, or BytesIO stream.
            filename: Original filename.
            user_id: ID of the user uploading.
            metadata: Additional metadata (title, tags, contexts).
            source_id: Optional source identifier (e.g. if redundant upload check is needed).
            source: Source of the file (e.g. "transcription", "youtube", etc.).
        """
        
        # ... (rest of logic unchanged until _add_file_record) ...
        # Since replace_file_content replaces chunks, I need to match carefully or replace larger chunk.
        # I'll replace the signature and the _add_file_record call first, then update definition.
        
        metadata = metadata or {}
        title = metadata.get("title", filename)
        
        # 1. Check if file exists (if source_id provided)
        if source_id:
            existing_file = self._get_file_by_source_and_user(user_id, source_id)
            if existing_file:
                print(f"File already exists: {existing_file['id']}")
                return {
                    "message": "File already exists",
                    "filename": filename,
                    "url": existing_file['file'],
                    "id": existing_file['id'],
                    "status": "exists"
                }

        # 2. Upload to Cloudinary
        try:
            upload_result = cloudinary.uploader.upload(
                file_input, 
                resource_type="auto",
                folder=f"user_{user_id}", # Optional organization
                public_id=f"{int(time.time())}_{filename.split('.')[0]}" # avoid overwrites
            )
            secure_url = upload_result.get("secure_url")
            
        except Exception as e:
            print(f"Cloudinary upload failed: {e}")
            raise Exception(f"Failed to upload to Cloudinary: {str(e)}")

        # 3. Save to Database
        try:
            inserted_file_id = self._add_file_record(
                user_id=user_id,
                file_url=secure_url,
                title=title,
                source_id=source_id,
                metadata=metadata,
                source=source
            )
            
            # ... (rest of method unchanged) ...
            
            # 4. Handle Contexts
            context_ids = metadata.get("contextIds", [])
            if context_ids:
                self._associate_contexts(inserted_file_id, context_ids)
                
            # 5. Handle Tags
            tags = metadata.get("tags", [])
            if tags:
                self._associate_tags(inserted_file_id, tags)

            return {
                "message": "File uploaded successfully!",
                "filename": filename,
                "url": secure_url,
                "id": inserted_file_id,
                "status": "uploaded"
            }

        except Exception as e:
            print(f"Database save failed: {e}")
            # Optional: Delete from Cloudinary if DB save fails
            raise Exception(f"Failed to save file record: {str(e)}")

    def _get_file_by_source_and_user(self, user_id: str, source_id: str) -> Optional[Dict]:
        # ... (unchanged) ...
        try:
            rs = self.db.execute(
                "SELECT * FROM files WHERE userId = ? AND sourceId = ?", 
                [user_id, source_id]
            )
            if rs.rows:
                # Convert row to dict
                row = rs.rows[0]
                columns = rs.columns
                return dict(zip(columns, row))
        except Exception as e:
            print(f"Error checking existing file: {e}")
        return None

    def _add_file_record(self, user_id: str, file_url: str, title: str, source_id: Optional[str], metadata: Dict, source: str) -> int:
        
        # Prepare metadata JSON string
        metadata_json = json.dumps(metadata)
        created_at = int(time.time() * 1000) # milliseconds matches JS new Date().getTime()
        
        source_id_val = source_id if source_id else "direct_upload"

        # Assuming 'files' table exists with these columns based on TS usage
        query = """
            INSERT INTO files (userId, file, createdAt, title, source, sourceId, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            RETURNING id
        """
        try:
            rs = self.db.execute(query, [
                user_id, 
                file_url, 
                created_at, 
                title, 
                source, 
                source_id_val, 
                metadata_json
            ])
            
            if rs.rows:
                return rs.rows[0][0] # ID
            return -1 # Should not happen with RETURNING
        except Exception as e:
             print(f"Insert error: {e}")
             raise e

    def _associate_contexts(self, file_id: int, context_ids: List[str]):
        if not context_ids:
            return
            
        values_placeholder = ", ".join(["(?, ?)"] * len(context_ids))
        query = f"INSERT OR IGNORE INTO file_contexts (fileId, contextId) VALUES {values_placeholder}"
        
        # Flatten parameters
        params = []
        for cid in context_ids:
            params.extend([file_id, cid])
            
        try:
            self.db.execute(query, params)
            print(f"Associated {len(context_ids)} contexts")
        except Exception as e:
            print(f"Context association error: {e}")

    def _associate_tags(self, file_id: int, tag_ids: List[str]):
        if not tag_ids:
            return
            
        values_placeholder = ", ".join(["(?, ?)"] * len(tag_ids))
        query = f"INSERT OR IGNORE INTO file_tags (fileId, tagId) VALUES {values_placeholder}"
        
        # Flatten parameters
        params = []
        for tid in tag_ids:
            params.extend([file_id, tid])
            
        try:
            self.db.execute(query, params)
            print(f"Associated {len(tag_ids)} tags")
        except Exception as e:
            print(f"Tag association error: {e}")
