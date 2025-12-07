import requests
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context
import fitz  # PyMuPDF
import cv2
import numpy as np
import easyocr
import json
import os
import re
import ssl

# GLOBAL SSL BYPASS FOR EASYOCR MODEL DOWNLOAD
# This fixes the "CERTIFICATE_VERIFY_FAILED" error in urllib/easyocr
ssl._create_default_https_context = ssl._create_unverified_context

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
TARGET_DATE = "20251129"  # YYYYMMDD
OUTPUT_JSON = f"yasak_{TARGET_DATE}.json"
USE_GPU = True

# ---------------------------------------------------------
# 1. NETWORK (TLS FIX)
# ---------------------------------------------------------
CIPHERS = "ECDHE+AESGCM:ECDHE+CHACHA20:ECDHE+AES256:!aNULL:!eNULL:!EXPORT:!DES:!MD5:!PSK:!RC4"

class TLSAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = create_urllib3_context(ciphers=CIPHERS)
        ctx.check_hostname = False       # Önce hostname kontrolünü kapat
        ctx.verify_mode = ssl.CERT_NONE  # Sonra sertifika doğrulamasını kapat
        kwargs["ssl_context"] = ctx
        return super().init_poolmanager(*args, **kwargs)

def get_pdf_url(date_str):
    year = date_str[:4]
    month = date_str[4:6]
    return f"https://www.resmigazete.gov.tr/eskiler/{year}/{month}/{date_str}.pdf"

import warnings
from urllib3.exceptions import InsecureRequestWarning

# Suppress only the single warning from urllib3 needed.
warnings.simplefilter('ignore', InsecureRequestWarning)

def download_pdf_to_memory(url):
    print(f"Downloading: {url}")
    session = requests.Session()
    session.mount("https://", TLSAdapter())
    session.mount("https://", TLSAdapter())
    
    # Full Browser Headers to look legit
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1"
    }
    session.headers.update(headers)
    
    try:
        # verify=False is often needed for gov.tr sites with legacy certs
        r = session.get(url, timeout=60, stream=True, verify=False)
        r.raise_for_status()
        print(f"Download Success: {len(r.content)} bytes")
        return r.content
    except Exception as e:
        status_code = getattr(e.response, 'status_code', 'N/A') if hasattr(e, 'response') else 'N/A'
        print(f"Download Failed. Status: {status_code}. Error: {e}")
        return None

# ---------------------------------------------------------
# 2. PDF PARSING LOGIC (THE FIX)
# ---------------------------------------------------------
def normalize_tr(text):
    """Normalize Turkish characters for search"""
    map_chars = {'İ': 'I', 'ı': 'i', 'Ş': 'S', 'ş': 's', 'Ğ': 'G', 'ğ': 'g', 'Ü': 'U', 'ü': 'u', 'Ö': 'O', 'ö': 'o', 'Ç': 'C', 'ç': 'c', 'Â': 'A'}
    text = text.upper()
    for k, v in map_chars.items():
        text = text.replace(k, v)
    return text

