import subprocess
import os

key_path = r"c:\Users\nicks\Documents\401k_crm\CRM-key-pair.pem"
ip = "100.24.66.49"

def upload_file(local_path, remote_path):
    print(f"Uploading {local_path} to {remote_path}...")
    with open(local_path, "rb") as f:
        file_content = f.read()
    
    cmd = [
        "ssh",
        "-i", key_path,
        "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=15",
        f"ubuntu@{ip}",
        f"cat > {remote_path}"
    ]
    
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate(input=file_content)
    
    if proc.returncode == 0:
        print(f"Successfully uploaded {local_path}")
    else:
        print(f"Failed to upload {local_path}. Return code: {proc.returncode}")
        print(f"stdout: {stdout.decode(errors='ignore')}")
        print(f"stderr: {stderr.decode(errors='ignore')}")

if __name__ == "__main__":
    upload_file(r"c:\Users\nicks\Documents\401k_crm\api\sync.py", "/home/ubuntu/401k_crm/api/sync.py")
    upload_file(r"c:\Users\nicks\Documents\401k_crm\api\prospects.py", "/home/ubuntu/401k_crm/api/prospects.py")
