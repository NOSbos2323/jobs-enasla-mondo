#!/usr/bin/env python3
"""
JobFinder Pre-renderer
يولّد ملفات HTML ثابتة لكل وظيفة، مقالة، دولة، مدينة، تصنيف
كل ملف يحتوي:
- <title> فريد
- <meta description> فريد
- <link rel="canonical"> فريد
- Open Graph tags فريدة
- JSON-LD JobPosting/BreadcrumbList كامل في الـ HTML
- <h1> واحد فقط هو عنوان الوظيفة/المقالة
"""
import json
import re
import os
import html as html_lib
from datetime import datetime, timedelta

BASE_URL = "https://jobs-enasla-mondo.vercel.app"
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(PROJECT_DIR, "dist")
JOBS_DIR = os.path.join(DIST_DIR, "jobs")
ARTICLES_DIR = os.path.join(DIST_DIR, "articles")
CATEGORIES_DIR = os.path.join(DIST_DIR, "categories")
COUNTRIES_DIR = os.path.join(DIST_DIR, "countries")

# Create directories
for d in [DIST_DIR, JOBS_DIR, ARTICLES_DIR, CATEGORIES_DIR, COUNTRIES_DIR]:
    os.makedirs(d, exist_ok=True)

# Load data - extract from index.html at runtime
with open(os.path.join(PROJECT_DIR, 'index.html'), 'r', encoding='utf-8') as f:
    ORIGINAL_HTML = f.read()

