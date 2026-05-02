from __future__ import annotations

import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent.parent / "data.db"


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db() -> None:
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS brands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                category TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS retailers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                region TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand_id INTEGER NOT NULL,
                retailer_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                sku TEXT NOT NULL UNIQUE,
                category TEXT NOT NULL,
                currency TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (brand_id) REFERENCES brands (id),
                FOREIGN KEY (retailer_id) REFERENCES retailers (id)
            );

            CREATE TABLE IF NOT EXISTS price_observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                observed_at TEXT NOT NULL,
                list_price REAL NOT NULL,
                sale_price REAL NOT NULL,
                source TEXT NOT NULL,
                FOREIGN KEY (product_id) REFERENCES products (id)
            );

            CREATE INDEX IF NOT EXISTS idx_products_brand_id
                ON products (brand_id);

            CREATE INDEX IF NOT EXISTS idx_price_observations_product_time
                ON price_observations (product_id, observed_at);
            """
        )
