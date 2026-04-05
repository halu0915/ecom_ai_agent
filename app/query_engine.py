from __future__ import annotations
import json
import re
import sqlite3
import pandas as pd


CATEGORY_KEYWORDS = {
    '跳蛋': '跳蛋',
    '按摩棒': '按摩棒',
    '睡衣': '睡衣 / 內衣',
    '內衣': '睡衣 / 內衣',
    '潤滑液': '潤滑液',
    '保險套': '保險套',
    '飛機杯': '飛機杯 / 男用玩具',
    'SM': 'SM / 束縛配件',
    'cos': '角色扮演 / COS服',
    '角色扮演': '角色扮演 / COS服',
}


def parse_query(user_query: str) -> dict:
    q = user_query.strip()
    filters = {
        'category_std': None,
        'max_price': None,
        'min_price': None,
        'min_rating': None,
        'sort_by': 'sold_30d',
        'sort_order': 'DESC',
        'limit': 20,
        'keyword': None,
    }
    q_lower = q.lower()

    for k, v in CATEGORY_KEYWORDS.items():
        if k.lower() in q_lower:
            filters['category_std'] = v
            break

    m = re.search(r'價格\s*(?:低於|小於|<=?|不超過)?\s*(\d+)', q)
    if m:
        filters['max_price'] = int(m.group(1))
    m = re.search(r'(\d+)\s*以下', q)
    if m:
        filters['max_price'] = int(m.group(1))

    m = re.search(r'價格\s*(?:高於|大於|>=?)\s*(\d+)', q)
    if m:
        filters['min_price'] = int(m.group(1))

    m = re.search(r'評分\s*(?:高於|大於|>=?)\s*(\d+(?:\.\d+)?)', q)
    if m:
        filters['min_rating'] = float(m.group(1))

    m = re.search(r'(?:前|top)\s*(\d+)', q_lower)
    if m:
        filters['limit'] = int(m.group(1))

    if '平均價格' in q:
        filters['sort_by'] = 'price'
        filters['sort_order'] = 'ASC'

    return filters


def generate_sql(filters: dict) -> tuple[str, list]:
    sql = "SELECT title_clean, category_std, brand, price, sold_30d, rating, reviews_count, shop_name, source_url FROM products WHERE 1=1"
    params = []
    if filters.get('category_std'):
        sql += ' AND category_std = ?'
        params.append(filters['category_std'])
    if filters.get('max_price') is not None:
        sql += ' AND price <= ?'
        params.append(filters['max_price'])
    if filters.get('min_price') is not None:
        sql += ' AND price >= ?'
        params.append(filters['min_price'])
    if filters.get('min_rating') is not None:
        sql += ' AND rating >= ?'
        params.append(filters['min_rating'])
    sql += f" ORDER BY {filters['sort_by']} {filters['sort_order']} LIMIT {int(filters['limit'])}"
    return sql, params


def run_query(conn: sqlite3.Connection, user_query: str) -> tuple[pd.DataFrame, dict, str]:
    filters = parse_query(user_query)
    sql, params = generate_sql(filters)
    df = pd.read_sql_query(sql, conn, params=params)
    conn.execute(
        'INSERT INTO agent_query_logs (user_query, parsed_filters, generated_sql, result_count) VALUES (?, ?, ?, ?)',
        (user_query, json.dumps(filters, ensure_ascii=False), sql, len(df))
    )
    conn.commit()
    return df, filters, sql


def build_insights(df: pd.DataFrame) -> list[str]:
    insights = []
    if df.empty:
        return ['目前沒有符合條件的商品。']
    if 'price' in df and df['price'].notna().any():
        insights.append(f"結果平均價格約為 {round(df['price'].mean(), 2)} 元。")
    if 'sold_30d' in df and df['sold_30d'].notna().any():
        insights.append(f"最高 30 天銷量約為 {int(df['sold_30d'].max())}。")
    if 'brand' in df and df['brand'].notna().any():
        top_brand = df['brand'].fillna('未知').value_counts().idxmax()
        insights.append(f"本批結果中出現最多的品牌是 {top_brand}。")
    return insights
