import sys
import os
import json
from typing import Any
from crewai.tools import tool

# Add parent directory to path to import tool_banned_check and services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from tool_banned_check import check_banned_status
except Exception as e:  # ImportError or runtime errors
    print(f"[WARN] tool_banned_check import failed: {e}")
    check_banned_status = None

try:
    from news_service import fetch_news_tr
except Exception as e:
    print(f"[WARN] news_service import failed: {e}")
    fetch_news_tr = None

try:
    from tobb_service import fetch_trade_registry
except Exception as e:
    print(f"[WARN] tobb_service import failed: {e}")
    fetch_trade_registry = None

try:
    from ihale_service import fetch_ihale_data
except Exception as e:
    print(f"[WARN] ihale_service import failed: {e}")
    fetch_ihale_data = None

try:
    from ilan_gov_service import fetch_ilan_gov_announcements
except Exception as e:
    print(f"[WARN] ilan_gov_service import failed: {e}")
    fetch_ilan_gov_announcements = None


def _coerce_str(val: Any) -> str:
    if isinstance(val, dict):
        # LLM sometimes sends schema dict like {"description": "...", "type": "..."}
        if "description" in val and "type" in val:
            # This is a schema, try to extract actual value
            desc = val.get("description")
            if desc and desc != "None" and not desc.startswith("{"):
                return str(desc)
            return ""
        elif "value" in val:
            val = val.get("value")
        else:
            val = ""
    if val is None:
        return ""
    return str(val)


def _coerce_bool(val: Any) -> bool:
    if isinstance(val, dict):
        val = val.get("value") if "value" in val else ""
    if isinstance(val, str):
        low = val.strip().lower()
        if low in ["true", "1", "yes", "y"]:
            return True
        if low in ["false", "0", "no", "n"]:
            return False
    return bool(val)


def _coerce_int(val: Any) -> int:
    if isinstance(val, dict):
        # LLM schema dict fix
        if "description" in val and "type" in val:
            desc = val.get("description")
            try:
                return int(desc) if desc and desc != "None" else 50
            except:
                return 50
        val = val.get("value") if "value" in val else 0
    try:
        return int(val)
    except Exception:
        return 0


def _validate_dates(start_date: str, end_date: str):
    def _norm(d):
        return "".join([c for c in d if c.isdigit()])
    s = _norm(start_date)
    e = _norm(end_date)
    if len(s) != 8 or len(e) != 8:
        raise ValueError("Dates must be YYYYMMDD or YYYY-MM-DD.")
    return s, e


class OrchestratorTools:

    @tool("Check Banned Status")
    def check_banned_tool(company_name: Any, start_date: Any, end_date: Any, force_scan: Any = False):
        """
        Checks Official Gazette bans via DB-first workflow.
        Inputs:
            - company_name (str)
            - start_date (YYYYMMDD)
            - end_date   (YYYYMMDD)
            - force_scan (bool) optional: ignore cache/DB and rescan PDFs.
        Returns: {"found": bool, "count": int, "records": [...]}
        """
        if check_banned_status:
            try:
                company = _coerce_str(company_name)
                s, e = _validate_dates(_coerce_str(start_date), _coerce_str(end_date))
                force = _coerce_bool(force_scan)
                return check_banned_status(
                    company_name=company,
                    start_date=s,
                    end_date=e,
                    force_scan=force,
                )
            except Exception as exc:
                return {"error": f"check_banned_tool validation failed: {exc}"}
        return {"error": "real tool not found, check python path."}

    @tool("Fetch Trade Registry")
    def fetch_trade_registry_tool(company_name: Any, start_date: Any, end_date: Any):
        """
        Fetches company details from Trade Registry (TOBB) with OCR.
        NOTE: This tool is OPTIONAL. If it fails (Login Failed), continue with other sources.
        """
        if fetch_trade_registry:
            try:
                company = _coerce_str(company_name)
                s, e = _validate_dates(_coerce_str(start_date), _coerce_str(end_date))
                result = fetch_trade_registry(company, s, e)
                # Check if login failed
                if isinstance(result, dict) and result.get("status") == "Login Failed":
                    return {
                        "status": "Trade Registry Unavailable",
                        "message": "TOBB login failed (CAPTCHA issue). This is expected and not a risk factor.",
                        "data": []
                    }
                return result
            except Exception as exc:
                return {
                    "status": "Trade Registry Unavailable",
                    "message": f"TOBB service error: {exc}. This is a technical issue, not a risk factor.",
                    "data": []
                }
        return {"error": "tobb_service not found"}

    @tool("Fetch News")
    def fetch_news_tool(company_name: Any, start_date: Any, end_date: Any, limit: Any = 100):
        """
        Fetches Turkish news within date range using Google News RSS.
        Returns list of {title, link, published, source, language}.
        """
        if fetch_news_tr:
            try:
                company = _coerce_str(company_name)
                s, e = _validate_dates(_coerce_str(start_date), _coerce_str(end_date))
                lim = _coerce_int(limit)
                items = fetch_news_tr(company, s, e, limit=lim)
                return {
                    "count": len(items),
                    "items": items,
                    "start_date": s,
                    "end_date": e,
                }
            except Exception as e:
                return {"error": f"news_service failed: {e}", "start_date": start_date, "end_date": end_date}
        return {"error": "news_service not found"}

    @tool("Fetch Tender Data")
    def fetch_ihale_tool(company_name: Any):
        """
        Fetches company tender/contract history from ihaleciler.com
        NOTE: This tool is OPTIONAL and may take 15-30 seconds. If it fails or times out, continue with other sources.
        Returns: {"status": str, "data": {...}, "message": str}
        """
        if fetch_ihale_data:
            try:
                company = _coerce_str(company_name)
                result = fetch_ihale_data(company, timeout=20000)  # 20 second timeout
                return result
            except Exception as exc:
                return {
                    "status": "error",
                    "data": None,
                    "message": f"Tender data fetch failed: {exc}. This is a technical issue, not a risk factor."
                }
        return {"status": "not_available", "data": None, "message": "ihale_service not found"}

    @tool("Fetch Public Announcements")
    def fetch_ilan_gov_tool(company_name: Any, start_date: Any, end_date: Any, max_results: Any = 20):
        """
        Fetches public announcements (court notices, bankruptcy, liquidation) from ilan.gov.tr
        NOTE: This tool is OPTIONAL. If it fails or times out, continue with other sources.
        Returns: {"status": str, "count": int, "announcements": [...]}
        """
        if fetch_ilan_gov_announcements:
            try:
                company = _coerce_str(company_name)
                s, e = _validate_dates(_coerce_str(start_date), _coerce_str(end_date))
                limit = _coerce_int(max_results)
                if limit <= 0:
                    limit = 20
                return fetch_ilan_gov_announcements(company, s, e, max_results=limit)
            except Exception as exc:
                return {
                    "status": "error",
                    "company": str(company_name),
                    "count": 0,
                    "announcements": [],
                    "message": f"Public announcements fetch failed: {exc}. This is a technical issue, not a risk factor."
                }
        return {
            "status": "not_available",
            "company": str(company_name),
            "count": 0,
            "announcements": [],
            "message": "ilan_gov_service not found"
        }
