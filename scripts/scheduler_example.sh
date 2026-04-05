#!/bin/bash
# 每日自動更新範例
cd /path/to/ecom_ai_agent || exit 1
source .venv/bin/activate
python scripts/run_etl.py
python scripts/generate_daily_report.py
