# 電商資料 AI Agent & 企業名錄抓取系統

這是一套整合了「靜態電商資料分析」與「動態企業名錄即時抓取」的 AI Agent 專案。

## 系統目標
- **即時線上抓取 (Live Fetch)**：
    - 支援 **中華黃頁 (IYP)**、**台灣黃頁 (Web66)** 與 **蝦皮 (Shopee)**。
    - 具備二級深層爬蟲（Deep Crawl）能力，自動抓取電話、傳真、信箱與詳細介紹。
    - 支援 **區域篩選** (台北、新北、桃園、台中等)。
- **資料分析與 ETL**：
    - 匯入 Octoparse / Instant Data Scraper 匯出的 CSV。
    - 自動清洗、分類、品牌標準化、去重。
- **視覺化輸出**：
    - 產出 **高畫質編排版 Excel** (含標題配色、交錯行著色、自動換行)。
    - 支援 Markdown 格式匯出。
    - 透過 Streamlit UI 進行即時查詢與視覺化。

## 專案結構

```text
.
├── app/
│   ├── app.py                  # Streamlit UI (整合 Live Fetch)
│   ├── db.py                   # SQLite schema 
│   ├── etl.py                  # 清洗、分類、入庫
│   ├── reports.py              # Markdown 報告輸出
│   └── query_engine.py         # 自然語言查詢解析
├── scripts/
│   ├── iyp_scraper.py          # 中華黃頁爬蟲核心
│   ├── web66_scraper.py        # 台灣黃頁爬蟲核心
│   ├── shopee_scraper.py       # 蝦皮 Playwright 爬蟲
│   ├── run_etl.py              # 離線資料 ETL
│   └── generate_daily_report.py
├── config/
│   ├── mapping_brand.csv       # 品牌對照
│   └── mapping_category.csv    # 類別規則
├── output/                     # 存放產出的資料與資料庫
└── requirements.txt            # 必要套件 (openpyxl, playwright, pandas, etc.)
```

## 安裝與啟動

```bash
# 1. 建立虛擬環境
python -m venv .venv
source .venv/bin/activate

# 2. 安裝套件
pip install -r requirements.txt

# 3. 安裝 Playwright 瀏覽器驅動
playwright install chromium

# 4. 啟動 UI
streamlit run app/app.py
```

## 使用說明
- **即時抓取**：進入 UI 的 `即時線上抓取` 分頁，選擇平台與區域，輸入關鍵字即可。
- **Excel 匯出**：抓取完成後可下載帶有排版樣式的 Excel 檔案，適合直接用於業務開發。

## 版本管理
本專案已初始化 Git，支援 GitHub 遠端部署。