# Extract SAMPLE_JOBS and ARTICLES from index.html using Node.js
import subprocess
def extract_js_data(var_name):
    """Extract a JS array from index.html using Node with bracket counting"""
    script = """
const fs = require('fs');
const html = fs.readFileSync(process.argv[1], 'utf8');
const varName = process.argv[2];
const startMarker = 'const ' + varName + ' = [';
const startIdx = html.indexOf(startMarker);
if (startIdx === -1) { console.error('NOT FOUND: ' + startMarker); process.exit(1); }
let i = startIdx + startMarker.length;
let depth = 1;
let safety = 0;
while (i < html.length && depth > 0 && safety < 1000000) {
  if (html[i] === '[') depth++;
  else if (html[i] === ']') depth--;
  i++;
  safety++;
}
if (depth !== 0) { console.error('UNBALANCED BRACKERS for ' + varName); process.exit(1); }
const arrStr = html.substring(startIdx + startMarker.length, i - 1);
try {
  const arr = eval('[' + arrStr + ']');
  process.stdout.write(JSON.stringify(arr));
} catch(e) {
  console.error('EVAL ERROR: ' + e.message);
  process.exit(1);
}
"""
    result = subprocess.run(['node', '-e', script, '--', os.path.join(PROJECT_DIR, 'index.html'), var_name], capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        print(f"Error extracting {var_name}: {result.stderr[:500]}")
        return []
    try:
        return json.loads(result.stdout.strip())
    except json.JSONDecodeError as e:
        print(f"JSON parse error for {var_name}: {e}")
        return []

JOBS = extract_js_data('SAMPLE_JOBS')
ARTICLES = extract_js_data('ARTICLES')
print(f"Loaded {len(JOBS)} jobs and {len(ARTICLES)} articles from index.html")

# Static data (mirror of JS)
CATEGORIES = [
    {"slug": "programming", "name": "البرمجة وتطوير البرمجيات", "icon": "💻", "description": "وظائف في تطوير المواقع والتطبيقات والبرمجيات، يشمل مطوري الواجهات الأمامية والخلفية ومطوري تطبيقات الهاتف ومهندسي البيانات."},
    {"slug": "engineering", "name": "الهندسة", "icon": "⚙️", "description": "وظائف هندسية في التخصصات المدنية والميكانيكية والكهربائية والكيميائية."},
    {"slug": "marketing", "name": "التسويق", "icon": "📢", "description": "وظائف في التسويق الرقمي وإدارة المحتوى والتسويق التقليدي والعلاقات العامة."},
    {"slug": "design", "name": "التصميم", "icon": "🎨", "description": "وظائف في التصميم الجرافيكي وتصميم واجهات المستخدم وتجربة المستخدم."},
    {"slug": "finance", "name": "المالية والمحاسبة", "icon": "💰", "description": "وظائف في المحاسبة والمراجعة والتحليل المالي والخزينة والاستثمار."},
    {"slug": "sales", "name": "المبيعات", "icon": "📈", "description": "وظائف في المبيعات الميدانية والتسويق الميداني وإدارة الحسابات."},
    {"slug": "healthcare", "name": "الصحة", "icon": "🏥", "description": "وظائف في القطاع الصحي تشمل الأطباء والممرضين والصيادلة والفنيين الطبيين."},
    {"slug": "education", "name": "التعليم", "icon": "📚", "description": "وظائف في التدريس والإشراف التربوي وتطوير المناهج."},
    {"slug": "administration", "name": "الإدارة", "icon": "📋", "description": "وظائف إدارية في إدارة المشاريع والموارد البشرية."},
    {"slug": "customer-service", "name": "خدمة العملاء", "icon": "🎧", "description": "وظائف في خدمة العملاء والدعم الفني ومراكز الاتصال."},
    {"slug": "trades", "name": "الحرف والصناعات اليدوية", "icon": "🔨", "description": "وظائف حرفية يدوية تشمل النجارة والسباكة والكهرباء والحدادة واللحام والدهان والبلاط والخياطة."},
    {"slug": "construction", "name": "البناء والإنشاءات", "icon": "🏗️", "description": "وظائف في قطاع البناء والإنشاءات."},
    {"slug": "automotive", "name": "المركبات والمحركات", "icon": "🚗", "description": "وظائف في صيانة وإصلاح السيارات والمركبات."},
    {"slug": "beauty", "name": "التجميل والعناية", "icon": "💅", "description": "وظائف في صالونات التجميل والعناية بالشعر والبشرة."},
    {"slug": "food-service", "name": "الطعام والمطاعم", "icon": "🍳", "description": "وظائف في المطاعم والمقاهي والفنادق."},
    {"slug": "security", "name": "الأمن والحراسة", "icon": "🛡️", "description": "وظائف في الأمن والحراسة وحماية المنشآت."},
    {"slug": "logistics", "name": "اللوجستيات والتخزين", "icon": "📦", "description": "وظائف في النقل والتخزين وسلاسل الإمداد."},
]

COUNTRIES = [
    {"slug": "algeria", "name": "الجزائر", "flag": "🇩🇿", "currency": "د.ج", "description": "وظائف في الجزائر بمختلف المجالات في القطاعين العام والخاص."},
    {"slug": "uae", "name": "الإمارات", "flag": "🇦🇪", "currency": "د.إ", "description": "وظائف في الإمارات العربية المتحدة في دبي وأبوظبي والشارقة."},
    {"slug": "saudi-arabia", "name": "السعودية", "flag": "🇸🇦", "currency": "ر.س", "description": "وظائف في المملكة العربية السعودية في الرياض وجدة والدمام."},
    {"slug": "qatar", "name": "قطر", "flag": "🇶🇦", "currency": "ر.ق", "description": "وظائف في قطر في الدوحة والمدن الأخرى."},
    {"slug": "kuwait", "name": "الكويت", "flag": "🇰🇼", "currency": "د.ك", "description": "وظائف في دولة الكويت في قطاعات النفط والخدمات."},
    {"slug": "oman", "name": "عُمان", "flag": "🇴🇲", "currency": "ر.ع", "description": "وظائف في سلطنة عُمان في مسقط وصلالة."},
    {"slug": "bahrain", "name": "البحرين", "flag": "🇧🇭", "currency": "د.ب", "description": "وظائف في مملكة البحرين في المنامة."},
    {"slug": "egypt", "name": "مصر", "flag": "🇪🇬", "currency": "ج.م", "description": "وظائف في مصر في القاهرة والإسكندرية والجيزة."},
    {"slug": "morocco", "name": "المغرب", "flag": "🇲🇦", "currency": "د.م", "description": "وظائف في المملكة المغربية في الدار البيضاء والرباط ومراكش."},
    {"slug": "tunisia", "name": "تونس", "flag": "🇹🇳", "currency": "د.ت", "description": "وظائف في تونس في تونس العاصمة وصفاقس."},
    {"slug": "jordan", "name": "الأردن", "flag": "🇯🇴", "currency": "د.أ", "description": "وظائف في المملكة الأردنية الهاشمية في عمّان."},
    {"slug": "lebanon", "name": "لبنان", "flag": "🇱🇧", "currency": "ل.ل", "description": "وظائف في لبنان في بيروت."},
    {"slug": "iraq", "name": "العراق", "flag": "🇮🇶", "currency": "د.ع", "description": "وظائف في العراق في بغداد والبصرة."},
    {"slug": "sudan", "name": "السودان", "flag": "🇸🇩", "currency": "ج.س", "description": "وظائف في السودان في الخرطوم."},
    {"slug": "libya", "name": "ليبيا", "flag": "🇱🇾", "currency": "د.ل", "description": "وظائف في ليبيا في طرابلس."},
    {"slug": "palestine", "name": "فلسطين", "flag": "🇵🇸", "currency": "ش.ج", "description": "وظائف في فلسطين في غزة ورام الله."},
    {"slug": "yemen", "name": "اليمن", "flag": "🇾🇪", "currency": "ر.ي", "description": "وظائف في اليمن في صنعاء وعدن."},
    {"slug": "syria", "name": "سوريا", "flag": "🇸🇾", "currency": "ل.س", "description": "وظائف في سوريا في دمشق وحلب."},
]

CITIES = [
    {"slug": "algiers", "name": "الجزائر العاصمة", "country": "algeria", "countryName": "الجزائر"},
    {"slug": "oran", "name": "وهران", "country": "algeria", "countryName": "الجزائر"},
    {"slug": "constantine", "name": "قسنطينة", "country": "algeria", "countryName": "الجزائر"},
    {"slug": "annaba", "name": "عنابة", "country": "algeria", "countryName": "الجزائر"},
    {"slug": "dubai", "name": "دبي", "country": "uae", "countryName": "الإمارات"},
    {"slug": "abu-dhabi", "name": "أبوظبي", "country": "uae", "countryName": "الإمارات"},
    {"slug": "sharjah", "name": "الشارقة", "country": "uae", "countryName": "الإمارات"},
    {"slug": "riyadh", "name": "الرياض", "country": "saudi-arabia", "countryName": "السعودية"},
    {"slug": "jeddah", "name": "جدة", "country": "saudi-arabia", "countryName": "السعودية"},
    {"slug": "dammam", "name": "الدمام", "country": "saudi-arabia", "countryName": "السعودية"},
    {"slug": "mecca", "name": "مكة المكرمة", "country": "saudi-arabia", "countryName": "السعودية"},
    {"slug": "medina", "name": "المدينة المنورة", "country": "saudi-arabia", "countryName": "السعودية"},
    {"slug": "doha", "name": "الدوحة", "country": "qatar", "countryName": "قطر"},
    {"slug": "kuwait-city", "name": "مدينة الكويت", "country": "kuwait", "countryName": "الكويت"},
    {"slug": "muscat", "name": "مسقط", "country": "oman", "countryName": "عُمان"},
    {"slug": "salalah", "name": "صلالة", "country": "oman", "countryName": "عُمان"},
    {"slug": "manama", "name": "المنامة", "country": "bahrain", "countryName": "البحرين"},
    {"slug": "cairo", "name": "القاهرة", "country": "egypt", "countryName": "مصر"},
    {"slug": "alexandria", "name": "الإسكندرية", "country": "egypt", "countryName": "مصر"},
    {"slug": "giza", "name": "الجيزة", "country": "egypt", "countryName": "مصر"},
    {"slug": "casablanca", "name": "الدار البيضاء", "country": "morocco", "countryName": "المغرب"},
    {"slug": "rabat", "name": "الرباط", "country": "morocco", "countryName": "المغرب"},
    {"slug": "marrakech", "name": "مراكش", "country": "morocco", "countryName": "المغرب"},
    {"slug": "tunis", "name": "تونس العاصمة", "country": "tunisia", "countryName": "تونس"},
    {"slug": "sfax", "name": "صفاقس", "country": "tunisia", "countryName": "تونس"},
    {"slug": "amman", "name": "عمّان", "country": "jordan", "countryName": "الأردن"},
    {"slug": "beirut", "name": "بيروت", "country": "lebanon", "countryName": "لبنان"},
    {"slug": "baghdad", "name": "بغداد", "country": "iraq", "countryName": "العراق"},
    {"slug": "basra", "name": "البصرة", "country": "iraq", "countryName": "العراق"},
    {"slug": "khartoum", "name": "الخرطوم", "country": "sudan", "countryName": "السودان"},
    {"slug": "tripoli", "name": "طرابلس", "country": "libya", "countryName": "ليبيا"},
    {"slug": "gaza", "name": "غزة", "country": "palestine", "countryName": "فلسطين"},
    {"slug": "ramallah", "name": "رام الله", "country": "palestine", "countryName": "فلسطين"},
    {"slug": "sanaa", "name": "صنعاء", "country": "yemen", "countryName": "اليمن"},
    {"slug": "aden", "name": "عدن", "country": "yemen", "countryName": "اليمن"},
    {"slug": "damascus", "name": "دمشق", "country": "syria", "countryName": "سوريا"},
    {"slug": "aleppo", "name": "حلب", "country": "syria", "countryName": "سوريا"},
]

EMPLOYMENT_TYPES = {
    "full-time": "دوام كامل",
    "part-time": "دوام جزئي",
    "contract": "عقد مؤقت",
    "remote": "عن بُعد",
    "internship": "تدريب"
}

# Realistic street addresses and postal codes per city (for JobPosting schema)
CITY_ADDRESSES = {
    "algiers": {"street": "شارع ديدوش مراد", "postalCode": "16000"},
    "oran": {"street": "شارع الأمير عبد القادر", "postalCode": "31000"},
    "constantine": {"street": "شارع زرقان", "postalCode": "25000"},
    "annaba": {"street": "شارع الثورة", "postalCode": "23000"},
    "dubai": {"street": "Sheikh Zayed Road", "postalCode": "00000"},
    "abu-dhabi": {"street": "Khalifa Street", "postalCode": "00000"},
    "sharjah": {"street": "King Abdul Aziz Street", "postalCode": "00000"},
    "riyadh": {"street": "طريق الملك فهد", "postalCode": "11564"},
    "jeddah": {"street": "طريق المدينة المنورة", "postalCode": "21441"},
    "dammam": {"street": "طريق الملك خالد", "postalCode": "32241"},
    "mecca": {"street": "شارع الحرم", "postalCode": "21955"},
    "medina": {"street": "شارع الملك عبدالعزيز", "postalCode": "42311"},
    "doha": {"street": "Al Corniche Street", "postalCode": "00000"},
    "kuwait-city": {"street": "Ahmed Al Jaber Street", "postalCode": "00000"},
    "muscat": {"street": "Sultan Qaboos Street", "postalCode": "112"},
    "salalah": {"street": "Al Wadi Street", "postalCode": "211"},
    "manama": {"street": "Government Avenue", "postalCode": "00000"},
    "cairo": {"street": "شارع التحرير", "postalCode": "11511"},
    "alexandria": {"street": "طريق الجيش", "postalCode": "21599"},
    "giza": {"street": "شارع الأهرام", "postalCode": "12511"},
    "casablanca": {"street": "Boulevard Mohammed V", "postalCode": "20000"},
    "rabat": {"street": "Avenue Mohammed V", "postalCode": "10000"},
    "marrakech": {"street": "Avenue Mohammed VI", "postalCode": "40000"},
    "tunis": {"street": "Avenue Habib Bourguiba", "postalCode": "1000"},
    "sfax": {"street": "Avenue Hedi Chaker", "postalCode": "3000"},
    "amman": {"street": "شارع الملكة رانيا", "postalCode": "11195"},
    "beirut": {"street": "Rue Bliss", "postalCode": "00000"},
    "baghdad": {"street": "شارع الرشيد", "postalCode": "10001"},
    "basra": {"street": "شارع الكورنيش", "postalCode": "61001"},
    "khartoum": {"street": "شارع النيل", "postalCode": "11111"},
    "tripoli": {"street": "شارع الجمهورية", "postalCode": "00000"},
    "gaza": {"street": "شارع عمر المختار", "postalCode": "00000"},
    "ramallah": {"street": "شارع المعصرة", "postalCode": "00000"},
    "sanaa": {"street": "شارع الزبيري", "postalCode": "00000"},
    "aden": {"street": "شارع الملكة أروى", "postalCode": "00000"},
    "damascus": {"street": "شارع الثورة", "postalCode": "00000"},
    "aleppo": {"street": "شارع الفرقان", "postalCode": "00000"},
}

def get_city_address(city_slug):
    """Get realistic street address and postal code for a city"""
    return CITY_ADDRESSES.get(city_slug, {"street": "الشارع الرئيسي", "postalCode": "00000"})

def slugify(text):
    """Generate URL-safe slug"""
    # For Arabic, just use the ID-based slug
    s = str(text).strip().lower()
    s = re.sub(r'\s+', '-', s)
    s = re.sub(r'[^\w\-]', '', s, flags=re.UNICODE)
    s = re.sub(r'-+', '-', s)
    return s.strip('-')

def job_slug(job):
    # Use only ID for URL safety, title is in the page content
    return f"job-{job['id']}"

def job_dates(job):
    """Convert daysAgo to actual date"""
    now = datetime.now()
    days_ago = job.get('daysAgo', 0)
    posted = now - timedelta(days=days_ago)
    valid_days = job.get('validThroughDays', 30)
    valid_through = posted + timedelta(days=valid_days)
    return posted.strftime('%Y-%m-%d'), valid_through.strftime('%Y-%m-%d')

def escape_html(text):
    if not text:
        return ''
    return html_lib.escape(str(text), quote=True)

def escape_js_string(text):
    """Escape for JSON-LD string"""
    if not text:
        return ''
    return json.dumps(str(text), ensure_ascii=False)

def get_category(slug):
    for c in CATEGORIES:
        if c['slug'] == slug:
            return c
    return None

def get_country(slug):
    for c in COUNTRIES:
        if c['slug'] == slug:
            return c
    return None

def get_city(slug):
    for c in CITIES:
        if c['slug'] == slug:
            return c
    return None

def extract_css_and_js(html):
    """Extract the <style> and <script> blocks from original index.html"""
    # Get CSS
    css_match = re.search(r'<style>([\s\S]*?)</style>', html)
    css = css_match.group(1) if css_match else ''

    # Get the main JS (skip JSON-LD scripts)
    js_blocks = []
    for m in re.finditer(r'<script>([\s\S]*?)</script>', html):
        content = m.group(1)
        if 'jobfinder_theme' in content or 'SAMPLE_JOBS' in content or 'fetchJobs' in content:
            js_blocks.append(content)

    return css, '\n'.join(js_blocks)

CSS, MAIN_JS = extract_css_and_js(ORIGINAL_HTML)

def build_head(title, description, canonical_path, og_type='website', keywords='', extra_schema=''):
    """Build complete <head> with unique metadata"""
    full_url = BASE_URL + canonical_path
    return f'''<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<meta name="google-site-verification" content="ReJX1QBSZfBdjvyLEsZR1dvg5d9V8F-ukyMzsVqhvFo">
<meta name="theme-color" content="#2563eb" id="themeColor">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
<meta name="googlebot" content="index, follow">
<meta name="author" content="JobFinder">
<meta name="color-scheme" content="light dark">
<title>{escape_html(title)}</title>
<meta name="description" content="{escape_html(description)}">
<link rel="canonical" href="{full_url}">
{f'<meta name="keywords" content="{escape_html(keywords)}">' if keywords else ''}
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="JobFinder">
<meta property="og:title" content="{escape_html(title)}">
<meta property="og:description" content="{escape_html(description)}">
<meta property="og:url" content="{full_url}">
<meta property="og:image" content="{BASE_URL}/og-image.png">
<meta property="og:locale" content="ar_AR">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{escape_html(title)}">
<meta name="twitter:description" content="{escape_html(description)}">
<meta name="twitter:image" content="{BASE_URL}/og-image.png">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' rx='20' fill='%232563eb'/><text y='70' x='50' font-size='60' text-anchor='middle' fill='white' font-family='Arial' font-weight='bold'>J</text></svg>">
<link rel="sitemap" type="application/xml" href="/sitemap.xml">
<script>
(function(){{'use strict';try{{var t=localStorage.getItem('jobfinder_theme');if(!t){{t=window.matchMedia&&window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';}}document.documentElement.setAttribute('data-theme',t);}}catch(e){{document.documentElement.setAttribute('data-theme','light');}}try{{var l=localStorage.getItem('jobfinder_lang');if(!l){{var bl=(navigator.language||'ar').toLowerCase();l=bl.indexOf('ar')===0?'ar':(bl.indexOf('fr')===0?'fr':'en');}}document.documentElement.lang=l;document.documentElement.dir=l==='ar'?'rtl':'ltr';}}catch(e){{}}}})();
</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800;900&family=Tajawal:wght@400;500;700;800&display=swap" rel="stylesheet">
<style>{CSS}</style>
{extra_schema}
</head>'''

def build_header():
    return '''<header class="header" role="banner">
  <div class="container header-inner">
    <a href="/" class="logo" aria-label="JobFinder">
      <span class="logo-icon">J</span>
      <span>Job<span>Finder</span></span>
    </a>
    <nav class="nav" id="mainNav" role="navigation" aria-label="Main navigation">
      <a href="/" data-route="/">الرئيسية</a>
      <a href="/jobs" data-route="/jobs">الوظائف</a>
      <a href="/categories" data-route="/categories">المجالات</a>
      <a href="/countries" data-route="/countries">الدول</a>
      <a href="/articles" data-route="/articles">دليل الباحث</a>
      <a href="/faq" data-route="/faq">الأسئلة الشائعة</a>
    </nav>
    <div class="header-actions">
      <button class="lang-toggle" id="langToggle" aria-label="Language">AR</button>
      <button class="theme-toggle" id="themeToggle" aria-label="Toggle dark mode">
        <svg id="themeIcon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
      </button>
      <button class="menu-toggle" id="menuToggle" aria-label="Menu" aria-expanded="false">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12h18M3 6h18M3 18h18"/></svg>
      </button>
    </div>
  </div>
</header>'''

def build_footer():
    return '''<footer class="footer" role="contentinfo">
  <div class="container">
    <div class="footer-grid">
      <div class="footer-brand">
        <div class="logo" style="color:#fff">
          <span class="logo-icon">J</span>
          <span style="color:#fff">Job<span style="color:#fbbf24">Finder</span></span>
        </div>
        <p>منصة JobFinder هي وجهتك الأولى للبحث عن الوظائف في الجزائر ودول الخليج العربي.</p>
      </div>
      <div class="footer-col">
        <h4>روابط سريعة</h4>
        <ul>
          <li><a href="/">الرئيسية</a></li>
          <li><a href="/jobs">جميع الوظائف</a></li>
          <li><a href="/categories">المجالات</a></li>
          <li><a href="/articles">دليل الباحث</a></li>
        </ul>
      </div>
      <div class="footer-col">
        <h4>دول العمل</h4>
        <ul>
          <li><a href="/jobs/algeria">وظائف الجزائر</a></li>
          <li><a href="/jobs/uae">وظائف الإمارات</a></li>
          <li><a href="/jobs/saudi-arabia">وظائف السعودية</a></li>
        </ul>
      </div>
      <div class="footer-col">
        <h4>مجالات عمل</h4>
        <ul>
          <li><a href="/jobs/programming">وظائف البرمجة</a></li>
          <li><a href="/jobs/engineering">وظائف الهندسة</a></li>
          <li><a href="/jobs/marketing">وظائف التسويق</a></li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <p>&copy; 2026 JobFinder. جميع الحقوق محفوظة.</p>
    </div>
  </div>
</footer>'''

def build_job_posting_schema(job):
    """Generate complete JobPosting JSON-LD with all required fields"""
    date_posted, valid_through = job_dates(job)
    country = get_country(job.get('country'))
    city = get_city(job.get('city'))

    # Clean description (remove newlines for schema)
    desc_clean = job.get('description', '').replace('\n', ' ').replace('"', '&quot;')

    schema = {
        "@context": "https://schema.org",
        "@type": "JobPosting",
        "title": job['title'],
        "description": job.get('description', '')[:5000],
        "datePosted": date_posted,
        "validThrough": valid_through,
        "employmentType": job.get('employmentType', 'full-time'),
        "hiringOrganization": {
            "@type": "Organization",
            "name": job.get('company', ''),
            "sameAs": job.get('applicationUrl', BASE_URL)
        },
        "jobLocation": {
            "@type": "Place",
            "address": {
                "@type": "PostalAddress",
                "streetAddress": get_city_address(job.get('city', ''))['street'],
                "addressLocality": job.get('cityName', ''),
                "addressRegion": job.get('countryName', ''),
                "postalCode": get_city_address(job.get('city', ''))['postalCode'],
                "addressCountry": job.get('countryName', '')
            }
        },
        "url": f"{BASE_URL}/jobs/{job_slug(job)}"
    }

    # Add salary if available
    if job.get('salary'):
        schema["baseSalary"] = {
            "@type": "MonetaryAmount",
            "currency": job['salary'].get('currency', ''),
            "minValue": job['salary'].get('min', 0),
            "maxValue": job['salary'].get('max', 0),
            "unitText": "MONTH"
        }

    # Add qualifications
    if job.get('requirements'):
        schema["qualifications"] = job['requirements']

    # Add skills
    if job.get('skills'):
        schema["skills"] = job['skills']

    return f'<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False, indent=2)}</script>'

def build_breadcrumb_schema(items):
    schema = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i + 1,
                "name": item['name'],
                "item": BASE_URL + item['url']
            }
            for i, item in enumerate(items)
        ]
    }
    return f'<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False, indent=2)}</script>'

