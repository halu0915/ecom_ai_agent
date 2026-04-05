# 電商資料 AI Agent

這是一套可落地的本地版 AI Agent 專案骨架，目標是把電商平台的原始抓取資料，轉成可查詢、可分析、可輸出 Markdown 報告的系統。

## 系統目標
- 匯入 Octoparse / Instant Data Scraper 匯出的 CSV
- 清洗商品資料
- 自動分類、品牌標準化、數值轉換、去重
- 寫入 SQLite
- 透過 Streamlit UI 查詢
- 自動輸出 Markdown 報告

## 專案結構

```text
.
├── app/
│   ├── app.py                  # Streamlit UI
│   ├── db.py                   # SQLite schema 與 upsert
│   ├── etl.py                  # 清洗、分類、去重、入庫
│   ├── reports.py              # Markdown 報告輸出
│   ├── query_engine.py         # 自然語言查詢解析 + SQL 生成
│   └── utils.py                # 共用工具
├── config/
│   ├── mapping_brand.csv       # 品牌對照表
│   └── mapping_category.csv    # 類別規則表（可擴展）
├── data/
│   └── shopee/                 # 放原始 CSV
├── reports/
│   ├── daily/
│   ├── query/
│   └── category/
├── output/
│   ├── clean/                  # 清洗後 CSV
│   └── db/
├── scripts/
│   ├── run_etl.py              # 手動執行 ETL
│   ├── generate_daily_report.py
│   └── scheduler_example.sh    # 自動更新範例
├── requirements.txt
└── .env.example
```

## 安裝

```bash
python -m venv .venv
source .venv/bin/activate   # Windows 用 .venv\\Scripts\\activate
pip install -r requirements.txt
```

## 放入原始資料
把 Octoparse / IDS 匯出的 CSV 放到：

```text
data/shopee/
```

## 執行 ETL

```bash
python scripts/run_etl.py
```

執行後會：
- 建立 SQLite 資料庫：`output/db/products.db`
- 匯出清洗後資料：`output/clean/`
- 產出每日摘要 Markdown：`reports/daily/`

## 啟動查詢 UI

```bash
streamlit run app/app.py
```

## 支援的查詢語句範例
- 找跳蛋類，價格 1000 以下，銷量前 10
- 找按摩棒類，評分高於 4.5，價格低於 1500
- 找睡衣類最熱賣商品
- 找潤滑液類平均價格

## 自動更新
可用 cron / 工作排程器呼叫：

```bash
python scripts/run_etl.py
python scripts/generate_daily_report.py
```

`scripts/scheduler_example.sh` 已附範例。

## 必要工具
### 必要
- Octoparse：主力抓取
- Instant Data Scraper：快速驗證
- Python：ETL / SQLite / 報表
- SQLite：查詢核心
- Streamlit：查詢 UI

### 建議
- Obsidian：管理 Markdown 報告
- Git：版本追蹤
- n8n / cron：自動更新

## 未來升級方向
1. 多平台擴充：momo / PChome / Amazon / 1688
2. 趨勢分析：product_snapshots 做 7 天 / 30 天變化
3. LLM 查詢代理：把自然語言轉成結構化查詢
4. 價格競爭力、品牌滲透率、爆品預測
5. 報告轉 PDF / Word / Email 摘要
