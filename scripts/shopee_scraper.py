import sys
import json
from playwright.sync_api import sync_playwright

def main(keyword):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Using a convincing user agent to bypass simple blocks
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        try:
            page.goto(f"https://shopee.tw/search?keyword={keyword}", timeout=20000)
            
            # Wait a few seconds to let Shopee scripts load items
            page.wait_for_timeout(4000)
            # Try to scroll down to trigger lazy loading
            page.mouse.wheel(0, 1000)
            page.wait_for_timeout(2000)
            
            # Extract elements. We look for 'a' tags that match Shopee product URL pattern (-i.)
            items = page.evaluate("""() => {
                let cards = Array.from(document.querySelectorAll('a'));
                let results = [];
                for(let a of cards) {
                    if (a.href && a.href.includes('-i.')) {
                        results.push({
                            title: a.innerText,
                            url: a.href
                        });
                    }
                }
                return results;
            }""")
            
            # Post process the raw text from the a-tag into Product Name and Price
            final_items = []
            seen = set()
            for x in items:
                lines = [line.strip() for line in x['title'].split('\n') if line.strip()]
                if len(lines) >= 2 and x['url'] not in seen:
                    title = lines[0]
                    # Find price line
                    price = '0'
                    for line in lines:
                        if '$' in line:
                            price = line
                            break
                    if price != '0':
                        final_items.append({'名稱': title, '價格': price, '網址': x['url']})
                        seen.add(x['url'])
                
            print(json.dumps({'success': True, 'data': final_items[:15]}, ensure_ascii=False))
        except Exception as e:
            print(json.dumps({"success": False, "error": str(e)}, ensure_ascii=False))
        finally:
            browser.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        print(json.dumps({"success": False, "error": "No keyword provided"}))
