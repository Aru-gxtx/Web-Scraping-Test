import pandas as pd
import glob
import os
from pathlib import Path
import re


def load_all_scraped_data():
    csv_files = [
        'sanneng/chakawal_products.csv',
        'sanneng/sannengvietnam_products.csv',
        'sanneng/tokopedia_products.csv',
        'sanneng/unopan_products.csv',
        'sanneng/coupang_products.csv',
        'sanneng/addon_search_products.csv'
    ]
    
    all_data = []
    
    for csv_file in csv_files:
        if os.path.exists(csv_file):
            try:
                df = pd.read_csv(csv_file, encoding='utf-8')
                print(f"Loaded {len(df)} products from {csv_file}")
                all_data.append(df)
            except Exception as e:
                print(f"Error loading {csv_file}: {e}")
        else:
            print(f"File not found: {csv_file}")
    
    if not all_data:
        print("No scraped data files found!")
        return pd.DataFrame()
    
    # Combine all data
    combined_df = pd.concat(all_data, ignore_index=True)
    print(f"\nTotal products loaded: {len(combined_df)}")
    
    return combined_df


def normalize_sku(sku):
    if pd.isna(sku):
        return None
    value = str(sku).strip().upper()
    if not value or value in {"N/A", "NAN", "NONE"}:
        return None

    value = value.replace(" ", "")
    extracted = re.search(r"SN\d+[A-Z0-9-]*", value)
    if extracted:
        return extracted.group(0)

    return value


def normalize_image_link(link):
    if pd.isna(link):
        return 'N/A'
    value = str(link).strip()
    if not value or value.upper() in {"N/A", "NONE", "NAN"}:
        return 'N/A'
    if value.startswith('//'):
        return f"https:{value}"
    return value


def row_has_valid_image(row):
    return normalize_image_link(row.get('image_link', 'N/A')) != 'N/A'


def populate_excel(excel_path, scraped_data):
    try:
        # Read the Excel file
        df_excel = pd.read_excel(excel_path, engine='openpyxl')
        print(f"\nLoaded Excel file: {excel_path}")
        print(f"Excel has {len(df_excel)} rows")
        print(f"Excel columns: {list(df_excel.columns)}")
    except Exception as e:
        print(f"Error loading Excel file: {e}")
        return
    
    mfr_column = None
    for col in df_excel.columns:
        if any(keyword in str(col).upper() for keyword in ['MFR', 'SKU', 'MODEL', 'CODE', '型號']):
            mfr_column = col
            break
    
    if mfr_column is None:
        print("Could not find MFR/SKU column in Excel. Using first column as MFR.")
        mfr_column = df_excel.columns[0]
    
    print(f"Using '{mfr_column}' as MFR/SKU column")
    
    # Normalize SKUs in both datasets
    df_excel['_normalized_sku'] = df_excel[mfr_column].apply(normalize_sku)
    scraped_data['_normalized_sku'] = scraped_data['sku'].apply(normalize_sku)
    
    # Normalize image links early
    if 'image_link' in scraped_data.columns:
        scraped_data['image_link'] = scraped_data['image_link'].apply(normalize_image_link)

    # Create a mapping from SKU to scraped data, preferring rows with valid image links
    sku_to_data = {}
    for _, row in scraped_data.iterrows():
        sku = row['_normalized_sku']
        if not sku:
            continue

        if sku not in sku_to_data:
            sku_to_data[sku] = row
            continue

        existing = sku_to_data[sku]
        if row_has_valid_image(row) and not row_has_valid_image(existing):
            sku_to_data[sku] = row
    
    print(f"\nUnique SKUs in scraped data: {len(sku_to_data)}")
    
    column_mapping = {
        'image_link': 'E',  # Column E: Image Link
        'overview': 'F',     # Column F: Overview
        'length': 'G',       # Column G: Length
        'width': 'H',        # Column H: Width
        'height': 'I',       # Column I: Height
        'volume': 'J',       # Column J: Volume
        'diameter': 'K',     # Column K: Diameter
        'color': 'L',        # Column L: Color
        'material': 'M',     # Column M: Material
        'ean_code': 'N',     # Column N: EAN Code
        'pattern': 'O',      # Column O: Pattern
        'barcode': 'P',      # Column P: Barcode
        'product_url': 'Q',  # Column Q: Product URL (optional)
        'source': 'R',       # Column R: Source (optional)
    }
    
    # Ensure columns exist in Excel (add if missing)
    col_names = {
        'E': 'Image Link',
        'F': 'Overview',
        'G': 'Length',
        'H': 'Width',
        'I': 'Height',
        'J': 'Volume',
        'K': 'Diameter',
        'L': 'Color',
        'M': 'Material',
        'N': 'EAN Code',
        'O': 'Pattern',
        'P': 'Barcode',
        'Q': 'Product URL',
        'R': 'Source',
    }
    
    # Add columns if they don't exist
    for col_letter, col_name in col_names.items():
        if col_name not in df_excel.columns:
            df_excel[col_name] = None
    
    # Populate the data
    matches = 0
    no_matches = 0
    
    for idx, row in df_excel.iterrows():
        excel_sku = row['_normalized_sku']
        
        if excel_sku and excel_sku in sku_to_data:
            scraped_row = sku_to_data[excel_sku]
            matches += 1
            
            # Populate each mapped column
            for scraped_col, excel_col_letter in column_mapping.items():
                excel_col_name = col_names[excel_col_letter]
                value = scraped_row.get(scraped_col, 'N/A')

                if scraped_col == 'image_link':
                    value = normalize_image_link(value)
                
                # Only populate if current value is empty/None
                if pd.isna(df_excel.at[idx, excel_col_name]) or df_excel.at[idx, excel_col_name] == '':
                    df_excel.at[idx, excel_col_name] = value
            
            print(f"Matched SKU: {excel_sku} from {scraped_row.get('source', 'unknown')}")
        else:
            no_matches += 1
            if excel_sku:
                print(f"No match for SKU: {excel_sku}")
    
    # Remove temporary column
    df_excel = df_excel.drop(columns=['_normalized_sku'])
    
    # Save the updated Excel file
    output_path = excel_path.replace('.xlsx', '_updated.xlsx')
    try:
        df_excel.to_excel(output_path, index=False, engine='openpyxl')
        print(f"\n{'='*60}")
        print(f"Updated Excel saved to: {output_path}")
        print(f"  Total rows: {len(df_excel)}")
        print(f"  Matched SKUs: {matches}")
        print(f"  No matches: {no_matches}")
        print(f"{'='*60}")
    except Exception as e:
        print(f"Error saving Excel file: {e}")


def main():
    print("="*60)
    print("SAN NENG Data Arranger")
    print("="*60)
    
    # Load scraped data
    scraped_data = load_all_scraped_data()
    
    if scraped_data.empty:
        print("\nNo scraped data available. Please run the spiders first.")
        return
    
    # Path to the Excel file
    excel_path = 'sources/SAN NENG.xlsx'
    
    if not os.path.exists(excel_path):
        print(f"\nError: Excel file not found at {excel_path}")
        return
    
    # Populate the Excel file
    populate_excel(excel_path, scraped_data)
    
    print("\n" + "="*60)
    print("Process completed!")
    print("="*60)


if __name__ == '__main__':
    main()