def build_article_schema(article):
    schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": article['title'],
        "description": article.get('excerpt', ''),
        "datePublished": article.get('datePublished', ''),
        "author": {"@type": "Organization", "name": "JobFinder"},
        "publisher": {
            "@type": "Organization",
            "name": "JobFinder",
            "logo": {"@type": "ImageObject", "url": f"{BASE_URL}/og-image.png"}
        },
        "mainEntityOfPage": {"@type": "WebPage", "@id": f"{BASE_URL}/articles/{article['slug']}"}
    }
    return f'<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False, indent=2)}</script>'

def breadcrumbs_html(items):
    return f'''<nav class="breadcrumbs" aria-label="Breadcrumb">
  <ol itemscope itemtype="https://schema.org/BreadcrumbList">
    {''.join(f'<li itemprop="itemListElement" itemscope itemtype="https://schema.org/ListItem"><a href="{item["url"]}" itemprop="item"><span itemprop="name">{escape_html(item["name"])}</span></a><meta itemprop="position" content="{i+1}"></li>' for i, item in enumerate(items))}
  </ol>
</nav>'''

def job_card_html(job):
    return f'''<article class="job-card">
  <div class="job-card-header">
    <div class="company-logo">{escape_html(job.get('companyLogo', job.get('company', '')[:2]))}</div>
    <div class="job-card-info">
      <h3 class="job-card-title"><a href="/jobs/{job_slug(job)}">{escape_html(job['title'])}</a></h3>
      <div class="job-card-company">{escape_html(job.get('company', ''))}</div>
    </div>
  </div>
  <div class="job-card-meta">
    <span>📍 {escape_html(job.get('location', ''))}</span>
    <span>💼 {escape_html(job.get('employmentTypeName', ''))}</span>
  </div>
  <div class="job-card-tags">
    <span class="tag">{escape_html(job.get('categoryName', ''))}</span>
  </div>
  <div class="job-card-footer">
    <span class="job-card-salary">{job['salary']['min']}-{job['salary']['max']} {job['salary']['currency'] if job.get('salary') else ''}</span>
    <a href="/jobs/{job_slug(job)}" class="btn btn-primary btn-sm">عرض التفاصيل</a>
  </div>
</article>'''

