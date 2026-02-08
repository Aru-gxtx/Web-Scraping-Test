import requests
from bs4 import BeautifulSoup
import pandas as pd
import random
import os
import re

BASE_URL = "https://www.silikomart.com/en/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

def get_category_links():
    print(f"Fetching categories from: {BASE_URL} ...")
    try:
        r = requests.get(BASE_URL, headers=HEADERS)
        if r.status_code != 200:
            print(f"Failed to load home page: {r.status_code}")
            return []
            
        soup = BeautifulSoup(r.content, "lxml")
        category_links = set()
        
        items = soup.select('nav.navigation li.level0 > a')
        if not items:
            items = soup.select('div.category li.category a')
            
        for a in items:
            if a.get('href'):
                category_links.add(a['href'])
                
        print(f"-> Found {len(category_links)} unique categories.")
        return list(category_links)

    except Exception as e:
        print(f"Error fetching categories: {e}")
        return []

def get_product_links_from_category(category_url):
    product_links = set()
    print(f"Processing Category: {category_url}")
    
    try:
        start_url = f"{category_url}?product_list_limit=100"
        r = requests.get(start_url, headers=HEADERS)
        soup = BeautifulSoup(r.content, "lxml")
        
        total_pages = 1
        page_items = soup.select("ul.pages-items li.item a.page span")
        valid_pages = [int(s.text) for s in page_items if s.text.isdigit()]
        if valid_pages:
            total_pages = max(valid_pages)
            
        print(f"  > Found {total_pages} page(s).")
        
        for page in range(1, total_pages + 1):
            page_url = f"{category_url}?p={page}&product_list_limit=100"
            if page > 1: # Avoid re-fetching page 1 if we want to be strictly efficient, but re-fetching ensures clean logic
                r = requests.get(page_url, headers=HEADERS)
                soup = BeautifulSoup(r.content, "lxml")
            
            items = soup.select("li.product-item a.product-item-photo")
            
            count_before = len(product_links)
            for a in items:
                if a.get('href'):
                    product_links.add(a['href'])
            
            print(f"    Page {page}: Found {len(product_links) - count_before} new products.")
            
    except Exception as e:
        print(f"  Error processing category: {e}")
        
    return list(product_links)

def scrape_single_product(product_url):
    try:
        r = requests.get(product_url, headers=HEADERS)
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
            
        sku_div = soup.find("div", itemprop="sku")
        if sku_div:
            data["Item No."] = sku_div.get_text(strip=True)
            data["Mfr Catalog No."] = data["Item No."]

        price_box = soup.find("div", class_="product-info-price")
        if price_box:
            price_span = price_box.find("span", class_="price")
            if price_span:
                data["# List Price"] = price_span.get_text(strip=True)

        stock_div = soup.find("div", class_="stock")
        if stock_div:
            status_text = stock_div.get_text(strip=True)
            data["Stock Description"] = status_text
            
            if "out of stock" in status_text.lower():
                data["Inactive"] = "Yes"
                data["# In Stock"] = "0"
            elif "in stock" in status_text.lower():
                data["Inactive"] = "No"

        overview = soup.find("div", itemprop="description")
        if overview:
            data["Short Description"] = overview.get_text(separator=" ", strip=True)

        crumbs = soup.select("div.breadcrumbs ul.items li.item")
        clean_crumbs = [c.get_text(strip=True) for c in crumbs if "Home" not in c.get_text()]
        
        if len(clean_crumbs) > 0: data["Main Category"] = clean_crumbs[0]
        if len(clean_crumbs) > 1: data["Sub1 Category"] = clean_crumbs[1]
        if len(clean_crumbs) > 2: data["Sub2 Category"] = clean_crumbs[2]

        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            data["Ecom Picture Name"] = og_image["content"]
        else:
            img = soup.find("img", class_="gallery-placeholder__image")
            if img and img.get("src"):
                data["Ecom Picture Name"] = img["src"]

        if data["Ecom Picture Name"] != "N/A":
            data["SAP Picture"] = data["Ecom Picture Name"].split("/")[-1]

        if data["Short Description"] != "N/A":
            warranty_match = re.search(r"(\d+\s*(?:year|month)s?[\s\-]*(?:warranty|guarantee))", data["Short Description"], re.IGNORECASE)
            if warranty_match:
                data["Warranty"] = warranty_match.group(1).title()

        return data

    except Exception as e:
        print(f"Error scraping product {product_url}: {e}")
        return None

if __name__ == "__main__":
    
    categories = get_category_links()
    
    # Limit categories for testing
    categories = categories[:2] 

    all_product_links = set()

    for cat in categories:
        links = get_product_links_from_category(cat)
        all_product_links.update(links)
        
    print(f"Total Unique Products Found: {len(all_product_links)}")
    
    all_data = []
    
    link_list = list(all_product_links)
    
    for i, link in enumerate(link_list):
        print(f"[{i+1}/{len(link_list)}] Scraping: {link}")
        data = scrape_single_product(link)
        if data:
            all_data.append(data)
      
    if all_data:
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
        file_name = "Silikomart_Full.xlsx"
        
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
            print(f"Created folder: {folder_name}")
            
        output_path = os.path.join(folder_name, file_name)
        df.to_excel(output_path, index=False)
        print(f"Success! Saved to: {output_path}")
    else:
        print("No data extracted.")