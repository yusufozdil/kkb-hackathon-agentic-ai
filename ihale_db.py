import os
import sqlite3
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "ihale_yasakli.db")


# ------------- Helpers -------------
def normalize_tr(text: str) -> str:
    if not text:
        return ""
    map_chars = {
        "İ": "I", "ı": "i", "Ş": "S", "ş": "s", "Ğ": "G", "ğ": "g",
        "Ü": "U", "ü": "u", "Ö": "O", "ö": "o", "Ç": "C", "ç": "c", "Â": "A"
    }
    t = text.upper().strip()
    for k, v in map_chars.items():
        t = t.replace(k, v)
    return t


def ensure_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS bans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name_raw TEXT,
            company_name_norm TEXT,
            mersis_no TEXT,
            vkn TEXT,
            ban_start_date TEXT,
            ban_end_date TEXT,
            gazete_tarihi TEXT,
            yasak_kayit_no TEXT,
            ikn TEXT,
            bakanlik TEXT,
            yasak_suresi TEXT,
            idare_unvan TEXT,
            idare_adres TEXT,
            vergi_no TEXT,
            tc_no TEXT,
            firma_adres TEXT,
            ortaklar_json TEXT,
            kaynak_pdf TEXT,
            page_no INTEGER,
            raw_json TEXT,
            hash TEXT UNIQUE,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cur.execute("CREATE INDEX IF NOT EXISTS idx_bans_name ON bans(company_name_norm)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_bans_dates ON bans(gazete_tarihi, ban_start_date)")
    conn.commit()
    conn.close()


def connect():
    ensure_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def make_hash(
    company_name_norm: str,
    gazete_tarihi: str,
    yasak_kayit_no: Optional[str],
    ikn: Optional[str],
    bakanlik: Optional[str],
) -> str:
    base = "|".join([
        company_name_norm or "",
        gazete_tarihi or "",
        yasak_kayit_no or "",
        ikn or "",
        bakanlik or "",
    ])
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


# ------------- Write -------------
def upsert_ban(record: Dict[str, Any]) -> Tuple[bool, Optional[int]]:
    """
    Inserts or updates a ban record. Returns (inserted, rowid).
    """
    conn = connect()
    cur = conn.cursor()

    company_name_norm = normalize_tr(record.get("company_name_raw") or record.get("company_name_norm"))
    gazete_tarihi = record.get("gazete_tarihi") or record.get("ban_start_date")
    yasak_kayit_no = record.get("yasak_kayit_no")
    ikn = record.get("ikn")
    bakanlik = record.get("bakanlik")

    rec_hash = record.get("hash") or make_hash(company_name_norm, gazete_tarihi, yasak_kayit_no, ikn, bakanlik)

    payload = {
        "company_name_raw": record.get("company_name_raw"),
        "company_name_norm": company_name_norm,
        "mersis_no": record.get("mersis_no"),
        "vkn": record.get("vkn"),
        "ban_start_date": record.get("ban_start_date"),
        "ban_end_date": record.get("ban_end_date"),
        "gazete_tarihi": gazete_tarihi,
        "yasak_kayit_no": yasak_kayit_no,
        "ikn": ikn,
        "bakanlik": bakanlik,
        "yasak_suresi": record.get("yasak_suresi"),
        "idare_unvan": record.get("idare_unvan"),
        "idare_adres": record.get("idare_adres"),
        "vergi_no": record.get("vergi_no"),
        "tc_no": record.get("tc_no"),
        "firma_adres": record.get("firma_adres"),
        "ortaklar_json": json.dumps(record.get("ortaklar") or [], ensure_ascii=False),
        "kaynak_pdf": record.get("kaynak_pdf"),
        "page_no": record.get("page_no"),
        "raw_json": json.dumps(record.get("raw") or {}, ensure_ascii=False),
        "hash": rec_hash,
    }

    placeholders = ", ".join([f":{k}" for k in payload.keys()])
    columns = ", ".join(payload.keys())
    update_assign = ", ".join([f"{k}=excluded.{k}" for k in payload.keys() if k != "hash"])

    cur.execute(
        f"""
        INSERT INTO bans ({columns})
        VALUES ({placeholders})
        ON CONFLICT(hash) DO UPDATE SET
            {update_assign},
            updated_at = CURRENT_TIMESTAMP
        """,
        payload,
    )
    conn.commit()
    rowid = cur.lastrowid
    inserted = cur.rowcount == 1
    conn.close()
    return inserted, rowid


