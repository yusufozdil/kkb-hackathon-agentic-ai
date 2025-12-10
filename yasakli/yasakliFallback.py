from playwright.sync_api import sync_playwright
import json

""" 
{
    "Firma Adı": "MAHAL OTOMOTİV MAKİNE İNŞAAT SANAYİ VE TİCARET LİMİTED ŞİRKETİ",
    "İhale Yapan / Karar Veren Kurum": "ENERJİ VE TABİİ KAYNAKLAR BAKANLIĞI / ETİ MADEN İŞLETMELERİ GENEL MÜDÜRLÜĞÜ / ENERJİ VE TABİİ KAYNAKLAR BAKANLIĞI / ETİ MADEN İŞLETMELERİ GENEL MÜDÜRLÜĞÜ",
    "Başlangıç Tarihi": "1 Kasım 2025",
    "Bitiş Tarihi": "1 Kasım 2027",
    "Süre / Kapsam": "2 Yıl"
  }
  """

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    page.goto(
        "https://app.ihalepro.com/kamu/yasakli-sorgulama?qCompany=MAHAL%20OTOMOT%C4%B0V%20MAK%C4%B0NE%20%C4%B0N%C5%9EAAT%20SANAY%C4%B0%20VE%20T%C4%B0CARET%20L%C4%B0M%C4%B0TED%20%C5%9E%C4%B0RKET%C4%B0&page=1&sort=restrictedId&direction=desc"
    )
    
    page.wait_for_selector("tr.ng-star-inserted.extra-row-first")
    
    rows = page.query_selector_all("tr.ng-star-inserted.extra-row-first")
    
    data = []
    for row in rows:
        cols = row.query_selector_all("td")
        if len(cols) >= 5:
            firma = cols[0].inner_text().strip()
            kurum = cols[1].inner_text().replace("\n", " / ").strip()
            baslangic = cols[2].query_selector("div") and cols[2].query_selector("div").inner_text().strip()
            bitis = cols[3].query_selector("div") and cols[3].query_selector("div").inner_text().strip()
            sure = cols[4].inner_text().replace("\n", " ").strip()
            
            data.append({
                "Firma Adı": firma,
                "İhale Yapan / Karar Veren Kurum": kurum,
                "Başlangıç Tarihi": baslangic,
                "Bitiş Tarihi": bitis,
                "Süre / Kapsam": sure
            })
    
    print(json.dumps(data, ensure_ascii=False, indent=2))
    browser.close()

