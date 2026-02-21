import pandas as pd
from playwright.sync_api import sync_playwright

INPUT_FILE = "sources/STEELITE.xlsx" 
OUTPUT_FILE = "STEELITE_Filled.xlsx"

def scrape_by_mfr():
    print(f"Loading data from {INPUT_FILE}...")
    df = pd.read_excel(INPUT_FILE)

    test_df = df.head(3).copy() 
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        for index, row in test_df.iterrows():
            mfr_code = row['Mfr Catalog No.']
            
            # Skip empty rows if any exist
            if pd.isna(mfr_code) or str(mfr_code).strip() == "":
                continue
                
            print(f"[{index + 1}/{len(test_df)}] Searching for MFR: {mfr_code}")
            
            search_url = f"https://www.webstaurantstore.com/search/{mfr_code}.html"
            
            try:
                page.goto(search_url)
                
                # Check if it loaded a product page. (Usually exact MFR matches redirect straight to the product!)
                try:
                    page.wait_for_selector("img#GalleryImage", timeout=5000)
                except Exception:
                    # If it didn't redirect, we might be on a search results page. Click the first result.
                    try:
                        first_product = page.locator('a[data-testid="itemLink"]').first
                        if first_product.count() > 0:
                            page.goto("https://www.webstaurantstore.com" + first_product.get_attribute("href"))
                            page.wait_for_selector("img#GalleryImage", timeout=5000)
                    except Exception:
                        print(f"  -> Could not find a product match for {mfr_code}. Skipping.")
                        continue
         
                try:
                    img_el = page.locator("img#GalleryImage").first
                    src = img_el.get_attribute("data-src") or img_el.get_attribute("src")
                    test_df.at[index, 'Image Link'] = src
                except Exception:
                    pass
                
                # Overview
                try:
                    overview_el = page.locator("ul.m-0.mb-5.p-0.list-none").first
                    raw_bullets = overview_el.inner_text().strip()
                    test_df.at[index, 'Overview'] = raw_bullets.replace('\n', ' | ')
                except Exception:
                    pass
                
                # Specifications
                desired_specs = [
                    "Length", "Width", "Height", "Volume", "Capacity", "Diameter", 
                    "Color", "Material", "EAN Code", "Pattern", "Barcode",
                    "Features", "Shape"
                ]
                
                for spec in desired_specs:
                    try:
                        locator_string = f"dt:has-text('{spec}') + dd"
                        val = page.locator(locator_string).first.inner_text().strip()
                        if spec == "Features":
                            val = val.replace("\n\xa0\n", ", ").replace("\n", ", ")
                        
                        if spec in test_df.columns:
                            test_df.at[index, spec] = val
                    except Exception:
                        pass
                
                # Edge Style (Handled separately because it is capitalized differently in your CSV)
                try:
                    val = page.locator("dt:has-text('Edge style') + dd").first.inner_text().strip()
                    if 'Edge Style' in test_df.columns:
                        test_df.at[index, 'Edge Style'] = val
                except Exception:
                    pass

                print("  -> Success!")
                page.wait_for_timeout(1000) # Small pause to avoid bot detection

            except Exception as e:
                print(f"  -> Error loading page for {mfr_code}")

        browser.close()
        
    test_df.to_excel(OUTPUT_FILE, index=False)
    print(f"\nAll done! Data saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    scrape_by_mfr()