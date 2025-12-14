"""
ilan.gov.tr Public Announcement Scraper
Fetches and analyzes public announcements about companies
Uses direct API calls for better performance and reliability
"""
import requests
import warnings
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

# Suppress SSL warnings
warnings.filterwarnings('ignore', message='Unverified HTTPS request')


class IlanGovScraper:
    BASE_URL = "https://www.ilan.gov.tr"
    API_URL = BASE_URL + "/api/api/services/app/Ad/AdsByFilter"
    
    def __init__(self, timeout: int = 30):  # seconds for requests
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "text/plain",
            "Content-Type": "application/json-patch+json",
            "X-Requested-With": "XMLHttpRequest",
            "X-Request-Origin": "IGT-UI",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.ilan.gov.tr/ilan/tum-ilanlar"
        })
    
    def search_announcements(
        self,
        company_name: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        max_results: int = 20
    ) -> Dict[str, Any]:
        """
        Search ilan.gov.tr for company announcements using direct API calls
        
        Args:
            company_name: Company name to search
            start_date: Start date (YYYYMMDD format)
            end_date: End date (YYYYMMDD format)
            max_results: Maximum number of results to fetch (default 20)
        
        Returns:
            {
                "status": "success" | "error" | "not_found",
                "company": str,
                "count": int,
                "announcements": [...]
            }
        """
        try:
            # Parse dates and format as DD.MM.YYYY
            if start_date:
                start_dt = datetime.strptime(start_date, "%Y%m%d")
                start_fmt = start_dt.strftime("%d.%m.%Y")
            else:
                start_dt = datetime(2020, 1, 1)
                start_fmt = "01.01.2020"
            
            if end_date:
                end_dt = datetime.strptime(end_date, "%Y%m%d")
                end_fmt = end_dt.strftime("%d.%m.%Y")
            else:
                end_dt = datetime.now()
                end_fmt = end_dt.strftime("%d.%m.%Y")
            
            # Build API request payload - CORRECT FORMAT with 'keys' object
            payload = {
                "keys": {
                    "q": [company_name],
                    "ppdmin": [start_fmt],
                    "ppdmax": [end_fmt]
                },
                "skipCount": 0,
                "maxResultCount": max_results
            }
            
            print(f"[ILAN.GOV.TR] Searching API for: {company_name}")
            print(f"[ILAN.GOV.TR] Date range: {start_fmt} to {end_fmt}")
            
            # Make API request
            response = self.session.post(
                self.API_URL,
                json=payload,
                timeout=self.timeout,
                verify=False
            )
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            
            if not data or 'result' not in data:
                return {
                    "status": "error",
                    "company": company_name,
                    "count": 0,
                    "announcements": [],
                    "message": "Invalid API response format"
                }
            
            result = data['result']
            ads = result.get('ads', [])
            
            if not ads:
                print(f"[ILAN.GOV.TR] ⚠️ No announcements found")
                return {
                    "status": "not_found",
                    "company": company_name,
                    "count": 0,
                    "announcements": [],
                    "message": f"No announcements found for '{company_name}' in the specified date range"
                }
            
            print(f"[ILAN.GOV.TR] ✅ Found {len(ads)} announcements")
            
            # Parse announcements
            announcements = []
            for ad in ads:
                try:
                    # Extract announcement type from filters
                    announcement_type = "Genel İlan"
                    for filter_item in ad.get('adTypeFilters', []):
                        if filter_item.get('key') == 'İlan Türü':
                            announcement_type = filter_item.get('value', announcement_type)
                            break
                    
                    # Build announcement URL
                    url = self.BASE_URL + ad.get('urlStr', '')
                    if not url.startswith('http'):
                        url = self.BASE_URL + '/' + url.lstrip('/')
                    
                    announcement = {
                        "title": ad.get('title', 'N/A'),
                        "link": url,
                        "publish_date": ad.get('publishStartDate', 'N/A'),
                        "summary": ad.get('title', '')[:300],
                        "full_text": "",  # Not fetching detail for performance
                        "announcement_type": announcement_type,
                        "institution": ad.get('advertiserName', 'N/A'),
                        "ad_no": ad.get('adNo', 'N/A'),
                        "location": f"{ad.get('addressCityName', '')} {ad.get('addressCountyName', '')}".strip(),
                    }
                    
                    announcements.append(announcement)
                
                except Exception as e:
                    print(f"[ILAN.GOV.TR] Error parsing announcement: {e}")
                    continue
            
            return {
                "status": "success",
                "company": company_name,
                "count": len(announcements),
                "announcements": announcements,
                "date_range": f"{start_date} to {end_date}"
            }
        
        except requests.RequestException as e:
            print(f"[ILAN.GOV.TR] API request error: {e}")
            return {
                "status": "error",
                "company": company_name,
                "count": 0,
                "announcements": [],
                "message": f"API request failed: {str(e)}"
            }
        except Exception as e:
            print(f"[ILAN.GOV.TR] Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "company": company_name,
                "count": 0,
                "announcements": [],
                "message": f"Error: {str(e)}"
            }


def fetch_ilan_gov_announcements(
    company_name: str,
    start_date: str,
    end_date: str,
    max_results: int = 20
) -> Dict[str, Any]:
    """
    High-level wrapper for ilan.gov.tr scraping
    
    Args:
        company_name: Company name to search
        start_date: Start date (YYYYMMDD)
        end_date: End date (YYYYMMDD)
        max_results: Maximum results to return (default 20)
    
    Returns:
        {
            "status": "success" | "error" | "not_found",
            "company": str,
            "count": int,
            "announcements": [...],
            "date_range": str
        }
    """
    scraper = IlanGovScraper()
    result = scraper.search_announcements(
        company_name=company_name,
        start_date=start_date,
        end_date=end_date,
        max_results=max_results
    )
    
    return result


if __name__ == "__main__":
    # Test
    print("Testing ilan.gov.tr API scraper...")
    
    result = fetch_ilan_gov_announcements(
        company_name="ARMİ AMBALAJ",
        start_date="20240207",
        end_date="20251213",
        max_results=10
    )
    
    print("\n" + "="*60)
    print(f"Status: {result['status']}")
    print(f"Company: {result['company']}")
    print(f"Count: {result['count']}")
    
    if result['announcements']:
        print(f"\nFirst 3 Announcements:")
        for i, ann in enumerate(result['announcements'][:3], 1):
            print(f"\n{i}. {ann['title']}")
            print(f"   Date: {ann['publish_date']}")
            print(f"   Type: {ann.get('announcement_type', 'N/A')}")
            print(f"   Institution: {ann.get('institution', 'N/A')}")
            print(f"   Location: {ann.get('location', 'N/A')}")
            print(f"   Link: {ann['link']}")
            print(f"   Summary: {ann.get('summary', '')[:100]}...")
