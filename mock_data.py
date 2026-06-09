import pandas as pd
import zipfile
import os

# Create Mock Excel
prospects = pd.DataFrame({
    'Employer Name': ['Acme Corp', 'Globex Inc', 'Initech'],
    'EIN': ['123456789', '987654321', '111222333'],
    'Contact': ['John Doe', 'Hank Scorpio', 'Peter Gibbons']
})
prospects.to_excel('Combined 401k Prospecting Plan.xlsx', index=False)

# Create Mock DOL CSV
dol_data = pd.DataFrame({
    'EIN': ['123456789', '987654321'],
    'SPONS_DFE_NAME': ['Acme Corp', 'Globex Corporation'],
    'TOT_ASSETS_END_AMT': [5000000, 12000000],
    'TOT_ACT_PARTCP_CNT': [50, 120],
    'ADMIN_NAME': ['Fidelity', 'Vanguard']
})
dol_data.to_csv('F_5500_2024_Latest.csv', index=False)

# Zip it
with zipfile.ZipFile('F_5500_2024_Latest.zip', 'w') as z:
    z.write('F_5500_2024_Latest.csv')
os.remove('F_5500_2024_Latest.csv')

print("Mock data created successfully!")
