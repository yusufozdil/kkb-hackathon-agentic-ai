"""
Intercept real API call from browser to see exact request/response
"""
from playwright.sync_api import sync_playwright
import json
import time

def intercept_api_call():
    """Capture real API call with all headers and cookies"""
    
    captured_requests = []
    captured_responses = []
    
    def handle_request(request):
        if 'AdsByFilter' in request.url:
            print(f"\n🔵 REQUEST INTERCEPTED:")
            print(f"URL: {request.url}")
            print(f"Method: {request.method}")
            print(f"\nHeaders:")
            for key, value in request.headers.items():
                print(f"  {key}: {value}")
            
            if request.post_data:
                print(f"\nPost Data:")
                try:
                    data = json.loads(request.post_data)
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                except:
                    print(request.post_data[:500])
            
            captured_requests.append({
                'url': request.url,
                'method': request.method,
                'headers': dict(request.headers),
                'post_data': request.post_data
            })
    
    def handle_response(response):
        if 'AdsByFilter' in response.url:
            print(f"\n🟢 RESPONSE INTERCEPTED:")
            print(f"Status: {response.status}")
            print(f"URL: {response.url}")
            
            try:
                body = response.body()
                data = json.loads(body)
                result = data.get('result', {})
                ads = result.get('ads', [])
                
                print(f"\nTotal ads in response: {len(ads)}")
                
                # Check for konkordato
                konkordato_ads = []
                for ad in ads:
                    title_lower = ad.get('title', '').lower()
                    if 'konkordato' in title_lower or ad.get('adNo') in ['ILN02161711', 'ILN02152900']:
                        konkordato_ads.append(ad)
                
                if konkordato_ads:
                    print(f"\n🎯 FOUND {len(konkordato_ads)} KONKORDATO ADS:")
                    for ad in konkordato_ads:
                        print(f"   • {ad.get('adNo')} - {ad.get('title')[:80]}")
                        print(f"     Date: {ad.get('publishStartDate')}")
                        print(f"     Institution: {ad.get('advertiserName')}")
                else:
                    print(f"\n⚠️  No konkordato ads found. Ad numbers in response:")
                    for ad in ads[:10]:
                        print(f"   • {ad.get('adNo')} - {ad.get('publishStartDate')}")
                
                captured_responses.append(data)
                
                # Save to file
                with open('captured_api_response.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"\n💾 Full response saved to captured_api_response.json")
                
            except Exception as e:
                print(f"Error parsing response: {e}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        
        # Set up listeners
        page.on("request", handle_request)
        page.on("response", handle_response)
        
        # Navigate to search page
        url = "https://www.ilan.gov.tr/ilan/tum-ilanlar?q=ARMİ%20AMBALAJ%20SANAYİ%20VE%20TİCARET%20ANONİM%20ŞİRKETİ&ppdmin=01.01.2024&ppdmax=13.12.2025"
        print(f"Navigating to: {url}\n")
        
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        
        # Wait for API call
        print("Waiting for API calls...")
        time.sleep(10)
        
        browser.close()
    
    # Save captured request for replication
    if captured_requests:
        with open('captured_api_request.json', 'w', encoding='utf-8') as f:
            json.dump(captured_requests[0], f, indent=2, ensure_ascii=False)
        print(f"\n💾 Request details saved to captured_api_request.json")
    
    return captured_requests, captured_responses


if __name__ == "__main__":
    intercept_api_call()