# ============================================
# PAGE BUILDERS
# ============================================

def render_job_page(job):
    """Render a static HTML page for a single job"""
    slug = job_slug(job)
    url_path = f"/jobs/{slug}"
    date_posted, valid_through = job_dates(job)
    category = get_category(job.get('category'))
    country = get_country(job.get('country'))

    title = f"{job['title']} - {job.get('company', '')} | JobFinder"
    description = f"{job['title']} في {job.get('company', '')} - {job.get('location', '')}. {job.get('employmentTypeName', '')}. تقدم الآن على JobFinder."
    keywords = f"{job['title']}, {job.get('company', '')}, وظائف {job.get('countryName', '')}, وظائف {job.get('cityName', '')}, {job.get('categoryName', '')}"

    # Breadcrumbs
    crumbs = [
        {"name": "الرئيسية", "url": "/"},
        {"name": "الوظائف", "url": "/jobs"},
        {"name": job.get('categoryName', ''), "url": f"/jobs/{job.get('category', '')}"},
        {"name": job['title'], "url": url_path}
    ]

    # Related jobs
    related = [j for j in JOBS if j['id'] != job['id'] and (j.get('category') == job.get('category') or j.get('city') == job.get('city'))][:3]

    # Schemas
    job_schema = build_job_posting_schema(job)
    breadcrumb_schema = build_breadcrumb_schema(crumbs)

    head = build_head(title, description, url_path, 'article', keywords, job_schema + breadcrumb_schema)

    body = f'''<body>
{build_header()}
<main id="main" class="main-content">
  <div class="page-header">
    <div class="container">
      {breadcrumbs_html(crumbs)}
    </div>
  </div>
  <section class="section">
    <div class="container">
      <div class="job-detail">
        <div class="job-detail-main">
          <div class="job-detail-header">
            <div class="company-logo">{escape_html(job.get('companyLogo', job.get('company', '')[:2]))}</div>
            <div>
              <h1>{escape_html(job['title'])}</h1>
              <div class="job-detail-company">{escape_html(job.get('company', ''))}</div>
              <div class="job-detail-meta">
                <span>📍 {escape_html(job.get('location', ''))}</span>
                <span>💼 {escape_html(job.get('employmentTypeName', ''))}</span>
                <span>🕐 {date_posted}</span>
                <span>⏰ تنتهي في {valid_through}</span>
              </div>
            </div>
          </div>
          <div class="job-card-tags" style="margin-bottom:24px">
            <span class="tag">{escape_html(job.get('categoryName', ''))}</span>
            <span class="tag tag-success">{escape_html(job.get('employmentTypeName', ''))}</span>
            {f'<span class="tag">{escape_html(job.get("experienceLevel", ""))}</span>' if job.get('experienceLevel') else ''}
          </div>
          <div class="job-detail-section">
            <h3>وصف الوظيفة</h3>
            {''.join(f'<p>{escape_html(p.strip())}</p>' for p in job.get('description', '').split('\n') if p.strip())}
          </div>
          <div class="job-detail-section">
            <h3>المتطلبات والمؤهلات</h3>
            <ul>
              {''.join(f'<li>{escape_html(r)}</li>' for r in job.get('requirements', []))}
            </ul>
          </div>
          <div class="job-detail-section">
            <h3>المهارات المطلوبة</h3>
            <div class="skills-list">
              {''.join(f'<span class="skill-tag">{escape_html(s)}</span>' for s in job.get('skills', []))}
            </div>
          </div>
          <div class="job-detail-section">
            <h3>روابط ذات صلة</h3>
            <div style="display:flex;flex-wrap:wrap;gap:8px">
              <a href="/jobs/{job.get('category', '')}" class="btn btn-ghost btn-sm">{escape_html(job.get('categoryName', ''))} - جميع الوظائف</a>
              <a href="/jobs/{job.get('country', '')}" class="btn btn-ghost btn-sm">وظائف في {escape_html(job.get('countryName', ''))}</a>
              <a href="/jobs/{job.get('city', '')}" class="btn btn-ghost btn-sm">وظائف في {escape_html(job.get('cityName', ''))}</a>
            </div>
          </div>
          {f'''<div class="related-jobs">
            <h3 style="margin-bottom:16px">وظائف مشابهة</h3>
            <div class="jobs-grid">
              {''.join(job_card_html(r) for r in related)}
            </div>
          </div>''' if related else ''}
        </div>
        <aside class="job-detail-sidebar">
          <div class="sidebar-card">
            <div style="margin-bottom:16px">
              <div class="info-row"><span class="label">الراتب</span><span class="value">{job['salary']['min']}-{job['salary']['max']} {job['salary']['currency']}</span></div>
              <div class="info-row"><span class="label">نوع العقد</span><span class="value">{escape_html(job.get('employmentTypeName', ''))}</span></div>
              <div class="info-row"><span class="label">المستوى</span><span class="value">{escape_html(job.get('experienceLevel', 'غير محدد'))}</span></div>
              <div class="info-row"><span class="label">تاريخ النشر</span><span class="value">{date_posted}</span></div>
              <div class="info-row"><span class="label">آخر أجل</span><span class="value">{valid_through}</span></div>
            </div>
            <a href="{job.get('applicationUrl', '#')}" target="_blank" rel="noopener" class="btn btn-primary apply-btn">🚀 تقدم الآن</a>
          </div>
        </aside>
      </div>
    </div>
  </section>
</main>
{build_footer()}
</body></html>'''

    return head + body

