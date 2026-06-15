import subprocess
import os

key_path = r"c:\Users\nicks\Documents\401k_crm\CRM-key-pair.pem"
ip = "100.24.66.49"

def run_remote_commands():
    # Shell script to run on remote host
    remote_script = """
    cd /home/ubuntu/401k_crm
    echo "=== Running Docker PS ==="
    sudo docker ps
    echo "=== Running Database WAL journal check ==="
    sudo docker compose exec -T web-backend python -c "
from api.database import engine
with engine.connect() as conn:
    print('Journal mode:', conn.exec_driver_sql('PRAGMA journal_mode').fetchone()[0])
"
    """
    
    cmd = [
        "ssh",
        "-i", key_path,
        "-o", "StrictHostKeyChecking=no",
        f"ubuntu@{ip}",
        "bash"
    ]
    
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate(input=remote_script.encode('utf-8'))
    
    import sys
    print("STDOUT:")
    sys.stdout.buffer.write(stdout)
    print("\nSTDERR:")
    sys.stdout.buffer.write(stderr)
    print()

if __name__ == "__main__":
    run_remote_commands()
