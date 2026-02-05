import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import time

BASE_URL = "https://www.bakedeco.com"
START_URL = "https://www.bakedeco.com/nav/brand.asp?pagestart=1&categoryID=0&price=0&manufacid=551&sortby=&clearance=0&va=1"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def get_product_links(start_url):
    print(f"Fetching list page: {start_url} ...")
    try:
        r = requests.get(start_url, headers=HEADERS)
        soup = BeautifulSoup(r.content, "lxml")
        
        product_links = set()
        
        for prd_column in soup.find_all("div", class_="prd_list_mid"):
            for link in prd_column.find_all("a", href=True):
                href = link["href"]
                if "detail.asp" in href:
                    product_links.add(href)
                    
        print(f"-> Found {len(product_links)} unique products.")
        return list(product_links)
        
    except Exception as e:
        print(f"Error fetching list page: {e}")
        return []

def scrape_single_product(relative_url):
    full_url = BASE_URL + relative_url if relative_url.startswith("/") else relative_url
    
    try:
        r = requests.get(full_url, headers=HEADERS)
        soup = BeautifulSoup(r.content, "lxml")
        
        try:
            h1_tag = soup.find("h1")
            product_name = h1_tag.text.strip()
            brand = product_name.split(" ")[0] 
        except:
            product_name = "N/A"
            brand = "N/A"

        item_num = "N/A"
        mfr_id = "N/A"
        
        item_div = soup.find("div", class_="item-number")
        if item_div:
            raw_text = item_div.text.strip() # "Item # 25152 MFR: 25.311.87.0098 ..."
            
            if "Item #" in raw_text:
                item_num = raw_text.split("Item #")[1].split("MFR")[0].strip()
            
            if "MFR:" in raw_text:
                mfr_id = raw_text.split("MFR:")[1].split("UPC")[0].strip()

        try:
            price = soup.find("div", class_="price").text.strip()
        except:
            price = "N/A"

        try:
            stock_tag = soup.find("strong", string=re.compile("Stock"))
            availability = stock_tag.text.strip() if stock_tag else "N/A"
        except:
            availability = "N/A"

        image_url = "N/A"
        img_container = soup.find("div", class_="prod-image-container")
        if img_container:
            img_tag = img_container.find("img")
            if img_tag:
                src = img_tag.get("src")
                image_url = BASE_URL + src

        main_cat = "N/A"
        sub_cat = "N/A"
        bread_div = soup.find("div", class_="bread")
        if bread_div:
            links = bread_div.find_all("a")
            if len(links) > 1: main_cat = links[1].text.strip()
            if len(links) > 2: sub_cat = links[2].text.strip()

        return {
            "Brand": brand,
            "Product Name": product_name,
            "Item Number": item_num,
            "Manufacturer ID": mfr_id,
            "Price": price,
            "Availability": availability,
            "Main Category": main_cat,
            "Sub Category": sub_cat,
            "Image URL": image_url,
            "Page URL": full_url
        }

    except Exception as e:
        print(f"Failed to scrape {full_url}: {e}")
        return None

if __name__ == "__main__":
    
    links = get_product_links(START_URL)
    
    all_data = []
    
    print("Starting data extraction...")
    for i, link in enumerate(links):
        print(f"[{i+1}/{len(links)}] Scraping: {link} ...")
        
        data = scrape_single_product(link)
        if data:
            all_data.append(data)
        
        time.sleep(0.5) 

    if all_data:
        print(f"Saving {len(all_data)} products to Excel...")
        df = pd.DataFrame(all_data)
        df.to_excel("Bakedeco_Full_Data.xlsx", index=False)
        print("Success! File saved as 'Bakedeco_Full_Data.xlsx'")
    else:
        print("No data was extracted.")