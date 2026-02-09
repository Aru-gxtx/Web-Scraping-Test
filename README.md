# Web-Scraping-Test

**Web-Scraping-Test** is a collection of Python scripts for a self-study project for an internship assessment. The goal is to extract specific product data (Silikomart brand) from various e-commerce platforms, normalize the data structure, and export it to Excel for analysis.

![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=flat&logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Data-Pandas-150458?style=flat&logo=pandas&logoColor=white)
![BeautifulSoup](https://img.shields.io/badge/Parsing-BeautifulSoup4-green?style=flat)
![Cloudscraper](https://img.shields.io/badge/Network-Cloudscraper-orange?style=flat)

## 📂 Data Collection Workflow

The scripts follow a modular extraction pipeline designed for reliability and accuracy:

1.  **Request & Bypass:** The scripts use `requests` or `cloudscraper` to mimic a real browser user-agent, bypassing basic anti-bot protections (Cloudflare/403 Forbidden errors).
2.  **HTML Parsing:** `BeautifulSoup` navigates the DOM tree.
3.  **Data Extraction:** Specific strategies (CSS Selectors, JSON-LD parsing, or Regex) apply depending on the site structure.
4.  **Normalization:** The code cleans data (whitespace removal, currency formatting) and maps it to a strict schema of 18 columns.
5.  **Export:** The final dataset saves automatically into a `/results` folder as an `.xlsx` file.

## 🌐 Target Websites & Strategies

### 1. Southern Hospitality
* **Method:** `cloudscraper` + `BeautifulSoup`.
* **Structure:** Standard e-commerce grid.
* **Key Feature:** Handles dynamic folder creation for results and cleans inconsistent whitespace in price fields.

### 2. Bakedeco
* **Method:** `requests` + `BeautifulSoup`.
* **Structure:** Hybrid (Tables `<td>` and Divs `<div>`).
* **Key Feature:** The script includes a **dual-strategy selector**. It first checks for table-based layouts; if that fails, it falls back to grid-based div extraction. This ensures no products are missed regardless of page layout variations.

### 3. Silikomart (Official Site)
* **Method:** `requests` + **Regex (Regular Expressions)**.
* **Structure:** Complex Magento 2 with hidden data.
* **Key Feature:** Standard HTML parsing fails because data is embedded in JavaScript variables (`dataLayer`, `dlObjects`). The script uses **Regex pattern matching** to hunt for raw strings like `"sku":"..."` and `"availability":"..."` directly in the source code, bypassing the need for complex JS rendering.

### 4. Meilleur du Chef
* **Method:** `cloudscraper` + **JSON-LD**.
* **Structure:** Structured Data.
* **Key Feature:** This site heavily utilizes **Schema.org (JSON-LD)**. The script parses the hidden JSON blocks to get the most accurate Price, Stock, and Breadcrumb data, falling back to HTML parsing only if the JSON is missing. It also includes robust pagination logic to traverse all pages.

## ⚠️ Issues Encountered & Solutions

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| **403 Forbidden** | Southern Hospitality & Meilleur block standard `requests`. | Switch to **Cloudscraper** library to negotiate TLS handshakes and mimic browser headers. |
| **Hidden Stock** | Silikomart stores stock status inside JavaScript `script` tags rather than visible HTML. | Implement **Regex** to extract the specific JSON string from the raw HTML text. |

## 🚀 Getting Started

### Prerequisites

* Python 3.x.x
* Required libraries:

```bash
pip install -r requirements.txt
```

### Installation & Usage

1.  Clone the repository or download the scripts.
2.  Run the specific script for the desired website (e.g., `meilleurduchef.py`).
3.  Check the console for progress logs.
4.  Find the output file in the newly created `results/` folder.

```bash
# Example Run
> py meilleurduchef.py

# Expected Output
Starting link collection...
Scanning page: https://www.meilleurduchef.com/en/shop/brands/silikomart.html
   -> Found 410 new products.
Total unique products found: 410

Starting product extraction...
[1/410] Scraping: https://www.meilleurduchef.com/en/shop/baking-supplies/cake-mould/yule-log-moulds/sil-silicone-mould-signature-yule-log.html
[2/410] Scraping: https://www.meilleurduchef.com/en/shop/baking-supplies/cake-mould/savarin-mould/mfe-silicone-mould-18-savarin.html
[3/410] Scraping: https://www.meilleurduchef.com/en/shop/baking-supplies/cake-mould/shaped-moulds/sil-silicone-mould-8-flowers-kiku.html
[4/410] Scraping: https://www.meilleurduchef.com/en/shop/baking-supplies/cake-mould/loaf-tins/sil-paris-travel-cake-mould-23-x-5-x-ht-5-cm.html
...
[410/410] Scraping: https://www.meilleurduchef.com/en/shop/baking-supplies/cake-mould/cake-decorating-moulds/sil-silicone-mould-6-pleated-round.html

Success! Saved to: results\MeilleurDuChef_Silikomart_Test_5.xlsx
```
