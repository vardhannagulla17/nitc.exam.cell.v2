"""
Supabase Storage Utility Functions
Handles file upload, download, and management with Supabase storage
"""
import os
from io import BytesIO
from datetime import datetime
from flask import current_app

# Try to import Supabase
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("Warning: Supabase not available in storage utility.")

class SupabaseStorage:
    def __init__(self):
        self.url = os.environ.get('SUPABASE_URL')
        self.key = os.environ.get('SUPABASE_ANON_KEY')
        self.bucket = os.environ.get('SUPABASE_BUCKET', 'uploads')
        self.client = None
        
        if SUPABASE_AVAILABLE and self.url and self.key:
            try:
                self.client = create_client(self.url, self.key)
            except Exception as e:
                print(f"Failed to initialize Supabase client: {str(e)}")
    
    def upload_file(self, filename: str, content: bytes, content_type: str = None) -> bool:
        """Upload file to Supabase storage"""
        if not self.client:
            return False
        
        try:
            # Use unique filename to avoid conflicts
            unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
            
            file_options = {}
            if content_type:
                file_options["content-type"] = content_type
            
            result = self.client.storage.from_(self.bucket).upload(
                unique_filename, 
                content,
                file_options=file_options
            )
            
            return bool(result)
        except Exception as e:
            print(f"Supabase upload error: {str(e)}")
            return False
    
    def download_file(self, filename: str) -> BytesIO:
        """Download file from Supabase storage"""
        if not self.client:
            return None
        
        try:
            result = self.client.storage.from_(self.bucket).download(filename)
            return BytesIO(result) if result else None
        except Exception as e:
            print(f"Supabase download error: {str(e)}")
            return None
    
    def delete_file(self, filename: str) -> bool:
        """Delete file from Supabase storage"""
        if not self.client:
            return False
        
        try:
            result = self.client.storage.from_(self.bucket).remove([filename])
            return bool(result)
        except Exception as e:
            print(f"Supabase delete error: {str(e)}")
            return False
    
    def list_files(self) -> list:
        """List all files in Supabase storage"""
        if not self.client:
            return []
        
        try:
            result = self.client.storage.from_(self.bucket).list()
            files = []
            
            for file_obj in result:
                if file_obj['name'] and not file_obj['name'].endswith('/'):
                    file_info = {
                        'name': file_obj['name'],
                        'size': file_obj.get('metadata', {}).get('size', 0) or 0,
                        'uploaded_at': datetime.fromisoformat(
                            file_obj['updated_at'].replace('Z', '+00:00')
                        ) if file_obj.get('updated_at') else datetime.now()
                    }
                    files.append(file_info)
            
            return sorted(files, key=lambda x: x['uploaded_at'], reverse=True)
        except Exception as e:
            print(f"Supabase list error: {str(e)}")
            return []
    
    def get_public_url(self, filename: str) -> str:
        """Get public URL for a file"""
        if not self.client:
            return None
        
        try:
            result = self.client.storage.from_(self.bucket).get_public_url(filename)
            return result
        except Exception as e:
            print(f"Supabase public URL error: {str(e)}")
            return None

# Global instance
storage = SupabaseStorage()