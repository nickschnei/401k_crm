import openpyxl
import sys

sys.stdout.reconfigure(encoding='utf-8')

wb = openpyxl.load_workbook("Combined 401k Prospecting Plan.xlsx", read_only=True)
ws = wb["Key List"]
print("--- Non-empty rows in Key List ---")
for idx, row in enumerate(ws.iter_rows(values_only=True)):
    non_empty = [x for x in row if x is not None]
    if non_empty:
        print(f"Row {idx}: {non_empty[:10]}")
wb.close()
