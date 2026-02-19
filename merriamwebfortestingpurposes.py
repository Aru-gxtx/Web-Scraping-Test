import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import json
import os  # <--- Added to handle folders

BASE_URL = "https://www.bakedeco.com"
START_URL = "https://www.bakedeco.com/nav/brand.asp?pagestart=1&categoryID=0&price=0&manufacid=551&sortby=&clearance=0&va=1"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def get_product_links(start_url):
    print(f"Fetching product list from: {start_url} ...")
    try:
        r = requests.get(start_url, headers=HEADERS)
        if r.status_code != 200:
            print(f"Failed to load page: {r.status_code}")
            return []
            
        soup = BeautifulSoup(r.content, "lxml")
        product_links = set()
        
        for prd_column in soup.find_all("div", class_="prd_list_mid"):
            for link in prd_column.find_all("a", href=True):
                href = link["href"]
                if "detail.asp" in href:
                    if href.startswith("http"):
                        full_link = href
                    else:
                        clean_href = href.lstrip("/") 
                        full_link = f"{BASE_URL}/{clean_href}"
                    
                    product_links.add(full_link)
        
        print(f"-> Found {len(product_links)} unique products.")
        return list(product_links)
        
    except Exception as e:
        print(f"Error fetching product list: {e}")
        return []

def scrape_single_product(full_url):
    try:
        r = requests.get(full_url, headers=HEADERS)
        if r.status_code != 200: 
            return None
            
        soup = BeautifulSoup(r.content, "lxml")
        
        data = {
            "Item No.": "N/A",
            "Mfr Catalog No.": "N/A",
            "Group Name": "Silikomart", 
            "Ecom Picture Name": "N/A",
            "SAP Picture": "N/A",
            "Inactive": "No",             # Default to No since page loaded
            "Indent Item": "N/A",
            "# In Stock": "N/A",          # Quantity not available in source
            "Production Date": "N/A",     # Date not available in source (2)
            "Item Description": "N/A",    # Main Title
            "Stock Description": "N/A",   # Status (In Stock/Out of Stock)
            "Warranty": "N/A",
            "Serial Managed": "No",       # Default to No
            "# List Price": "N/A",
            "Main Category": "N/A",
            "Sub1 Category": "N/A",
            "Sub2 Category": "N/A",
            "Short Description": "N/A"    # Technical Specs
        }

        try:
            h1 = soup.find("h1")
            if h1:
                prod_name = h1.text.strip()
                data["Item Description"] = prod_name
                
                if "Silikomart" in prod_name:
                    data["Group Name"] = "Silikomart"
                else:
                    data["Group Name"] = prod_name.split(" ")[0]
        except: pass

        try:
            item_div = soup.find("div", class_="item-number")
            if item_div:
                raw_text = item_div.text.strip()
                if "Item #" in raw_text:
                    parts = raw_text.split("Item #")[1]
                    val = parts.split("MFR")[0].split("|")[0].strip()
                    data["Item No."] = val
                
                if "MFR" in raw_text:
                    parts = raw_text.split("MFR")[1]
                    val = parts.replace(":", "").split("UPC")[0].strip()
                    data["Mfr Catalog No."] = val

            # Sync Item No and Mfr Catalog No if one is missing
            if data["Item No."] == "N/A" and data["Mfr Catalog No."] != "N/A":
                data["Item No."] = data["Mfr Catalog No."]
            elif data["Mfr Catalog No."] == "N/A" and data["Item No."] != "N/A":
                data["Mfr Catalog No."] = data["Item No."]
                
        except: pass

        try:
            price_div = soup.find("div", class_="price")
            if price_div:
                data["# List Price"] = price_div.text.strip().replace("Our Price:", "").strip()
        except: pass

        try:
            status_found = "N/A"
            
            json_tag = soup.find("script", type="application/ld+json")
            if json_tag:
                try:
                    ld_data = json.loads(json_tag.string)
                    if isinstance(ld_data, list): ld_data = ld_data[0]
                    offers = ld_data.get("offers", {})
                    if isinstance(offers, list): offers = offers[0]
                    
                    availability = offers.get("availability", "")
                    if "InStock" in availability:
                        status_found = "In Stock"
                    elif "OutOfStock" in availability:
                        status_found = "Out of Stock"
                    elif "PreOrder" in availability:
                         status_found = "Backorder"
                         
                    qty = offers.get("inventoryLevel", {}).get("value")
                    if qty:
                        data["# In Stock"] = qty
                except: pass

            # Failsafe if status wasn't found in JSON, check page elements
            if status_found == "N/A":
                stock_strong = soup.find("strong", string=re.compile(r"^In Stock$", re.I))
                if stock_strong:
                    status_found = "In Stock"
                else:
                    other_strong = soup.find("strong", string=re.compile(r"Out of Stock|Backorder|Special Order", re.I))
                    if other_strong:
                        status_found = other_strong.text.strip()
            
            data["Stock Description"] = status_found
            
        except: pass

        try:
            img_container = soup.find("div", class_="prod-image-container")
            if img_container:
                img = img_container.find("img")
                if img and img.get("src"):
                    src = img["src"]
                    if src.startswith("http"):
                        full_img_url = src
                    else:
                        full_img_url = f"{BASE_URL}/{src.lstrip('/')}"
                    
                    data["Ecom Picture Name"] = full_img_url
                    data["SAP Picture"] = full_img_url.split("/")[-1]
        except: pass

        try:
            bread_div = soup.find("div", class_="bread")
            if bread_div:
                links = bread_div.find_all("a")
                if len(links) > 1: data["Main Category"] = links[1].text.strip()
                if len(links) > 2: data["Sub1 Category"] = links[2].text.strip()
                if len(links) > 3: data["Sub2 Category"] = links[3].text.strip()
        except: pass

        try:
            short_desc_div = soup.find("div", class_="desc short")
            if short_desc_div:
                clean_text = short_desc_div.get_text(separator=" | ").strip()
                data["Short Description"] = clean_text[:500]
            else:
                meta_desc = soup.find("meta", attrs={"name": "description"})
                if meta_desc:
                    data["Short Description"] = meta_desc["content"].strip()
                else:
                    desc_div = soup.find("div", id="ndisplay")
                    if desc_div:
                        data["Short Description"] = desc_div.text.strip()[:200] + "..."
        except: pass

        return data

    except Exception as e:
        print(f"Error scraping {full_url}: {e}")
        return None

