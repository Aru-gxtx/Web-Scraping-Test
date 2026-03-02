import pandas as pd
import csv

# Check Excel
df_excel = pd.read_excel('results/STEELITE_Populated_v0.5.xlsx')
print('Excel Stats:')
print(f'  Total products: {len(df_excel)}')
print(f'  Has Image Link: {df_excel["Image Link"].notna().sum()}')
print(f'  Sample Mfr Codes (first 10):')
for code in df_excel["Mfr Catalog No."].head(10):
    print(f'    {code}')

# Check steelitehome CSV
with open('steelite/steelitehome_products.csv', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))
    print(f'\nSteeliteHome CSV:')
    print(f'  Total products: {len(rows)}')
    print(f'  Has images: {sum(1 for r in rows if r.get("image_link") and r["image_link"] != "N/A")}')
    print(f'  Sample manufacturers (first 5):')
    for r in rows[:5]:
        print(f'    {r["manufacturer"][:30]}')

# Check wasserstrom CSV  
with open('steelite/wasserstrom_products.csv', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))
    print(f'\nWasserstrom CSV:')
    print(f'  Total products: {len(rows)}')
    print(f'  Has images: {sum(1 for r in rows if r.get("image_link") and r["image_link"] != "N/A")}')
    print(f'  Sample manufacturers (first 5):')
    for r in rows[:5]:
        print(f'    {r["manufacturer"][:30]}')
