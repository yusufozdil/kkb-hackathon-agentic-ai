import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
import cv2
import numpy as np
import re
from requests_toolbelt.multipart.encoder import MultipartEncoder
import json
import time
import easyocr
import os
import sys

# Ensure TOBB dir is on path for module resolution
sys.path.append(os.path.dirname(__file__))

try:
    from TOBB import TOBBOCR
except ImportError:
    try:
        import TOBBOCR  # fallback if package path not resolved
    except ImportError as e:
        TOBBOCR = None
        print(f"[WARN] TOBBOCR import failed: {e}")

class TTSClient:
    BASE = "https://www.ticaretsicil.gov.tr"
    INDEX_URL = BASE + "/index.php"
    LOGIN_URL = BASE + "/view/modal/uyegirisi_ok.php"
    ILAN_PAGE_URL = BASE + "/view/hizlierisim/ilangoruntuleme.php"
    ILAN_POST_URL = BASE + "/view/hizlierisim/ilangoruntuleme_ok.php"

    def __init__(self, email, password, ocr_reader=None, manual_cookies=None):
        self.email = email
        self.password = password
        self.manual_cookies = manual_cookies  # Dict of cookie_name: cookie_value
        self.session = requests.Session()
        # Higher UA for login reliability
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7"
        })
        self.ocr_reader = ocr_reader or easyocr.Reader(["en"], gpu=False)

    def solve_captcha(self, img_bytes):
        img = Image.open(BytesIO(img_bytes)).convert("L")
        arr = np.array(img)
        
        # AGGRESSIVE PREPROCESSING
        # 1. Contrast enhancement (histogram equalization)
        arr = cv2.equalizeHist(arr)
        # 2. Median blur to remove noise
        arr = cv2.medianBlur(arr, 3)
        
        candidates = []
        # Extended threshold range + multiple preprocessing strategies
        for thr in [60, 80, 100, 120, 140, 160, 180, 200]:
            _, thresh = cv2.threshold(arr, thr, 255, cv2.THRESH_BINARY)
            
            # Try multiple morphology strategies
            for morph_strategy in ["dilate", "erode", "open", "close"]:
                kernel = np.ones((2, 2), np.uint8)
                if morph_strategy == "dilate":
                    processed = cv2.dilate(thresh, kernel, iterations=1)
                elif morph_strategy == "erode":
                    processed = cv2.erode(thresh, kernel, iterations=1)
                elif morph_strategy == "open":
                    processed = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
                else:  # close
                    processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=1)
                
                clean_rgb = cv2.cvtColor(np.uint8(processed), cv2.COLOR_GRAY2RGB)
                res = self.ocr_reader.readtext(
                    clean_rgb,
                    detail=0,
                    allowlist="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789",
                    paragraph=False,
                )
                if res:
                    text = "".join([c for c in res[0].upper() if c.isalnum()])
                    if len(text) >= 3:  # CAPTCHA typically 4 chars, accept 3+
                        candidates.append(text)
        
        if not candidates:
            return ""
        
        # Pick most common candidate (voting), then longest
        from collections import Counter
        counted = Counter(candidates)
        if counted:
            most_common = counted.most_common(1)[0][0]
            return most_common
        return sorted(candidates, key=len, reverse=True)[0]

    def login(self, retries=12, wait_seconds=2.0):
        # 🔓 BYPASS: Try manual cookies first
        if self.manual_cookies:
            print("[COOKIE BYPASS] Using manual session cookies, skipping CAPTCHA")
            for cookie_name, cookie_value in self.manual_cookies.items():
                self.session.cookies.set(cookie_name, cookie_value, domain='www.ticaretsicil.gov.tr', path='/')
                print(f"[COOKIE] Set {cookie_name}={cookie_value[:20]}...")
            
            # Test if cookies work
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
                "Referer": self.INDEX_URL
            }
            test_response = self.session.get(self.ILAN_PAGE_URL, headers=headers)
            print(f"[COOKIE TEST] Status={test_response.status_code}, Length={len(test_response.content)}")
            
            # If response is valid (not redirect, has content), cookies work
            if test_response.status_code == 200 and len(test_response.content) > 5000:
                print("[COOKIE BYPASS] ✅ Manual cookies are VALID! Skipping CAPTCHA entirely.")
                return True
            else:
                print("[COOKIE BYPASS] ⚠️ Manual cookies EXPIRED or INVALID. Falling back to CAPTCHA login...")
        
        # Normal CAPTCHA flow
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": self.INDEX_URL
        }

        for attempt in range(1, retries + 1):
            print(f"LOGIN ATTEMPT {attempt}")
            try:
                r = self.session.get(self.INDEX_URL, headers=headers)
                soup = BeautifulSoup(r.text, "html.parser")
                img_tag = soup.find("img", src=re.compile("captcha.php"))
                if not img_tag:
                    raise Exception("CAPTCHA not found")

                cap_url = img_tag["src"]
                if cap_url.startswith("/"):
                    cap_url = self.BASE + cap_url

                cap_img = self.session.get(cap_url, headers=headers).content
                cap_code = self.solve_captcha(cap_img)
                print("CAPTCHA:", cap_code)

                payload = {"LoginEmail": self.email, "LoginSifre": self.password, "Captcha": cap_code}
                resp = self.session.post(self.LOGIN_URL, data=payload, headers=headers)
                
                print(f"[LOGIN] Response status={resp.status_code}, text={resp.text[:100]}")
                print(f"[LOGIN] Response headers: {dict(resp.headers)}")
                print(f"[LOGIN] Set-Cookie headers: {resp.headers.get('Set-Cookie', 'NONE')}")
                print(f"[LOGIN] Session cookies after POST: {dict(self.session.cookies)}")

                if resp.text.strip() == "1":
                    print("Login OK")
                    # Manually check and add cookies if needed
                    if not self.session.cookies:
                        print("[LOGIN][WARN] No cookies set after successful login! Checking response cookies...")
                        print(f"[LOGIN] resp.cookies: {dict(resp.cookies)}")
                    
                    ilan_page = self.session.get(self.ILAN_PAGE_URL, headers=headers)
                    print(f"[LOGIN] ILAN_PAGE GET status={ilan_page.status_code}")
                    print(f"[LOGIN] Session cookies after ILAN_PAGE GET: {dict(self.session.cookies)}")
                    return True

                print("Login failed with this captcha.")
                snippet = resp.text[:2000].replace("\n", " ")
                print(f"[LOGIN][{attempt}] resp status={resp.status_code}, snippet: {snippet}")
            except Exception as e:
                print("Error:", e)
            time.sleep(wait_seconds)

        print("All login attempts failed.")
        return False

    def fetch_ilanlar(self, mudurluk_id, ticaret_unvani="", sicil_no="", tarih1="", tarih2=""):
        """
        Fetch ilanlar from TOBB using the correct endpoint and parameters.
        Site returns all results in a single request (no pagination needed).
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "tr,en-US;q=0.9,en;q=0.8",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": self.BASE,
            "Referer": self.ILAN_PAGE_URL,
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin"
        }
        
        print(f"[ILAN] Starting fetch with cookies: {dict(self.session.cookies)}")

        # Simple form parameters - no draw/start/length needed
        fields_dict = {
            "SicilMudurluguId": str(mudurluk_id),
            "TicSicNo": sicil_no if sicil_no else "",
            "TicaretUnvani": ticaret_unvani if ticaret_unvani else "",
            "Tarih1": tarih1 if tarih1 else "",
            "Tarih2": tarih2 if tarih2 else ""
        }
        
        print(f"[ILAN][POST] URL: {self.ILAN_POST_URL}")
        print(f"[ILAN][POST] fields: {fields_dict}")
        
        form = MultipartEncoder(fields=fields_dict)
        headers["Content-Type"] = form.content_type
        
        r = self.session.post(self.ILAN_POST_URL, headers=headers, data=form, timeout=30)
        print(f"[ILAN][POST] status={r.status_code} content-length={len(r.text)} content-type={r.headers.get('Content-Type', 'N/A')}")
        
        # Parse response
        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.find("table", id="tblIlanGoruntuleme")
        
        if table is None:
            snippet = r.text[:2000].replace("\n", " ")
            print(f"[WARN] Table not found; HTML snippet (first 2000 chars): {snippet}")
            
            # Check if response looks like full HTML page (indicates session/auth issue)
            if "<!DOCTYPE" in r.text or "<html" in r.text:
                print(f"[WARN] Response appears to be full HTML page, not table data. Possible session issue.")
                
            return {"status": "Login Problem or No Data", "data": [], "html_snippet": snippet}

        tbody = table.find("tbody")
        if tbody is None:
            print(f"[WARN] tbody not found in table")
            return {"status": "No Data", "data": []}
            
        rows = tbody.find_all("tr")
        print(f"[ILAN] Found {len(rows)} rows in table")
        
        if not rows:
            return {"status": "No Data", "data": []}

        all_records = []
        for row in rows:
            cols = [td.get_text(strip=True) for td in row.find_all("td")]
            if len(cols) < 7:  # Skip malformed rows
                continue
                
            pdf_a = row.find("a", href=True)
            pdf = pdf_a["href"] if pdf_a else None
            
            all_records.append({
                "Mudurluk": cols[0],
                "SicilNo": cols[1],
                "Unvan": cols[2],
                "YayinTarihi": cols[3],
                "Sayi": cols[4],
                "Sayfa": cols[5],
                "IlanTuru": cols[6],
                "PDF": pdf
            })

        print(f"[ILAN] Successfully extracted {len(all_records)} records")
        return {"status": "success", "data": all_records}

    def fetch_pdf(self, first_url):
        try:
            print(f"[PDF] Açılıyor: {first_url}")
            headers = {"User-Agent": "Mozilla/5.0", "Referer": self.ILAN_PAGE_URL}
            r = self.session.get(first_url, headers=headers)
            if r.status_code != 200:
                print("[PDF] HTML sayfası yüklenemedi.")
                return None

            soup = BeautifulSoup(r.text, "html.parser")
            link_tag = soup.find("embed")
            if not link_tag:
                print("[PDF] PDF linki bulunamadı.")
                return None

            pdf_url = link_tag["src"]
            if pdf_url.startswith("/"):
                pdf_url = self.BASE + pdf_url

            pdf_res = self.session.get(pdf_url, headers=headers, allow_redirects=True)
            if pdf_res.status_code != 200:
                print("[PDF] PDF indirilemedi.")
                return None

            print("[PDF] PDF başarıyla indirildi.")
            return pdf_res.content
        except Exception as e:
            print(f"[PDF] Hata: {e}")
            return None

    def attach_ocr_to_ilans(self, ilan_list, tmp_dir="ocr_tmp"):
        os.makedirs(tmp_dir, exist_ok=True)
        enriched = []
        used_section = False

        print(f"[OCR] Processing {len(ilan_list)} ilan entries...")

        for ilan in ilan_list:
            try:
                print("\n------------------------------------")
                print(f"[OCR] Processing ilan: {ilan.get('Unvan', '')}")
                ilan_turu = ilan.get("IlanTuru", "").upper()
                target_phrase = ilan.get("Unvan", "").upper()

                if "KURULU" in ilan_turu:
                    section_type = "KURULUS"
                elif "PAY" in ilan_turu and not used_section:
                    section_type = "PAY"
                    used_section = True
                elif "SERMAYE" in ilan_turu and not used_section:
                    section_type = "SERMAYE"
                    used_section = True
                else:
                    print("[OCR] Skipped: Irrelevant IlanTuru or already processed PAY/SERMAYE.")
                    ilan["OCR"] = None
                    enriched.append(ilan)
                    continue

                print(f"[OCR] Section type chosen: {section_type}")
                first_url = self.BASE + "/view/hizlierisim/" + ilan["PDF"]
                print(f"[OCR] First URL for PDF: {first_url}")

                raw_pdf = self.fetch_pdf(first_url)
                if not raw_pdf:
                    print("[OCR] PDF download failed. Skipping OCR.")
                    ilan["OCR"] = None
                    enriched.append(ilan)
                    continue

                guid = ilan["PDF"].split("=")[-1]
                pdf_path = os.path.join(tmp_dir, f"{guid}.pdf")
                with open(pdf_path, "wb") as f:
                    f.write(raw_pdf)

                print("[OCR] Running TOBBOCR...")
                ocr = TOBBOCR.TOBBOCR(dpi=200, gpu=True)
                paragraphs = ocr.run(pdf_path=pdf_path, section_type=section_type, target_company=target_phrase)
                ilan["OCR"] = paragraphs
                enriched.append(ilan)
                print(f"[OCR] OCR result: {paragraphs}")

            except Exception as e:
                print(f"[ERROR] OCR failed for ilan: {e}")
                ilan["OCR"] = None
                enriched.append(ilan)

        return enriched

    # ----------------------
    # MAIN ENTRY METHOD
    # ----------------------
    def main(self, mudurluk_id, sicil_no, tarih1, tarih2):
        session_ok = self.login()
        if not session_ok:
            print("Login failed completely.")
            return

        result = self.fetch_ilanlar(
            mudurluk_id=mudurluk_id,
            sicil_no=sicil_no,
            tarih1=tarih1,
            tarih2=tarih2
        )

        if result["status"] == "success":
            enriched = self.attach_ocr_to_ilans(result["data"])
            result = {"status": "success", "data": enriched}

        print(json.dumps(result, indent=4, ensure_ascii=False))


if __name__ == "__main__":
    client = TTSClient(email="Ng8224@gmail.com", password="E9HMFDawP8$tuc")
    client.main(
        mudurluk_id=232,
        sicil_no="310797-5",
        tarih1="01.12.2025",
        tarih2="14.12.2025"
    )
