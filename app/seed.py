from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from random import Random

from app.db import get_connection


DEMO_BRANDS = [
    {"name": "Nike", "category": "Apparel"},
    {"name": "Apple", "category": "Electronics"},
    {"name": "Samsung", "category": "Electronics"},
    {"name": "Levi's", "category": "Apparel"},
    {"name": "Dyson", "category": "Home"},
    {"name": "Nintendo", "category": "Gaming"},
]

DEMO_RETAILERS = [
    {"name": "Amazon", "region": "US"},
    {"name": "Best Buy", "region": "US"},
    {"name": "Target", "region": "US"},
    {"name": "Walmart", "region": "US"},
]

DEMO_PRODUCTS = [
    {"brand": "Nike", "retailer": "Amazon", "name": "Air Zoom Pegasus", "sku": "NIKE-PEG-001", "category": "Running Shoes", "currency": "USD", "list_price": 140},
    {"brand": "Apple", "retailer": "Best Buy", "name": "AirPods Pro", "sku": "APPLE-AIRPODS-001", "category": "Audio", "currency": "USD", "list_price": 249},
    {"brand": "Samsung", "retailer": "Amazon", "name": "Galaxy Buds", "sku": "SAMSUNG-BUDS-001", "category": "Audio", "currency": "USD", "list_price": 149},
    {"brand": "Levi's", "retailer": "Target", "name": "501 Original Jeans", "sku": "LEVIS-501-001", "category": "Denim", "currency": "USD", "list_price": 79},
    {"brand": "Dyson", "retailer": "Walmart", "name": "V8 Cordless Vacuum", "sku": "DYSON-V8-001", "category": "Vacuum", "currency": "USD", "list_price": 469},
    {"brand": "Nintendo", "retailer": "Target", "name": "Switch OLED", "sku": "NINTENDO-SWITCH-001", "category": "Console", "currency": "USD", "list_price": 349},
]

SEASONAL_DISCOUNTS = {
    "Nike": {1: 0.18, 5: 0.12, 11: 0.28, 12: 0.22},
    "Apple": {11: 0.14, 12: 0.09},
    "Samsung": {3: 0.12, 7: 0.14, 11: 0.24},
    "Levi's": {1: 0.2, 8: 0.18, 11: 0.32, 12: 0.25},
    "Dyson": {4: 0.1, 11: 0.27, 12: 0.16},
    "Nintendo": {7: 0.08, 11: 0.15, 12: 0.1},
}


def seed_demo_data() -> dict:
    random = Random(7)
    created_at = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        has_data = connection.execute("SELECT COUNT(*) AS count FROM brands").fetchone()["count"]
        if has_data:
            return {
                "message": "Demo data already exists",
                "brands_created": 0,
                "retailers_created": 0,
                "products_created": 0,
                "observations_created": 0,
            }

        brand_ids = {}
        for brand in DEMO_BRANDS:
            cursor = connection.execute(
                "INSERT INTO brands (name, category, created_at) VALUES (?, ?, ?)",
                (brand["name"], brand["category"], created_at),
            )
            brand_ids[brand["name"]] = cursor.lastrowid

        retailer_ids = {}
        for retailer in DEMO_RETAILERS:
            cursor = connection.execute(
                "INSERT INTO retailers (name, region, created_at) VALUES (?, ?, ?)",
                (retailer["name"], retailer["region"], created_at),
            )
            retailer_ids[retailer["name"]] = cursor.lastrowid

        product_rows = []
        for product in DEMO_PRODUCTS:
            cursor = connection.execute(
                """
                INSERT INTO products (
                    brand_id, retailer_id, name, sku, category, currency, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    brand_ids[product["brand"]],
                    retailer_ids[product["retailer"]],
                    product["name"],
                    product["sku"],
                    product["category"],
                    product["currency"],
                    created_at,
                ),
            )
            product_rows.append(
                {
                    "id": cursor.lastrowid,
                    "brand": product["brand"],
                    "list_price": product["list_price"],
                }
            )

        observations_created = 0
        start_date = date.today() - timedelta(days=728)
        total_weeks = 105

        for product in product_rows:
            base_price = float(product["list_price"])
            brand_discounts = SEASONAL_DISCOUNTS[product["brand"]]

            for week in range(total_weeks):
                observed_on = start_date + timedelta(days=week * 7)
                monthly_discount = brand_discounts.get(observed_on.month, 0.0)
                random_noise = random.uniform(-0.03, 0.03)
                promo_spike = 0.05 if random.random() > 0.94 else 0.0
                effective_discount = max(0.0, min(monthly_discount + promo_spike + random_noise, 0.45))
                sale_price = round(base_price * (1 - effective_discount), 2)

                connection.execute(
                    """
                    INSERT INTO price_observations (
                        product_id, observed_at, list_price, sale_price, source
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        product["id"],
                        observed_on.isoformat(),
                        base_price,
                        sale_price,
                        "demo_seed",
                    ),
                )
                observations_created += 1

    return {
        "message": "Demo data created",
        "brands_created": len(DEMO_BRANDS),
        "retailers_created": len(DEMO_RETAILERS),
        "products_created": len(DEMO_PRODUCTS),
        "observations_created": observations_created,
    }
