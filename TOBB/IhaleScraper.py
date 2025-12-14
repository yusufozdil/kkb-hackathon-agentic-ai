from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
import time
import urllib.parse

class IhaleScraper:
    def __init__(self, company_name: str, headless: bool = True, timeout: int = 15000):
        self.company_name = company_name
        self.headless = headless
        self.timeout = timeout
        self.base_url = "https://www.ihaleciler.com/analyze"
        self.url = f"{self.base_url}?contractortitle_in={urllib.parse.quote_plus(self.company_name)}"
        self.html_content = None

    # ------------------------
    # Playwright Scraper
    # ------------------------
    def scrape(self):
        with sync_playwright() as p:
            print("🚀 Launching browser...")
            browser = p.chromium.launch(headless=self.headless)
            page = browser.new_page()

            # Set realistic User-Agent
            page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/120.0.0.0 Safari/537.36"
            })

            print(f"🔗 Navigating to {self.url}")
            page.goto(self.url)

            # Wait for all dynamic tables to load
            table_ids = [
                "yearanalysis",
                "cpvanalysis",
                "provinceanalysis",
                "worktypeanalysis",
                "procedureanalysis",
                "offertypeanalysis"
            ]

            for table_id in table_ids:
                print(f"⏳ Waiting for table '{table_id}' to load...")
                try:
                    page.wait_for_function(f"""
                    () => {{
                        const cell = document.querySelector('#{table_id} tbody tr td');
                        return cell && cell.innerText.trim() !== 'Yükleniyor...';
                    }}
                    """, timeout=self.timeout)
                except Exception as e:
                    print(f"⚠️ Warning: Timeout waiting for table '{table_id}' ({e})")

            # Optional buffer
            time.sleep(1)
            self.html_content = page.content()
            browser.close()
            print("✅ Scraping complete.")

    # ------------------------
    # BeautifulSoup Parsers
    # ------------------------
    @staticmethod
    def clean_text(text):
        if not text:
            return None
        return " ".join(text.split())

    @classmethod
    def parse_summary_stats(cls, soup):
        summary_data = {}
        container = soup.find("div", id="summary-stats-content")
        if not container:
            return summary_data

        for row in container.find_all("div", class_="row"):
            label_div = row.find("div", class_="responsive-left")
            if not label_div:
                continue
            key = cls.clean_text(label_div.get_text())

            value_div = row.find("div", class_="responsive-right")
            values = []
            if value_div:
                # Remove buttons
                for btn in value_div.find_all("a", class_="btn"):
                    btn.decompose()
                children = value_div.find_all("div", recursive=False)
                if children:
                    for child in children:
                        values.append(cls.clean_text(child.get_text()))
                else:
                    values.append(cls.clean_text(value_div.get_text()))
            summary_data[key] = values
        return summary_data

    @classmethod
    def parse_datatable(cls, soup, table_id):
        table = soup.find("table", id=table_id)
        if not table:
            return []

        headers = [cls.clean_text(th.get_text()) for th in table.find("thead").find_all("th")] if table.find("thead") else []
        tbody = table.find("tbody")
        data = []

        if tbody:
            for row in tbody.find_all("tr"):
                cells = row.find_all("td")
                # Skip empty/loading rows
                if len(cells) == 1 and "dataTables_empty" in cells[0].get("class", []):
                    continue

                row_data = {}
                for i, cell in enumerate(cells):
                    for btn in cell.find_all("a", class_="btn"):
                        btn.decompose()
                    text = cls.clean_text(cell.get_text(separator=" "))
                    if i < len(headers):
                        row_data[headers[i]] = text
                if row_data:
                    data.append(row_data)
        return data

    # ------------------------
    # Process HTML
    # ------------------------
    def process_html(self):
        if not self.html_content:
            raise ValueError("HTML content is empty. Run scrape() first.")

        soup = BeautifulSoup(self.html_content, "html.parser")
        return {
            "Summary_Analysis": self.parse_summary_stats(soup),
            "Yearly_Stats": self.parse_datatable(soup, "yearanalysis"),
            "Sectors_CPV": self.parse_datatable(soup, "cpvanalysis"),
            "Provinces": self.parse_datatable(soup, "provinceanalysis"),
            "Work_Types": self.parse_datatable(soup, "worktypeanalysis"),
            "Procedures": self.parse_datatable(soup, "procedureanalysis"),
            "Offer_Types": self.parse_datatable(soup, "offertypeanalysis")
        }

# ------------------------
# Main Execution
# ------------------------
if __name__ == "__main__":
    company_name = "DOVİ MODÜLER MOBİLYA İMALAT SANAYİ VE TİCARET LİMİTED ŞİRKETİ"
    scraper = IhaleScraper(company_name)
    
    scraper.scrape()  # 1. Get HTML
    result = scraper.process_html()  # 2. Parse HTML

    print(json.dumps(result, indent=4, ensure_ascii=False))
    
    # Optional: Save to JSON file
    with open("ihale_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4, ensure_ascii=False)
        print("📁 Saved to ihale_result.json")