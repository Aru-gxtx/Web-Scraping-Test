import cloudscraper
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import re
import os  # <--- Added to handle folders

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
        if r.status_code != 200:
            return None

        soup = BeautifulSoup(r.content, "lxml")
        
        data = {
            "Item No.": "N/A",
            "Mfr Catalog No.": "N/A",
            "Group Name": "Silikomart",
            "Ecom Picture Name": "N/A",
            "SAP Picture": "N/A",
            "Inactive": "No",
            "Indent Item": "N/A",
            "# In Stock": "N/A",
            "Production Date": "N/A",
            "Item Description": "N/A",
            "Stock Description": "N/A",
            "Warranty": "N/A",
            "Serial Managed": "No",
            "# List Price": "N/A",
            "Main Category": "N/A",
            "Sub1 Category": "N/A",
            "Sub2 Category": "N/A",
            "Short Description": "N/A"
        }
        
        h1 = soup.find("h1", class_="page-title")
        if h1:
            data["Item Description"] = h1.get_text(strip=True)
        # Failsafe if title not found in h1
        else:
            title_tag = soup.find("title")
            if title_tag:
                data["Item Description"] = title_tag.text.split("|")[0].strip()

        sku_div = soup.find("div", itemprop="sku")
        if sku_div:
            data["Item No."] = sku_div.text.strip()

        th = soup.find("th", string=re.compile(r"Manufacturer Part Number", re.I))
        if th:
            td = th.find_next_sibling("td")
            if td:
                data["Mfr Catalog No."] = td.text.strip()

        price_span = soup.find("span", class_="price")
        if price_span:
            data["# List Price"] = price_span.text.strip()

        stock_container = soup.find("span", class_="stock-level")
        if not stock_container:
            stock_container = soup.find("div", class_="stock")

        if stock_container:
            status_text = stock_container.get_text(separator=" ").strip()
            status_text = " ".join(status_text.split())
            data["Stock Description"] = status_text
            
            if "Out of Stock" in status_text:
                data["Inactive"] = "Yes"
                data["# In Stock"] = "0"
            elif "In Stock" in status_text:
                data["Inactive"] = "No"

        breads = soup.select("div.breadcrumbs li")
        if len(breads) > 2: 
            data["Main Category"] = breads[2].text.strip()
        if len(breads) > 3: 
            data["Sub1 Category"] = breads[3].text.strip()
        if len(breads) > 4: 
            data["Sub2 Category"] = breads[4].text.strip()

        desc_tab = soup.find("div", id="product_description")
        
        if desc_tab:
            inner_desc = desc_tab.find("div", class_="description")
            if inner_desc:
                full_desc_text = inner_desc.get_text(separator="\n", strip=True)
            else:
                full_desc_text = desc_tab.get_text(separator="\n", strip=True).replace("Product Description", "").strip()
            
            data["Short Description"] = full_desc_text

        if data["Short Description"] == "N/A" or not data["Short Description"]:
             overview = soup.find("div", class_="product-info-overview")
             if overview:
                 data["Short Description"] = overview.text.strip()

        img_tag = soup.find("img", class_="gallery-placeholder__image")
        if img_tag and img_tag.get("src"):
             data["Ecom Picture Name"] = img_tag.get("src")
        else:
            main_img_div = soup.find("div", class_="gallery-placeholder")
            if main_img_div:
                img = main_img_div.find("img")
                if img:
                     data["Ecom Picture Name"] = img.get("src")

        if data["Ecom Picture Name"] != "N/A":
             data["SAP Picture"] = data["Ecom Picture Name"].split("/")[-1]

        return data

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
        print("Processing data...")
        df = pd.DataFrame(all_data)
        
        cols = [
            "Item No.", "Mfr Catalog No.", "Group Name", "Ecom Picture Name", 
            "SAP Picture", "Inactive", "Indent Item", "# In Stock", 
            "Production Date", "Item Description", "Stock Description", 
            "Warranty", "Serial Managed", "# List Price", "Main Category", 
            "Sub1 Category", "Sub2 Category", "Short Description"
        ]
        
        df = df.reindex(columns=cols, fill_value="N/A")
        
        folder_name = "results"
        file_name = "SouthernHospitality_Full.xlsx"
        
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
            print(f"Created folder: {folder_name}")
            
        output_path = os.path.join(folder_name, file_name)
        
        df.to_excel(output_path, index=False)
        print(f"Done! File saved successfully to: {output_path}")
    else:
        print("No data found. Check if the site is blocking the scraper.")