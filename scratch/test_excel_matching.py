import openpyxl
import sqlite3
import re

wb = openpyxl.load_workbook("Combined 401k Prospecting Plan.xlsx", read_only=True)
sheet_names = wb.sheetnames
wb.close()

conn = sqlite3.connect("prospects.db")
conn.row_factory = sqlite3.Row
prospects = conn.execute("SELECT * FROM pipeline_prospects").fetchall()
conn.close()

def clean_name(name):
    if not name:
        return ""
    # Lowercase
    n = name.lower()
    # Remove common corporate suffixes
    n = re.sub(r'\b(inc|llc|corp|co|group|ltd|solutions|pc|llp|incorporated|corporation|d/b/a|sol\.)\b', '', n)
    # Remove non-alphanumeric characters
    n = re.sub(r'[^a-z0-9]', '', n)
    return n

print(f"Sheet names: {sheet_names}\n")

matches = {}
for p in prospects:
    p_name = p["employer_name"]
    p_clean = clean_name(p_name)
    
    # Try to find a matching sheet
    matched_sheet = None
    # 1. Exact cleaned match
    for s in sheet_names:
        if s == 'Key List':
            continue
        s_clean = clean_name(s)
        if p_clean == s_clean or p_clean.startswith(s_clean) or s_clean.startswith(p_clean):
            matched_sheet = s
            break
            
    # 2. Substring matching if still none
    if not matched_sheet:
        for s in sheet_names:
            if s == 'Key List':
                continue
            s_clean = clean_name(s)
            # check if one contains the other (if long enough)
            if len(s_clean) > 3 and len(p_clean) > 3:
                if s_clean in p_clean or p_clean in s_clean:
                    matched_sheet = s
                    break

    matches[p_name] = matched_sheet

# Print results
matched_count = 0
for k, v in matches.items():
    if v:
        matched_count += 1
    print(f"Prospect: {k:<50} -> Sheet: {v}")
print(f"\nTotal matched: {matched_count}/{len(prospects)}")
