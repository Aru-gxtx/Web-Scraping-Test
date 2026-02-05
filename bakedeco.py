import requests
from bs4 import BeautifulSoup
import re
import pandas as pd

baseurl = "https://www.bakedeco.com"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

print("Fetching product list...")
r = requests.get("https://www.bakedeco.com/nav/brand.asp?pagestart=1&categoryID=0&price=0&manufacid=551&sortby=&clearance=0&va=1", headers=headers)
soup = BeautifulSoup(r.content, "lxml")

product_url = set()

for prd_column in soup.find_all("div", class_="prd_list_mid"):
    for link in prd_column.find_all("a", href=True):
        product_url.add(link["href"])

print(f"Found {len(product_url)} unique links. Starting scrape...")

all_products_data = []

for url in list(product_url):
    if "detail.asp" in url:
        try:
            full_link = baseurl + url if url.startswith("/") else url
            
            r = requests.get(full_link, headers=headers)
            soup = BeautifulSoup(r.content, "lxml")

            brand = soup.find("h1", style="width:100%;float:left;").text.strip().split(" ")[0]
            product_name = soup.find("h1", style="width:100%;float:left;").text.strip()
            
            mfr_div = soup.find("div", class_="item-number")
            if mfr_div and "MFR:" in mfr_div.text:
                manufacturer_id = mfr_div.text.strip().split("MFR: ")[1].split("UPC")[0].strip()
            else:
                manufacturer_id = "N/A"

            img_container = soup.find("div", class_="prod-image-container")
            if img_container and img_container.find("img"):
                image_url = baseurl + img_container.find("img").get("src")
            else:
                image_url = "N/A"

            stock_tag = soup.find("strong", string=re.compile("Stock"))
            availability = stock_tag.text.strip() if stock_tag else "N/A"

            bread_div = soup.find("div", class_="bread")
            if bread_div:
                links = bread_div.find_all("a")
                category = links[2].text.strip() if len(links) >= 3 else "N/A"
            else:
                category = "N/A"

            desc_div = soup.find("div", class_="description-item")
            if desc_div and desc_div.find_all("p"):
                description = desc_div.find_all("p")[0].text.strip()
            else:
                description = "N/A"

            product_data = {
                "Brand": brand,
                "Product Name": product_name,
                "Manufacturer ID": manufacturer_id,
                "Product URL": full_link,
                "Image URL": image_url,
                "Availability": availability,
                "Category": category,
                "Description": description
            }
            
            all_products_data.append(product_data)
            print(f"Scraped: {product_name[:30]}...") # Print progress

        except Exception as e:
            print(f"Error scraping {url}: {e}")
            continue

print("Saving to Excel...")
df = pd.DataFrame(all_products_data)
df.to_excel("Bakedeco_Products.xlsx", index=False)
print("Done! File saved as 'Bakedeco_Products.xlsx'")