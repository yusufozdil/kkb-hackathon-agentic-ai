import feedparser
from datetime import datetime
import json

def google_news_search(query, start_date=None, end_date=None):
    # Build Google query with date operators
    q = query.replace(" ", "+")
    google_query = q

    if start_date:
        google_query += f"+after:{start_date.strftime('%Y-%m-%d')}"
    if end_date:
        google_query += f"+before:{end_date.strftime('%Y-%m-%d')}"

    url = f"https://news.google.com/rss/search?q={google_query}&hl=en&gl=US&ceid=US:en"

    feed = feedparser.parse(url)
    results = []

    for entry in feed.entries:
        try:
            pub_date = datetime(*entry.published_parsed[:6])
        except:
            continue

        # safety filtering
        if start_date and pub_date < start_date:
            continue
        if end_date and pub_date > end_date:
            continue

        results.append({
            "title": entry.title,
            "link": entry.link,
            "published": pub_date.isoformat()
        })

    return results


# Example usage
start = datetime(2025, 12, 1)
end = datetime(2025, 12, 10)

news = google_news_search("ASELSAN", start_date=start, end_date=end)

with open("news_result.json", "w", encoding="utf-8") as f:
    json.dump(news, f, indent=4, ensure_ascii=False)

print(f"Saved {len(news)} items to news_result.json")
