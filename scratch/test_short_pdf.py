import sys
import os
sys.path.insert(0, os.path.abspath("."))

from utils.pdf_generator import compile_raw_form_5500_sf_pdf, compile_diagnostic_pdf

test_record = {
    "ein": "123456789",
    "employer_name": "Acme Technologies Inc",
    "plan_name": "Acme 401(k) Profit Sharing Plan",
    "schedule_type": "SF",
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

try:
    print("Testing compile_raw_form_5500_sf_pdf...")
    pdf_buffer = compile_raw_form_5500_sf_pdf(test_record)
    content = pdf_buffer.getvalue()
    print(f"Success! Raw Form 5500-SF PDF generated, size: {len(content)} bytes")
    print("ALL TESTS PASSED SUCCESSFULLY!")
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