def bulk_upsert(records: List[Dict[str, Any]]) -> int:
    count = 0
    for rec in records:
        inserted, _ = upsert_ban(rec)
        if inserted:
            count += 1
    return count


# ------------- Read -------------
def _date_in_range(value: Optional[str], start: str, end: str) -> bool:
    if not value:
        return False
    return start <= value <= end


def query_bans(company_name: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """
    Looks up bans by normalized company name within date range (inclusive).
    Uses gazete_tarihi as primary date filter; falls back to ban_start_date.
    """
    conn = connect()
    cur = conn.cursor()
    norm = f"%{normalize_tr(company_name)}%"
    cur.execute(
        """
        SELECT * FROM bans
        WHERE company_name_norm LIKE ?
          AND (
                (gazete_tarihi IS NOT NULL AND gazete_tarihi BETWEEN ? AND ?)
             OR (ban_start_date IS NOT NULL AND ban_start_date BETWEEN ? AND ?)
          )
        ORDER BY gazete_tarihi DESC
        """,
        (norm, start_date, end_date, start_date, end_date),
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_latest_date() -> Optional[str]:
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT MAX(gazete_tarihi) FROM bans")
    row = cur.fetchone()
    conn.close()
    return row[0] if row and row[0] else None


# ------------- Utils -------------
def parse_entry_to_record(entry: Dict[str, Any], date_str: str, pdf_url: Optional[str], page_no: int) -> Dict[str, Any]:
    yasakli = entry.get("Yasakli_Firma") or {}
    global_info = entry.get("Global_Info") or {}
    idare = entry.get("Idare") or {}
    ortaklar = entry.get("Ortaklar") or []

    return {
        "company_name_raw": yasakli.get("Unvan"),
        "company_name_norm": normalize_tr(yasakli.get("Unvan")),
        "vergi_no": yasakli.get("Vergi_No"),
        "tc_no": yasakli.get("TC_No"),
        "firma_adres": yasakli.get("Adres"),
        "ban_start_date": date_str,
        "ban_end_date": None,
        "gazete_tarihi": date_str,
        "yasak_kayit_no": global_info.get("Yasak_Kayit_No"),
        "ikn": global_info.get("IKN"),
        "bakanlik": global_info.get("Bakanlik"),
        "yasak_suresi": global_info.get("Yasak_Suresi") or "1 Yıl",
        "idare_unvan": idare.get("Unvan"),
        "idare_adres": idare.get("Adres"),
        "ortaklar": ortaklar,
        "kaynak_pdf": pdf_url,
        "page_no": page_no,
        "raw": entry,
    }


def format_query_response(rows: List[Dict[str, Any]], start_date: str = None, end_date: str = None) -> Dict[str, Any]:
    # Fix null yasak_suresi for existing records
    processed_rows = []
    for r in rows:
        row_dict = dict(r)
        if not row_dict.get("yasak_suresi"):
            row_dict["yasak_suresi"] = "1 Yıl"
        processed_rows.append(row_dict)

    result = {
        "found": len(processed_rows) > 0,
        "count": len(processed_rows),
        "records": processed_rows,
    }
    if start_date and end_date:
        result["date_range_checked"] = f"{start_date} to {end_date}"
    return result


if __name__ == "__main__":
    ensure_db()
    print(f"DB initialized at {DB_PATH}")

