import os
import zipfile
import subprocess

local_root = r"c:\Users\nicks\Documents\401k_crm"
key_path = r"c:\Users\nicks\Documents\401k_crm\CRM-key-pair.pem"
ip = "100.24.66.49"
zip_name = "update.zip"
zip_path = os.path.join(local_root, zip_name)

# List of specific files to package
files_to_package = [
    "api/audits.py",
    "api/auth.py",
    "api/database.py",
    "api/discovery.py",
    "api/prospects.py",
    "api/sync.py",
    "api/agent.py",
    "frontend/src/components/Sidebar.tsx",
    "frontend/src/components/AppLayout.tsx",
    "frontend/src/components/ChatSidebar.tsx",
    "frontend/src/app/layout.tsx",
    "frontend/src/middleware.ts",
    "frontend/src/services/api.ts",
    "frontend/src/app/discovery/page.tsx",
    "frontend/src/app/login/page.tsx",
    "utils/audit_engine.py",
    "utils/auth.py",
    "utils/pii.py",
    "check_db.py",
    "diagnose_eins.py",
    "excel_debug.py",
    "excel_debug.txt",
    "run_sync_tenant.py",
    "utils/fallback_5500.py",
    "main.py",
    "requirements.txt",
    "config.py",
    "scratch/check_api_key.py",
    "docker-compose.yml",
    "api/trip.py",
    "utils/geocoder.py",
    "frontend/src/components/TripMap.tsx",
    "frontend/src/app/planner/page.tsx",
    "frontend/package.json",
    "frontend/package-lock.json",
    "scratch/enrich_addresses.py"
]

# List of folders to package completely (empty to speed up deployment)
folders_to_package = []

# Remote files to delete (since they are deleted locally)
files_to_delete_remote = [
    "run_sync.py",
    "check_prospects.py"
]

def create_zip():
    print(f"Creating ZIP file at {zip_path}...")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # 1. Add individual files
        for rel_path in files_to_package:
            full_path = os.path.join(local_root, rel_path.replace("/", "\\"))
            if os.path.exists(full_path):
                print(f"  Adding file: {rel_path}")
                zipf.write(full_path, rel_path)
            else:
                print(f"  WARNING: File not found locally: {rel_path}")
                
        # 2. Add folders
        for folder in folders_to_package:
            folder_path = os.path.join(local_root, folder)
            if os.path.exists(folder_path):
                print(f"  Adding folder: {folder}")
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        if "Zone.Identifier" in file or file.endswith(".pyc"):
                            continue
                        file_full_path = os.path.join(root, file)
                        rel_file_path = os.path.relpath(file_full_path, local_root).replace("\\", "/")
                        zipf.write(file_full_path, rel_file_path)
            else:
                print(f"  WARNING: Folder not found locally: {folder}")
                
    size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    print(f"ZIP file created successfully. Size: {size_mb:.2f} MB")

def upload_zip():
    print(f"Uploading {zip_name} to remote server at {ip} via SSH stdin pipe...")
    with open(zip_path, "rb") as f:
        zip_content = f.read()
        
    cmd = [
        "ssh",
        "-i", key_path,
        "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=20",
        f"ubuntu@{ip}",
        f"cat > /home/ubuntu/401k_crm/{zip_name}"
    ]
    
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate(input=zip_content)
    
    if proc.returncode == 0:
        print("Successfully uploaded ZIP file.")
        return True
    else:
        print("Failed to upload ZIP file.")
        print(f"stdout: {stdout.decode(errors='ignore')}")
        print(f"stderr: {stderr.decode(errors='ignore')}")
        return False

def extract_and_restart():
    print("Executing extraction and docker-compose restart on the remote host...")
    
    # Construct script to run on remote
    remote_script = f"""
    cd /home/ubuntu/401k_crm
    echo "--- Extracting update.zip ---"
    unzip -o {zip_name}
    rm {zip_name}
    
    echo "--- Deleting obsolete files ---"
    """
    
    for f in files_to_delete_remote:
        remote_script += f"\n    rm -f {f}"
        
    remote_script += """
    echo "--- Rebuilding and restarting containers ---"
    sudo docker compose down
    sudo docker compose up -d --build
    
    echo "--- Checking running containers ---"
    sudo docker ps
    """
    
    cmd = [
        "ssh",
        "-i", key_path,
        "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=20",
        f"ubuntu@{ip}",
        "bash"
    ]
    
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate(input=remote_script.encode('utf-8'))
    
    print(f"Remote command return code: {proc.returncode}")
    print("STDOUT:")
    print(stdout.decode('utf-8', errors='ignore').encode('ascii', errors='ignore').decode('ascii'))
    print("STDERR:")
    print(stderr.decode('utf-8', errors='ignore').encode('ascii', errors='ignore').decode('ascii'))
    
    # Cleanup local zip
    if os.path.exists(zip_path):
        os.remove(zip_path)
        print("Cleaned up local ZIP archive.")

def main():
    try:
        create_zip()
        if upload_zip():
            extract_and_restart()
    except Exception as e:
        print(f"An error occurred during deployment: {e}")

if __name__ == "__main__":
    main()
