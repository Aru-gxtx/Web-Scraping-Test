#!/usr/bin/env python
import csv
import os
import re
import ssl
from pathlib import Path
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

import pandas as pd
from scrapy import Selector


PROJECT_ROOT = Path(__file__).parent
SANNENG_DIR = PROJECT_ROOT / "sanneng"
INPUT_EXCEL = PROJECT_ROOT / "sources" / "SAN NENG.xlsx"
OUTPUT_CSV = SANNENG_DIR / "addon_search_products.csv"


CSV_INPUTS = [
    SANNENG_DIR / "chakawal_products.csv",
    SANNENG_DIR / "sannengvietnam_products.csv",
    SANNENG_DIR / "tokopedia_products.csv",
    SANNENG_DIR / "unopan_products.csv",
    SANNENG_DIR / "coupang_products.csv",
]


OUTPUT_FIELDS = [
    "sku",
    "name",
    "image_link",
    "overview",
    "length",
    "width",
    "height",
    "diameter",
    "volume",
    "material",
    "color",
    "pattern",
    "ean_code",
    "barcode",
    "upc",
    "product_url",
    "source",
]


COMMON_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,zh-TW;q=0.8",
}


def normalize_sku(value):
    if pd.isna(value):
        return None
    text = str(value).strip().upper()
    if not text or text in {"N/A", "NAN", "NONE"}:
        return None
    text = text.replace(" ", "")
    match = re.search(r"SN\d+[A-Z0-9-]*", text)
    if match:
        return match.group(0)
    return text


def normalize_image_link(link):
    if not link:
        return "N/A"
    text = str(link).strip()
    if not text or text.upper() in {"N/A", "NAN", "NONE"}:
        return "N/A"
    if text.startswith("//"):
        return f"https:{text}"
    return text


def fetch_html(url, headers=None, timeout=20):
    merged_headers = dict(COMMON_HEADERS)
    if headers:
        merged_headers.update(headers)

    req = Request(url=url, headers=merged_headers)
    ctx = ssl.create_default_context()
    with urlopen(req, timeout=timeout, context=ctx) as response:
        return response.read().decode("utf-8", errors="ignore")


def build_default_item(sku, source):
    return {
        "sku": sku,
        "name": "N/A",
        "image_link": "N/A",
        "overview": "N/A",
        "length": "N/A",
        "width": "N/A",
        "height": "N/A",
        "diameter": "N/A",
        "volume": "N/A",
        "material": "N/A",
        "color": "N/A",
        "pattern": "N/A",
        "ean_code": "N/A",
        "barcode": "N/A",
        "upc": "N/A",
        "product_url": "N/A",
        "source": source,
    }


def search_unopan_by_sku(sku):
    search_url = f"https://www.unopan.tw/search?q={quote_plus(sku)}"
    try:
        html = fetch_html(search_url, headers={"Referer": "https://www.unopan.tw/"})
    except Exception:
        return None

    sel = Selector(text=html)
    cards = sel.css("div.item")
    if not cards:
        cards = sel.css("a[href*='/products/']")

    best = None
    for card in cards:
        href = card.css("a[href*='/products/']::attr(href)").get() or card.css("a::attr(href)").get()
        title = card.css("p.product_title::text").get() or card.css("a::attr(data-name)").get() or ""
        image = card.css("a.product_image::attr(style)").get()
        if image:
            image_match = re.search(r"url\((?:&quot;|\")?(.*?)(?:&quot;|\")?\)", image)
            image = image_match.group(1) if image_match else image
        if not image:
            image = card.css("img::attr(src)").get() or card.css("img::attr(data-src)").get()

        if href and href.startswith("/"):
            href = f"https://www.unopan.tw{href}"

        text_blob = f"{title} {href}".upper()
        if sku.upper() in text_blob:
            best = (title, href, image)
            break
        if best is None and href:
            best = (title, href, image)

    if not best:
        return None

    title, href, image = best
    item = build_default_item(sku=sku.upper(), source="unopan.tw-addon")
    item["name"] = title.strip() if title else f"SANNENG {sku}"
    item["product_url"] = href if href else search_url
    item["image_link"] = normalize_image_link(image)
    return item


