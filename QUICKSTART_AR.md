# دليل البدء السريع 🚀

## الإعداد الأولي (5 دقائق)

### 1. تثبيت المتطلبات الأساسية
```bash
chmod +x setup.sh
./setup.sh
```

### 2. إعداد Google Drive API

**الخطوة 1: إنشاء المشروع**
1. اذهب إلى https://console.cloud.google.com/
2. اضغط "New Project"
3. اختر اسم للمشروع (مثلاً: arabic-ocr)

**الخطوة 2: تفعيل Google Drive API**
1. من القائمة الجانبية، اختر "APIs & Services" > "Library"
2. ابحث عن "Google Drive API"
3. اضغط "Enable"

**الخطوة 3: إنشاء Credentials**
1. اذهب إلى "APIs & Services" > "Credentials"
2. اضغط "Create Credentials" > "OAuth client ID"
3. اختر "Desktop app"
4. حمّل ملف JSON
5. أعد تسميته إلى `credentials.json`
6. ضعه في مجلد المشروع

### 3. الحصول على Folder ID من Google Drive

**الطريقة السهلة:**
1. افتح مجلد المستندات في Google Drive
2. انظر إلى URL في المتصفح:
   ```
   https://drive.google.com/drive/folders/1ABcDefGhI_JKLmnoPQR-stUVwXyz
   ```
3. الجزء بعد `/folders/` هو الـ Folder ID
4. انسخه إلى ملف `.env`:
   ```
   GOOGLE_DRIVE_FOLDER_ID=1ABcDefGhI_JKLmnoPQR-stUVwXyz
   ```

## بدء المعالجة

### تجربة سريعة (10 ملفات)
```bash
# 1. مزامنة الملفات
python main.py --sync

# 2. معالجة 10 ملفات فقط للتجربة
python main.py --process --limit 10

# 3. عرض النتائج
python main.py --stats
```

### معالجة كاملة
```bash
# معالجة جميع الملفات
python main.py --process

# إذا توقفت المعالجة، استكمل من حيث توقفت
python main.py --process

# إعادة معالجة الملفات الفاشلة
python main.py --retry
```

### معالجة بأقصى سرعة (على خادم GPU)
```bash
python main.py --process --workers 8 --batch-size 32
```

## مراقبة التقدم

### عرض الإحصائيات
```bash
python main.py --stats
```

### مراجعة السجلات
```bash
# السجل الرئيسي
tail -f logs/ocr_processing.log

# سجل الأخطاء فقط
tail -f logs/errors.log
```

### التحقق من قاعدة البيانات
```bash
python -c "
from src.models.database import SessionLocal, get_processing_stats
db = SessionLocal()
stats = get_processing_stats(db)
print(f'تم: {stats[\"completed\"]}/{stats[\"total\"]} ({stats[\"completion_rate\"]}%)')
print(f'معدل الدقة: {stats[\"avg_confidence\"]:.2f}')
db.close()
"
```

## الملفات المُنتَجة

ستجد الملفات المحولة في:
```
data/output/
├── document1.txt      # نص خام
├── document1.docx     # مستند Word
├── document2.txt
└── document2.docx
```

## حل المشاكل الشائعة

### مشكلة: "Google credentials not found"
**الحل:**
```bash
# تأكد من وجود الملف
ls credentials.json

# تأكد من المسار الصحيح في .env
cat .env
```

### مشكلة: "Out of GPU memory"
**الحل:** قلل استخدام الذاكرة في `config.py`:
```python
NUM_WORKERS = 2
BATCH_SIZE = 8
PADDLE_GPU_MEM = 4000
```

### مشكلة: "Poppler not found"
**الحل:**
```bash
# Ubuntu/Debian
sudo apt-get install poppler-utils

# macOS
brew install poppler
```

### مشكلة: دقة OCR منخفضة
**الحل:** زد دقة الصورة في `config.py`:
```python
IMAGE_DPI = 400
ENHANCE_IMAGE = True
CONTRAST_ENHANCEMENT = True
```

## نصائح للأداء الأمثل

### 1. للمستندات ذات الجودة المنخفضة
```python
# في config.py
IMAGE_DPI = 400
DENOISE = True
CONTRAST_ENHANCEMENT = True
BINARIZATION = True
```

### 2. للمعالجة السريعة
```python
# في config.py
NUM_WORKERS = 8
BATCH_SIZE = 32
CLEAR_TEMP_FILES = True
```

### 3. لتوفير المساحة
```python
# في config.py
SAVE_IMAGES = False
CLEAR_TEMP_FILES = True
```

### 4. للمستندات القانونية الدقيقة
```python
# في config.py
REMOVE_DIACRITICS = False
VALIDATE_ARABIC = True
EXTRACT_ARTICLE_NUMBERS = True
EXTRACT_DATES = True
```

## تقدير الوقت

على خادم GPU 40GB مع RAM 256GB:

| عدد الملفات | الوقت المتوقع |
|-------------|---------------|
| 100 ملف | ~10-15 دقيقة |
| 1,000 ملف | ~1-2 ساعة |
| 10,000 ملف | ~12-24 ساعة |
| 100,000 ملف | ~5-7 أيام |

**ملاحظة:** الوقت يعتمد على:
- حجم الملفات
- عدد الصفحات
- جودة المسح الضوئي
- سرعة الإنترنت

## الدعم

إذا واجهت مشاكل:
1. راجع ملفات السجلات في `logs/`
2. تحقق من `ocr_tracking.db` للحالة
3. اطلع على README.md للتفاصيل الكاملة

## الأوامر المفيدة

```bash
# عرض المساعدة
python main.py --help

# تشغيل config للتحقق من الإعدادات
python config.py

# اختبار اتصال Google Drive
python -c "from src.google_drive_handler import test_connection; test_connection()"

# اختبار محرك OCR
python -c "from src.ocr_engine import test_ocr_engine; test_ocr_engine()"
```

---

**جاهز للبدء؟** 🎯

```bash
# ابدأ الآن!
python main.py --sync --process --limit 10
```

بالتوفيق! 🚀
