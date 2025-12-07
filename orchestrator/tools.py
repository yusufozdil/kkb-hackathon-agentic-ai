import sys
import os
import json
from crewai.tools import tool

# Add parent directory to path to import tool_banned_check
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from tool_banned_check import check_banned_status
except ImportError:
    check_banned_status = None

class OrchestratorTools:
    
    @tool("Check Banned Status")
    def check_banned_tool(date_str: str, company_name: str = None):
        """
        Checks the Official Gazette for banned company decisions on a specific date.
        Input: 
            - date_str: Date string like '20251129'.
            - company_name: (Optional) Company name to filter by. significantly speeds up the search.
        Returns: List of found banned records.
        """
        if check_banned_status:
            return check_banned_status(date_str, company_name)
        else:
            return "Error: real tool not found, check python path."

    @tool("Fetch Trade Registry")
    def fetch_trade_registry_tool(company_name: str):
        """
        Fetches company details from Trade Registry.
        Input: Company Name.
        Returns: Mocked trade registry data.
        """
        return {
            "found": True,
            "company_name": company_name,
            "capital": "100.000 TL",
            "managers": ["Ahmet Yılmaz"],
            "address": "Organize Sanayi Bölgesi, Ankara",
            "raw_text_summary": f"Ticaret Sicil Gazetesi kayıtlarına göre {company_name} firması faal durumdadır."
        }

    @tool("Fetch News")
    def fetch_news_tool(company_name: str):
        """
        Fetches news and sentiment analysis for a company.
        Input: Company Name.
        Returns: Mocked news data.
        """
        return {
            "positive_count": 2,
            "negative_count": 1,
            "summary": f"{company_name} hakkında genel olarak olumlu haberler mevcuttur. Yeni yatırımlar gündemde.",
            "headlines": [
                "Büyük Yatırım Kararı",
                "Hisse Değerleri Arttı",
                "Küçük Çaplı İş Kazası"
            ]
        }
