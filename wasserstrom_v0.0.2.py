import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import os

INPUT_FILE = 'results/STEELITE_Updated.xlsx'
OUTPUT_FILE = 'results/STEELITE_Updated_v0.0.2.xlsx'

def get_spec_value_webstaurant(driver, label_text):
    try:
        xpath = f"//dt[contains(text(), '{label_text}')]/following-sibling::dd"
        return driver.find_element(By.XPATH, xpath).text.strip()
    except: return ""

def get_spec_wasserstrom(driver, mfr_code, label_text):
    try:
        # Construct search URL (Wasserstrom uses MFR in search well)
        url = f"https://www.wasserstrom.com/search?searchTerm={mfr_code}"
        driver.get(url)
        
        # If redirected to product page, find the div with the heading then its sibling 'item'
        xpath = f"//div[@class='heading' and contains(text(), '{label_text}')]/following-sibling::div[@class='item']"
        return driver.find_element(By.XPATH, xpath).text.strip()
    except: return ""

def get_barcode_utopia(driver, mfr_code):
    try:
        url = f"https://www.steelite-utopia.com/products/{mfr_code}"
        driver.get(url)
        xpath = "//span[contains(text(), 'Outer Barcode')]/following-sibling::span[@class='info-value']"
        return driver.find_element(By.XPATH, xpath).text.strip()
    except: return ""

df = pd.read_excel(INPUT_FILE)
options = webdriver.ChromeOptions()
options.page_load_strategy = 'eager'
options.add_argument('--headless')
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

try:
    for index, row in df.iloc[542:].iterrows():
        mfr_code = str(row['Mfr Catalog No.']).strip()
        if not mfr_code or mfr_code == 'nan' or mfr_code == "": continue

        print(f"[{index + 1} / {len(df)}] Scraping MFR: {mfr_code}...")

        df.at[index, 'Barcode'] = get_barcode_utopia(driver, mfr_code)

        df.at[index, 'Volume'] = get_spec_wasserstrom(driver, mfr_code, "Volume")
        df.at[index, 'Pattern'] = get_spec_wasserstrom(driver, mfr_code, "Pattern")

        search_url = f"https://www.webstaurantstore.com/search/{mfr_code}.html"
        driver.get(search_url)

        if "search" in driver.current_url or len(driver.find_elements(By.ID, "GalleryImage")) == 0:
            try:
                driver.find_element(By.CSS_SELECTOR, 'a[data-testid="itemLink"]').click()
            except: continue

        # Extract Webstaurant Data
        try:
            # Image & Overview
            try: df.at[index, 'Image Link'] = driver.find_element(By.ID, "GalleryImage").get_attribute("src")
            except: pass
            try:
                ovs = driver.find_elements(By.CSS_SELECTOR, "ul.list-none li span")
                df.at[index, 'Overview'] = " | ".join([i.text for i in ovs if i.text.strip()])
            except: pass

            # Specs
            df.at[index, 'Height'] = get_spec_value_webstaurant(driver, "Height")
            df.at[index, 'Capacity'] = get_spec_value_webstaurant(driver, "Capacity")
            df.at[index, 'Color'] = get_spec_value_webstaurant(driver, "Color")
            df.at[index, 'Material'] = get_spec_value_webstaurant(driver, "Material")
            df.at[index, 'Features'] = get_spec_value_webstaurant(driver, "Features")
            df.at[index, 'Shape'] = get_spec_value_webstaurant(driver, "Shape")
            df.at[index, 'Edge Style'] = get_spec_value_webstaurant(driver, "Edge Style")
            df.at[index, 'Length'] = get_spec_value_webstaurant(driver, "Length")
            df.at[index, 'Width'] = get_spec_value_webstaurant(driver, "Width")
            
            dia = get_spec_value_webstaurant(driver, "Diameter")
            if not dia: dia = get_spec_value_webstaurant(driver, "Top")
            df.at[index, 'Diameter'] = dia

            print(f"   -> Complete data captured.")
        except Exception as e:
            print(f"   -> Webstaurant error: {e}")

        if index % 20 == 0:
            print(f"--- Saving Progress at Row {index + 1} ---")
            df.to_excel(OUTPUT_FILE, index=False)

finally:
    df.to_excel(OUTPUT_FILE, index=False)
    driver.quit()
    print(f"Finished! File saved to {OUTPUT_FILE}")