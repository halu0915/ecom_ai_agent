import sys
import json
import re
from playwright.sync_api import sync_playwright

def main(keyword, city="all"):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        import urllib.parse
        encoded_kw = urllib.parse.quote(keyword)
        try:
            all_results = []
            for p_num in range(1, 4):
                page.goto(f"https://www.iyp.com.tw/search?q={encoded_kw}&type=keywords&city={city}&page={p_num}", timeout=20000)
                page.wait_for_timeout(3000)
            
                # Extract elements via javascript
                results = page.evaluate("""() => {
                    let cards = Array.from(document.querySelectorAll('.search-list > div'));
                    let data = [];
                    for(let card of cards) {
                        let nameEl = card.querySelector('a.line-clamp-1.text-xl');
                        if(!nameEl) continue;
                        let name = nameEl.innerText.trim();
                        let url = nameEl.href;
                        
                        let phone = '';
                        let address = '';
                        let desc = '';
                        
                        let descEl = card.querySelector('.line-clamp-2, .line-clamp-3');
                        if(descEl) desc = descEl.innerText;
                        
                        let infoRows = card.querySelectorAll('.text-sm.text-neutral-700 > div.flex');
                        for(let row of infoRows) {
                            let text = row.textContent.trim();
                            if(text.includes('call')) phone = text.replace('call', '').trim();
                            else if(text.includes('location_on')) address = text.replace('location_on', '').trim();
                        }
                        
                        data.push({
                            '名稱': name,
                            '網址': url,
                            '電話': phone,
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
            
            import ssl
            import urllib.request
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            # Post-process to extract Fax and Email using Regex on Description
            final_items = []
            for item in all_results[:30]:
                # 嘗試從描述中萃取傳真號碼
                fax = ""
                fax_match = re.search(r'傳真[:： ]?([0-9\-]+)', item['描述'])
                if fax_match:
                    fax = fax_match.group(1)
                
                # 嘗試從描述中萃取信箱 (Email)
                email = ""
                email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', item['描述'])
                if email_match:
                    email = email_match.group(0)
                    
                # 二級爬蟲：前往公司詳細頁面抓取缺少資訊
                if (not fax or not email) and item.get('電話'):
                    phone_clean = re.sub(r'[^0-9]', '', item['電話'])
                    if phone_clean:
                        try:
                            # 由於 IYP 有時會有 SSL 憑證問題，忽略驗證
                            req = urllib.request.Request(f"https://www.iyp.com.tw/{phone_clean}", headers={'User-Agent': 'Mozilla/5.0'})
                            res = urllib.request.urlopen(req, context=ctx, timeout=5)
                            html = res.read().decode('utf-8', errors='ignore')
                            
                            # 找信箱
                            if not email:
                                # 匹配 <h3...>公司信箱</h3> ... <span...>email@addr.com</span>
                                em_m = re.search(r'公司信箱</h3>[\s\S]*?<span[^>]*>([^<]+@[^<]+\.[^<]+)</span>', html)
                                if em_m: email = em_m.group(1).strip()
                            
                            # 找傳真
                            if not fax:
                                fx_m = re.search(r'傳真</h3>[\s\S]*?<span[^>]*>([0-9\-]+)</span>', html)
                                if fx_m: fax = fx_m.group(1).strip()
                                
                            # 如果描述太短，從詳情頁抓 meta description
                            if len(item.get('描述', '')) < 20:
                                meta_desc = re.search(r'<meta name="description" content="([^"]+)"', html)
                                if meta_desc:
                                    item['描述'] = meta_desc.group(1)

                        except Exception as e:
                            sys.stderr.write(f"Err fetching IYP detail {phone_clean}: {e}\\n")
                
                final_items.append({
                    '平台': '中華黃頁 IYP',
                    '名稱': item['名稱'],
                    '電話': item['電話'],
                    '傳真': fax,
                    '信箱': email,
                    '地址': item['地址'],
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
