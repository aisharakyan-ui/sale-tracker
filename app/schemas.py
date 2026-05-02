from __future__ import annotations

from datetime import date
from typing import List

from pydantic import BaseModel


class BrandOut(BaseModel):
    id: int
    name: str
    category: str


class ProductOut(BaseModel):
    id: int
    brand_id: int
    retailer_id: int
    brand_name: str
    retailer_name: str
    name: str
    sku: str
    category: str
    currency: str


class PricePoint(BaseModel):
    observed_at: date
    list_price: float
    sale_price: float
    discount_pct: float


class PriceHistoryOut(BaseModel):
    product_id: int
    product_name: str
    brand_name: str
    retailer_name: str
    currency: str
    points: List[PricePoint]
    min_price: float
    max_price: float
    average_price: float
    median_price: float
    latest_price: float


class SaleCalendarMonth(BaseModel):
    month: int
    month_name: str
    sale_events: int
    total_observations: int
    sale_rate: float
    average_discount_pct: float


class SaleCalendarOut(BaseModel):
    brand_id: int
    brand_name: str
    days_analyzed: int
    sale_threshold: float
    months: List[SaleCalendarMonth]
    top_sale_months: List[str]


class SeedResponse(BaseModel):
    message: str
    brands_created: int
    retailers_created: int
    products_created: int
    observations_created: int
