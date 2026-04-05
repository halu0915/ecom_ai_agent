import sys
import json
import re
import ssl
import urllib.request
import urllib.parse
from playwright.sync_api import sync_playwright

def main(keyword, city="all"):
    # Web66 City Code Mapping
    city_map = {
        'all': '1000',
        'Taipei': '1111',       # 台北基隆
        'NewTaipei': '1113',    # 新北
        'Taoyuan': '1200',      # 桃竹苗
        'Taichung': '1300',     # 中彰投
        'Tainan': '1400',       # 雲嘉南
        'Kaohsiung': '1500',    # 高屏
    }
    baera_code = city_map.get(city, '1000')

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        encoded_kw = urllib.parse.quote(keyword)
        try:
            all_results = []
            for p_num in range(1, 4): # Fetch up to 3 pages
                sys.stderr.write(f"Fetching page {p_num}\\n")
                page.goto(f"https://www.web66.com.tw/web/SEC?keyword={encoded_kw}&Baera={baera_code}&pageNo={p_num}", wait_until='domcontentloaded', timeout=15000)
                sys.stderr.write(f"Waiting page {p_num}\\n")
                page.wait_for_timeout(1000)
                sys.stderr.write(f"Evaluating page {p_num} Javascript\\n")
                
                # Extract elements via javascript
                results = page.evaluate("""() => {
                    let cards = Array.from(document.querySelectorAll('dd .ListBox'));
                    let data = [];
                    for(let card of cards) {
                        let titleEl = card.querySelector('h3 > a.listtite');
                        if(!titleEl) continue;
                        
                        let name = titleEl.innerText.trim();
                        let title = name;
                        
                        let companyEl = card.querySelector('span.sB > a');
                        if (companyEl) {
                            name = companyEl.innerText.trim();
                        }
                        
                        let url = companyEl ? companyEl.href : titleEl.href;
                        
                        let locEl = card.querySelector('span.sB');
                        let address = '';
                        if(locEl) {
                            let locMatch = locEl.innerText.match(/\[(.*?)\]/);
                            if(locMatch) address = locMatch[1];
                        }
                        
                        let descEl = card.querySelector('.List_bref');
                        let desc = descEl ? descEl.innerText.trim() : '';
                        
                        data.push({
                            '標題': title,
                            '名稱': name,
                            '網址': url,
                            '地址': address,
                            '描述': desc
                        });
                    }
                    return data;
                }""")
                if not results:
                    break
                all_results.extend(results)
                if len(all_results) >= 30:
                    break
            
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            # Deep crawl for Fax, Phone and Email
            final_items = []
            for item in all_results[:30]:
                sys.stderr.write(f"Fetching detail: {item['網址']}\\n")
                phone = ""
                fax = ""
                email = ""
                address = item['地址']
                
                if item.get('網址') and item['網址'].startswith('http'):
                    try:
                        req = urllib.request.Request(item['網址'], headers={'User-Agent': 'Mozilla/5.0'})
                        res = urllib.request.urlopen(req, context=ctx, timeout=3)
                        html = res.read().decode('utf-8', errors='ignore')
                        
                        # 找電話： <div class="orp">電話：02-25532056</div> 或 手機：...
                        phone_m = re.search(r'電話：([^<]+)</div>', html)
                        if phone_m: phone = phone_m.group(1).strip()
                        
                        mobile_m = re.search(r'手機：([^<]+)</div>', html)
                        mobile_val = mobile_m.group(1).strip() if mobile_m else ""
                        if mobile_val:
                            if phone: phone += " / " + mobile_val
                            else: phone = mobile_val
                        
                        # 找傳真： <div class="orp">傳真：02-25501234</div>
                        fax_m = re.search(r'傳真：([^<]+)</div>', html)
                        if fax_m: fax = fax_m.group(1).strip()
                        
                        # 找確切地址
                        addr_m = re.search(r'公司位置：([^<]+)</div>', html)
                        if addr_m: address = addr_m.group(1).strip()
                        
                        # 找公司介紹 (從詳情頁面更新描述)
                        desc_m = re.search(r'<div class="exptext pagecontent">(.*?)</div>', html, re.DOTALL)
                        detail_desc = ""
                        if desc_m:
                            desc_html = desc_m.group(1)
                            # 移除 HTML 標籤
                            desc_text = re.sub(r'<[^>]+>', ' ', desc_html).strip()
                            if desc_text:
                                item['描述'] = desc_text
                                detail_desc = desc_text

                        # 找信箱： Web66 通常會隱藏為 s***@...
                        # 先找 masked 版
                        email_m = re.search(r'Email:([a-zA-Z0-9.\*_]+@[a-zA-Z0-9.\*_]+)', html)
                        if email_m: email = email_m.group(1).strip()
                        
                        # 嘗試從描述中找可能未經遮罩的 Email
                        if detail_desc:
                            raw_email_m = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', detail_desc)
                            if raw_email_m:
                                email = raw_email_m.group(0)

                    except Exception as e:
                        sys.stderr.write(f"Err fetching {item['網址']}: {e}\\n")
                
                final_items.append({
                    '平台': '台灣黃頁 Web66',
                    '名稱': item['名稱'],
                    '電話': phone,
                    '傳真': fax,
                    '信箱': email,
                    '地址': address,
                    '描述': item.get('描述', '')[:300] + ('...' if len(item.get('描述', '')) > 300 else ''),
                    '真實頁面網址': item['網址']
                })
                
            print(json.dumps({'success': True, 'data': final_items}, ensure_ascii=False))
        except Exception as e:
            print(json.dumps({"success": False, "error": str(e)}, ensure_ascii=False))
        finally:
            browser.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        kw = sys.argv[1]
        c = sys.argv[2] if len(sys.argv) > 2 else "all"
        main(kw, c)
    else:
        print(json.dumps({"success": False, "error": "No keyword provided"}, ensure_ascii=False))
