from __future__ import annotations
from pathlib import Path
from datetime import datetime
import pandas as pd


def write_markdown(path: str, content: str):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding='utf-8')


def daily_summary_markdown(df: pd.DataFrame, keyword: str = '情趣用品', platform: str = 'Shopee') -> str:
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    total = len(df)
    categories = df['category_std'].fillna('其他').value_counts().head(10)
    avg_price = round(df['price'].dropna().mean(), 2) if df['price'].notna().any() else None
    median_price = round(df['price'].dropna().median(), 2) if df['price'].notna().any() else None
    top = df.sort_values('sold_30d', ascending=False).head(10)[['title_clean','category_std','brand','price','sold_30d']]
    top_md = top.to_markdown(index=False) if not top.empty else '無資料'

    cats = '\n'.join([f"- {k}：{v}" for k, v in categories.items()]) or '- 無資料'
    return f"""# {platform} {keyword} 每日摘要

日期：{now}

## 本次更新概況
- 平台：{platform}
- 關鍵字：{keyword}
- 清洗後筆數：{total}

## 類別分布
{cats}

## 價格概況
- 平均價格：{avg_price}
- 中位數價格：{median_price}

## 銷量 Top 10
{top_md}
"""


def query_result_markdown(user_query: str, result_df: pd.DataFrame, insights: list[str]) -> str:
    table_md = result_df.to_markdown(index=False) if not result_df.empty else '無符合條件資料'
    bullets = '\n'.join([f"{i+1}. {x}" for i, x in enumerate(insights)]) if insights else '1. 無'
    return f"""# 查詢結果

## 使用者查詢
{user_query}

## 結果表
{table_md}

## AI 洞察
{bullets}
"""
