import requests
from bs4 import BeautifulSoup
import pandas as pd
import random
import os
import re
import json

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
        
        items = soup.select("li.product-item a.product-item-photo")
        for a in items:
            if a.get('href'):
                product_links.add(a['href'])
        
        print(f"    Found {len(product_links)} products in this category.")
            
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

        try:
            scripts = soup.find_all("script")
            for script in scripts:
                if script.string and "dlObjects" in script.string:
                    match = re.search(r'var dlObjects=\[(.*?)\];', script.string, re.DOTALL)
                    if match:
                        json_str = match.group(1)
                        dl_data = json.loads(json_str)
                        
                        if "ecommerce" in dl_data and "detail" in dl_data["ecommerce"]:
                            prod_info = dl_data["ecommerce"]["detail"]["products"][0]
                            
                            # I read somewhere that Item No and MFR can often be the same
                            if "id" in prod_info:
                                data["Item No."] = prod_info["id"]
                                data["Mfr Catalog No."] = prod_info["id"]
                          
                            if "dimension4" in prod_info:
                                data["Stock Description"] = prod_info["dimension4"]
                                if "In stock" in data["Stock Description"]:
                                    data["# In Stock"] = "In Stock"
                                    data["Inactive"] = "No"
                                else:
                                    data["Inactive"] = "Yes"
                                    data["# In Stock"] = "0"
                            
                            if "price" in prod_info:
                                data["# List Price"] = prod_info["price"]

                            if "category" in prod_info and prod_info["category"]:
                                cat_path = prod_info["category"].split("/")
                                if len(cat_path) > 0: data["Main Category"] = cat_path[0]
                                if len(cat_path) > 1: data["Sub1 Category"] = cat_path[1]
                                if len(cat_path) > 2: data["Sub2 Category"] = cat_path[2]
        except:
            pass

        # Failsafe for categories not found
        if data["Main Category"] == "N/A":
            crumbs = soup.select("div.breadcrumbs ul.items li.item")
            clean_crumbs = [c.get_text(strip=True) for c in crumbs if "Home" not in c.get_text()]
            if len(clean_crumbs) > 0: data["Main Category"] = clean_crumbs[0]
            if len(clean_crumbs) > 1: data["Sub1 Category"] = clean_crumbs[1]
            if len(clean_crumbs) > 2: data["Sub2 Category"] = clean_crumbs[2]

        # Failsafe for SKU not found
        if data["Item No."] == "N/A":
            ld_scripts = soup.find_all("script", type="application/ld+json")
            for script in ld_scripts:
                try:
                    js_data = json.loads(script.string)
                    if isinstance(js_data, list): js_data = js_data[0]
                    
                    if "sku" in js_data:
                        data["Item No."] = js_data["sku"]
                        data["Mfr Catalog No."] = js_data["sku"]
                        
                    if "offers" in js_data:
                        offer = js_data["offers"]
                        if isinstance(offer, list): offer = offer[0]
                        
                        avail = offer.get("availability", "")
                        if "InStock" in avail:
                            data["Stock Description"] = "In Stock"
                            data["# In Stock"] = "In Stock"
                            data["Inactive"] = "No"
                        elif "OutOfStock" in avail:
                            data["Stock Description"] = "Out of Stock"
                            data["# In Stock"] = "0"
                            data["Inactive"] = "Yes"
                except: continue

        if data["Stock Description"] == "N/A":
            meta_avail = soup.find("meta", property="product:availability")
            if meta_avail:
                content = meta_avail.get("content", "").lower()
                if "instock" in content:
                    data["Stock Description"] = "In Stock"
                    data["# In Stock"] = "In Stock"
                    data["Inactive"] = "No"
                else:
                    data["Stock Description"] = "Out of Stock"
                    data["# In Stock"] = "0"
                    data["Inactive"] = "Yes"

        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc:
             data["Short Description"] = meta_desc["content"].strip()

        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            data["Ecom Picture Name"] = og_image["content"]
        else:
            img = soup.find("img", class_="gallery-placeholder__image")
            if img and img.get("src"):
                data["Ecom Picture Name"] = img["src"]

        if data["Ecom Picture Name"] != "N/A":
            data["SAP Picture"] = data["Ecom Picture Name"].split("/")[-1]

        return data

    except Exception as e:
        print(f"Error scraping product {product_url}: {e}")
        return None

if __name__ == "__main__":
    
    categories = get_category_links()
    
    all_product_links = set()

    for cat in categories:
        links = get_product_links_from_category(cat)
        all_product_links.update(links)
        if len(all_product_links):
            break
        
    print(f"Total Unique Products Found: {len(all_product_links)}")
    
    all_data = []
    link_list = list(all_product_links)
    
    print(f"\n--- SCRAPING {len(link_list)} PRODUCTS (TEST LIMIT) ---")
    
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
        file_name = "Silikomart_Final_Test.xlsx"
        
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
            
        output_path = os.path.join(folder_name, file_name)
        df.to_excel(output_path, index=False)
        print(f"Success! Saved {len(df)} records to: {output_path}")
    else:
        print("No data extracted.")