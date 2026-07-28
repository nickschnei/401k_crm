import sys
import re

# Try importing different PDF libraries
try:
    import pypdf
    print("pypdf available!")
    reader = pypdf.PdfReader(r"C:\Users\nicks\Downloads\Branded_Fiduciary_Diagnostics\Ball Systems INC_020444227.pdf")
    print("Ball Systems Pages:", len(reader.pages))
    reader2 = pypdf.PdfReader(r"C:\Users\nicks\Downloads\Branded_Fiduciary_Diagnostics\Kirkpatrick Management Co_037966510.pdf")
    print("Kirkpatrick Pages:", len(reader2.pages))
    sys.exit(0)
except ImportError:
    pass

try:
    import PyPDF2
    print("PyPDF2 available!")
    reader = PyPDF2.PdfReader(r"C:\Users\nicks\Downloads\Branded_Fiduciary_Diagnostics\Ball Systems INC_020444227.pdf")
    print("Ball Systems Pages:", len(reader.pages))
    reader2 = PyPDF2.PdfReader(r"C:\Users\nicks\Downloads\Branded_Fiduciary_Diagnostics\Kirkpatrick Management Co_037966510.pdf")
    print("Kirkpatrick Pages:", len(reader2.pages))
    sys.exit(0)
except ImportError:
    pass

try:
    from reportlab.pdfgen import canvas
    print("ReportLab is available, checking content parsing manually...")
    with open(r"C:\Users\nicks\Downloads\Branded_Fiduciary_Diagnostics\Ball Systems INC_020444227.pdf", "rb") as f:
        data = f.read()
    counts = [int(x) for x in re.findall(b'/Count\s+(\d+)', data)]
    print("Ball Systems page counts found:", counts)
    
    with open(r"C:\Users\nicks\Downloads\Branded_Fiduciary_Diagnostics\Kirkpatrick Management Co_037966510.pdf", "rb") as f:
        data2 = f.read()
    counts2 = [int(x) for x in re.findall(b'/Count\s+(\d+)', data2)]
    print("Kirkpatrick page counts found:", counts2)
except Exception as e:
    print("Error:", e)