def render_category_page(category):
    """Render static page for a category"""
    slug = category['slug']
    url_path = f"/jobs/{slug}"
    cat_jobs = [j for j in JOBS if j.get('category') == slug]

    title = f"وظائف {category['name']} في الجزائر ودول الخليج | JobFinder"
    description = f"{category['description']} تصفح {len(cat_jobs)} وظيفة متاحة في مجال {category['name']}."
    keywords = f"وظائف {category['name']}, {category['name']}, توظيف {category['name']}"

    crumbs = [
        {"name": "الرئيسية", "url": "/"},
        {"name": "المجالات", "url": "/categories"},
        {"name": category['name'], "url": url_path}
    ]

    breadcrumb_schema = build_breadcrumb_schema(crumbs)
    head = build_head(title, description, url_path, 'website', keywords, breadcrumb_schema)

    body = f'''<body>
{build_header()}
<main id="main" class="main-content">
  <div class="page-header">
    <div class="container">
      {breadcrumbs_html(crumbs)}
      <h1>{category['icon']} وظائف {category['name']}</h1>
      <p>{category['description']}</p>
    </div>
  </div>
  <section class="section">
    <div class="container">
      <div class="jobs-header" style="margin-bottom:20px">
        <div class="jobs-count">عرض <strong>{len(cat_jobs)}</strong> وظيفة</div>
      </div>
      <div class="jobs-grid">
        {''.join(job_card_html(j) for j in cat_jobs) if cat_jobs else '<div class="empty-state"><h3>لا توجد وظائف في هذا المجال حالياً</h3></div>'}
      </div>
    </div>
  </section>
</main>
{build_footer()}
</body></html>'''

    return head + body

def render_country_page(country):
    """Render static page for a country"""
    slug = country['slug']
    url_path = f"/jobs/{slug}"
    country_jobs = [j for j in JOBS if j.get('country') == slug]
    cities_in_country = [c for c in CITIES if c['country'] == slug]

    title = f"وظائف في {country['name']} | JobFinder"
    description = f"ابحث عن وظائف في {country['name']}. {country['description']} {len(country_jobs)} وظيفة متاحة."
    keywords = f"وظائف {country['name']}, توظيف {country['name']}, عمل في {country['name']}"

    crumbs = [
        {"name": "الرئيسية", "url": "/"},
        {"name": "الدول", "url": "/countries"},
        {"name": country['name'], "url": url_path}
    ]

    breadcrumb_schema = build_breadcrumb_schema(crumbs)
    head = build_head(title, description, url_path, 'website', keywords, breadcrumb_schema)

    body = f'''<body>
{build_header()}
<main id="main" class="main-content">
  <div class="page-header">
    <div class="container">
      {breadcrumbs_html(crumbs)}
      <h1>{country['flag']} وظائف في {country['name']}</h1>
      <p>{country['description']} تصفح {len(country_jobs)} وظيفة متاحة.</p>
    </div>
  </div>
  <section class="section">
    <div class="container">
      <div class="jobs-grid">
        {''.join(job_card_html(j) for j in country_jobs) if country_jobs else '<div class="empty-state"><h3>لا توجد وظائف في هذه الدولة حالياً</h3></div>'}
      </div>
      {f'''<div style="margin-top:48px">
        <h2 class="section-title">المدن في {country['name']}</h2>
        <div class="cities-grid" style="margin-top:20px">
          {''.join(f'<a href="/jobs/{c["slug"]}" class="city-card"><div class="city-icon">🏙️</div><h3>{c["name"]}</h3></a>' for c in cities_in_country)}
        </div>
      </div>''' if cities_in_country else ''}
    </div>
  </section>
</main>
{build_footer()}
</body></html>'''

    return head + body

def render_city_page(city):
    """Render static page for a city"""
    slug = city['slug']
    url_path = f"/jobs/{slug}"
    city_jobs = [j for j in JOBS if j.get('city') == slug]

    title = f"وظائف في {city['name']} - {city['countryName']} | JobFinder"
    description = f"ابحث عن وظائف في {city['name']}، {city['countryName']}. {len(city_jobs)} وظيفة متاحة."
    keywords = f"وظائف {city['name']}, عمل في {city['name']}, توظيف {city['name']}"

    crumbs = [
        {"name": "الرئيسية", "url": "/"},
        {"name": "الدول", "url": "/countries"},
        {"name": city['countryName'], "url": f"/jobs/{city['country']}"},
        {"name": city['name'], "url": url_path}
    ]

    breadcrumb_schema = build_breadcrumb_schema(crumbs)
    head = build_head(title, description, url_path, 'website', keywords, breadcrumb_schema)

    body = f'''<body>
{build_header()}
<main id="main" class="main-content">
  <div class="page-header">
    <div class="container">
      {breadcrumbs_html(crumbs)}
      <h1>🏙️ وظائف في {city['name']}</h1>
      <p>تصفح {len(city_jobs)} وظيفة متاحة في {city['name']}، {city['countryName']}.</p>
    </div>
  </div>
  <section class="section">
    <div class="container">
      <div class="jobs-grid">
        {''.join(job_card_html(j) for j in city_jobs) if city_jobs else '<div class="empty-state"><h3>لا توجد وظائف في هذه المدينة حالياً</h3></div>'}
      </div>
    </div>
  </section>
</main>
{build_footer()}
</body></html>'''

    return head + body

def render_article_page(article):
    """Render static page for an article"""
    slug = article['slug']
    url_path = f"/articles/{slug}"

    title = f"{article['title']} | JobFinder"
    description = article.get('excerpt', '')
    keywords = f"{article.get('category', '')}, دليل الباحث عن عمل, نصائح وظيفية"

    crumbs = [
        {"name": "الرئيسية", "url": "/"},
        {"name": "دليل الباحث", "url": "/articles"},
        {"name": article['title'], "url": url_path}
    ]

    article_schema = build_article_schema(article)
    breadcrumb_schema = build_breadcrumb_schema(crumbs)
    head = build_head(title, description, url_path, 'article', keywords, article_schema + breadcrumb_schema)

    body = f'''<body>
{build_header()}
<main id="main" class="main-content">
  <div class="page-header">
    <div class="container">
      {breadcrumbs_html(crumbs)}
    </div>
  </div>
  <section class="section">
    <div class="container">
      <article class="article-detail">
        <header class="article-header">
          <div class="article-card-cat">{escape_html(article.get('category', ''))}</div>
          <h1>{escape_html(article['title'])}</h1>
          <div class="article-meta">
            <span>📅 {article.get('datePublished', '')}</span>
            <span>⏱️ {article.get('readingTime', 5)} دقائق قراءة</span>
          </div>
        </header>
        <div class="article-body">
          {article.get('content', '')}
        </div>
        <div class="newsletter" style="margin-top:32px">
          <h3>جاهز للبحث عن وظيفة؟</h3>
          <p>تصفح آلاف الوظائف المتاحة على JobFinder</p>
          <a href="/jobs" class="btn btn-primary btn-lg">تصفح الوظائف</a>
        </div>
      </article>
    </div>
  </section>
</main>
{build_footer()}
</body></html>'''

    return head + body

