import requests
from bs4 import BeautifulSoup
import re

baseurl = "https://www.bakedeco.com"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

r = requests.get("https://www.bakedeco.com/nav/brand.asp?pagestart=1&categoryID=0&price=0&manufacid=551&sortby=&clearance=0&va=1", headers=headers)

soup = BeautifulSoup(r.content, "lxml")

productlist = soup.find_all("div", class_="prd_column")

product_url = set()

for prd_column in productlist:
    for link in prd_column.find_all("a", href=True):
        full_link = baseurl + link["href"]
        product_url.add(full_link) # .add() automatically ignores duplicates

testlink = "https://www.bakedeco.com/detail.asp?id=25152&categoryid=0"

r = requests.get(testlink, headers=headers)

soup = BeautifulSoup(r.content, "lxml")

brand = soup.find("h1", style="width:100%;float:left;").text.strip().split(" ")[0]
product_name = soup.find("h1", style="width:100%;float:left;").text.strip()
manufacturer_id = soup.find("div", class_="item-number").text.strip().split("MFR: ")[1].split("UPC")[0]
image_url = soup.find("div", class_="prod-image-container").find("img").get("src")
availability = soup.find("strong", string=re.compile("Stock")).text.strip()
category = soup.find("div", class_="bread").find_all("a")[2].text.strip()

print(brand)
print(product_name)
print(manufacturer_id)
print(testlink)
print(baseurl + image_url)
print(availability)
print(category)
for h in range(5):
    product_description_overview = soup.find("div", class_="description-item").find_all("p")[h].text.strip()
    print(product_description_overview)
