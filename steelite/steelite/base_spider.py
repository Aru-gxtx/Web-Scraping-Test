# Base spider utilities for common functionality
import csv
import scrapy


class BaseSteeeliteSpider(scrapy.Spider):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.product_data = []
    
    def get_csv_fieldnames(self):
        return [
            'name', 'item_sku', 'model_number', 'manufacturer', 
            'image_link', 'overview', 'material', 'color', 'pattern', 
            'length', 'width', 'height', 'volume_capacity', 'diameter',
            'country_of_origin', 'upc_barcode', 'ean_code', 
            'hazmat', 'oversize', 'marketplace_uom', 'product_url'
        ]
    
    def normalize_product(self, product):
        fieldnames = self.get_csv_fieldnames()
        for field in fieldnames:
            if field not in product:
                product[field] = 'N/A'
        return product
    
    def save_to_csv(self, filename):
        if not self.product_data:
            self.logger.info("No product data to save")
            return
        
        fieldnames = self.get_csv_fieldnames()
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for product in self.product_data:
                    writer.writerow(product)
            self.logger.info(f"✓ Saved {len(self.product_data)} products to {filename}")
        except Exception as e:
            self.logger.error(f"Error saving to CSV: {e}")
    
    def closed(self, reason):
        if hasattr(self, 'csv_filename'):
            self.save_to_csv(self.csv_filename)
        self.logger.info(f"Spider closed. Total products: {len(self.product_data)}")
