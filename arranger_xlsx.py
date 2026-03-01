import pandas as pd

def populate_sheet1_data():
    sheet1_path = 'results/STEELITE_Populated_v0.3.xlsx'                # Target (format we are keeping)
    sheet2_path = 'steelite/STEELITE_Updated_v0.7.2.csv'                 # Source (your spider output)
    output_path = 'results/STEELITE_Populated_v0.4.xlsx'                # Where the new data will be saved

    print("Loading datasets...")
    df1 = pd.read_excel(sheet1_path, dtype=str) 
    df2 = pd.read_csv(sheet2_path, dtype=str)

    print(f"Sheet1 columns: {df1.columns.tolist()}")
    print(f"Sheet2 columns: {df2.columns.tolist()}")

    # REVERSED MAPPING: 'Target Column in Sheet 1' : 'Source Column in Sheet 2'
    column_mapping = {
        'Image Link': 'image_link',
        'Overview': 'overview',
        'Length': 'length',
        'Width': 'width',
        'Height': 'height',
        'Capacity': 'volume',  # Changed from 'capacity' to 'volume'
        'Diameter': 'diameter',
        'Color': 'color',
        'Material': 'material',
        'EAN Code': 'ean_code',
        'Barcode': 'barcode',
    }

    # Use mfr as the key to match with Mfr Catalog No.
    df1['Mfr Catalog No.'] = df1['Mfr Catalog No.'].str.strip()
    df2['mfr'] = df2['mfr'].str.strip()

    df2.drop_duplicates(subset=['mfr'], keep='first', inplace=True)
    
    df2.set_index('mfr', inplace=True)

    print("Pulling data from Sheet 2 to populate Sheet 1...")
    
    for col_target, col_source in column_mapping.items():
        if col_target in df1.columns and col_source in df2.columns:
            df1[col_target] = df1['Mfr Catalog No.'].map(df2[col_source]).fillna(df1[col_target])
            print(f"  ✓ Populated '{col_target}' from '{col_source}'")
        else:
            print(f"  ✗ Skipped '{col_target}' → '{col_source}' (column missing)")

    df1.to_excel(output_path, index=False)
    print(f"\n✓ Data successfully transferred! Saved to: {output_path}")

if __name__ == "__main__":
    populate_sheet1_data()