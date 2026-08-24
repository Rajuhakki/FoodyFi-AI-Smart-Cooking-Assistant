import os
import zipfile

zip_filename = "FoodyFi-AI-Smart-Cooking-Assistant.zip"
exclude_dirs = {'__pycache__', '.git', '.venv', 'venv'}

def create_project_zip():
    file_count = 0
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk('.'):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for file in files:
                if file in (zip_filename, 'make_zip.py') or file.endswith('.pyc'):
                    continue
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, '.')
                zipf.write(file_path, arcname)
                file_count += 1
                
    size_mb = os.path.getsize(zip_filename) / (1024 * 1024)
    print(f"Successfully generated {zip_filename} containing {file_count} files ({size_mb:.2f} MB).")

if __name__ == '__main__':
    create_project_zip()
