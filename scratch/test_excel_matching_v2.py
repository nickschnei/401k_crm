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

STOP_WORDS = {
    "inc", "llc", "corp", "group", "co", "pc", "llp", "ltd", 
    "and", "etc", "solutions", "of", "the", "company", "corporation",
    "incorporated", "association"
}

def get_significant_words(name):
    if not name:
        return []
    # Lowercase & split by non-alphanumeric
    words = re.findall(r'[a-z0-9]+', name.lower())
    # Filter stop words
    return [w for w in words if w not in STOP_WORDS]

def find_best_sheet_match(p_name, sheet_names):
    p_words = get_significant_words(p_name)
    if not p_words:
        return None
        
    best_sheet = None
    best_score = 0 # Number of matching significant words
    
    for s in sheet_names:
        if s == 'Key List':
            continue
        s_words = get_significant_words(s)
        if not s_words:
            continue
            
        # Count intersection of words
        intersection = set(p_words) & set(s_words)
        score = len(intersection)
        
        # If score is equal, tie-break by length of match
        if score > best_score:
            best_score = score
            best_sheet = s
        elif score == best_score and score > 0:
            # Check if one is a substring of the other
            p_str = "".join(p_words)
            s_str = "".join(s_words)
            if p_str in s_str or s_str in p_str:
                best_sheet = s

    # Require that at least 50% of the sheet name's significant words (or prospect's) are matched
    if best_score > 0:
        s_words = get_significant_words(best_sheet)
        min_req = min(len(p_words), len(s_words))
        # If at least half of the smaller word list matches, we consider it a hit
        if best_score >= max(1, min_req * 0.5):
            return best_sheet

    return None

matches = {}
for p in prospects:
    p_name = p["employer_name"]
    matches[p_name] = find_best_sheet_match(p_name, sheet_names)

matched_count = 0
for k, v in matches.items():
    if v:
        matched_count += 1
    print(f"Prospect: {k:<50} -> Sheet: {v}")
print(f"\nTotal matched: {matched_count}/{len(prospects)}")