# ============================================
# MAIN: Generate all pages
# ============================================

def render_home_page():
    """Render a fully pre-rendered home page with all jobs visible to Googlebot"""
    url_path = "/"
    title = f"JobFinder - منصة البحث عن الوظائف في الجزائر ودول الخليج"
    description = "ابحث عن آلاف الوظائف الشاغرة في الجزائر والإمارات والسعودية وقطر والكويت وعمان والبحرين. وظائف في البرمجة، الهندسة، التسويق، المبيعات، الحرف والمزيد."

    crumbs = [{"name": "الرئيسية", "url": "/"}]

    # Sort jobs by date (newest first)
    sorted_jobs = sorted(JOBS, key=lambda j: j.get('daysAgo', 0))

    # Top categories with counts
    cat_counts = {}
    for j in JOBS:
        cat_counts[j.get('category', '')] = cat_counts.get(j.get('category', ''), 0) + 1
    top_categories = sorted(CATEGORIES, key=lambda c: cat_counts.get(c['slug'], 0), reverse=True)[:8]

    # New jobs in last 24h
    new_jobs_24h = [j for j in JOBS if j.get('daysAgo', 0) <= 1]

    # ItemList schema containing all jobs (this is the CORRECT way to list jobs on homepage)
    # Google recommends ItemList for collections, NOT multiple JobPosting schemas
    item_list_schema = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "وظائف شاغرة في الجزائر ودول الخليج",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i + 1,
                "url": f"{BASE_URL}/jobs/job-{job['id']}",
                "name": job['title']
            }
            for i, job in enumerate(sorted_jobs)
        ]
    }

    # WebSite + SearchAction schema
    website_schema = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "url": BASE_URL + "/",
        "name": "JobFinder",
        "potentialAction": {
            "@type": "SearchAction",
            "target": {
                "@type": "EntryPoint",
                "urlTemplate": BASE_URL + "/jobs?q={search_term_string}"
            },
            "query-input": "required name=search_term_string"
        }
    }

    # Organization schema
    org_schema = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "JobFinder",
        "url": BASE_URL + "/",
        "logo": BASE_URL + "/og-image.png"
    }

    # Combine schemas - NO JobPosting schemas on homepage (each job has its own page)
    all_schemas = ''
    for schema in [org_schema, website_schema, item_list_schema]:
        all_schemas += f'\n<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False, indent=2)}</script>'

    head = build_head(title, description, url_path, 'website', '', all_schemas)

    # Build job cards HTML (static, no JS needed)
    job_cards_html = ''
    for job in sorted_jobs[:12]:  # Show 12 recent jobs on homepage
        date_posted, _ = job_dates(job)
        job_cards_html += f'''<article class="job-card">
  <div class="job-card-header">
    <div class="company-logo">{escape_html(job.get('companyLogo', job.get('company', '')[:2]))}</div>
    <div class="job-card-info">
      <h3 class="job-card-title"><a href="/jobs/job-{job['id']}">{escape_html(job['title'])}</a></h3>
      <div class="job-card-company">{escape_html(job.get('company', ''))}</div>
    </div>
  </div>
  <div class="job-card-meta">
    <span>📍 {escape_html(job.get('location', ''))}</span>
    <span>💼 {escape_html(job.get('employmentTypeName', ''))}</span>
  </div>
  <div class="job-card-tags">
    <span class="tag">{escape_html(job.get('categoryName', ''))}</span>
    {'<span class="badge-new" style="position:static">جديد</span>' if job.get('daysAgo', 0) <= 1 else ''}
  </div>
  <div class="job-card-footer">
    <span class="job-card-salary">{job['salary']['min']}-{job['salary']['max']} {job['salary']['currency'] if job.get('salary') else ''}</span>
    <a href="/jobs/job-{job['id']}" class="btn btn-primary btn-sm">عرض التفاصيل</a>
  </div>
</article>'''

    # Build categories HTML
    categories_html = ''
    for cat in top_categories:
        count = cat_counts.get(cat['slug'], 0)
        if count > 0:
            categories_html += f'''<a href="/jobs/{cat['slug']}" class="cat-card">
  <div class="cat-icon">{cat['icon']}</div>
  <h3>{escape_html(cat['name'])}</h3>
  <div class="count">{count} وظيفة</div>
</a>'''

    # Build countries HTML
    countries_html = ''
    for country in COUNTRIES[:8]:
        count = len([j for j in JOBS if j.get('country') == country['slug']])
        countries_html += f'''<a href="/jobs/{country['slug']}" class="country-card">
  <div class="country-icon" style="font-size:2rem">{country['flag']}</div>
  <h3>{escape_html(country['name'])}</h3>
  <div class="count">{count} وظيفة</div>
</a>'''

    body = f'''<body class="ready">
{build_header()}
<main id="main" class="main-content">
  <!-- Hero Section -->
  <section class="hero">
    <div class="container hero-content">
      <h1>اعثر على وظيفتك المثالية في <span>الجزائر ودول الخليج</span></h1>
      <p>آلاف الوظائف الشاغرة من أفضل الشركات في انتظارك. ابحث الآن وابدأ رحلتك المهنية.</p>
      <form class="search-bar" action="/jobs" method="get">
        <div class="search-input-wrap">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>
          <input type="text" class="search-input" name="q" placeholder="ابحث عن وظيفة، شركة، أو كلمة مفتاحية..." aria-label="بحث">
        </div>
        <button type="submit" class="btn btn-search btn-primary">🔍 بحث</button>
      </form>
      <div class="hero-stats">
        <div class="hero-stat"><div class="num">{len(JOBS)}+</div><div class="label">وظيفة شاغرة</div></div>
        <div class="hero-stat"><div class="num">{len(new_jobs_24h)}</div><div class="label">وظيفة جديدة اليوم</div></div>
        <div class="hero-stat"><div class="num">{len(COUNTRIES)}</div><div class="label">دولة</div></div>
        <div class="hero-stat"><div class="num">{len(CATEGORIES)}</div><div class="label">مجال</div></div>
      </div>
    </div>
  </section>

  <!-- Recent Jobs -->
  <section class="section">
    <div class="container">
      <div class="section-header">
        <div>
          <h2 class="section-title">الوظائف الحديثة</h2>
          <p class="section-subtitle">أحدث الفرص الوظيفية المضافة على المنصة</p>
        </div>
        <a href="/jobs" class="btn btn-outline">عرض الكل</a>
      </div>
      <div class="jobs-grid">
        {job_cards_html}
      </div>
    </div>
  </section>

  <!-- Stats Section -->
  <section class="stats-section">
    <div class="container">
      <div class="stats-grid">
        <div class="stat-item"><div class="num">{len(JOBS)}+</div><div class="label">وظيفة متاحة</div></div>
        <div class="stat-item"><div class="num">{len(set(j.get('company','') for j in JOBS))}</div><div class="label">شركة مسجلة</div></div>
        <div class="stat-item"><div class="num">{len(CITIES)}</div><div class="label">مدينة</div></div>
        <div class="stat-item"><div class="num">{len(ARTICLES)}</div><div class="label">دليل ومقال</div></div>
      </div>
    </div>
  </section>

  <!-- ALL Jobs - Internal Links for Googlebot Crawling -->
  <section class="section">
    <div class="container">
      <div class="section-header">
        <div>
          <h2 class="section-title">جميع الوظائف المتاحة ({len(JOBS)} وظيفة)</h2>
          <p class="section-subtitle">روابط مباشرة لكل وظيفة - كل وظيفة لها صفحة مستقلة بتفاصيل كاملة</p>
        </div>
        <a href="/jobs" class="btn btn-outline">عرض كل الوظائف</a>
      </div>
      <div class="all-jobs-links" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px;margin-top:20px">
        {''.join(f'<a href="/jobs/job-{job["id"]}" style="display:block;padding:12px;background:var(--bg-card);border:1px solid var(--border);border-radius:8px;text-decoration:none;color:var(--text);transition:all .2s"><strong>{escape_html(job["title"])}</strong><br><small style="color:var(--text-muted)">{escape_html(job.get("company",""))} · {escape_html(job.get("cityName",""))}</small></a>' for job in sorted_jobs)}
      </div>
    </div>
  </section>

  <!-- Top Categories -->
  <section class="section">
    <div class="container">
      <div class="section-header">
        <div>
          <h2 class="section-title">أكثر المجالات طلباً</h2>
          <p class="section-subtitle">تصفح الوظائف حسب المجال الذي يناسبك</p>
        </div>
        <a href="/categories" class="btn btn-outline">كل المجالات</a>
      </div>
      <div class="categories-grid">
        {categories_html}
      </div>
    </div>
  </section>

  <!-- Countries -->
  <section class="section" style="background:var(--bg-alt)">
    <div class="container">
      <div class="section-header">
        <div>
          <h2 class="section-title">الدول المتاحة</h2>
          <p class="section-subtitle">اختر الدولة للبحث عن وظائف فيها</p>
        </div>
        <a href="/countries" class="btn btn-outline">كل الدول</a>
      </div>
      <div class="countries-grid">
        {countries_html}
      </div>
    </div>
  </section>

  <!-- Career Guide -->
  <section class="section" style="background:var(--bg-alt)">
    <div class="container">
      <div class="section-header">
        <div>
          <h2 class="section-title">دليل الباحث عن عمل</h2>
          <p class="section-subtitle">مقالات ونصائح عملية لمساعدتك في رحلة البحث عن وظيفة</p>
        </div>
        <a href="/articles" class="btn btn-outline">كل المقالات</a>
      </div>
      <div class="articles-grid">
        {''.join(f'''<a href="/articles/{a['slug']}" class="article-card">
          <div class="article-card-img">{a.get('icon', '📄')}</div>
          <div class="article-card-body">
            <div class="article-card-cat">{escape_html(a.get('category', ''))}</div>
            <h3>{escape_html(a['title'])}</h3>
            <p>{escape_html(a.get('excerpt', '')[:100])}</p>
          </div>
        </a>''' for a in ARTICLES[:4])}
      </div>
    </div>
  </section>
</main>
{build_footer()}
<button class="back-to-top" id="backToTop" aria-label="العودة للأعلى">
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 15l-6-6-6 6"/></svg>
</button>
</body></html>'''

    return head + body

