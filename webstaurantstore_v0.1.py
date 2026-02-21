from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException
import time
import json

def get_spec_value(driver, label_text):
    try:
        # Matches the text in <dt> and gets the adjacent <dd>
        xpath = f"//dt[contains(text(), '{label_text}')]/following-sibling::dd"
        return driver.find_element(By.XPATH, xpath).text.strip()
    except:
        return "N/A"

options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.page_load_strategy = 'eager'

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.set_page_load_timeout(60)

category_urls = set()
results = []

try:
    print("Fetching category links...")
    driver.get("https://www.webstaurantstore.com/vendor/steelite-international.html")
    time.sleep(3)

    elements = driver.find_elements(By.CSS_SELECTOR, 'a[data-testid="vendor-cats ag-item"]')
    for el in elements:
        href = el.get_attribute('href')
        if href:
            category_urls.add(href)

    test_categories = list(category_urls)
    print(f"Testing {len(test_categories)} categories...")

    for cat_url in test_categories:
        print(f"\n--- Category: {cat_url} ---")
        try:
            driver.get(cat_url)
            time.sleep(2)

            product_elements = driver.find_elements(By.CSS_SELECTOR, 'a[data-testid="itemLink"]')
            
            if product_elements:
                product_url = product_elements[0].get_attribute('href')
                print(f"Visiting Product: {product_url}")
                
                driver.get(product_url)
                time.sleep(4) # Slightly longer wait for all specs to render

                try:
                    mfr_el = driver.find_element(By.CSS_SELECTOR, '[data-testid="product-detail-heading-vendor-number"] .uppercase')
                    mfr_code = mfr_el.text.strip()
                except:
                    mfr_code = "N/A"

                try:
                    img = driver.find_element(By.ID, "GalleryImage").get_attribute("src")
                except:
                    img = "Not Found"

                try:
                    # Target the span inside the list items
                    ov_elements = driver.find_elements(By.CSS_SELECTOR, "ul.list-none li span")
                    overview = " | ".join([i.text for i in ov_elements if i.text.strip()])
                except:
                    overview = "N/A"

                item_data = {
                    "MFR Code": mfr_code,
                    "URL": product_url,
                    "Image": img,
                    "Overview": overview,
                    "Height": get_spec_value(driver, "Height"),
                    "Capacity": get_spec_value(driver, "Capacity"),
                    "Color": get_spec_value(driver, "Color"),
                    "Material": get_spec_value(driver, "Material"),
                    "Shape": get_spec_value(driver, "Shape"),
                    "Diameter": get_spec_value(driver, "Diameter"),
                    "Features": get_spec_value(driver, "Features")
                }
                
                results.append(item_data)
                print(f"   -> Successfully scraped MFR: {mfr_code}")

        except TimeoutException:
            print(f"   -> Timeout on {cat_url}. Skipping...")
            continue

finally:
    driver.quit()

# Final Clean Output
print("\n" + "="*50)
print(json.dumps(results, indent=4))

"""
print("\n" + "="*50)
print("FINAL RESULTS:")
for data in results:
    print(f"\nProduct: {data['URL']}")
    print(f"\nImaget: {data['Image']}")
    print(f"\nOverview: {data['Overview']}")
    print(f"\nHeight: {data['Height']}")
    print(f"\nCapacity: {data['Capacity']}")
    print(f"\nColor: {data['Color']}")
    print(f"\nMaterial: {data['Material']}")
    print(f"\nFeatures: {data['Features']}")
"""