import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import os

INPUT_FILE = 'sources/STEELITE.xlsx'
OUTPUT_FILE = 'results/STEELITE_Updated.xlsx'

# Helper for WebstaurantStore (dt/dd layout)
def get_spec_value(driver, label_text):
    try:
        xpath = f"//dt[contains(text(), '{label_text}')]/following-sibling::dd"
        return driver.find_element(By.XPATH, xpath).text.strip()
    except:
        return ""

# NEW Helper for Steelite-Utopia (span class layout)
def get_barcode_utopia(driver, mfr_code):
    try:
        utopia_url = f"https://www.steelite-utopia.com/products/{mfr_code}"
        driver.get(utopia_url)
        time.sleep(2)
        # Finds the span with class info-value that is a sibling to "Outer Barcode"
        xpath = "//span[contains(text(), 'Outer Barcode')]/following-sibling::span[@class='info-value']"
        return driver.find_element(By.XPATH, xpath).text.strip()
    except:
        return ""

# Load Excel
df = pd.read_excel(INPUT_FILE)

options = webdriver.ChromeOptions()
options.page_load_strategy = 'eager'
options.add_argument('--headless')
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

try:
    for index, row in df.iterrows():
        mfr_code = str(row['Mfr Catalog No.']).strip()
        
        if not mfr_code or mfr_code == 'nan' or mfr_code == "":
            continue

        print(f"[{index + 1} / {len(df)}] Processing MFR: {mfr_code}...")

        barcode = get_barcode_utopia(driver, mfr_code)
        df.at[index, 'Barcode'] = barcode

        search_url = f"https://www.webstaurantstore.com/search/{mfr_code}.html"
        driver.get(search_url)
        time.sleep(3)

        # Search result handling logic
        if "search" in driver.current_url or len(driver.find_elements(By.ID, "GalleryImage")) == 0:
            try:
                first_result = driver.find_element(By.CSS_SELECTOR, 'a[data-testid="itemLink"]')
                first_result.click()
                time.sleep(3)
            except:
                print(f"   -> No Webstaurant result for {mfr_code}")
                continue

        # Scrape the product page data
        try:
            # (Image, Overview, and existing Specs logic...)
            df.at[index, 'Height'] = get_spec_value(driver, "Height")
            df.at[index, 'Capacity'] = get_spec_value(driver, "Capacity")
            df.at[index, 'Color'] = get_spec_value(driver, "Color")
            df.at[index, 'Material'] = get_spec_value(driver, "Material")
            df.at[index, 'Diameter'] = get_spec_value(driver, "Diameter")
            df.at[index, 'Edge Style'] = get_spec_value(driver, "Edge Style")
            df.at[index, 'Length'] = get_spec_value(driver, "Length")
            df.at[index, 'Width'] = get_spec_value(driver, "Width")

            print(f"   -> Success! Barcode: {barcode if barcode else 'N/A'}")

        except Exception as e:
            print(f"   -> Webstaurant scrape failed: {e}")

        # Save progress every 5 rows
        if index % 5 == 0:
            df.to_excel(OUTPUT_FILE, index=False)

finally:
    df.to_excel(OUTPUT_FILE, index=False)
    driver.quit()
    print(f"Finished! Updated file saved as: {OUTPUT_FILE}")