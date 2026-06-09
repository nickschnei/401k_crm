import pandas as pd

df = pd.read_excel('Combined 401k Prospecting Plan.xlsx', header=5)
with open('excel_debug.txt', 'w', encoding='utf-8') as f:
    f.write(f"Columns: {list(df.columns)}\n\n")
    f.write(f"Shape: {df.shape}\n\n")
    for i in range(min(5, len(df))):
        f.write(f"Row {i}: {dict(df.iloc[i])}\n\n")