def search_coupang_by_sku(sku):
    query = f"SaNNeNg {sku}"
    search_url = f"https://www.tw.coupang.com/search?component=&q={quote_plus(query)}"
    headers = {"Referer": "https://www.tw.coupang.com/"}

    try:
        html = fetch_html(search_url, headers=headers)
    except Exception:
        return None

    sel = Selector(text=html)
    cards = sel.css("li.ProductUnit_productUnit__Qd6sv")
    if not cards:
        cards = sel.css("a[href*='/products/']")

    best = None
    for card in cards:
        anchor = card.css("a[href*='/products/']")
        href = anchor.css("::attr(href)").get()
        title = card.css("div.ProductUnit_productNameV2__cV9cw::text").get() or anchor.css("::attr(data-name)").get() or ""
        image = card.css("img::attr(src)").get() or card.css("img::attr(data-src)").get()

        if href and href.startswith("/"):
            href = f"https://www.tw.coupang.com{href}"

        text_blob = f"{title} {href}".upper()
        if sku.upper() in text_blob:
            best = (title, href, image)
            break
        if best is None and href:
            best = (title, href, image)

    if not best:
        return None

    title, href, image = best
    item = build_default_item(sku=sku.upper(), source="tw.coupang.com-addon")
    item["name"] = title.strip() if title else f"SANNENG {sku}"
    item["product_url"] = href if href else search_url
    item["image_link"] = normalize_image_link(image)
    return item


def get_existing_skus():
    found = set()
    for path in CSV_INPUTS:
        if not path.exists():
            continue
        try:
            df = pd.read_csv(path, encoding="utf-8")
        except Exception:
            continue
        if "sku" not in df.columns:
            continue
        for raw_sku in df["sku"].tolist():
            normalized = normalize_sku(raw_sku)
            if normalized:
                found.add(normalized)
    return found


def get_excel_target_skus():
    if not INPUT_EXCEL.exists():
        return []

    try:
        df = pd.read_excel(INPUT_EXCEL, engine="openpyxl")
    except Exception:
        return []

    mfr_col = None
    for col in df.columns:
        col_text = str(col).upper()
        if any(token in col_text for token in ["MFR", "SKU", "MODEL", "CODE", "型號"]):
            mfr_col = col
            break
    if mfr_col is None:
        mfr_col = df.columns[0]

    skus = []
    for value in df[mfr_col].tolist():
        normalized = normalize_sku(value)
        if normalized:
            skus.append(normalized)
    return sorted(set(skus))


def save_addon_rows(rows):
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "N/A") for field in OUTPUT_FIELDS})


def main():
    print("=" * 60)
    print("SKU SEARCH ADD-ON ENRICHMENT")
    print("=" * 60)

    existing_skus = get_existing_skus()
    target_skus = get_excel_target_skus()
    missing = [sku for sku in target_skus if sku not in existing_skus]

    print(f"Existing scraped SKUs: {len(existing_skus)}")
    print(f"Excel target SKUs: {len(target_skus)}")
    print(f"Missing SKUs to search: {len(missing)}")

    if not missing:
        save_addon_rows([])
        print(f"No missing SKUs. Wrote empty addon file: {OUTPUT_CSV}")
        return

    # Keep run time manageable
    max_search = int(os.getenv("ADDON_MAX_SEARCH", "120"))
    search_pool = missing[:max_search]
    print(f"Searching first {len(search_pool)} missing SKUs (ADDON_MAX_SEARCH={max_search})")

    enriched_rows = []
    for idx, sku in enumerate(search_pool, start=1):
        print(f"[{idx:03}/{len(search_pool):03}] Searching {sku}")

        unopan_item = search_unopan_by_sku(sku)
        if unopan_item and unopan_item.get("image_link") != "N/A":
            enriched_rows.append(unopan_item)
            print("  -> Found on unopan")
            continue

        coupang_item = search_coupang_by_sku(sku)
        if coupang_item and coupang_item.get("image_link") != "N/A":
            enriched_rows.append(coupang_item)
            print("  -> Found on coupang")
            continue

        print("  -> Not found")

    # Deduplicate by SKU, prioritize unopan over coupang
    dedup = {}
    for row in enriched_rows:
        sku = normalize_sku(row.get("sku"))
        if not sku:
            continue
        if sku not in dedup:
            dedup[sku] = row
            continue
        current_src = str(dedup[sku].get("source", ""))
        next_src = str(row.get("source", ""))
        if "unopan" in next_src and "unopan" not in current_src:
            dedup[sku] = row

    final_rows = list(dedup.values())
    save_addon_rows(final_rows)

    print("-" * 60)
    print(f"Addon rows saved: {len(final_rows)}")
    print(f"Output file: {OUTPUT_CSV}")
    print("=" * 60)


if __name__ == "__main__":
    main()
