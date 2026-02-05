import cloudscraper
from bs4 import BeautifulSoup
import pandas as pd
import time
import random

scraper = cloudscraper.create_scraper()

BASE_URL = "https://www.southernhospitality.co.nz"
START_URL = "https://www.southernhospitality.co.nz/brands/silikomart.html"

def get_product_links(start_url):
    print(f"Fetching list page: {start_url} ...")
    try:
        r = scraper.get(start_url)
        if r.status_code != 200:
            print(f"Blocked! Status code: {r.status_code}")
            return []

        soup = BeautifulSoup(r.content, "lxml")
        
        product_links = set()
        
        cards = soup.select("div.product-item-details")
        print(f"Found {len(cards)} product cards on list page.")

        for card in cards:
            link_tag = card.find("a", href=True)
            if link_tag:
                product_links.add(link_tag["href"])
                    
        print(f"-> Found {len(product_links)} unique product links.")
        return list(product_links)

    except Exception as e:
        print(f"Error fetching list: {e}")
        return []

def scrape_single_product(product_url):
    try:
        time.sleep(random.uniform(1, 3)) 
        
        r = scraper.get(product_url)
        soup = BeautifulSoup(r.content, "lxml")
        
        h1 = soup.find("h1", class_="page-title")
        item_desc = h1.text.strip() if h1 else "N/A"
        
        sku_div = soup.find("div", itemprop="sku")
        item_no = sku_div.text.strip() if sku_div else "N/A"

        mfr_no = "N/A"
        th = soup.find("th", string="Manufacturer Part Number")
        if th:
            mfr_no = th.find_next_sibling("td").text.strip()

        price_span = soup.find("span", class_="price")
        list_price = price_span.text.strip() if price_span else "N/A"

        stock_div = soup.find("div", class_="stock")
        if stock_div:
            stock_desc = stock_div.text.strip() # e.g. "In Stock"
            is_in_stock = "Yes" if "In Stock" in stock_desc else "No"
        else:
            stock_desc = "N/A"
            is_in_stock = "Unknown"

        inactive = "Yes" if "Out of Stock" in stock_desc else "No"

        main_cat = "N/A"
        sub1_cat = "N/A"
        sub2_cat = "N/A"
        
        breads = soup.select("div.breadcrumbs li")
        if len(breads) > 1: main_cat = breads[1].text.strip()
        if len(breads) > 2: sub1_cat = breads[2].text.strip()
        if len(breads) > 3: sub2_cat = breads[3].text.strip()

        short_desc_div = soup.find("div", class_="product-info-overview")
        short_desc = short_desc_div.text.strip() if short_desc_div else "N/A"
        
        warranty = "Check Description" 

        img_tag = soup.find("img", class_="gallery-placeholder__image")
        if img_tag:
            ecom_pic = img_tag.get("src")
        else:
            ecom_pic = "N/A"

        group_name = "Silikomart" # Hardcoded based on URL
        sap_picture = "Internal Data (Not Public)"
        indent_item = "Internal Data (Not Public)"
        prod_date = "Internal Data (Not Public)"
        serial_manage = "Internal Data (Not Public)"

        return {
            "Item No": item_no,
            "Mfr Catalog No": mfr_no,
            "Group Name": group_name,
            "Ecom Picture Name": ecom_pic,
            "Sap Picture": sap_picture,
            "Inactive": inactive,
            "Indent Item": indent_item,
            "In Stock": is_in_stock,
            "Production Date": prod_date,
            "Item Description": item_desc,
            "Stock Description": stock_desc,
            "Warranty": warranty,
            "Serial Manage": serial_manage,
            "List Price": list_price,
            "Main Category": main_cat,
            "Sub1 Category": sub1_cat,
            "Sub2 Category": sub2_cat,
            "Short Description": short_desc,
            "Product URL": product_url
        }

    except Exception as e:
        print(f"Error scraping {product_url}: {e}")
        return None

if __name__ == "__main__":
    
    links = get_product_links(START_URL)
    
    all_data = []
    
    print("Starting extraction...")
    for i, link in enumerate(links):
        print(f"[{i+1}/{len(links)}] Scraping: {link}")
        
        data = scrape_single_product(link)
        if data:
            all_data.append(data)
            
    if all_data:
        print("Saving to Excel...")
        df = pd.DataFrame(all_data)
        df.to_excel("SouthernHospitality_Full.xlsx", index=False)
        print("Done! File saved as 'SouthernHospitality_Full.xlsx'")
    else:
        print("No data found. Check if the site is blocking the scraper.")