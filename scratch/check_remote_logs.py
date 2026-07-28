import subprocess
import os

key_path = r"c:\Users\nicks\Documents\401k_crm\CRM-key-pair.pem"
ip = "100.24.66.49"

cmd = [
    "ssh",
    "-i", key_path,
    "-o", "StrictHostKeyChecking=no",
    "-o", "ConnectTimeout=20",
    f"ubuntu@{ip}",
    "sudo docker logs crm-backend --tail 100"
]

try:
    print(f"Fetching docker logs from AWS EC2 ({ip})...")
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
    print("STDOUT:")
    print(res.stdout.decode('utf-8', errors='ignore'))
    print("STDERR:")
    print(res.stderr.decode('utf-8', errors='ignore'))
except Exception as e:
    print(f"Error fetching logs: {e}")
