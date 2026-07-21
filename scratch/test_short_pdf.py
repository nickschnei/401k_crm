import sys
import os
sys.path.insert(0, os.path.abspath("."))

import config
from utils.pdf_generator import compile_diagnostic_pdf

print(f"Config BASE_DIR: {config.BASE_DIR}")
test_record = {
    "ein": "123456789",
    "employer_name": "Acme Inc",
    "plan_name": "401(k) Savings Plan",
    "schedule_type": "SF",
    "total_assets": 1000000.0,
    "active_participants": 50,
    "total_eligible_employees": 60,
    "admin_expenses": 5000.0,
    "corrective_distributions": 0.0,
    "participation_rate": 0.833,
    "fee_ratio": 0.005,
    "compliance_failed": False,
    "fee_flag": False,
    "participation_flag": False,
}

try:
    pdf = compile_diagnostic_pdf(test_record, "Test pitch")
    print(f"Diagnostic PDF compiled cleanly: {len(pdf.getvalue())} bytes")
    print("ALL ROUTE PRE-CHECKS PASSED!")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
