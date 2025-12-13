import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables (for TOBB cookies)
load_dotenv()

from TOBB.TicaretScraper import TicaretScraper
from TOBB.TTSClient import TTSClient


def _format_ddmmyyyy(date_str: str) -> str:
    # Input: YYYYMMDD
    dt = datetime.strptime(date_str, "%Y%m%d")
    return dt.strftime("%d.%m.%Y")


def search_company(company_name: str, mudurluk_file: str) -> List[Dict[str, Any]]:
    scraper = TicaretScraper(company_name, mudurluk_file=mudurluk_file)    
    return scraper.get_results() or []


def fetch_ilan_ocr(mudurluk_id: str, sicil_no: str, start_date: str, end_date: str, email: str, password: str) -> Dict[str, Any]:
    # 🔓 Load manual cookies from environment (CAPTCHA bypass)
    manual_cookies = {}
    cookie0 = os.getenv("TOBB_COOKIE_0")  # atrsrv-101020155
    cookie1 = os.getenv("TOBB_COOKIE_1")  # atrsrv-101041123
    cookie2 = os.getenv("TOBB_COOKIE_2")  # atrsrv-101041124
    
    if cookie0:
        manual_cookies["atrsrv-101020155"] = cookie0  # TOBB session cookie
        print(f"[TOBB] Loaded atrsrv-101020155: {cookie0[:20]}...")
    if cookie1:
        manual_cookies["atrsrv-101041123"] = cookie1  # TOBB session cookie
        print(f"[TOBB] Loaded atrsrv-101041123: {cookie1[:20]}...")
    if cookie2:
        manual_cookies["atrsrv-101041124"] = cookie2  # TOBB session cookie
        print(f"[TOBB] Loaded atrsrv-101041124: {cookie2[:20]}...")
    
    client = TTSClient(email=email, password=password, manual_cookies=manual_cookies if manual_cookies else None)
    
    # CRITICAL: Login first! (will use manual cookies if available)
    print("[TOBB] Attempting login...")
    if not client.login():
        print("[TOBB] Login failed!")
        return {"status": "Login Failed", "data": []}
    
    print("[TOBB] Login successful, fetching ilanlar...")
    tarih1 = _format_ddmmyyyy(start_date)
    tarih2 = _format_ddmmyyyy(end_date)
    result = client.fetch_ilanlar(mudurluk_id=mudurluk_id, sicil_no=sicil_no, tarih1=tarih1, tarih2=tarih2)

    if result.get("status") != "success":
        return result

    enriched = client.attach_ocr_to_ilans(result["data"])
    return {"status": "success", "data": enriched}


def fetch_trade_registry(company_name: str, start_date: str, end_date: str) -> Dict[str, Any]:
    """
    High-level helper: arama + ilan çekme + OCR.
    Env değişkenleri: TTS_EMAIL, TTS_PASSWORD
    """
    email = os.getenv("TTS_EMAIL")
    password = os.getenv("TTS_PASSWORD")
    if not email or not password:
        return {"status": "error", "message": "Set TTS_EMAIL and TTS_PASSWORD env vars."}

    mudurluk_file = os.path.join(os.path.dirname(__file__), "TOBB", "mudurluk.json")
    search_results = search_company(company_name, mudurluk_file)
    if not search_results:
        return {"status": "not_found", "message": "Şirket bulunamadı", "data": []}

    # Basit seçim: ilk sonuç
    first = search_results[0]
    mudurluk_id = first.get("mudurluk")
    sicil_no = first.get("sicil_no")
    if not mudurluk_id or not sicil_no:
        return {"status": "error", "message": "mudurluk_id veya sicil_no eksik", "data": search_results}

    # 🎯 PERFORMANCE: Skip OCR (too slow), just fetch ilan list
    # Old: fetch_ilan_ocr (includes OCR processing)
    # New: Direct fetch without OCR
    
    # Create TTSClient and login
    manual_cookies = {}
    cookie0 = os.getenv("TOBB_COOKIE_0")
    cookie1 = os.getenv("TOBB_COOKIE_1")
    cookie2 = os.getenv("TOBB_COOKIE_2")
    
    if cookie0:
        manual_cookies["atrsrv-101020155"] = cookie0
        print(f"[TOBB] Loaded atrsrv-101020155: {cookie0[:20]}...")
    if cookie1:
        manual_cookies["atrsrv-101041123"] = cookie1
        print(f"[TOBB] Loaded atrsrv-101041123: {cookie1[:20]}...")
    if cookie2:
        manual_cookies["atrsrv-101041124"] = cookie2
        print(f"[TOBB] Loaded atrsrv-101041124: {cookie2[:20]}...")
    
    from TOBB.TTSClient import TTSClient
    client = TTSClient(email=email, password=password, manual_cookies=manual_cookies if manual_cookies else None)
    
    print("[TOBB] Attempting login...")
    if not client.login():
        print("[TOBB] Login failed!")
        return {"status": "Login Failed", "data": []}
    
    print("[TOBB] Login successful, fetching ilanlar (WITHOUT OCR for speed)...")
    tarih1 = _format_ddmmyyyy(start_date)
    tarih2 = _format_ddmmyyyy(end_date)
    
    # Fetch ilanlar WITHOUT OCR
    ilan_data = client.fetch_ilanlar(mudurluk_id=mudurluk_id, sicil_no=sicil_no, tarih1=tarih1, tarih2=tarih2)
    
    if ilan_data.get("status") != "success":
        return ilan_data
    
    ilanlar = ilan_data["data"]
    
    # Limit to prevent LLM timeout (max 10 for demo)
    total_found = len(ilanlar)
    if len(ilanlar) > 10:
        print(f"[TOBB] ⚠️ {total_found} ilan bulundu, ilk 10'u kullanılıyor (LLM timeout engellemek için)")
        ilanlar = ilanlar[:10]
    
    # Remove OCR field if present to reduce payload size
    for ilan in ilanlar:
        if 'OCR' in ilan:
            del ilan['OCR']
        if 'ocr_text' in ilan:
            del ilan['ocr_text']
    
    return {
        "status": "success",
        "search_result": first,
        "ilanlar": ilanlar,
        "total_found": total_found,
        "returned": len(ilanlar),
    }

