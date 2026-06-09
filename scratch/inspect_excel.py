import sys
import os
sys.path.append(os.getcwd())

import pandas as pd

onedrive_excel = "C:\\Users\\nicks\\OneDrive\\Documents\\Combined 401k Prospecting Plan.xlsx"
local_excel = "Combined 401k Prospecting Plan.xlsx"

print("OneDrive exists:", os.path.exists(onedrive_excel))
print("Local exists:", os.path.exists(local_excel))

for path in [onedrive_excel, local_excel]:
    if os.path.exists(path):
        print(f"\nInspecting: {path}")
        try:
            for h in [0, 5]:
                print(f"--- Header row {h} ---")
                df = pd.read_excel(path, header=h)
                # Print columns after stripping non-ascii characters or encoding to ascii ignore
                cols = [str(c).encode('ascii', 'ignore').decode('ascii') for c in df.columns]
                print("Columns:", cols)
                print("Shape:", df.shape)
                # Print head without emoji errors
                head_str = df.head(3).to_string()
                print(head_str.encode('ascii', 'ignore').decode('ascii'))
        except Exception as e:
            print("Error reading:", e)