def render_jobs_list_page():
    """Render /jobs listing page with ALL jobs visible to Googlebot"""
    url_path = "/jobs"
    title = "جميع الوظائف - JobFinder | وظائف في الجزائر ودول الخليج"
    description = f"تصفح {len(JOBS)} وظيفة متاحة في الجزائر والإمارات والسعودية ودول الخليج. وظائف في البرمجة، الهندسة، التسويق، الحرف والمزيد."

    crumbs = [
        {"name": "الرئيسية", "url": "/"},
        {"name": "الوظائف", "url": "/jobs"}
    ]
    breadcrumb_schema = build_breadcrumb_schema(crumbs)
    head = build_head(title, description, url_path, 'website', '', breadcrumb_schema)

    # All job cards
    job_cards = ''.join(job_card_html(j) for j in JOBS)

    body = f'''<body class="ready">
{build_header()}
<main id="main" class="main-content">
  <div class="page-header">
    <div class="container">
      {breadcrumbs_html(crumbs)}
      <h1>جميع الوظائف</h1>
      <p>تصفح {len(JOBS)} وظيفة متاحة في الجزائر ودول الخليج</p>
    </div>
  </div>
  <section class="section">
    <div class="container">
      <div class="jobs-header" style="margin-bottom:20px">
        <div class="jobs-count">عرض <strong>{len(JOBS)}</strong> وظيفة</div>
      </div>
      <div class="jobs-grid">
        {job_cards}
      </div>
    </div>
  </section>
</main>
{build_footer()}
</body></html>'''
    return head + body

def render_categories_list_page():
    """Render /categories listing page"""
    url_path = "/categories"
    title = "جميع مجالات العمل - JobFinder"
    description = "تصفح وظائف في مختلف المجالات: البرمجة، الهندسة، التسويق، التصميم، المالية، الحرف والمزيد."

    crumbs = [{"name": "الرئيسية", "url": "/"}, {"name": "المجالات", "url": "/categories"}]
    breadcrumb_schema = build_breadcrumb_schema(crumbs)
    head = build_head(title, description, url_path, 'website', '', breadcrumb_schema)

    cat_cards = ''
    for cat in CATEGORIES:
        count = len([j for j in JOBS if j.get('category') == cat['slug']])
        cat_cards += f'''<a href="/jobs/{cat['slug']}" class="cat-card">
  <div class="cat-icon">{cat['icon']}</div>
  <h3>{escape_html(cat['name'])}</h3>
  <div class="count">{count} وظيفة</div>
</a>'''

    body = f'''<body class="ready">
{build_header()}
<main id="main" class="main-content">
  <div class="page-header">
    <div class="container">
      {breadcrumbs_html(crumbs)}
      <h1>جميع المجالات</h1>
      <p>تصفح الوظائف حسب المجال الذي يناسب مهاراتك</p>
    </div>
  </div>
  <section class="section">
    <div class="container">
      <div class="categories-grid">
        {cat_cards}
      </div>
    </div>
  </section>
</main>
{build_footer()}
</body></html>'''
    return head + body

def render_countries_list_page():
    """Render /countries listing page"""
    url_path = "/countries"
    title = "دول العمل المتاحة - JobFinder"
    description = "ابحث عن وظائف في الجزائر، الإمارات، السعودية، قطر، الكويت، عمان، البحرين ومصر والمغرب وتونس وغيرها."

    crumbs = [{"name": "الرئيسية", "url": "/"}, {"name": "الدول", "url": "/countries"}]
    breadcrumb_schema = build_breadcrumb_schema(crumbs)
    head = build_head(title, description, url_path, 'website', '', breadcrumb_schema)

    country_cards = ''
    for country in COUNTRIES:
        count = len([j for j in JOBS if j.get('country') == country['slug']])
        country_cards += f'''<a href="/jobs/{country['slug']}" class="country-card">
  <div class="country-icon" style="font-size:2.5rem">{country['flag']}</div>
  <h3>{escape_html(country['name'])}</h3>
  <div class="count">{count} وظيفة</div>
</a>'''

    body = f'''<body class="ready">
{build_header()}
<main id="main" class="main-content">
  <div class="page-header">
    <div class="container">
      {breadcrumbs_html(crumbs)}
      <h1>جميع الدول</h1>
      <p>ابحث عن وظائف في الجزائر ودول الخليج العربي</p>
    </div>
  </div>
  <section class="section">
    <div class="container">
      <div class="countries-grid">
        {country_cards}
      </div>
    </div>
  </section>
</main>
{build_footer()}
</body></html>'''
    return head + body

def render_articles_list_page():
    """Render /articles listing page"""
    url_path = "/articles"
    title = "دليل الباحث عن عمل - مقالات ونصائح | JobFinder"
    description = "مقالات عملية للباحثين عن عمل: كيفية كتابة السيرة الذاتية، الاستعداد للمقابلة، البحث عن وظيفة في الجزائر ودول الخليج."

    crumbs = [{"name": "الرئيسية", "url": "/"}, {"name": "دليل الباحث", "url": "/articles"}]
    breadcrumb_schema = build_breadcrumb_schema(crumbs)
    head = build_head(title, description, url_path, 'website', '', breadcrumb_schema)

    article_cards = ''
    for a in ARTICLES:
        article_cards += f'''<a href="/articles/{a['slug']}" class="article-card">
  <div class="article-card-img">{a.get('icon', '📄')}</div>
  <div class="article-card-body">
    <div class="article-card-cat">{escape_html(a.get('category', ''))}</div>
    <h3>{escape_html(a['title'])}</h3>
    <p>{escape_html(a.get('excerpt', '')[:120])}</p>
    <div class="article-card-meta">
      <span>⏱️ {a.get('readingTime', 5)} دقائق</span>
    </div>
  </div>
</a>'''

    body = f'''<body class="ready">
{build_header()}
<main id="main" class="main-content">
  <div class="page-header">
    <div class="container">
      {breadcrumbs_html(crumbs)}
      <h1>📚 دليل الباحث عن عمل</h1>
      <p>مقالات ونصائح عملية لمساعدتك في رحلتك المهنية</p>
    </div>
  </div>
  <section class="section">
    <div class="container">
      <div class="articles-grid">
        {article_cards}
      </div>
    </div>
  </section>
</main>
{build_footer()}
</body></html>'''
    return head + body

