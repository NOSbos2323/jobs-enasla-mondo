# 🚀 دليل النشر على Vercel

تم تجهيز المشروع بالكامل للنشر على Vercel. اتبع إحدى الطريقتين التاليتين:

---

## ✅ الطريقة 1: النشر المباشر من Vercel Dashboard (الأسهل)

1. اذهب إلى [vercel.com](https://vercel.com) وسجل الدخول بحسابك (يُفضل استخدام حساب GitHub)
2. اضغط **"Add New"** → **"Project"**
3. اختر مستودع `NOSbos2323/jobs-enasla-mondo` من قائمة GitHub
4. في إعدادات المشروع:
   - **Framework Preset**: Other (تلقائي)
   - **Root Directory**: `./` (افتراضي)
   - **Build Command**: (اتركه فارغاً - لا حاجة للبناء)
   - **Output Directory**: `./` (افتراضي)
5. اضغط **"Deploy"**
6. انتظر دقيقة حتى يكتمل النشر
7. ستحصل على رابط مثل: `https://jobs-enasla-mondo.vercel.app`

### تخصيص الدومين (اختياري)
- من إعدادات المشروع → **Domains**
- أضف `jobs-enasla-mondo.vercel.app` أو دومين مخصص

---

## ✅ الطريقة 2: النشر التلقائي عبر GitHub Actions

هذه الطريقة تنشر الموقع تلقائياً عند كل `git push` إلى فرع `main`.

### الخطوات:

1. اذهب إلى [vercel.com/tokens](https://vercel.com/account/tokens)
2. أنشئ توكن جديد باسم `GitHub Actions`
3. انسخ قيمة التوكن

4. اذهب إلى إعدادات مستودع GitHub:
   `https://github.com/NOSbos2323/jobs-enasla-mondo/settings/secrets/actions`

5. أضف Secret جديد:
   - **Name**: `VERCEL_TOKEN`
   - **Value**: (التوكن الذي نسخته)

6. (اختياري) للحصول على ORG_ID:
   - من Vercel Dashboard → Settings → General → Copy "Vercel ID"
   - أضفه كـ Secret باسم `VERCEL_ORG_ID`

7. اذهب إلى تبويب **Actions** في GitHub
8. اختر workflow **"Deploy to Vercel"**
9. اضغط **"Run workflow"**

---

## 🔗 الروابط المهمة بعد النشر

- **الموقع**: `https://jobs-enasla-mondo.vercel.app`
- **GitHub**: `https://github.com/NOSbos2323/jobs-enasla-mondo`
- **Vercel Dashboard**: `https://vercel.com/dashboard`

---

## ⚙️ ملاحظات تقنية

- ملف `vercel.json` يحتوي على إعدادات routing للـ SPA
- جميع المسارات (`/jobs/*`, `/articles/*`, إلخ) تُعاد إلى `index.html`
- الـ JavaScript router يتعامل مع العرض الديناميكي
- لا حاجة لـ build step — الموقع ثابت بالكامل

---

## 🧪 اختبار محلي قبل النشر

```bash
# تشغيل خادم محلي
npx serve .

# أو
python3 -m http.server 8000

# ثم افتح http://localhost:3000 (أو 8000)
```

---

## ❓ استكشاف الأخطاء

### المشكلة: الروابط الداخلية ترجع 404
**الحل**: تأكد أن `vercel.json` موجود وتم رفعه مع المشروع.

### المشكلة: الصفحة بيضاء
**الحل**: افتح Developer Tools (F12) → Console للتحقق من أخطاء JavaScript.

### المشكلة: الخطوط لا تظهر
**الحل**: تأكد من اتصال الإنترنت، الخطوط محملة من Google Fonts CDN.

---

## 📞 الدعم

للأسئلة أو المشاكل، راجع [README.md](./README.md) أو افتح Issue في GitHub.
