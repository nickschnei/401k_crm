import pypdf

reader = pypdf.PdfReader(r"C:\Users\nicks\Documents\401k_crm\Branded_Fiduciary_Diagnostics\Ball Systems INC_020444227.pdf")
print("Total Pages:", len(reader.pages))
for idx, page in enumerate(reader.pages):
    print(f"\n--- Page {idx+1} ---")
    print(page.extract_text()[:400])
