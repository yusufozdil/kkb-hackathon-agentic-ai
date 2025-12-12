import requests
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context
import fitz  # PyMuPDF
import cv2
import numpy as np
import json
import re
from datetime import datetime, timedelta
import torch
from doctr.models import ocr_predictor

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
USE_GPU = True
CIPHERS = "ECDHE+AESGCM:ECDHE+CHACHA20:ECDHE+AES256:!aNULL:!eNULL:!EXPORT:!DES:!MD5:!PSK:!RC4"

# ---------------------------------------------------------
# 1. NETWORK (TLS FIX)
# ---------------------------------------------------------
class TLSAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = create_urllib3_context(ciphers=CIPHERS)
        kwargs["ssl_context"] = ctx
        return super().init_poolmanager(*args, **kwargs)

def get_pdf_url(date_str):
    year = date_str[:4]
    month = date_str[4:6]
    return f"https://www.resmigazete.gov.tr/eskiler/{year}/{month}/{date_str}.pdf"

def download_pdf_to_memory(url):
    print(f"⬇️ Downloading: {url}")
    session = requests.Session()
    session.mount("https://", TLSAdapter())
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    try:
        r = session.get(url, timeout=60, stream=True)
        r.raise_for_status()
        return r.content
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

# ---------------------------------------------------------
# 2. PDF PARSING LOGIC
# ---------------------------------------------------------
def normalize_tr(text):
    """Normalize Turkish characters for search"""
    map_chars = {'İ': 'I', 'ı': 'i', 'Ş': 'S', 'ş': 's', 'Ğ': 'G', 'ğ': 'g',
                 'Ü': 'U', 'ü': 'u', 'Ö': 'O', 'ö': 'o', 'Ç': 'C', 'ç': 'c', 'Â': 'A'}
    text = text.upper()
    for k, v in map_chars.items():
        text = text.replace(k, v)
    return text

def pdf_bytes_to_images(pdf_bytes):
    """
    Extract pages that may contain 'YASAKLAMA KARARI' from PDFs
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    in_ads_section = False

    print("🔍 Scanning PDF structure...")

    for page_num, page in enumerate(doc):
        text_raw = page.get_text("text")
        text_norm = normalize_tr(text_raw)

        if "CESITLI ILANLAR" in text_norm:
            in_ads_section = True
            print(f"   -> 'ÇEŞİTLİ İLÂNLAR' found on Page {page_num + 1}. Starting scan.")

        if not in_ads_section:
            continue

        has_keyword = "YASAKLAMA KARARI" in text_norm or "YASAKLANAN" in text_norm
        footer_check = "-1" in text_raw[-100:] if len(text_raw) > 100 else False

        if has_keyword or footer_check:
            print(f"   -> Extracting Page {page_num + 1}...")
            pix = page.get_pixmap(matrix=fitz.Matrix(2.5, 2.5))
            img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)

            if pix.n == 3: img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            elif pix.n == 4: img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGBA2BGR)
            else: img_cv = img_array

            yield page_num + 1, img_cv

# ---------------------------------------------------------
# 3. COMPUTER VISION & OCR (Doctr GPU)
# ---------------------------------------------------------


device = "cuda" if USE_GPU and torch.cuda.is_available() else "cpu"
print(f"🧠 Initializing Doctr OCR on {device.upper()}...")
ocr_model = ocr_predictor(pretrained=True, detect_language=True).to(device)

def process_single_page(img, page_num):
    """Runs Doctr OCR on a single page image"""
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    result = ocr_model([img_rgb])
    json_output = result.export()
    all_text = []
    for page in json_output["pages"]:
        for block in page["blocks"]:
            for line in block["lines"]:
                line_text = " ".join([w["value"] for w in line["words"]])
                all_text.append(line_text)
    plain_text = "\n".join(all_text)
    return plain_text

# ---------------------------------------------------------
# 4. MAIN SCRIPT
# ---------------------------------------------------------
if __name__ == "__main__":
    start_date_str = "20251209"  # YYYYMMDD
    end_date_str   = "20251209"  # YYYYMMDD

    start_date = datetime.strptime(start_date_str, "%Y%m%d")
    end_date = datetime.strptime(end_date_str, "%Y%m%d")

    all_results = []

    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime("%Y%m%d")
        url = get_pdf_url(date_str)
        pdf_bytes = download_pdf_to_memory(url)
        if pdf_bytes:
            for page_num, img in pdf_bytes_to_images(pdf_bytes):
                cleaned_text = process_single_page(img, page_num)
                if cleaned_text:
                    all_results.append({
                        "date": date_str,
                        "page": page_num,
                        "text": cleaned_text
                    })
                    print(f"✅ Processed {date_str} page {page_num}, {len(cleaned_text)} chars")
        current_date += timedelta(days=1)

    if all_results:
        filename = f"yasak_{start_date_str}_{end_date_str}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(all_results, f, ensure_ascii=False, indent=4)
        print(f"\n✅ Saved all {len(all_results)} records to {filename}")
