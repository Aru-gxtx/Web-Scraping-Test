import os

print("\n========== SPIDER STATUS SUMMARY ==========\n")

spiders = [
    ('steelitehome.com', 'steelite/steelitehome_products.csv'),
    ('wasserstrom.com', 'steelite/wasserstrom_products.csv'),
    ('steelite-utopia.com', 'steelite/utopia_products.csv'),
    ('webstaurantstore vendor', 'steelite/webstaurantstore_vendor_products.csv'),
    ('webstaurantstore search', 'steelite/webstaurantstore_big_products.csv'),
    ('stephensons.com', 'steelite/stephensons_products.csv'),
    ('kitchenrestock.com', 'steelite/kitchenrestock_products.csv'),
    ('us.steelite.com', 'steelite/us_steelite_products.csv'),
    ('williamsfoodequipment.com', 'steelite/williamsfoodequipment_products.csv'),
]

total = 0
working = 0

for name, path in spiders:
    if os.path.exists(path):
        with open(path) as f:
            count = len(f.readlines()) - 1
        if count > 0:
            print(f"✓ {name:30} {count:4} products")
            total += count
            working += 1
        else:
            print(f"✗ {name:30}    0 products (empty)")
    else:
        print(f"✗ {name:30}    No output file")

print(f"\n{'='*47}")
print(f"TOTAL: {total} products from {working}/9 websites")
print(f"{'='*47}\n")
