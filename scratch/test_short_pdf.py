import sys
import os
sys.path.insert(0, os.path.abspath("."))

from utils.pdf_generator import compile_short_form_pdf, compile_diagnostic_pdf

test_record = {
    "ein": "123456789",
    "employer_name": "Acme Technologies Inc",
    "plan_name": "Acme 401(k) Profit Sharing Plan",
    "schedule_type": "H",
    "total_assets": 12500000.0,
    "active_participants": 240,
    "total_eligible_employees": 310,
    "admin_expenses": 14500.0,
    "corrective_distributions": 0.0,
    "participation_rate": 0.774,
    "fee_ratio": 0.0075,
    "compliance_failed": False,
    "fee_red_flag": True,
    "participation_red_flag": False,
    "administrator_name": "Acme Fiduciary Board"
}

test_pitch = "Acme Technologies appears to have elevated fee ratio exposure (75 bps). We recommend executing a fee compression benchmark."

try:
    print("Testing compile_short_form_pdf...")
    pdf_buffer = compile_short_form_pdf(test_record, test_pitch)
    content = pdf_buffer.getvalue()
    print(f"Success! Short Form PDF generated, size: {len(content)} bytes")
    
    print("Testing compile_diagnostic_pdf...")
    diag_buffer = compile_diagnostic_pdf(test_record, test_pitch)
    diag_content = diag_buffer.getvalue()
    print(f"Success! Diagnostic PDF generated, size: {len(diag_content)} bytes")
    print("ALL PDF TESTS PASSED!")
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
