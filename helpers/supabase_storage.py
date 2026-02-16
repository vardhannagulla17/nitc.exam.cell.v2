"""
Supabase Storage Utility Functions
Handles file upload, download, and management with Supabase storage
"""
import os
import json
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

# Bucket names for absentee management
PENDING_ABSENTEE_BUCKET = 'pending_absentee'
APPROVED_ABSENTEE_BUCKET = 'approved_absentee'
REJECTED_ABSENTEE_BUCKET = 'rejected_absentee'

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


class AbsenteeStorage:
    """Handles absentee-specific storage operations with dedicated buckets"""
    
    def __init__(self):
        self._client = None
        self._initialized = False
    
    @property
    def client(self):
        """Lazy initialization of Supabase client"""
        if not self._initialized:
            self._initialize_client()
        return self._client
    
    def _initialize_client(self):
        """Initialize the Supabase client with current environment variables"""
        self._initialized = True
        url = os.environ.get('SUPABASE_URL')
        # Use SERVICE_ROLE_KEY for admin operations like deleting files
        # Fall back to ANON_KEY if service role key not available
        key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or os.environ.get('SUPABASE_ANON_KEY')
        
        if SUPABASE_AVAILABLE and url and key:
            try:
                self._client = create_client(url, key)
                print(f"[DEBUG] AbsenteeStorage client initialized successfully")
            except Exception as e:
                print(f"Failed to initialize Supabase client for AbsenteeStorage: {str(e)}")
                self._client = None
        else:
            if not SUPABASE_AVAILABLE:
                print("[DEBUG] Supabase not available")
            if not url:
                print("[DEBUG] SUPABASE_URL not set")
            if not key:
                print("[DEBUG] SUPABASE_ANON_KEY not set")
    
    def _generate_filename(self, marked_by: str, course_code: str, exam_date: str, batch_id: str = None) -> str:
        """Generate a unique filename for absentee records"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        if batch_id:
            return f"{exam_date}_{course_code}_{marked_by}_{batch_id}.json"
        return f"{exam_date}_{course_code}_{marked_by}_{timestamp}.json"
    
    def upload_pending_absentees(self, absentees: list, marked_by: str, exam_date: str) -> tuple:
        """
        Upload absentee records to pending_absentee bucket
        Returns: (success: bool, filename: str, message: str)
        """
        if not self.client:
            return False, None, "Supabase client not initialized"
        
        if not absentees:
            return False, None, "No absentees to upload"
        
        try:
            course_code = absentees[0].get('course_code', 'UNKNOWN')
            filename = self._generate_filename(marked_by, course_code, exam_date)
            
            # Create JSON content
            content = json.dumps({
                'exam_date': exam_date,
                'marked_by': marked_by,
                'course_code': course_code,
                'uploaded_at': datetime.now().isoformat(),
                'absentees': absentees
            }, indent=2)
            
            # Upload to pending bucket
            result = self.client.storage.from_(PENDING_ABSENTEE_BUCKET).upload(
                filename,
                content.encode('utf-8'),
                file_options={"content-type": "application/json"}
            )
            
            if result:
                return True, filename, f"Successfully uploaded {len(absentees)} absentees to pending"
            return False, None, "Upload failed"
            
        except Exception as e:
            print(f"Error uploading pending absentees: {str(e)}")
            return False, None, f"Upload error: {str(e)}"
    
    def move_to_approved(self, filename: str) -> tuple:
        """
        Move absentee file from pending to approved bucket
        Returns: (success: bool, message: str)
        """
        if not self.client:
            return False, "Supabase client not initialized"
        
        try:
            # Download from pending bucket
            content = self.client.storage.from_(PENDING_ABSENTEE_BUCKET).download(filename)
            if not content:
                return False, f"File {filename} not found in pending bucket"
            
            # Upload to approved bucket
            result = self.client.storage.from_(APPROVED_ABSENTEE_BUCKET).upload(
                filename,
                content,
                file_options={"content-type": "application/json"}
            )
            
            if result:
                # Delete from pending bucket
                self.client.storage.from_(PENDING_ABSENTEE_BUCKET).remove([filename])
                return True, f"Moved {filename} to approved bucket"
            
            return False, "Failed to upload to approved bucket"
            
        except Exception as e:
            print(f"Error moving to approved: {str(e)}")
            return False, f"Move error: {str(e)}"
    
    def move_to_rejected(self, filename: str) -> tuple:
        """
        Move absentee file from pending to rejected bucket
        Returns: (success: bool, message: str)
        """
        if not self.client:
            return False, "Supabase client not initialized"
        
        try:
            # Download from pending bucket
            content = self.client.storage.from_(PENDING_ABSENTEE_BUCKET).download(filename)
            if not content:
                return False, f"File {filename} not found in pending bucket"
            
            # Upload to rejected bucket
            result = self.client.storage.from_(REJECTED_ABSENTEE_BUCKET).upload(
                filename,
                content,
                file_options={"content-type": "application/json"}
            )
            
            if result:
                # Delete from pending bucket
                self.client.storage.from_(PENDING_ABSENTEE_BUCKET).remove([filename])
                return True, f"Moved {filename} to rejected bucket"
            
            return False, "Failed to upload to rejected bucket"
            
        except Exception as e:
            print(f"Error moving to rejected: {str(e)}")
            return False, f"Move error: {str(e)}"
    
    def list_pending_absentees(self) -> list:
        """List all files in pending_absentee bucket"""
        if not self.client:
            return []
        
        try:
            result = self.client.storage.from_(PENDING_ABSENTEE_BUCKET).list()
            return [f for f in result if f.get('name') and not f['name'].endswith('/')]
        except Exception as e:
            print(f"Error listing pending absentees: {str(e)}")
            return []
    
    def list_approved_absentees(self) -> list:
        """List all files in approved_absentee bucket"""
        if not self.client:
            return []
        
        try:
            result = self.client.storage.from_(APPROVED_ABSENTEE_BUCKET).list()
            return [f for f in result if f.get('name') and not f['name'].endswith('/')]
        except Exception as e:
            print(f"Error listing approved absentees: {str(e)}")
            return []
    
    def list_rejected_absentees(self) -> list:
        """List all files in rejected_absentee bucket"""
        if not self.client:
            return []
        
        try:
            result = self.client.storage.from_(REJECTED_ABSENTEE_BUCKET).list()
            return [f for f in result if f.get('name') and not f['name'].endswith('/')]
        except Exception as e:
            print(f"Error listing rejected absentees: {str(e)}")
            return []
    
    def get_approved_absentees_data(self, exam_date: str = None) -> list:
        """
        Get all absentee data from approved_absentee bucket
        Optionally filter by exam_date
        Returns: list of absentee records
        """
        if not self.client:
            return []
        
        try:
            files = self.list_approved_absentees()
            all_absentees = []
            
            for file_info in files:
                filename = file_info.get('name')
                if not filename:
                    continue
                
                # Filter by exam_date if provided (filename format: {exam_date}_{course}_{user}_{ts}.json)
                if exam_date and not filename.startswith(exam_date):
                    continue
                
                try:
                    content = self.client.storage.from_(APPROVED_ABSENTEE_BUCKET).download(filename)
                    if content:
                        data = json.loads(content.decode('utf-8'))
                        absentees = data.get('absentees', [])
                        # Add metadata to each absentee
                        for a in absentees:
                            a['_file'] = filename
                            a['_marked_by'] = data.get('marked_by')
                            a['_exam_date'] = data.get('exam_date')
                        all_absentees.extend(absentees)
                except Exception as e:
                    print(f"Error reading file {filename}: {str(e)}")
                    continue
            
            return all_absentees
            
        except Exception as e:
            print(f"Error getting approved absentees data: {str(e)}")
            return []
    
    def download_approved_file(self, filename: str) -> BytesIO:
        """Download a specific file from approved_absentee bucket"""
        if not self.client:
            return None
        
        try:
            content = self.client.storage.from_(APPROVED_ABSENTEE_BUCKET).download(filename)
            return BytesIO(content) if content else None
        except Exception as e:
            print(f"Error downloading approved file: {str(e)}")
            return None
    
    def delete_from_pending(self, filename: str) -> bool:
        """Delete a file from pending_absentee bucket"""
        if not self.client:
            return False
        
        try:
            self.client.storage.from_(PENDING_ABSENTEE_BUCKET).remove([filename])
            return True
        except Exception as e:
            print(f"Error deleting from pending: {str(e)}")
            return False
    
    def clear_bucket(self, bucket_name: str) -> tuple:
        """
        Delete all files from a specific bucket
        Returns: (success: bool, message: str, deleted_count: int)
        """
        if not self.client:
            return False, "Supabase client not initialized", 0
        
        try:
            # List all files in the bucket
            print(f"[DEBUG] Listing files in bucket: {bucket_name}")
            files = self.client.storage.from_(bucket_name).list()
            print(f"[DEBUG] Raw files response: {files}")
            
            file_list = [f.get('name') for f in files if f.get('name') and not f['name'].endswith('/')]
            print(f"[DEBUG] Files to delete: {file_list}")
            
            if not file_list:
                return True, f"No files to delete in {bucket_name} bucket", 0
            
            # Delete all files
            print(f"[DEBUG] Attempting to delete {len(file_list)} files from {bucket_name}")
            result = self.client.storage.from_(bucket_name).remove(file_list)
            print(f"[DEBUG] Delete result: {result}")
            
            deleted_count = len(file_list)
            
            # Verify deletion
            verification = self.client.storage.from_(bucket_name).list()
            remaining = [f for f in verification if f.get('name') and not f['name'].endswith('/')]
            print(f"[DEBUG] Files remaining after deletion: {len(remaining)}")
            
            if len(remaining) == 0:
                return True, f"Successfully deleted {deleted_count} files from {bucket_name} bucket", deleted_count
            else:
                return False, f"Attempted to delete {deleted_count} files but {len(remaining)} remain in {bucket_name} bucket", deleted_count
            
        except Exception as e:
            error_msg = f"Error clearing {bucket_name} bucket: {str(e)}"
            print(f"[ERROR] {error_msg}")
            import traceback
            traceback.print_exc()
            return False, error_msg, 0
    
    def clear_pending_bucket(self) -> tuple:
        """Clear all files from pending_absentee bucket"""
        return self.clear_bucket(PENDING_ABSENTEE_BUCKET)
    
    def clear_approved_bucket(self) -> tuple:
        """Clear all files from approved_absentee bucket"""
        return self.clear_bucket(APPROVED_ABSENTEE_BUCKET)
    
    def clear_rejected_bucket(self) -> tuple:
        """Clear all files from rejected_absentee bucket"""
        return self.clear_bucket(REJECTED_ABSENTEE_BUCKET)
    
    def clear_all_absentee_buckets(self) -> dict:
        """
        Clear all absentee buckets (pending, approved, rejected)
        Returns: dict with results for each bucket
        """
        results = {
            'pending': self.clear_pending_bucket(),
            'approved': self.clear_approved_bucket(),
            'rejected': self.clear_rejected_bucket()
        }
        return results


# Global instance for absentee storage
absentee_storage = AbsenteeStorage()