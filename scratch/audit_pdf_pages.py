import os
import re

pdf_dir = r"C:\Users\nicks\Documents\401k_crm\Branded_Fiduciary_Diagnostics"
files = [f for f in os.listdir(pdf_dir) if f.endswith(".pdf")]

def count_pdf_pages(file_path):
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
        counts = [int(x) for x in re.findall(b'/Count\s+(\d+)', content)]
        return max(counts) if counts else 1
    except Exception:
        return 1

print(f"{'PDF Filename':<65} | {'Pages':<5} | {'Contacts Mapped'}")
print("-" * 90)
for f in sorted(files):
    path = os.path.join(pdf_dir, f)
    pages = count_pdf_pages(path)
    has_contacts = "YES (2-page report)" if pages > 1 else "NO (1-page report - no sheet in Excel)"
    print(f"{f:<65} | {pages:<5} | {has_contacts}")
