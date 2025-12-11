import requests
from bs4 import BeautifulSoup
import easyocr
from PIL import Image
import numpy as np
import json
import cv2
import time

class TicaretScraper:
    BASE = "https://www.ticaretsicil.gov.tr"
    FORM_URL = BASE + "/view/hizlierisim/unvansorgulama.php"
    CAPTCHA_URL = BASE + "/assets/captcha/captcha.php"
    POST_URL = BASE + "/view/hizlierisim/unvansorgulama_ok.php"

    def __init__(self, search_term, mudurluk_file="mudurluk.json"):
        self.search_term = search_term
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": self.FORM_URL
        }
        # Load SICIL mapping
        with open(mudurluk_file, "r", encoding="utf-8") as f:
            self.SICIL_IDS = json.load(f)
        # OCR reader (CPU)
        self.reader = easyocr.Reader(['en', 'tr'], gpu=False)

    def solve_captcha(self, path):
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        # Try multiple thresholds and keep best guess
        candidates = []
        for thr in [110, 130, 150, 180]:
            _, thresh = cv2.threshold(img, thr, 255, cv2.THRESH_BINARY)
            res = self.reader.readtext(thresh, detail=0, paragraph=False, allowlist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
            if res:
                text = "".join(res).replace(" ", "").upper()
                candidates.append(text)
        if not candidates:
            return ""
        # pick longest (more confident)
        return sorted(candidates, key=len, reverse=True)[0]
    def get_mudurluk_id(self, name):
        # Search SICIL_IDS by value
        for k, v in self.SICIL_IDS.items():
            if v.strip().upper() == name.strip().upper():
                return k
        return None  # Not found

    def get_results(self):
        print("Opening form page...")
        self.session.get(self.FORM_URL, headers=self.headers)
        # Try CAPTCHA up to 8 times if it fails
        for attempt in range(8):
            print(f"Downloading CAPTCHA... Attempt {attempt+1}")
            cap = self.session.get(self.CAPTCHA_URL, headers=self.headers)
            with open("captcha.png", "wb") as f:
                f.write(cap.content)
            captcha_text = self.solve_captcha("captcha.png")
            if not captcha_text:
                print("Failed to read CAPTCHA, retrying...")
                time.sleep(1.5)
                continue
            print("CAPTCHA solved as:", captcha_text)
            payload = {
                "YeniSorgu": "1",
                "UnvanSorgu": self.search_term,
                "Captcha": captcha_text
            }
            res = self.session.post(self.POST_URL, data=payload, headers=self.headers)
            html = res.text
            soup = BeautifulSoup(html, "html.parser")
            table = soup.find("table")
            if table:
                results = []
                for tr in table.find_all("tr")[1:]:
                    tds = [td.get_text(strip=True) for td in tr.find_all("td")]
                    if len(tds) >= 4:
                        mudurluk_id = tds[0]
                        results.append({
                            "mudurluk": self.get_mudurluk_id(tds[3]),
                            "sicil_no": tds[2],
                            "unvan": tds[1],
                            "sehir": tds[3]
                        })
                return results
            else:
                print("Table not found, retrying...")
                time.sleep(2)
        print("Failed to fetch results after multiple attempts.")
        return []

# ------------------------------
# USAGE
# ------------------------------
if __name__ == "__main__":
    scraper = TicaretScraper("EKOMO", mudurluk_file="TOBB/mudurluk.json")
    data = scraper.get_results()
    print(json.dumps(data, indent=2, ensure_ascii=False))
