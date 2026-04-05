from __future__ import annotations
import glob
import re
from datetime import datetime
from pathlib import Path
import pandas as pd

from app.db import init_db, sync_mapping_table, upsert_products, insert_snapshots
from app.reports import daily_summary_markdown, write_markdown
from app.utils import parse_price, parse_sold, normalize_text, make_product_hash, text_similarity

RENAME_MAP = {
    '商品標題': 'title_raw', '標題': 'title_raw', 'title': 'title_raw',
    '價格': 'price', 'price': 'price',
    '原價': 'price_original',
    '已售': 'sold_text_raw', '月銷量': 'sold_text_raw',
    '評價數': 'reviews_count', '評論數': 'reviews_count',
    '評分': 'rating',
    '品牌': 'brand_raw',
    '分類': 'category_raw', '類別': 'category_raw', 'category_path_raw': 'category_raw',
    '連結': 'source_url', '商品連結': 'source_url',
    '賣場': 'shop_name', '店家': 'shop_name'
}

REQ_COLS = [
    'platform','source_url','list_url','title_raw','title_clean','brand_raw','brand',
    'manufacturer','model','category_raw','category_std','price','price_original',
    'currency','sold_text_raw','sold_total_est','sold_30d','rating','reviews_count',
    'shop_name','seller_id','options_json','product_hash','last_seen_at'
]


def load_mapping(config_dir: str):
    brand_df = pd.read_csv(Path(config_dir) / 'mapping_brand.csv')
    cat_df = pd.read_csv(Path(config_dir) / 'mapping_category.csv')
    cat_df = cat_df[cat_df['is_active'] == 1].sort_values('priority')
    brand_map = {str(r['alias']).strip().lower(): r['normalized_brand'] for _, r in brand_df.iterrows()}
    cat_patterns = [(re.compile(str(r['pattern_regex']), flags=re.I), r['category_std']) for _, r in cat_df.iterrows()]
    return brand_df, cat_df, brand_map, cat_patterns


def normalize_brand(value, brand_map):
    if pd.isna(value):
        return None
    t = str(value).strip().lower()
    return brand_map.get(t, str(value).strip())


def map_category(text1, text2, cat_patterns):
    combined = ' '.join([str(text1 or ''), str(text2 or '')])
    for pat, cat in cat_patterns:
        if pat.search(combined):
            return cat
    return '其他'


def deduplicate(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.sort_values(['brand', 'title_clean', 'price'], na_position='last').reset_index(drop=True)
    keep = []
    used = set()
    for i, row_i in df.iterrows():
        if i in used:
            continue
        group = [i]
        for j in range(i + 1, len(df)):
            if j in used:
                continue
            row_j = df.iloc[j]
            same_brand = row_i.get('brand') and row_i.get('brand') == row_j.get('brand')
            sim = text_similarity(row_i.get('title_clean'), row_j.get('title_clean'))
            price_i = row_i.get('price')
            price_j = row_j.get('price')
            price_gap_ok = True
            if pd.notna(price_i) and pd.notna(price_j):
                price_gap_ok = abs(price_i - price_j) / max(price_i, 1) < 0.2
            if same_brand and sim > 0.86 and price_gap_ok:
                used.add(j)
                group.append(j)
        best = df.iloc[group].sort_values(['sold_30d', 'rating', 'reviews_count'], ascending=[False, False, False]).iloc[0]
        keep.append(best)
        used.add(i)
    return pd.DataFrame(keep).reset_index(drop=True)


def run_etl(data_dir='data/shopee', config_dir='config', db_path='output/db/products.db', report_dir='reports/daily'):
    files = glob.glob(str(Path(data_dir) / '*.csv'))
    if not files:
        raise FileNotFoundError(f'找不到原始 CSV：{data_dir}')

    raw = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    raw = raw.rename(columns={k: v for k, v in RENAME_MAP.items() if k in raw.columns})

    brand_df, cat_df, brand_map, cat_patterns = load_mapping(config_dir)

    df = raw.copy()
    for col in REQ_COLS:
        if col not in df.columns:
            df[col] = None

    df['platform'] = df['platform'].fillna('Shopee')
    df['title_clean'] = df['title_raw'].apply(normalize_text)
    df['price'] = df['price'].apply(parse_price)
    df['price_original'] = df['price_original'].apply(parse_price)
    df['sold_total_est'] = df['sold_text_raw'].apply(parse_sold)
    df['sold_30d'] = df['sold_total_est']
    df['brand'] = df['brand_raw'].apply(lambda x: normalize_brand(x, brand_map))
    df['category_std'] = df.apply(lambda r: map_category(r.get('category_raw'), r.get('title_clean'), cat_patterns), axis=1)
    df['currency'] = df['currency'].fillna('TWD')
    df['last_seen_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    df['product_hash'] = df.apply(lambda r: make_product_hash(r.get('brand'), r.get('title_clean'), r.get('model'), r.get('price')), axis=1)

    # numeric cleaning
    for c in ['rating', 'reviews_count']:
        df[c] = pd.to_numeric(df[c], errors='coerce')

    df = deduplicate(df[REQ_COLS].copy())

    clean_dir = Path('output/clean')
    clean_dir.mkdir(parents=True, exist_ok=True)
    out_csv = clean_dir / f"shopee_clean_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(out_csv, index=False, encoding='utf-8-sig')

    conn = init_db(db_path)
    sync_mapping_table(conn, 'brand_mapping', brand_df)
    sync_mapping_table(conn, 'category_mapping', cat_df[['pattern_regex','category_std','priority','is_active']])
    upsert_products(conn, df)
    insert_snapshots(conn, df)

    md = daily_summary_markdown(df)
    report_path = Path(report_dir) / f"{datetime.now().strftime('%Y-%m-%d')}_shopee_daily_summary.md"
    write_markdown(report_path, md)

    return {
        'rows': len(df),
        'csv_path': str(out_csv),
        'db_path': db_path,
        'report_path': str(report_path),
    }
