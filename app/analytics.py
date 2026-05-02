from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from statistics import median

from app.db import get_connection


MONTH_NAMES = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
}


class AnalyticsNotFoundError(Exception):
    pass


def _start_date(days: int) -> str:
    return (date.today() - timedelta(days=days)).isoformat()


def list_brands() -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT id, name, category FROM brands ORDER BY name"
        ).fetchall()
    return [dict(row) for row in rows]


def list_products() -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                p.id,
                p.brand_id,
                p.retailer_id,
                b.name AS brand_name,
                r.name AS retailer_name,
                p.name,
                p.sku,
                p.category,
                p.currency
            FROM products p
            JOIN brands b ON b.id = p.brand_id
            JOIN retailers r ON r.id = p.retailer_id
            ORDER BY b.name, p.name
            """
        ).fetchall()
    return [dict(row) for row in rows]


def get_price_history(product_id: int, days: int) -> dict:
    start_date = _start_date(days)

    with get_connection() as connection:
        product = connection.execute(
            """
            SELECT
                p.id,
                p.name,
                p.currency,
                b.name AS brand_name,
                r.name AS retailer_name
            FROM products p
            JOIN brands b ON b.id = p.brand_id
            JOIN retailers r ON r.id = p.retailer_id
            WHERE p.id = ?
            """,
            (product_id,),
        ).fetchone()

        if product is None:
            raise AnalyticsNotFoundError("Product not found")

        observations = connection.execute(
            """
            SELECT observed_at, list_price, sale_price
            FROM price_observations
            WHERE product_id = ? AND observed_at >= ?
            ORDER BY observed_at
            """,
            (product_id, start_date),
        ).fetchall()

    if not observations:
        raise AnalyticsNotFoundError("No price history found")

    points = []
    prices = []

    for row in observations:
        list_price = float(row["list_price"])
        sale_price = float(row["sale_price"])
        discount_pct = 0.0 if list_price == 0 else round((1 - sale_price / list_price) * 100, 2)
        points.append(
            {
                "observed_at": datetime.fromisoformat(row["observed_at"]).date(),
                "list_price": list_price,
                "sale_price": sale_price,
                "discount_pct": discount_pct,
            }
        )
        prices.append(sale_price)

    return {
        "product_id": product["id"],
        "product_name": product["name"],
        "brand_name": product["brand_name"],
        "retailer_name": product["retailer_name"],
        "currency": product["currency"],
        "points": points,
        "min_price": round(min(prices), 2),
        "max_price": round(max(prices), 2),
        "average_price": round(sum(prices) / len(prices), 2),
        "median_price": round(median(prices), 2),
        "latest_price": round(prices[-1], 2),
    }


def get_brand_sale_calendar(brand_id: int, days: int, sale_threshold: float) -> dict:
    start_date = _start_date(days)

    with get_connection() as connection:
        brand = connection.execute(
            "SELECT id, name FROM brands WHERE id = ?",
            (brand_id,),
        ).fetchone()

        if brand is None:
            raise AnalyticsNotFoundError("Brand not found")

        rows = connection.execute(
            """
            SELECT
                p.id AS product_id,
                po.observed_at,
                po.list_price,
                po.sale_price
            FROM products p
            JOIN price_observations po ON po.product_id = p.id
            WHERE p.brand_id = ? AND po.observed_at >= ?
            ORDER BY p.id, po.observed_at
            """,
            (brand_id, start_date),
        ).fetchall()

    if not rows:
        raise AnalyticsNotFoundError("No observations found for brand")

    product_prices: dict[int, list[float]] = defaultdict(list)
    for row in rows:
        product_prices[row["product_id"]].append(float(row["sale_price"]))

    product_medians = {
        product_id: median(prices) for product_id, prices in product_prices.items()
    }

    monthly_totals = {
        month: {"sale_events": 0, "total_observations": 0, "discounts": []}
        for month in range(1, 13)
    }

    for row in rows:
        observed_date = datetime.fromisoformat(row["observed_at"]).date()
        sale_price = float(row["sale_price"])
        list_price = float(row["list_price"])
        baseline = product_medians[row["product_id"]]
        is_sale = sale_price <= baseline * sale_threshold

        bucket = monthly_totals[observed_date.month]
        bucket["total_observations"] += 1

        if is_sale:
            bucket["sale_events"] += 1
            if list_price > 0:
                bucket["discounts"].append((1 - sale_price / list_price) * 100)

    months = []
    for month, values in monthly_totals.items():
        total_observations = values["total_observations"]
        sale_events = values["sale_events"]
        sale_rate = 0.0 if total_observations == 0 else round(sale_events / total_observations, 4)
        average_discount_pct = (
            0.0
            if not values["discounts"]
            else round(sum(values["discounts"]) / len(values["discounts"]), 2)
        )
        months.append(
            {
                "month": month,
                "month_name": MONTH_NAMES[month],
                "sale_events": sale_events,
                "total_observations": total_observations,
                "sale_rate": sale_rate,
                "average_discount_pct": average_discount_pct,
            }
        )

    ranked = sorted(
        months,
        key=lambda item: (item["sale_rate"], item["average_discount_pct"], item["sale_events"]),
        reverse=True,
    )

    top_sale_months = [
        month["month_name"] for month in ranked if month["sale_events"] > 0
    ][:3]

    return {
        "brand_id": brand["id"],
        "brand_name": brand["name"],
        "days_analyzed": days,
        "sale_threshold": sale_threshold,
        "months": months,
        "top_sale_months": top_sale_months,
    }
