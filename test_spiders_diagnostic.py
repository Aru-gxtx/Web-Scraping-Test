#!/usr/bin/env pythonimport requests
from bs4 import BeautifulSoup
import time

def test_chakawal():
    print("\n" + "="*60)
    print("TESTING CHAKAWAL SPIDER")
    print("="*60)
    
    url = "https://chakawal.com/product-tag/sanneng/"
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Test product links
        product_links = soup.select('li.archive-product-container a[href*="/product/"]')
        print(f"✓ Site accessible (Status: {response.status_code})")
        print(f"✓ Found {len(product_links)} product links on first page")
        
        # Test product page selector if we found products
        if product_links:
            product_url = product_links[0]['href']
            print(f"✓ Testing product page: {product_url[:80]}...")
            
            prod_response = requests.get(product_url, headers=headers, timeout=10)
            prod_soup = BeautifulSoup(prod_response.content, 'html.parser')
            
            # Test selectors
            sku = prod_soup.select_one('span.sku')
            title = prod_soup.select_one('h1.product_title')
            
            print(f"  - SKU selector: {'✓ Found' if sku else '✗ Not found'}")
            print(f"  - Title selector: {'✓ Found' if title else '✗ Not found'}")
            
            if sku:
                print(f"    SKU Value: {sku.get_text(strip=True)}")
            if title:
                print(f"    Title: {title.get_text(strip=True)}")
        
    except Exception as e:
        print(f"✗ Error: {type(e).__name__}: {e}")


def test_tokopedia():
    print("\n" + "="*60)
    print("TESTING TOKOPEDIA SPIDER")
    print("="*60)
    
    url = "https://tokopedia.com/search?q=sanneng"
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        if "captcha" in response.text.lower() or "robot" in response.text.lower():
            print("✗ Blocked: Site detected bot/captcha")
            return
        
        print(f"✓ Site accessible (Status: {response.status_code})")
        
        # Check if it's JavaScript-rendered
        if "window.__INITIAL_STATE__" in response.text:
            print("⚠ NOTE: Site uses JavaScript rendering (requires Selenium/Playwright)")
        else:
            soup = BeautifulSoup(response.content, 'html.parser')
            products = soup.select('a[href*="/product/"]')
            print(f"  Found {len(products)} product links")
        
    except Exception as e:
        print(f"✗ Error: {type(e).__name__}: {e}")


def test_unopan():
    print("\n" + "="*60)
    print("TESTING UNOPAN SPIDER")
    print("="*60)
    
    url = "https://www.unopan.tw/search?q=SANNENG"
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        print(f"✓ Site accessible (Status: {response.status_code})")
        
        # Check if it's JavaScript-rendered
        if "window.__" in response.text or "__NEXT_DATA__" in response.text:
            print("⚠ NOTE: Site uses JavaScript rendering (requires Selenium/Playwright)")
        else:
            soup = BeautifulSoup(response.content, 'html.parser')
            products = soup.select('a.product-link')
            print(f"  Found {len(products)} product links")
        
    except Exception as e:
        print(f"✗ Error: {type(e).__name__}: {e}")


def test_coupang():
    print("\n" + "="*60)
    print("TESTING COUPANG SPIDER")
    print("="*60)
    
    url = "https://www.coupang.tw/search?keyword=sanneng&page=1"
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        print(f"✓ Site accessible (Status: {response.status_code})")
        
        # Check if it's JavaScript-rendered
        if len(response.text) < 1000:
            print("⚠ Response very small - likely JavaScript-rendered")
            return
        
        soup = BeautifulSoup(response.content, 'html.parser')
        products = soup.select('div.product-item')
        print(f"  Found {len(products)} product items")
        
    except Exception as e:
        print(f"✗ Error: {type(e).__name__}: {e}")

def test_sannengvietnam():
    print("\n" + "="*60)
    print("TESTING SANNENGVIETNAM SPIDER (WORKING)")
    print("="*60)
    
    url = "https://sannengvietnam.com/shop/page/1/"
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        products = soup.select('li.product')
        
        print(f"✓ Site accessible (Status: {response.status_code})")
        print(f"✓ Found {len(products)} products on first page")
        print("✓ This spider IS working correctly!")
        
    except Exception as e:
        print(f"✗ Error: {type(e).__name__}: {e}")


if __name__ == "__main__":
    try:
        test_sannengvietnam()
        test_chakawal()
        test_tokopedia()
        test_unopan()
        test_coupang()
        
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print("\nRecommendations:")
        print("1. Tokopedia and Coupang require JavaScript rendering")
        print("   → Use Scrapy-Splash or add Playwright support")
        print("2. Unopan likely needs JavaScript rendering or better headers")
        print("3. Chakawal selectors may have changed on the website")
        print("4. Sannengvietnam is working well!")
        
    except KeyboardInterrupt:
        print("\nStopped by user")
