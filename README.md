# JobFinder - منصة البحث عن الوظائف

موقع وظائف احترافي مبني بـ HTML5 + CSS3 + JavaScript فقط (ملف واحد `index.html`)، يستهدف الباحثين عن عمل في الجزائر ودول الخليج العربي.

## ✨ المميزات

### 🎯 البحث والفلترة
- بحث بالكلمات المفتاحية
- فلترة حسب الدولة، المدينة، المجال، نوع العقد
- ترتيب حسب الأحدث / الراتب
- Pagination ذكي
- صفحة تفاصيل لكل وظيفة

### 🔍 SEO احترافي
- HTML semantic صحيح (`<html lang="ar" dir="rtl">`)
- Title و Meta description ديناميكية
- Canonical URL ديناميكي
- Open Graph + Twitter Card
- Schema.org JSON-LD:
  - JobPosting لكل وظيفة
  - BreadcrumbList
  - WebSite + SearchAction
  - Organization
  - FAQPage
  - Article

### 📄 الصفحات
- `/` — الصفحة الرئيسية
- `/jobs` — جميع الوظائف مع فلاتر
- `/jobs/:category` — صفحة المجال (programming, engineering, marketing, ...)
- `/jobs/:country` — صفحة الدولة (algeria, uae, saudi-arabia, ...)
- `/jobs/:city` — صفحة المدينة (algiers, dubai, riyadh, ...)
- `/jobs/:title-company-id` — تفاصيل الوظيفة
- `/categories` — كل المجالات
- `/countries` — كل الدول
- `/articles` — دليل الباحث عن عمل
- `/articles/:slug` — مقال فردي
- `/faq` — الأسئلة الشائعة
- `/about` — من نحن

### 📚 دليل الباحث عن عمل (8 مقالات)
1. كيفية كتابة CV احترافي
2. كيفية كتابة رسالة تحفيزية
3. أفضل مواقع البحث عن عمل
4. كيفية الاستعداد لمقابلة العمل
5. وظائف بدون خبرة
6. كيفية البحث عن وظيفة في الجزائر
7. كيفية البحث عن وظيفة في الإمارات
8. كيفية البحث عن وظيفة في السعودية

### 🎨 التصميم
- Responsive (Mobile First)
- RTL support
- Dark mode اختياري
- Header ثابت
- Sidebar للفلاتر
- Cards للوظائف
- أبيض مع لون أساسي أزرق

### ⚡ الأداء
- بدون مكتبات خارجية (vanilla JS)
- CSS مدمج داخل الملف
- خطوط Google Fonts (Cairo + Tajawal)
- Lazy rendering
- Core Web Vitals friendly

### 🔗 Internal Linking ذكي
- صفحة الوظيفة تربط إلى المجال، المدينة، الدولة، وظائف مشابهة، ومقالات
- صفحة المجال تربط إلى الوظائف والمدن
- صفحة المدينة تربط إلى الوظائف والمجالات والمدن القريبة

### 🛠️ بنية قابلة للتطوير
الدوال التالية مصممة لاستبدالها لاحقاً بـ API حقيقي:

```javascript
async function fetchJobs()          // → استبدل بـ fetch('/api/jobs')
async function fetchJobById(id)     // → استبدل بـ fetch('/api/jobs/:id')
async function fetchArticles()      // → استبدل بـ fetch('/api/articles')
async function fetchArticleBySlug() // → استبدل بـ fetch('/api/articles/:slug')
```

## 🚀 التشغيل محلياً

```bash
# بأي خادم ملفات ثابتة
npx serve .
# أو
python3 -m http.server 8000
```

## 📦 النشر على Vercel

المشروع جاهز للنشر على Vercel. ملف `vercel.json` يحتوي على إعدادات routing اللازمة لـ SPA.

```bash
npm i -g vercel
vercel --prod
```

## ⚠️ ملاحظة حول البيانات

الوظائف المعروضة هي **بيانات تجريبية** لأغراض العرض والتطوير. لربط الموقع بـ API حقيقي:

1. عدّل دالة `fetchJobs()` لجلب البيانات من endpoint حقيقي
2. تأكد من أن الـ response يطابق نفس بنية البيانات المتوقعة
3. لا حاجة لتغيير أي كود آخر في الواجهة

## 📝 SEO الأخلاقي

هذا المشروع يلتزم بممارسات SEO بيضاء (White Hat):
- ✅ محتوى أصلي ومفيد
- ✅ Structured Data صحيح
- ✅ Internal linking منطقي
- ❌ لا keyword stuffing
- ❌ لا hidden text
- ❌ لا cloaking
- ❌ لا doorway pages
- ❌ لا محتوى مختلف لـ Googlebot

## 📄 الترخيص

© 2026 JobFinder. جميع الحقوق محفوظة.

