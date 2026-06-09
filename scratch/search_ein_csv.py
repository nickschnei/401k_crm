import sys
import os
sys.path.append(os.getcwd())

from utils.audit_engine import _csv_files

ein = "188021660"
print(f"Searching for EIN {ein} in all unzipped CSV files...")

found = False
for f in _csv_files("."):
    try:
        with open(f, "r", encoding="utf-8", errors="ignore") as handle:
            line_num = 0
            for line in handle:
                line_num += 1
                if ein in line or "18-8021660" in line:
                    print(f"Found in {f} on line {line_num}!")
                    print("Line snippet:", line[:200].strip())
                    found = True
                    break
    except Exception as e:
        print(f"Error reading {f}: {e}")

if not found:
    print(f"EIN {ein} was not found in ANY CSV file!")
