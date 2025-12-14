"""
İhale Data Service - ihaleciler.com integration
"""
from typing import Dict, Any
import sys
import os

# Add TOBB directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "TOBB"))

try:
    from TOBB.IhaleScraper import IhaleScraper
    IHALE_SCRAPER_AVAILABLE = True
except ImportError as e:
    print(f"[WARN] IhaleScraper import failed: {e}")
    IHALE_SCRAPER_AVAILABLE = False


def fetch_ihale_data(company_name: str, timeout: int = 15000) -> Dict[str, Any]:
    """
    Fetch tender/contract data from ihaleciler.com
    
    Args:
        company_name: Company name to search
        timeout: Playwright timeout in milliseconds (default 15 seconds)
    
    Returns:
        {
            "status": "success" | "error" | "not_available",
            "data": {...} or None,
            "message": str
        }
    """
    if not IHALE_SCRAPER_AVAILABLE:
        return {
            "status": "not_available",
            "data": None,
            "message": "IhaleScraper module not available. Install playwright: pip install playwright && playwright install chromium"
        }
    
    try:
        print(f"[IHALE] Fetching tender data for: {company_name}")
        scraper = IhaleScraper(company_name, headless=True, timeout=timeout)
        
        # Scrape HTML content
        scraper.scrape()
        
        # Parse and structure data
        result = scraper.process_html()
        
        # Check if any meaningful data was found
        summary = result.get("Summary_Analysis", {})
        yearly_stats = result.get("Yearly_Stats", [])
        
        if not summary and not yearly_stats:
            return {
                "status": "not_found",
                "data": None,
                "message": f"No tender records found for '{company_name}' on ihaleciler.com"
            }
        
        print(f"[IHALE] ✅ Found data: {len(yearly_stats)} yearly records")
        return {
            "status": "success",
            "data": result,
            "message": "Tender data successfully retrieved"
        }
    
    except Exception as e:
        print(f"[IHALE] ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "data": None,
            "message": f"Failed to fetch tender data: {str(e)}"
        }


if __name__ == "__main__":
    # Test
    result = fetch_ihale_data("TURKCELL")
    print("\n" + "="*60)
    print("IHALE DATA RESULT")
    print("="*60)
    print(f"Status: {result['status']}")
    print(f"Message: {result['message']}")
    
    if result['data']:
        data = result['data']
        print(f"\nSummary Keys: {list(data.get('Summary_Analysis', {}).keys())}")
        print(f"Yearly Stats: {len(data.get('Yearly_Stats', []))} records")
        print(f"Sectors: {len(data.get('Sectors_CPV', []))} records")
        print(f"Provinces: {len(data.get('Provinces', []))} records")

