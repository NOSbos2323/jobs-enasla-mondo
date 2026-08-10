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
    """Extract a JS array from index.html using Node"""
    script = f"""
const fs = require('fs');
const html = fs.readFileSync('{os.path.join(PROJECT_DIR, 'index.html')}', 'utf8');
const re = new RegExp('const {var_name} = \\\\[([\\\\s\\\\S]*?)\\\\n\\\\];');
const m = html.match(re);
if (!m) {{ console.log('NOT FOUND'); process.exit(1); }}
const arr = eval('[' + m[1] + ']');
console.log(JSON.stringify(arr));
"""
    result = subprocess.run(['node', '-e', script], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error extracting {var_name}: {result.stderr}")
        return []
    return json.loads(result.stdout.strip())

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
                "addressLocality": job.get('cityName', ''),
                "addressRegion": job.get('countryName', ''),
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

def main():
    # 1. Copy original index.html as the home page
    with open(os.path.join(DIST_DIR, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(ORIGINAL_HTML)
    print(f"✓ Home page (index.html)")

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

    # 7. Copy static files
    for fname in ['robots.txt', 'sitemap.xml', 'og-image.png', '_redirects']:
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
