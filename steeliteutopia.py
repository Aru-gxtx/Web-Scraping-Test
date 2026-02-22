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
        # Use 'contains' to be flexible with labels like "Top Diameter"
        xpath = f"//dt[contains(text(), '{label_text}')]/following-sibling::dd"
        return driver.find_element(By.XPATH, xpath).text.strip()
    except:
        return ""

# Helper for Steelite-Utopia Barcode
def get_barcode_utopia(driver, mfr_code):
    try:
        utopia_url = f"https://www.steelite-utopia.com/products/{mfr_code}"
        driver.get(utopia_url)
        time.sleep(2)
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

        # Handle Search Grid vs Direct Product Page
        if "search" in driver.current_url or len(driver.find_elements(By.ID, "GalleryImage")) == 0:
            try:
                first_result = driver.find_element(By.CSS_SELECTOR, 'a[data-testid="itemLink"]')
                first_result.click()
                time.sleep(3)
            except:
                print(f"   -> No Webstaurant product page found for {mfr_code}")
                continue

        try:
            # Image Link
            try:
                img_el = driver.find_element(By.ID, "GalleryImage")
                df.at[index, 'Image Link'] = img_el.get_attribute("src")
            except: pass

            # Overview
            try:
                ov_elements = driver.find_elements(By.CSS_SELECTOR, "ul.list-none li span")
                df.at[index, 'Overview'] = " | ".join([i.text for i in ov_elements if i.text.strip()])
            except: pass

            # All Specifications
            df.at[index, 'Height'] = get_spec_value(driver, "Height")
            df.at[index, 'Capacity'] = get_spec_value(driver, "Capacity")
            df.at[index, 'Color'] = get_spec_value(driver, "Color")
            df.at[index, 'Material'] = get_spec_value(driver, "Material")
            df.at[index, 'Features'] = get_spec_value(driver, "Features")
            df.at[index, 'Shape'] = get_spec_value(driver, "Shape")
            df.at[index, 'Edge Style'] = get_spec_value(driver, "Edge Style")
            df.at[index, 'Length'] = get_spec_value(driver, "Length")
            df.at[index, 'Width'] = get_spec_value(driver, "Width")
            
            # Flexible Diameter check
            dia = get_spec_value(driver, "Diameter")
            if not dia: dia = get_spec_value(driver, "Top")
            df.at[index, 'Diameter'] = dia

            print(f"   -> Success! Found Specs & Barcode.")

        except Exception as e:
            print(f"   -> Webstaurant extraction failed: {e}")

        # Save progress every 5 rows
        if index % 5 == 0:
            df.to_excel(OUTPUT_FILE, index=False)

finally:
    df.to_excel(OUTPUT_FILE, index=False)
    driver.quit()
    print(f"Finished! Updated file saved as: {OUTPUT_FILE}")