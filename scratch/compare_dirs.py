import os
import hashlib
import subprocess

local_root = r"c:\Users\nicks\Documents\401k_crm"
remote_root = "/home/ubuntu/401k_crm"
key_path = r"c:\Users\nicks\Documents\401k_crm\CRM-key-pair.pem"
ip = "100.24.66.49"

exclude_dirs = {
    "venv", "node_modules", ".next", "__pycache__", ".git", "extracted_data", ".streamlit", "scratch"
}
exclude_files = {
    "prospects.db", "celerydb.sqlite", "celeryresults.sqlite", "streamlit.log", 
    "CRM-Key.pem", "CRM-key-pair.pem"
}

def get_md5(path):
    hash_md5 = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def get_local_files():
    files = {}
    for root, dirs, filenames in os.walk(local_root):
        # Filter directories in place
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for filename in filenames:
            if filename in exclude_files:
                continue
            if filename.endswith(".pyc") or filename.endswith(".xlsx.zone.identifier") or "Zone.Identifier" in filename:
                continue
            full_path = os.path.join(root, filename)
            rel_path = os.path.relpath(full_path, local_root).replace("\\", "/")
            files[rel_path] = {
                "size": os.path.getsize(full_path),
                "md5": get_md5(full_path),
                "local_path": full_path
            }
    return files

def get_remote_files():
    # We will run a command on the remote host to list files with sizes and MD5s
    # Excluding files & dirs we don't care about
    cmd_str = f"""
    cd {remote_root} && find . -type f | while read file; do
        # check if file should be excluded
        clean_file=$(echo "$file" | sed 's|^./||')
        first_part=$(echo "$clean_file" | cut -d'/' -f1)
        base_name=$(basename "$clean_file")
        
        # simple check for excludes
        if [[ "$first_part" == "venv" || "$first_part" == "node_modules" || "$first_part" == ".next" || "$first_part" == "__pycache__" || "$first_part" == ".git" || "$first_part" == "extracted_data" || "$first_part" == ".streamlit" || "$first_part" == "scratch" ]]; then
            continue
        fi
        if [[ "$base_name" == "prospects.db" || "$base_name" == "celerydb.sqlite" || "$base_name" == "celeryresults.sqlite" || "$base_name" == "streamlit.log" || "$base_name" == "CRM-Key.pem" || "$base_name" == "CRM-key-pair.pem" ]]; then
            continue
        fi
        if [[ "$base_name" == *.pyc || "$base_name" == *Zone.Identifier* ]]; then
            continue
        fi
        
        size=$(stat -c%s "$file" 2>/dev/null || stat -f%z "$file")
        md5=$(md5sum "$file" 2>/dev/null | awk '{{print $1}}' || md5 -q "$file")
        echo "$clean_file|$size|$md5"
    done
    """
    
    cmd = [
        "ssh", "-i", key_path,
        "-o", "StrictHostKeyChecking=no",
        f"ubuntu@{ip}",
        cmd_str
    ]
    
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    
    if proc.returncode != 0:
        print("Error getting remote files:")
        print(stderr.decode(errors='ignore'))
        return None
        
    remote_files = {}
    for line in stdout.decode(errors='ignore').splitlines():
        line = line.strip()
        if not line or "|" not in line:
            continue
        parts = line.split("|")
        if len(parts) == 3:
            rel_path, size, md5 = parts
            remote_files[rel_path] = {
                "size": int(size),
                "md5": md5
            }
    return remote_files

def main():
    print("Gathering local file information...")
    local_files = get_local_files()
    print(f"Found {len(local_files)} local files (excluding virtualenvs, DBs, node_modules, etc.).")
    
    print("Gathering remote file information from AWS EC2...")
    remote_files = get_remote_files()
    if remote_files is None:
        print("Failed to contact remote host.")
        return
    print(f"Found {len(remote_files)} remote files (excluding virtualenvs, DBs, node_modules, etc.).")
    
    modified = []
    added = []
    deleted = []
    matched = 0
    
    for rel_path, info in local_files.items():
        if rel_path not in remote_files:
            added.append(rel_path)
        else:
            r_info = remote_files[rel_path]
            if info["md5"] != r_info["md5"]:
                modified.append(rel_path)
            else:
                matched += 1
                
    for rel_path in remote_files:
        if rel_path not in local_files:
            deleted.append(rel_path)
            
    print("\n--- RESULTS ---")
    print(f"Identical files: {matched}")
    
    print(f"\nFiles modified locally ({len(modified)}):")
    for f in modified:
        print(f"  [MODIFIED] {f}")
        
    print(f"\nFiles added locally ({len(added)}):")
    for f in added:
        print(f"  [ADDED] {f}")
        
    print(f"\nFiles on remote but not local ({len(deleted)}):")
    for f in deleted:
        print(f"  [DELETED ON LOCAL] {f}")

if __name__ == "__main__":
    main()
