import subprocess
import base64
import os

key_path = r"c:\Users\nicks\Documents\401k_crm\CRM-key-pair.pem"
ip = "100.24.66.49"

def main():
    print("Reading and base64-encoding files...")
    
    with open(r"c:\Users\nicks\Documents\401k_crm\api\sync.py", "rb") as f:
        sync_b64 = base64.b64encode(f.read()).decode('utf-8')
        
    with open(r"c:\Users\nicks\Documents\401k_crm\api\prospects.py", "rb") as f:
        prospects_b64 = base64.b64encode(f.read()).decode('utf-8')
        
    # Build the shell script to execute on the remote machine
    remote_script = f"""
cat << 'EOF' > /tmp/sync.py.b64
{sync_b64}
EOF
base64 -d /tmp/sync.py.b64 > /home/ubuntu/401k_crm/api/sync.py
rm /tmp/sync.py.b64

cat << 'EOF' > /tmp/prospects.py.b64
{prospects_b64}
EOF
base64 -d /tmp/prospects.py.b64 > /home/ubuntu/401k_crm/api/prospects.py
rm /tmp/prospects.py.b64

echo "Files copied successfully. Restarting docker containers..."
cd /home/ubuntu/401k_crm
sudo docker-compose down
sudo docker-compose up -d --build
echo "Containers restarted and rebuilt successfully!"
"""

    print("Executing single SSH connection to deploy and restart...")
    cmd = [
        "ssh",
        "-i", key_path,
        "-o", "StrictHostKeyChecking=no",
        "-o", "ConnectTimeout=20",
        f"ubuntu@{ip}",
        "bash"
    ]
    
    # Run SSH and pass the script via stdin
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate(input=remote_script.encode('utf-8'))
    
    print(f"Return code: {proc.returncode}")
    print("STDOUT:")
    print(stdout.decode(errors='ignore'))
    print("STDERR:")
    print(stderr.decode(errors='ignore'))

if __name__ == "__main__":
    main()
