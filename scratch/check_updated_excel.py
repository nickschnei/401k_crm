import os
import sys
import datetime
sys.path.append(os.getcwd())

onedrive_excel = "C:\\Users\\nicks\\OneDrive\\Documents\\Combined 401k Prospecting Plan.xlsx"
local_excel = "Combined 401k Prospecting Plan.xlsx"

for name, path in [("OneDrive", onedrive_excel), ("Local", local_excel)]:
    if os.path.exists(path):
        mtime = os.path.getmtime(path)
        dt = datetime.datetime.fromtimestamp(mtime)
        size = os.path.getsize(path)
        print(f"{name} Excel: size={size} bytes, modified={dt}")
    else:
        print(f"{name} Excel: does not exist")
