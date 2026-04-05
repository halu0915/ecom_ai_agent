from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from app.etl import run_etl

if __name__ == '__main__':
    result = run_etl(
        data_dir=str(ROOT / 'data' / 'shopee'),
        config_dir=str(ROOT / 'config'),
        db_path=str(ROOT / 'output' / 'db' / 'products.db'),
        report_dir=str(ROOT / 'reports' / 'daily'),
    )
    print('ETL 完成')
    for k, v in result.items():
        print(f'{k}: {v}')
