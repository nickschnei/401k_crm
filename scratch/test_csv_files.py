import sys
import os
sys.path.append(os.getcwd())

from utils.audit_engine import _csv_files
print("CSV files detected by _csv_files('.'):")
for f in _csv_files("."):
    print(f"- {f} (size: {os.path.getsize(f)} bytes)")