if __name__ == "__main__":
    print("--- Starting Scraper ---")
    
    all_links = get_product_links(START_URL)
    
    if not all_links:
        print("No products found. Please check the URL.")
    else:
        all_products = []
        for i, link in enumerate(all_links):
            print(f"[{i+1}/{len(all_links)}] Scraping: {link}")
            product_data = scrape_single_product(link)
            if product_data:
                all_products.append(product_data)
            
        if all_products:
            df = pd.DataFrame(all_products)
            
            cols = [
                "Item No.", "Mfr Catalog No.", "Group Name", "Ecom Picture Name", 
                "SAP Picture", "Inactive", "Indent Item", "# In Stock", 
                "Production Date", "Item Description", "Stock Description", 
                "Warranty", "Serial Managed", "# List Price", "Main Category", 
                "Sub1 Category", "Sub2 Category", "Short Description"
            ]
            
            df = df.reindex(columns=cols, fill_value="N/A")
            
            folder_name = "results"
            file_name = "Bakedeco_Silikomart_Final.xlsx"
            
            if not os.path.exists(folder_name):
                os.makedirs(folder_name)
                print(f"Created folder: {folder_name}")
            
            output_path = os.path.join(folder_name, file_name)
            
            df.to_excel(output_path, index=False)
            print(f"\nSuccess! Saved {len(df)} records to '{output_path}'.")
        else:
            print("\nNo data extracted.")