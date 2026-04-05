from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from app.db import get_conn
from app.reports import daily_summary_markdown, write_markdown

if __name__ == '__main__':
    conn = get_conn(str(ROOT / 'output' / 'db' / 'products.db'))
    df = pd.read_sql_query('SELECT * FROM products', conn)
    md = daily_summary_markdown(df)
    out = ROOT / 'reports' / 'daily' / 'manual_daily_summary.md'
    write_markdown(out, md)
    print(f'已輸出：{out}')
