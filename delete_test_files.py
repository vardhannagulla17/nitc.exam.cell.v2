import os
import glob

# Get all test files
test_py_files = glob.glob('test_*.py')
test_html_files = glob.glob('test_*.html')
sample_html_files = glob.glob('sample_*.html')

all_files = test_py_files + test_html_files + sample_html_files

print("=" * 50)
print("Deleting Test Files from Local Disk")
print("=" * 50)
print()

deleted_count = 0
skipped_count = 0

for file in all_files:
    try:
        if os.path.exists(file):
            os.remove(file)
            print(f"[DELETED] {file}")
            deleted_count += 1
        else:
            print(f"[SKIP] {file} (not found)")
            skipped_count += 1
    except Exception as e:
        print(f"[ERROR] Could not delete {file}: {e}")
        skipped_count += 1

print()
print("=" * 50)
print(f"Cleanup Complete!")
print(f"  Deleted: {deleted_count} files")
print(f"  Skipped: {skipped_count} files")
print("=" * 50)