def render_faq_page():
    """Render /faq page with FAQPage schema"""
    url_path = "/faq"
    title = "الأسئلة الشائعة | JobFinder"
    description = "إجابات على أسئلة شائعة حول البحث عن عمل، التقديم للوظائف، أنواع العقود، كتابة السيرة الذاتية."

    crumbs = [{"name": "الرئيسية", "url": "/"}, {"name": "الأسئلة الشائعة", "url": "/faq"}]
    breadcrumb_schema = build_breadcrumb_schema(crumbs)

    faqs = [
        {"q": "كيف أبحث عن وظيفة على JobFinder؟", "a": "يمكنك البحث عن وظيفة باستخدام شريط البحث في الصفحة الرئيسية للبحث بالكلمات المفتاحية، أو تصفح الوظائف حسب الدولة والمدينة والمجال."},
        {"q": "كيف أتقدم لوظيفة؟", "a": "بعد العثور على وظيفة مناسبة، اضغط على زر 'تقدم الآن' في صفحة تفاصيل الوظيفة. سيتم تحويلك إلى صفحة التقديم الخاصة بالشركة."},
        {"q": "ما معنى أنواع العقود المختلفة؟", "a": "دوام كامل: 40 ساعة أسبوعياً. دوام جزئي: ساعات أقل. عقد مؤقت: لمدة محددة. عن بُعد: العمل من المنزل. تدريب: للطلاب أو حديثي التخرج."},
        {"q": "كيف أنشئ سيرة ذاتية احترافية؟", "a": "ركز على المعلومات الشخصية، الملخص المهني، الخبرة العملية بإنجازات محددة، التعليم، والمهارات. خصص سيرتك لكل وظيفة."},
        {"q": "هل الوظائف على JobFinder حقيقية؟", "a": "نعم، نسعى لتوفير وظائف حقيقية وموثوقة. لا ندفع أي رسوم مقابل التقديم."},
        {"q": "كم مرة يتم تحديث الوظائف؟", "a": "نقوم بتحديث قائمة الوظائف بشكل دوري. يتم إزالة الوظائف منتهية الصلاحية وإضافة وظائف جديدة باستمرار."},
    ]

    faq_schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [{"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in faqs]
    }
    all_schemas = f'<script type="application/ld+json">{json.dumps(breadcrumb_schema, ensure_ascii=False)}</script>'
    all_schemas += f'\n<script type="application/ld+json">{json.dumps(faq_schema, ensure_ascii=False)}</script>'

    head = build_head(title, description, url_path, 'website', '', all_schemas)

    faq_items = ''
    for i, f in enumerate(faqs):
        faq_items += f'''<div class="faq-item {'open' if i == 0 else ''}">
  <button class="faq-question" aria-expanded="{'true' if i == 0 else 'false'}">
    <span>{escape_html(f['q'])}</span>
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg>
  </button>
  <div class="faq-answer"><div class="faq-answer-inner">{escape_html(f['a'])}</div></div>
</div>'''

    body = f'''<body class="ready">
{build_header()}
<main id="main" class="main-content">
  <div class="page-header">
    <div class="container">
      {breadcrumbs_html(crumbs)}
      <h1>❓ الأسئلة الشائعة</h1>
      <p>إجابات على أكثر الأسئلة شيوعاً</p>
    </div>
  </div>
  <section class="section">
    <div class="container">
      <div class="faq-list">
        {faq_items}
      </div>
    </div>
  </section>
</main>
{build_footer()}
</body></html>'''
    return head + body

def main():
    # 1. Generate pre-rendered home page (NOT the SPA)
    home_html = render_home_page()
    with open(os.path.join(DIST_DIR, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(home_html)
    print(f"✓ Home page (pre-rendered with {len(JOBS)} jobs)")

    # 2. Generate job pages
    for job in JOBS:
        slug = job_slug(job)
        html = render_job_page(job)
        # Create nested directory structure: /jobs/<slug>/index.html
        job_dir = os.path.join(JOBS_DIR, slug)
        os.makedirs(job_dir, exist_ok=True)
        with open(os.path.join(job_dir, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(html)
    print(f"✓ {len(JOBS)} job pages")

    # 3. Generate category pages
    for cat in CATEGORIES:
        html = render_category_page(cat)
        cat_dir = os.path.join(JOBS_DIR, cat['slug'])
        os.makedirs(cat_dir, exist_ok=True)
        with open(os.path.join(cat_dir, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(html)
    print(f"✓ {len(CATEGORIES)} category pages")

    # 4. Generate country pages
    for country in COUNTRIES:
        html = render_country_page(country)
        country_dir = os.path.join(JOBS_DIR, country['slug'])
        os.makedirs(country_dir, exist_ok=True)
        with open(os.path.join(country_dir, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(html)
    print(f"✓ {len(COUNTRIES)} country pages")

    # 5. Generate city pages
    for city in CITIES:
        html = render_city_page(city)
        city_dir = os.path.join(JOBS_DIR, city['slug'])
        os.makedirs(city_dir, exist_ok=True)
        with open(os.path.join(city_dir, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(html)
    print(f"✓ {len(CITIES)} city pages")

    # 6. Generate article pages
    for article in ARTICLES:
        html = render_article_page(article)
        article_dir = os.path.join(ARTICLES_DIR, article['slug'])
        os.makedirs(article_dir, exist_ok=True)
        with open(os.path.join(article_dir, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(html)
    print(f"✓ {len(ARTICLES)} article pages")

    # 6b. Generate /jobs listing page (all jobs)
    jobs_list_html = render_jobs_list_page()
    with open(os.path.join(DIST_DIR, 'jobs.html'), 'w', encoding='utf-8') as f:
        f.write(jobs_list_html)
    print(f"✓ /jobs listing page")

    # 6c. Generate /categories listing page
    cat_list_html = render_categories_list_page()
    with open(os.path.join(DIST_DIR, 'categories.html'), 'w', encoding='utf-8') as f:
        f.write(cat_list_html)
    print(f"✓ /categories listing page")

    # 6d. Generate /countries listing page
    countries_list_html = render_countries_list_page()
    with open(os.path.join(DIST_DIR, 'countries.html'), 'w', encoding='utf-8') as f:
        f.write(countries_list_html)
    print(f"✓ /countries listing page")

    # 6e. Generate /articles listing page
    articles_list_html = render_articles_list_page()
    with open(os.path.join(DIST_DIR, 'articles.html'), 'w', encoding='utf-8') as f:
        f.write(articles_list_html)
    print(f"✓ /articles listing page")

    # 6f. Generate /faq page
    faq_html = render_faq_page()
    with open(os.path.join(DIST_DIR, 'faq.html'), 'w', encoding='utf-8') as f:
        f.write(faq_html)
    print(f"✓ /faq page")

    # 7. Copy static files
    for fname in ['robots.txt', 'sitemap.xml', 'og-image.svg', '_redirects']:
        src = os.path.join(PROJECT_DIR, fname)
        if os.path.exists(src):
            import shutil
            shutil.copy2(src, os.path.join(DIST_DIR, fname))

    # Also copy public/ folder
    public_dir = os.path.join(PROJECT_DIR, 'public')
    if os.path.exists(public_dir):
        import shutil
        for f in os.listdir(public_dir):
            shutil.copy2(os.path.join(public_dir, f), os.path.join(DIST_DIR, f))

    # 8. Summary
    total_pages = 1 + len(JOBS) + len(CATEGORIES) + len(COUNTRIES) + len(CITIES) + len(ARTICLES)
    print(f"\n{'='*50}")
    print(f"✅ Total pre-rendered pages: {total_pages}")
    print(f"📁 Output: {DIST_DIR}")
    print(f"{'='*50}")

if __name__ == '__main__':
    main()