def pdf_bytes_to_images(pdf_bytes, company_filter=None):
    """
    State Machine for PDF extraction:
    1. Wait for 'CESITLI ILANLAR'.
    2. Check for 'YASAKLAMA KARARI'.
    3. Check for '-1' in footer.
    
    Args:
        company_filter (str): If set, scans text layer first. 
                              Yields image ONLY if company name is found in text.
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    
    in_ads_section = False
    
    print("Scanning PDF structure...")

    filter_norm = normalize_tr(company_filter) if company_filter else None

    for page_num, page in enumerate(doc):
        text_raw = page.get_text("text") # Get plain text
        text_norm = normalize_tr(text_raw)
        
        # 1. LOOK FOR START TRIGGER
        if "CESITLI ILANLAR" in text_norm:
            in_ads_section = True
            print(f"   -> 'ÇEŞİTLİ İLÂNLAR' found on Page {page_num + 1}. Starting scan.")

        # If we haven't hit the section yet, skip
        if not in_ads_section:
            continue

        # 2. CHECK IF THIS PAGE IS A "BAN" PAGE
        # Criteria A: Must have "YASAKLAMA KARARI"
        has_keyword = "YASAKLAMA KARARI" in text_norm or "YASAKLANAN" in text_norm
        
        # Criteria B: Footer Check ("-1")
        footer_check = "-1" in text_raw[-100:] if len(text_raw) > 100 else False

        if has_keyword:
            # OPTIMIZATION: Text Filter Check
            if filter_norm:
                # If we are looking for a specific company, and it's NOT in the text layer,
                # we skip the expensive OCR / Image rendering.
                if filter_norm not in text_norm:
                    # print(f"   [Skipping Page {page_num+1}: Keyword found but Company '{company_filter}' not in text]")
                    continue
                else:
                    print(f"    MATCH! Company '{company_filter}' found in text on Page {page_num+1}!")

            print(f"   -> extracting Page {page_num + 1}...")
            
            # Render Page to OpenCV Image
            pix = page.get_pixmap(matrix=fitz.Matrix(2.5, 2.5))
            img_array = np.frombuffer(pix.samples, dtype=np.uint8)
            img_array = img_array.reshape(pix.h, pix.w, pix.n)
            
            if pix.n == 3: img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            elif pix.n == 4: img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGBA2BGR)
            else: img_cv = img_array
            
            yield (page_num + 1, img_cv)
        
        # 3. STOP CONDITION (Optional Logic)
        elif in_ads_section and len(text_raw) > 200 and not footer_check:
            pass

# ---------------------------------------------------------
# 3. COMPUTER VISION & OCR (SAME AS BEFORE)
# ---------------------------------------------------------
def clean_ocr(text):
    if not text: return ""
    text = text.replace("\n", " ")
    text = re.sub(r'^[|:;\-\.\s]+', '', text)
    text = re.sub(r'[|:;\-\.\s]+$', '', text)
    return text.strip()

def get_sorted_rows(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (50, 1))
    v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 50))
    grid_mask = cv2.add(cv2.morphologyEx(thresh, cv2.MORPH_OPEN, h_kernel, iterations=2),
                        cv2.morphologyEx(thresh, cv2.MORPH_OPEN, v_kernel, iterations=2))
    
    contours, _ = cv2.findContours(grid_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
    cells = []
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if w > 30 and h > 20 and w < img.shape[1] - 50:
            cells.append((x, y, w, h))

    cells.sort(key=lambda b: b[1])
    rows = []
    if not cells: return []
    
    current_row = [cells[0]]
    for i in range(1, len(cells)):
        if abs(cells[i][1] - current_row[-1][1]) < 20:
            current_row.append(cells[i])
        else:
            current_row.sort(key=lambda b: b[0])
            rows.append(current_row)
            current_row = [cells[i]]
    current_row.sort(key=lambda b: b[0])
    rows.append(current_row)
    return rows

def process_single_page(img, page_num, reader):
    rows = get_sorted_rows(img)
    if not rows: return None

    entry = {
        "Page": page_num,
        "Global_Info": {"Yasak_Kayit_No": None, "IKN": None, "Bakanlik": None, "Yasak_Suresi": None},
        "Idare": {"Unvan": None, "Adres": None},
        "Yasakli_Firma": {"Unvan": None, "Vergi_No": None, "TC_No": None, "Adres": None},
        "Ortaklar": []
    }
    current_section = "HEAD" 

    for row_cells in rows:
        row_texts = []
        for (x, y, w, h) in row_cells:
            roi = img[y+2:y+h-2, x+2:x+w-2]
            roi = cv2.copyMakeBorder(roi, 10, 10, 10, 10, cv2.BORDER_CONSTANT, value=[255, 255, 255])
            res = reader.readtext(roi, detail=0)
            txt = clean_ocr(" ".join(res))
            if len(txt) > 1: row_texts.append(txt)

        if not row_texts: continue
        full_row = " ".join(row_texts).upper()

        if "3.İHALEYİ" in full_row or "3.IHALEYI" in full_row: current_section = "IDARE"; continue
        if "4.İHALELERE" in full_row: current_section = "YASAKLI"; continue
        if "5.ORTAK" in full_row: current_section = "ORTAK"; continue

        key, val = "", ""
        if len(row_texts) >= 2: key, val = row_texts[0], row_texts[1]
        elif len(row_texts) == 1 and ":" in row_texts[0]:
            parts = row_texts[0].split(":", 1)
            key, val = parts[0], parts[1]
        
        if not val: continue
        key_low = key.lower()
        val_clean = clean_ocr(val)

        if "kayıt no" in key_low and "ihale" not in key_low: entry["Global_Info"]["Yasak_Kayit_No"] = val_clean
        elif "ikn" in key_low: entry["Global_Info"]["IKN"] = val_clean
        elif "bakanlık" in key_low: entry["Global_Info"]["Bakanlik"] = val_clean
        elif "süre" in key_low: entry["Global_Info"]["Yasak_Suresi"] = val_clean

        elif current_section == "IDARE":
            if "adı" in key_low: entry["Idare"]["Unvan"] = val_clean
            elif "adresi" in key_low: entry["Idare"]["Adres"] = val_clean

        elif current_section == "YASAKLI":
            if "adı" in key_low:
                if entry["Yasakli_Firma"]["Unvan"]: entry["Yasakli_Firma"]["Unvan"] += " | " + val_clean
                else: entry["Yasakli_Firma"]["Unvan"] = val_clean
            elif "vergi" in key_low: entry["Yasakli_Firma"]["Vergi_No"] = val_clean
            elif "t.c" in key_low: entry["Yasakli_Firma"]["TC_No"] = val_clean
            elif "adresi" in key_low: entry["Yasakli_Firma"]["Adres"] = val_clean

        elif current_section == "ORTAK":
            if "adı" in key_low: entry["Ortaklar"].append({"Unvan": val_clean, "ID": None})
            elif ("vergi" in key_low or "t.c" in key_low):
                if entry["Ortaklar"]: entry["Ortaklar"][-1]["ID"] = val_clean

    return entry

# ---------------------------------------------------------
# MAIN FUNCTION WRAPPER
# ---------------------------------------------------------
def check_banned_status(date_str, company_name=None):
    """
    Checks the Official Gazette for banned company decisions.
    
    Args:
        date_str (str): Date in YYYYMMDD format.
        company_name (str, optional): Specific company to search for. 
                                      If provided, uses FAST text-based pre-filtering.
                                      If None, performs SLOW full OCR scan of all relevant pages.
    """
    # 0. CHECK CACHED JSON (Full Dataset)
    # If we have already scanned the entire day, just look it up!
    if os.path.exists(OUTPUT_JSON):
        print(f"⚡ Loading cached results from {OUTPUT_JSON}...")
        try:
            with open(OUTPUT_JSON, "r", encoding="utf-8") as f:
                all_results = json.load(f)
            
            if company_name:
                # Filter cached results
                search_norm = normalize_tr(company_name)
                filtered = [r for r in all_results if search_norm in normalize_tr(str(r.get("Yasakli_Firma", {}).get("Unvan", "")))]
                return filtered
            return all_results
        except Exception as e:
            print(f"Cache read error: {e}")

    # 1. DOWNLOAD OR LOAD PDF
    url = get_pdf_url(date_str)
    pdf_filename = f"{date_str}.pdf"
    
    if os.path.exists(pdf_filename):
        print(f"Using cached PDF: {pdf_filename}")
        with open(pdf_filename, "rb") as f:
            pdf_data = f.read()
    else:
        pdf_data = download_pdf_to_memory(url)
        if pdf_data:
            with open(pdf_filename, "wb") as f:
                f.write(pdf_data)
                print(f"Saved PDF to cache: {pdf_filename}")

    final_results = []
    
    if pdf_data:
        print(f"Initializing OCR for date {date_str}...")
        if company_name:
            print(f"FAST MODE: Searching specific company: '{company_name}'")
            
        reader = easyocr.Reader(['tr'], gpu=USE_GPU)
        
        # We pass company_name to the generator to enable Smart Skip
        for page_num, img_cv in pdf_bytes_to_images(pdf_data, company_filter=company_name):
            try:
                data = process_single_page(img_cv, page_num, reader)
                if data and (data["Yasakli_Firma"]["Unvan"] or data["Global_Info"]["Yasak_Kayit_No"]):
                    final_results.append(data)
            except Exception as e:
                print(f"Error Page {page_num}: {e}")

        # Only save Full JSON if we did a Full Scan (no filter)
        if not company_name:
            if final_results:
                with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
                    json.dump(final_results, f, ensure_ascii=False, indent=4)
                print(f"Saved {len(final_results)} records to {OUTPUT_JSON}")

    return final_results

if __name__ == "__main__":
    results = check_banned_status(TARGET_DATE)
    if results:
        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
        print(f"Saved {len(results)} records to {OUTPUT_JSON}")
    else:
        print("No records found.")
