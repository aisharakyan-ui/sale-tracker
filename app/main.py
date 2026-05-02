from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query

from app.analytics import (
    AnalyticsNotFoundError,
    get_brand_sale_calendar,
    get_price_history,
    list_brands,
    list_products,
)
from app.db import init_db
from app.schemas import BrandOut, PriceHistoryOut, ProductOut, SaleCalendarOut, SeedResponse
from app.seed import seed_demo_data


app = FastAPI(
    title="Brand Sale Tracker",
    description="Track product price history and estimate when brands tend to go on sale.",
    version="0.1.0",
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/brands", response_model=list[BrandOut])
def brands() -> list[dict]:
    return list_brands()


@app.get("/products", response_model=list[ProductOut])
def products() -> list[dict]:
    return list_products()


@app.get("/products/{product_id}/price-history", response_model=PriceHistoryOut)
def product_price_history(
    product_id: int,
    days: int = Query(default=730, ge=30, le=730),
) -> dict:
    try:
        return get_price_history(product_id=product_id, days=days)
    except AnalyticsNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.get("/brands/{brand_id}/sale-calendar", response_model=SaleCalendarOut)
def brand_sale_calendar(
    brand_id: int,
    days: int = Query(default=730, ge=30, le=730),
    sale_threshold: float = Query(default=0.90, gt=0.5, lt=1.0),
) -> dict:
    try:
        return get_brand_sale_calendar(
            brand_id=brand_id,
            days=days,
            sale_threshold=sale_threshold,
        )
    except AnalyticsNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.post("/seed-demo-data", response_model=SeedResponse)
def seed() -> dict:
    return seed_demo_data()
