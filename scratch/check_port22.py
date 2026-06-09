import socket
import sys

ip = "100.24.66.49"
port = 22

def main():
    print(f"Checking if port {port} is open on {ip}...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3.0)
    try:
        s.connect((ip, port))
        print("SUCCESS: Port 22 is OPEN!")
        s.close()
    except socket.timeout:
        print("FAILED: Port 22 connection TIMED OUT.")
    except Exception as e:
        print(f"FAILED: Connection error: {e}")

if __name__ == "__main__":
    main()
