import sys
import json
import urllib.parse
from playwright.sync_api import sync_playwright
import urllib.request
import re

def main(keyword, city='all'):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Using a mobile/modern user agent to avoid basic blocks
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        # Mapping my internal city codes to IYP city codes
        # Options: Taipei, NewTaipei, Taoyuan, Taichung, Tainan, Kaohsiung, all
        city_map = {
            'Taipei': 'Taipei',
            'NewTaipei': 'NewTaipei',
            'Taoyuan': 'Taoyuan',
            'Taichung': 'Taichung',
            'Tainan': 'Tainan',
            'Kaohsiung': 'Kaohsiung'
        }
        city_code = city_map.get(city, 'all')
        
        encoded_kw = urllib.parse.quote(keyword)
        # New IYP Search URL structure
        search_url = f"https://www.iyp.com.tw/search?q={encoded_kw}&type=keywords&city={city_code}"
        
        try:
            page.goto(search_url, wait_until='domcontentloaded', timeout=30000)
            
            # Wait for result cards to appear
            page.wait_for_selector('a.text-xl.font-bold', timeout=10000)
            
            # Extract items using a robust JS function
            items = page.evaluate("""() => {
                let cards = Array.from(document.querySelectorAll('div.bg-white.rounded-lg.border'));
                let results = [];
                for(let card of cards) {
                    let nameLink = card.querySelector('a.text-xl.font-bold');
                    if (!nameLink) continue;
                    
                    let name = nameLink.innerText.trim();
                    let url = nameLink.href;
                    
                    // Address/Phone logic: look for Material Icons
                    let icons = Array.from(card.querySelectorAll('span.material-symbols-rounded'));
                    let address = "";
                    let phone = "";
                    let desc = "";
                    
                    // Desc is usually the text before icons
                    let descEl = card.querySelector('div.text-neutral-500');
                    if (descEl) desc = descEl.innerText.trim();
                    
                    for(let icon of icons) {
                        let text = icon.innerText.trim();
                        if (text === 'location_on') {
                            address = icon.parentElement.innerText.replace('location_on', '').trim();
                        } else if (text === 'call') {
                            phone = icon.parentElement.innerText.replace('call', '').trim();
                        }
                    }
                    
                    results.push({
                        '名稱': name,
                        '地址': address,
                        '電話': phone,
                        '網址': url,
                        '描述': desc
                    });
                }
                return results;
            }""")
            
            final_items = []
            # Secondary Deep Crawl for Fax/Email
            for item in items[:15]: # Limit to 15 for performance
                email = ""
                fax = ""
                
                # IYP Detail page crawl
                if item['網址'] and 'iyp.com.tw' in item['網址']:
                    try:
                        req = urllib.request.Request(item['網址'], headers={'User-Agent': 'Mozilla/5.0'})
                        with urllib.request.urlopen(req, timeout=5) as response:
                            html = response.read().decode('utf-8')
                            
                            # Match <h3...>公司信箱</h3> ... <span...>email@addr.com</span>
                            em_m = re.search(r'公司信箱</h3>[\s\S]*?<span[^>]*>([^<]+@[^<]+\.[^<]+)</span>', html)
                            if em_m: email = em_m.group(1).strip()
                            
                            # Find Fax
                            fx_m = re.search(r'傳真</h3>[\s\S]*?<span[^>]*>([0-9\-]+)</span>', html)
                            if fx_m: fax = fx_m.group(1).strip()
                            
                            # Fallback description from meta
                            if len(item.get('描述', '')) < 20:
                                meta_desc = re.search(r'<meta name="description" content="([^"]+)"', html)
                                if meta_desc: item['描述'] = meta_desc.group(1)
                    except:
                        pass
                
                final_items.append({
                    '平台': '中華黃頁 IYP',
                    '名稱': item['名稱'],
                    '電話': item['電話'],
                    '傳真': fax,
                    '信箱': email,
                    '地址': item['地址'],
                    '描述': item.get('描述', '')[:300],
                    '真實頁面網址': item['網址']
                })
            
            print(json.dumps({'success': True, 'data': final_items}, ensure_ascii=False))
            
        except Exception as e:
            # sys.stderr.write(f"Scraper Error: {e}\n")
            print(json.dumps({"success": False, "error": str(e)}, ensure_ascii=False))
        finally:
            browser.close()

if __name__ == "__main__":
    kw = sys.argv[1] if len(sys.argv) > 1 else '五金'
    ct = sys.argv[2] if len(sys.argv) > 2 else 'all'
    main(kw, ct)
