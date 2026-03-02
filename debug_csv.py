import csv
import os

csv_files = [
    'steelite/steelitehome_products.csv',
    'steelite/wasserstrom_products.csv',
]

for csv_file in csv_files:
    if os.path.exists(csv_file):
        with open(csv_file) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            print(f"\n{csv_file}: {len(rows)} products")
            if rows:
                for k, v in list(rows[0].items())[:12]:
                    val = str(v)[:60] if v else "[EMPTY]"
                    print(f"  {k}: {val}")
        print()
