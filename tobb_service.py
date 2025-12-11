import os
from datetime import datetime
from typing import Dict, Any, List, Optional

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
    client = TTSClient(email=email, password=password)
    
    # CRITICAL: Login first!
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

    ilan_data = fetch_ilan_ocr(mudurluk_id, sicil_no, start_date, end_date, email, password)
    if ilan_data.get("status") != "success":
        return ilan_data

    return {
        "status": "success",
        "search_result": first,
        "ilanlar": ilan_data["data"],
    }

