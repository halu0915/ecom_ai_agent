from __future__ import annotations
import sqlite3
from pathlib import Path
import pandas as pd

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT,
    source_url TEXT UNIQUE,
    list_url TEXT,
    title_raw TEXT,
    title_clean TEXT,
    brand_raw TEXT,
    brand TEXT,
    manufacturer TEXT,
    model TEXT,
    category_raw TEXT,
    category_std TEXT,
    price REAL,
    price_original REAL,
    currency TEXT,
    sold_text_raw TEXT,
    sold_total_est INTEGER,
    sold_30d INTEGER,
    rating REAL,
    reviews_count INTEGER,
    shop_name TEXT,
    seller_id TEXT,
    options_json TEXT,
    product_hash TEXT,
    last_seen_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS product_snapshots (
    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_hash TEXT,
    source_url TEXT,
    captured_at TEXT DEFAULT CURRENT_TIMESTAMP,
    price REAL,
    sold_total_est INTEGER,
    sold_30d INTEGER,
    rating REAL,
    reviews_count INTEGER
);

CREATE TABLE IF NOT EXISTS category_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_regex TEXT,
    category_std TEXT,
    priority INTEGER,
    is_active INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS brand_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alias TEXT,
    normalized_brand TEXT
);

CREATE TABLE IF NOT EXISTS agent_query_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_query TEXT,
    parsed_filters TEXT,
    generated_sql TEXT,
    result_count INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


def get_conn(db_path: str):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str):
    conn = get_conn(db_path)
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    return conn


def sync_mapping_table(conn: sqlite3.Connection, table_name: str, df: pd.DataFrame):
    conn.execute(f"DELETE FROM {table_name}")
    df.to_sql(table_name, conn, if_exists='append', index=False)
    conn.commit()


def upsert_products(conn: sqlite3.Connection, df: pd.DataFrame):
    cols = [
        'platform','source_url','list_url','title_raw','title_clean','brand_raw','brand',
        'manufacturer','model','category_raw','category_std','price','price_original',
        'currency','sold_text_raw','sold_total_est','sold_30d','rating','reviews_count',
        'shop_name','seller_id','options_json','product_hash','last_seen_at'
    ]
    placeholders = ','.join(['?'] * len(cols))
    updates = ','.join([f"{c}=excluded.{c}" for c in cols if c != 'source_url']) + ",updated_at=CURRENT_TIMESTAMP"
    sql = f"""
    INSERT INTO products ({','.join(cols)})
    VALUES ({placeholders})
    ON CONFLICT(source_url) DO UPDATE SET {updates};
    """
    clean_df = df[cols].where(pd.notnull(df[cols]), None)
    rows = clean_df.values.tolist()
    conn.executemany(sql, rows)
    conn.commit()


def insert_snapshots(conn: sqlite3.Connection, df: pd.DataFrame):
    snap = df[['product_hash','source_url','price','sold_total_est','sold_30d','rating','reviews_count']].copy()
    snap.to_sql('product_snapshots', conn, if_exists='append', index=False)
    conn.commit()
