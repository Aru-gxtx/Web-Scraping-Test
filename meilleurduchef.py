import cloudscraper
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import pandas as pd
import json
import re
import time
import random
import os

BASE_URL = "https://www.meilleurduchef.com"
START_URL = "https://www.meilleurduchef.com/en/shop/brands/silikomart.html"

scraper = cloudscraper.create_scraper()

def get_product_links(start_url):
    product_links = set()
    
    print(f"Scanning page: {start_url}")
    try:
        time.sleep(random.uniform(1, 2))
        r = scraper.get(start_url)
        if r.status_code != 200:
            print(f"Failed to load page: {r.status_code}")
            return []
            
        soup = BeautifulSoup(r.content, "lxml")
        
        cards = soup.select("div.card-product a.card-link")
        if not cards: 
            cards = soup.select("div.cell-content a")
            
        new_links = 0
        for a in cards:
            href = a.get('href')
            if href and "/shop/" in href: 
                full_link = urljoin(BASE_URL, href)
                if full_link not in product_links:
                    product_links.add(full_link)
                    new_links += 1
        
        print(f"   -> Found {new_links} products.")
            
    except Exception as e:
        print(f"Error on list page: {e}")
        
    print(f"Total unique products found: {len(product_links)}")
    return list(product_links)

def scrape_single_product(url):
    try:
        time.sleep(random.uniform(0.5, 1.5))
        r = scraper.get(url)
        if r.status_code != 200: return None
        
        soup = BeautifulSoup(r.content, "lxml")
        
        data = {
            "Item No.": "N/A", "Mfr Catalog No.": "N/A", "Group Name": "Silikomart",
            "Ecom Picture Name": "N/A", "SAP Picture": "N/A", "Inactive": "No",
            "Indent Item": "N/A", "# In Stock": "N/A", "Production Date": "N/A",
            "Item Description": "N/A", "Stock Description": "N/A", "Warranty": "N/A",
            "Serial Managed": "No", "# List Price": "N/A", "Main Category": "N/A",
            "Sub1 Category": "N/A", "Sub2 Category": "N/A", "Short Description": "N/A"
        }
        
        scripts = soup.find_all("script", type="application/ld+json")
        for script in scripts:
            try:
                js = json.loads(script.string)
                
                items = []
                if isinstance(js, list): items = js
                elif isinstance(js, dict):
                    if "@graph" in js: items = js["@graph"]
                    else: items = [js]

                for item in items:
                    item_type = item.get("@type", "")

                    if item_type == "Product":
                        data["Item Description"] = item.get("name", "N/A")
                        
                        imgs = item.get("image")
                        if isinstance(imgs, list) and len(imgs) > 0: data["Ecom Picture Name"] = imgs[0]
                        elif isinstance(imgs, str): data["Ecom Picture Name"] = imgs
                        
                        if "sku" in item: data["Item No."] = item["sku"]
                        elif "gtin13" in item: data["Item No."] = item["gtin13"]
                        if "mpn" in item: data["Mfr Catalog No."] = item["mpn"]

                        offers = item.get("offers")
                        if isinstance(offers, dict):
                            data["# List Price"] = offers.get("price", "N/A")
                            avail = offers.get("availability", "")
                            if "InStock" in avail:
                                data["Stock Description"] = "In Stock"
                                data["Inactive"] = "No"
                            elif "OutOfStock" in avail or "Discontinued" in avail:
                                data["Stock Description"] = "Out of Stock"
                                data["# In Stock"] = "0"
                                data["Inactive"] = "Yes"
                        
                        data["Short Description"] = item.get("description", "N/A")

                    elif item_type == "BreadcrumbList":
                        itemList = item.get("itemListElement", [])
                        itemList.sort(key=lambda x: x.get("position", 0))
                        
                        cats = [x.get("name") for x in itemList if x.get("position") > 1]
                        
                        if len(cats) > 0: data["Main Category"] = cats[0]
                        if len(cats) > 1: data["Sub1 Category"] = cats[1]
                        if len(cats) > 2: data["Sub2 Category"] = cats[2]

            except: continue

        # Categories worst case option if not found in JSON
        if data["Main Category"] == "N/A":
            nav_bread = soup.find("nav", id="breadcrumb")
            if nav_bread:
                lis = nav_bread.select("ol li")
                clean_cats = []
                for li in lis:
                    txt = li.get_text(strip=True)
                    if txt and "Home" not in txt and "Accueil" not in txt:
                        clean_cats.append(txt)
                
                if len(clean_cats) > 0 and clean_cats[-1] in data["Item Description"]:
                    clean_cats.pop()
                    
                if len(clean_cats) > 0: data["Main Category"] = clean_cats[0]
                if len(clean_cats) > 1: data["Sub1 Category"] = clean_cats[1]
                if len(clean_cats) > 2: data["Sub2 Category"] = clean_cats[2]

        if data["Item Description"] == "N/A":
            h1 = soup.find("h1")
            if h1: data["Item Description"] = h1.get_text(strip=True)

        if data["Item No."] == "N/A":
            ref_span = soup.find("span", class_="ref")
            if not ref_span: ref_span = soup.find(string=re.compile(r"Ref\."))
            if ref_span:
                text = ref_span.get_text(strip=True) if hasattr(ref_span, 'get_text') else ref_span
                clean_ref = re.sub(r"[^\d]", "", text)
                if clean_ref: data["Item No."] = clean_ref

        if data["Ecom Picture Name"] == "N/A":
            main_img = soup.select_one("img#product-main-image, div.main-image img")
            if main_img and main_img.get("src"):
                data["Ecom Picture Name"] = urljoin(BASE_URL, main_img["src"])

        if data["Ecom Picture Name"] != "N/A" and data["Ecom Picture Name"].startswith("//"):
            data["Ecom Picture Name"] = "https:" + data["Ecom Picture Name"]

        if data["Item No."] != "N/A" and data["Mfr Catalog No."] == "N/A":
            data["Mfr Catalog No."] = data["Item No."]
        elif data["Mfr Catalog No."] != "N/A" and data["Item No."] == "N/A":
            data["Item No."] = data["Mfr Catalog No."]
            
        if data["Ecom Picture Name"] != "N/A":
            data["SAP Picture"] = data["Ecom Picture Name"].split("/")[-1]

        if data["Short Description"] != "N/A":
            w_match = re.search(r"(\d+)\s*(?:year|month)s?\s*warranty", data["Short Description"], re.IGNORECASE)
            if w_match: data["Warranty"] = w_match.group(0).title()
        
        if data["Stock Description"] == "N/A":
            if soup.find(string=re.compile(r"Unavailable|Out of stock|Discontinued", re.I)):
                data["Inactive"] = "Yes"
                data["Stock Description"] = "Out of Stock"
                data["# In Stock"] = "0"
            else:
                data["Inactive"] = "No" 

        return data

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

if __name__ == "__main__":
    
    all_links = get_product_links(START_URL)
    
    all_data = []
    
    print("Starting product extraction...")
    for i, link in enumerate(all_links):
        print(f"[{i+1}/{len(all_links)}] Scraping: {link}")
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
        file_name = "MeilleurDuChef_Silikomart_NoPage.xlsx"
        
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
            
        output_path = os.path.join(folder_name, file_name)
        
        df.to_excel(output_path, index=False)
        print(f"\nSuccess! Saved to: {output_path}")
    else:
        print("No data extracted.")