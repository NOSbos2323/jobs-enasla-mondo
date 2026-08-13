#!/usr/bin/env python3
"""Generate sitemap.xml with job-{id} slug pattern"""
from datetime import datetime
import os

BASE_URL = "https://jobs-enasla-mondo.vercel.app"
TODAY = datetime.now().strftime("%Y-%m-%d")

STATIC_PAGES = [
    ("/", "1.0", "daily"),
    ("/jobs", "0.9", "hourly"),
    ("/categories", "0.8", "weekly"),
    ("/countries", "0.8", "weekly"),
    ("/articles", "0.8", "weekly"),
    ("/faq", "0.6", "monthly"),
    ("/about", "0.5", "monthly"),
]

CATEGORIES = ["programming","engineering","marketing","design","finance","sales","healthcare","education","administration","customer-service","trades","construction","automotive","beauty","food-service","security","logistics"]
COUNTRIES = ["algeria","uae","saudi-arabia","qatar","kuwait","oman","bahrain","egypt","morocco","tunisia","jordan","lebanon","iraq","sudan","libya","palestine","yemen","syria"]
CITIES = ["algiers","oran","constantine","annaba","dubai","abu-dhabi","sharjah","riyadh","jeddah","dammam","mecca","medina","doha","kuwait-city","muscat","salalah","manama","cairo","alexandria","giza","casablanca","rabat","marrakech","tunis","sfax","amman","beirut","baghdad","basra","khartoum","tripoli","gaza","ramallah","sanaa","aden","damascus","aleppo"]
ARTICLES = ["how-to-write-cv","cover-letter","best-job-search-websites","interview-preparation","jobs-without-experience","jobs-algeria","jobs-uae","jobs-saudi-arabia"]
JOB_IDS = list(range(1, 102))

def generate():
    urls = []
    for path, prio, freq in STATIC_PAGES:
        urls.append(f'  <url>\n    <loc>{BASE_URL}{path}</loc>\n    <lastmod>{TODAY}</lastmod>\n    <changefreq>{freq}</changefreq>\n    <priority>{prio}</priority>\n  </url>')
    for c in CATEGORIES:
        urls.append(f'  <url>\n    <loc>{BASE_URL}/jobs/{c}</loc>\n    <lastmod>{TODAY}</lastmod>\n    <changefreq>daily</changefreq>\n    <priority>0.8</priority>\n  </url>')
    for c in COUNTRIES:
        urls.append(f'  <url>\n    <loc>{BASE_URL}/jobs/{c}</loc>\n    <lastmod>{TODAY}</lastmod>\n    <changefreq>daily</changefreq>\n    <priority>0.8</priority>\n  </url>')
    for c in CITIES:
        urls.append(f'  <url>\n    <loc>{BASE_URL}/jobs/{c}</loc>\n    <lastmod>{TODAY}</lastmod>\n    <changefreq>daily</changefreq>\n    <priority>0.7</priority>\n  </url>')
    for a in ARTICLES:
        urls.append(f'  <url>\n    <loc>{BASE_URL}/articles/{a}</loc>\n    <lastmod>{TODAY}</lastmod>\n    <changefreq>monthly</changefreq>\n    <priority>0.7</priority>\n  </url>')
    for jid in JOB_IDS:
        urls.append(f'  <url>\n    <loc>{BASE_URL}/jobs/job-{jid}</loc>\n    <lastmod>{TODAY}</lastmod>\n    <changefreq>weekly</changefreq>\n    <priority>0.9</priority>\n  </url>')
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{chr(10).join(urls)}\n</urlset>\n'

if __name__ == "__main__":
    xml = generate()
    out = "/home/z/my-project/jobs-enasla-mondo/dist/sitemap.xml"
    with open(out, "w", encoding="utf-8") as f:
        f.write(xml)
    # Also copy to root
    with open("/home/z/my-project/jobs-enasla-mondo/sitemap.xml", "w", encoding="utf-8") as f:
        f.write(xml)
    print(f"✓ Sitemap: {xml.count('<url>')} URLs")
