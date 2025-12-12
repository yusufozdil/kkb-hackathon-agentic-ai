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
from datetime import datetime, timedelta
from typing import Optional, List, Dict

from ihale_db import (
    ensure_db,
    upsert_ban,
    parse_entry_to_record,
    query_bans,
    format_query_response,
    normalize_tr,
    DB_PATH,
)

# GLOBAL SSL BYPASS FOR EASYOCR MODEL DOWNLOAD
# This fixes the "CERTIFICATE_VERIFY_FAILED" error in urllib/easyocr
ssl._create_default_https_context = ssl._create_unverified_context

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
TARGET_DATE = "20251129"  # YYYYMMDD
OUTPUT_JSON = f"yasak_{TARGET_DATE}.json"
USE_GPU = True
PDF_CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "pdf_cache")

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
# 4. DB + SCAN HELPERS
# ---------------------------------------------------------
def ensure_pdf_cache():
    os.makedirs(PDF_CACHE_DIR, exist_ok=True)


def scan_date_and_store(date_str: str, company_filter: Optional[str] = None, reader=None, save_pdf: bool = False) -> List[Dict]:
    """
    Downloads a given date's gazette, scans for bans, upserts DB, and returns stored records.
    """
    ensure_db()
    ensure_pdf_cache()

    pdf_url = get_pdf_url(date_str)
    pdf_filename = os.path.join(PDF_CACHE_DIR, f"{date_str}.pdf")
    pdf_data = None

    if os.path.exists(pdf_filename):
        with open(pdf_filename, "rb") as f:
            pdf_data = f.read()
    else:
        pdf_data = download_pdf_to_memory(pdf_url)
        if pdf_data and save_pdf:
            with open(pdf_filename, "wb") as f:
                f.write(pdf_data)

    if not pdf_data:
        return []

    local_reader = reader or easyocr.Reader(["tr"], gpu=USE_GPU)
    stored_records = []

    for page_num, img_cv in pdf_bytes_to_images(pdf_data, company_filter=company_filter):
        try:
            data = process_single_page(img_cv, page_num, local_reader)
            if data:
                unvan = data.get("Yasakli_Firma", {}).get("Unvan")
                yasak_no = data.get("Global_Info", {}).get("Yasak_Kayit_No")
                print(f"[DEBUG] Page {page_num}: Unvan='{unvan}', Yasak_No='{yasak_no}'")
                
                if unvan or yasak_no:
                    record = parse_entry_to_record(data, date_str, pdf_url, page_num)
                    inserted, rowid = upsert_ban(record)
                    if inserted:
                        print(f"[DB] ✅ Inserted record ID={rowid} for '{unvan or yasak_no}'")
                    else:
                        print(f"[DB] ⚠️ Updated existing record for '{unvan or yasak_no}'")
                    stored_records.append(record)
                else:
                    print(f"[SKIP] Page {page_num}: No Unvan/Yasak_No found, skipping DB insert")
            else:
                print(f"[SKIP] Page {page_num}: process_single_page returned None")
        except Exception as e:
            print(f"[ERROR] Page {page_num}: {e}")

    return stored_records


def backfill_range(start_date: str, end_date: str, company_filter: Optional[str] = None, save_pdf: bool = False) -> Dict[str, int]:
    """
    Scans a date range (inclusive) and stores results in DB.
    """
    ensure_db()
    start_dt = datetime.strptime(start_date, "%Y%m%d")
    end_dt = datetime.strptime(end_date, "%Y%m%d")
    reader = easyocr.Reader(["tr"], gpu=USE_GPU)
    total = 0
    scanned = 0

    current = start_dt
    while current <= end_dt:
        date_str = current.strftime("%Y%m%d")
        results = scan_date_and_store(date_str, company_filter=company_filter, reader=reader, save_pdf=save_pdf)
        total += len(results)
        scanned += 1
        current += timedelta(days=1)

    return {"scanned_days": scanned, "inserted_records": total}

# ---------------------------------------------------------
# MAIN FUNCTION WRAPPER
# ---------------------------------------------------------
def check_banned_status(
    date_str: Optional[str] = None,
    company_name: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    force_scan: bool = False,
):
    """
    Yeni akış: Önce DB'den bakar, gerekirse tarayıp DB'yi doldurur.

    Args:
        date_str: Tek tarih (YYYYMMDD) için hızlandırılmış çağrı. start/end yoksa kullanılır.
        company_name: Firma adı (normalizasyon içerir).
        start_date, end_date: Tarih aralığı (YYYYMMDD). Boşsa date_str kullanılır.
        force_scan: True ise DB sonucundan bağımsız yeniden tarar ve DB'ye yazar.
    Returns:
        {"found": bool, "count": int, "records": [...]}
    """
    if not (start_date and end_date):
        if not date_str:
            raise ValueError("start_date/end_date veya date_str verilmelidir")
        start_date = end_date = date_str

    ensure_db()

    # 1) DB sorgusu
    rows = []
    if not force_scan:
        rows = query_bans(company_name or "", start_date, end_date)
        if rows:
            return format_query_response(rows)

    # 2) Canlı tarama ve DB'ye yazma
    reader = easyocr.Reader(["tr"], gpu=USE_GPU)
    start_dt = datetime.strptime(start_date, "%Y%m%d")
    end_dt = datetime.strptime(end_date, "%Y%m%d")

    current = start_dt
    while current <= end_dt:
        cur_date = current.strftime("%Y%m%d")
        scan_date_and_store(cur_date, company_filter=company_name, reader=reader, save_pdf=True)
        current += timedelta(days=1)

    rows = query_bans(company_name or "", start_date, end_date)
    return format_query_response(rows)

if __name__ == "__main__":
    res = check_banned_status(TARGET_DATE)
    if res and res.get("records"):
        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=4)
        print(f"Saved {res.get('count', 0)} records to {OUTPUT_JSON} | DB: {DB_PATH}")
    else:
        print("No records found.")
