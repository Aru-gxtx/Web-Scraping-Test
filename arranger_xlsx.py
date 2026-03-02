import pandas as pd
import os
import glob

def populate_sheet1_data():
    excel_path = 'results/STEELITE_Populated_v0.4.xlsx'  # Target Excel file
    output_path = 'results/STEELITE_Populated_v0.5.xlsx' # Output file

    print("Loading datasets...")
    df1 = pd.read_excel(excel_path, dtype=str) 
    
    # Find and merge all *_products.csv files from spider folder
    csv_files = glob.glob('steelite/*_products.csv')
    print(f"Found {len(csv_files)} spider CSV files")
    
    if not csv_files:
        print("  WARNING: No *_products.csv files found! Creating empty sheet.")
        df2 = pd.DataFrame()
    else:
        # Read all CSV files and concatenate them
        dfs = []
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file, dtype=str)
                dfs.append(df)
                print(f"  [OK] Loaded {csv_file}: {len(df)} rows")
            except Exception as e:
                print(f"  [ERROR] Error loading {csv_file}: {e}")
        
        if dfs:
            df2 = pd.concat(dfs, ignore_index=True)
            print(f"\nTotal merged rows from all spiders: {len(df2)}")
        else:
            df2 = pd.DataFrame()

    print(f"Excel columns: {df1.columns.tolist()}")
    if not df2.empty:
        print(f"Spider data columns: {df2.columns.tolist()}")

    # REVERSED MAPPING: 'Target Column in Sheet 1' : 'Source Column in Sheet 2'
    column_mapping = {
        'Image Link': 'image_link',
        'Overview': 'overview',
        'Length': 'length',
        'Width': 'width',
        'Height': 'height',
        'Capacity': 'volume_capacity',  # Spider outputs 'volume_capacity'
        'Diameter': 'diameter',
        'Color': 'color',
        'Material': 'material',
        'EAN Code': 'ean_code',
        'Barcode': 'upc_barcode',  # Spider outputs 'upc_barcode'
        'Pattern': 'pattern',
    }

    # Use manufacturer as the key to match with Mfr Catalog No.
    df1['Mfr Catalog No.'] = df1['Mfr Catalog No.'].fillna("").astype(str).str.strip()
    
    if not df2.empty:
        df2['manufacturer'] = df2['manufacturer'].fillna("").astype(str).str.strip()
        df2.drop_duplicates(subset=['manufacturer'], keep='first', inplace=True)
        df2.set_index('manufacturer', inplace=True)
        
        print("Pulling data from spiders to populate Excel...")
        
        for col_target, col_source in column_mapping.items():
            if col_target in df1.columns and not df2.empty:
                # Use manufacturer as key to match rows
                try:
                    matched_data = df1['Mfr Catalog No.'].map(df2[col_source] if col_source in df2.columns else pd.Series())
                    # Only update cells that currently are empty or NaN
                    df1[col_target] = df1[col_target].where(df1[col_target].fillna("").str.strip() != "", matched_data)
                    populated_count = matched_data.notna().sum()
                    if populated_count > 0:
                        print(f"  ✓ Populated '{col_target}' ({populated_count} rows)")
                    else:
                        print(f"  ✗ No data found for '{col_target}'")
                except Exception as e:
                    print(f"  ✗ Error with '{col_target}': {e}")
            else:
                print(f"  ✗ Skipped '{col_target}' (column missing or no spider data)")
    else:
        print("  WARNING: No spider data available - Excel will not be populated")

    df1.to_excel(output_path, index=False)
    print(f"\n✓ Data successfully transferred! Saved to: {output_path}")

if __name__ == "__main__":
    populate_sheet1_data()