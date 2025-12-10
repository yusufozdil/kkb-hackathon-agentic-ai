from playwright.sync_api import sync_playwright
import json

url = "https://www.ihaleciler.com/analyze?contractortitle_in=DOV%C4%B0+MOD%C3%9CLER+MOB%C4%B0LYA+%C4%B0MALAT+SANAY%C4%B0+VE+T%C4%B0CARET+L%C4%B0M%C4%B0TED+%C5%9E%C4%B0RKET%C4%B0"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    page.goto(url)
    page.wait_for_selector("#yearanalysis")  # wait for table to load
    
    rows = page.query_selector_all("#yearanalysis tbody tr")
    first_page_data = []
    
    for row in rows:
        cols = row.query_selector_all("td")
        first_page_data.append([col.inner_text().strip() for col in cols])
    
    browser.close()
    
    print(json.dumps(first_page_data, ensure_ascii=False, indent=2))
