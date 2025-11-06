import os
from werkzeug.utils import secure_filename
from flask import current_app

def allowed_file(filename, allowed_extensions=None):
    """Check if file extension is allowed"""
    if allowed_extensions is None:
        allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', {'xlsx', 'xls'})
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def get_uploaded_files():
    """Get list of uploaded files with their details"""
    files = []
    try:
        upload_folder = current_app.config['UPLOAD_FOLDER']
        # Ensure the upload folder exists
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder, exist_ok=True)
            return files

        for filename in os.listdir(upload_folder):
            try:
                filepath = os.path.join(upload_folder, filename)
                if os.path.isfile(filepath):
                    file_info = {
                        'name': filename,
                        'size': os.path.getsize(filepath),
                        'uploaded_at': os.path.getctime(filepath)
                    }
                    files.append(file_info)
            except Exception as e:
                print(f"Error processing file {filename}: {str(e)}")
                continue
        
        # Sort files by upload date, newest first
        return sorted(files, key=lambda x: x['uploaded_at'], reverse=True)
    except Exception as e:
        print(f"Error listing uploaded files: {str(e)}")
        return []

def ensure_directories_exist():
    """Ensure all required directories exist (skip on Vercel)"""
    # Skip directory creation on Vercel (read-only filesystem)
    if os.environ.get('VERCEL'):
        return
    
    directories = [
        current_app.config['UPLOAD_FOLDER'],
        current_app.config['DOWNLOAD_FOLDER']
    ]
    
    # Add program-level directories
    for program in current_app.config.get('PROGRAM_LEVELS', ['UG', 'PG', 'PhD']):
        directories.append(os.path.join(current_app.config['DOWNLOAD_FOLDER'], program))
    
    for directory in directories:
        if directory:  # Skip None values
            try:
                os.makedirs(directory, exist_ok=True)
            except Exception as e:
                print(f'Error creating directory {directory}: {str(e)}')

def delete_file_safely(filepath):
    """Safely delete a file if it exists"""
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False
    except Exception as e:
        print(f"Error deleting file {filepath}: {str(e)}")
        return False

def get_file_size_formatted(size_bytes):
    """Convert file size to human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"
