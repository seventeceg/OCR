# نظام OCR للمستندات القانونية العربية / Arabic Legal Documents OCR System

نظام متقدم لتحويل أكثر من 100,000 ملف PDF من المستندات القانونية العربية إلى نصوص قابلة للبحث والتحرير باستخدام تقنيات التعلم العميق ومعالجة GPU.

An advanced system for converting 100K+ Arabic legal PDF documents to searchable and editable text using deep learning and GPU acceleration.

## ⭐ المميزات الرئيسية / Key Features

### 🚀 الأداء العالي / High Performance
- **معالجة موزعة** مع دعم Multi-processing
- **تسريع GPU** باستخدام CUDA
- **معالجة دفعية** Batch Processing محسّنة
- **إدارة ذاكرة ذكية** لمعالجة آلاف الملفات

### 🎯 دقة عالية للنصوص العربية / High Accuracy for Arabic
- **PaddleOCR** المُحسّن للغة العربية
- **معالجة مسبقة متقدمة** للصور (denoising, deskewing, enhancement)
- **تصحيح تلقائي** للأخطاء الشائعة في OCR العربي
- **معالجة خاصة** للمستندات القانونية

### 📊 إدارة وتتبع / Management & Tracking
- **قاعدة بيانات SQLite** لتتبع التقدم
- **استكمال تلقائي** بعد الانقطاع
- **إعادة محاولة ذكية** للملفات الفاشلة
- **تقارير مفصلة** عن الأداء والدقة

### 🔗 تكامل Google Drive / Google Drive Integration
- **مزامنة تلقائية** مع Google Drive
- **تنزيل ذكي** مع تخزين مؤقت
- **معالجة مباشرة** من السحابة

### 📁 صيغ متعددة / Multiple Output Formats
- **TXT** - نص خام
- **DOCX** - مستند Word
- **Searchable PDF** - PDF قابل للبحث (قريباً)

## 🛠️ المتطلبات / Requirements

### النظام / System
- **Python** 3.8+
- **GPU** مع CUDA (موصى به: 40GB VRAM)
- **RAM** 16GB+ (موصى به: 256GB للمعالجة الموازية)
- **Storage** مساحة كافية للملفات المؤقتة والمخرجات

### المكتبات / Libraries
جميع المكتبات موجودة في `requirements.txt`

## 📦 التثبيت / Installation

### 1. استنساخ المشروع / Clone Repository
```bash
git clone <repository-url>
cd ocr
```

### 2. إنشاء بيئة افتراضية / Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # على Linux/Mac
# أو / or
venv\Scripts\activate  # على Windows
```

### 3. تثبيت المتطلبات / Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. تثبيت Poppler (لـ pdf2image)
**على Ubuntu/Debian:**
```bash
sudo apt-get install poppler-utils
```

**على macOS:**
```bash
brew install poppler
```

**على Windows:**
قم بتحميل Poppler من [هنا](https://github.com/oschwartz10612/poppler-windows/releases/)

### 5. إعداد Google Drive API

1. انتقل إلى [Google Cloud Console](https://console.cloud.google.com/)
2. أنشئ مشروع جديد
3. فعّل Google Drive API
4. أنشئ OAuth 2.0 credentials
5. حمّل ملف `credentials.json` وضعه في مجلد المشروع

### 6. إعداد المتغيرات البيئية / Configure Environment

أنشئ ملف `.env`:
```bash
GOOGLE_DRIVE_FOLDER_ID=your_folder_id_here
GOOGLE_CREDENTIALS_PATH=credentials.json
```

## 🚀 الاستخدام / Usage

### 1. مزامنة الملفات من Google Drive
```bash
python main.py --sync
```

### 2. معالجة الملفات / Process Files
```bash
# معالجة جميع الملفات المعلقة
python main.py --process

# معالجة عدد محدد من الملفات
python main.py --process --limit 100

# تخصيص عدد الـ workers وحجم الدفعة
python main.py --process --workers 8 --batch-size 32
```

### 3. عرض الإحصائيات / Show Statistics
```bash
python main.py --stats
```

### 4. إعادة معالجة الملفات الفاشلة / Retry Failed Files
```bash
python main.py --retry
```

### 5. سير عمل كامل / Complete Workflow
```bash
# 1. مزامنة من Drive
python main.py --sync

# 2. معالجة الملفات
python main.py --process

# 3. عرض النتائج
python main.py --stats
```

## ⚙️ الإعدادات / Configuration

يمكنك تخصيص الإعدادات في ملف `config.py`:

### إعدادات الأداء / Performance Settings
```python
NUM_WORKERS = 4          # عدد workers المتوازية
BATCH_SIZE = 16          # حجم الدفعة
IMAGE_DPI = 300          # دقة الصورة (300-400 للمستندات القانونية)
PADDLE_GPU_MEM = 8000    # ذاكرة GPU لكل عملية (MB)
```

### إعدادات OCR / OCR Settings
```python
OCR_ENGINE = "paddleocr"           # المحرك: paddleocr, easyocr, tesseract
PADDLE_USE_GPU = True              # استخدام GPU
OCR_LANGUAGES = ['ar', 'en']       # اللغات المدعومة
```

### إعدادات المعالجة / Processing Settings
```python
ENHANCE_IMAGE = True               # تحسين الصورة
DENOISE = True                     # إزالة الضوضاء
DESKEW = True                      # تصحيح الانحراف
BINARIZATION = True                # التحويل للأبيض والأسود
```

### إعدادات النص العربي / Arabic Text Settings
```python
NORMALIZE_NUMBERS = True           # توحيد الأرقام
FIX_ARABIC_LIGATURES = True        # إصلاح الحروف المتصلة
CORRECT_COMMON_ERRORS = True       # تصحيح الأخطاء الشائعة
REMOVE_DIACRITICS = False          # إزالة التشكيل (False للدقة القانونية)
```

## 📊 هيكل المشروع / Project Structure

```
ocr/
├── main.py                    # نقطة الدخول الرئيسية
├── config.py                  # ملف الإعدادات
├── requirements.txt           # المكتبات المطلوبة
├── README.md                  # هذا الملف
├── src/                       # الكود المصدري
│   ├── __init__.py
│   ├── google_drive_handler.py    # معالج Google Drive
│   ├── pdf_processor.py            # معالج PDF
│   ├── ocr_engine.py               # محرك OCR
│   ├── arabic_postprocessor.py    # معالج النص العربي
│   └── models/
│       ├── __init__.py
│       └── database.py            # نماذج قاعدة البيانات
├── data/                      # البيانات
│   ├── input/                 # ملفات الإدخال المؤقتة
│   ├── output/                # الملفات المحولة
│   ├── temp/                  # ملفات مؤقتة
│   └── quarantine/            # ملفات بها مشاكل
├── logs/                      # ملفات السجلات
└── models/                    # نماذج ML المحملة
```

## 🎯 أمثلة الاستخدام / Usage Examples

### مثال 1: معالجة سريعة لعدد محدود
```bash
python main.py --sync --process --limit 10
```

### مثال 2: معالجة بالحد الأقصى للأداء
```bash
python main.py --process --workers 8 --batch-size 32
```

### مثال 3: معالجة مع استكمال تلقائي
```bash
# سيستكمل تلقائياً من حيث توقف
python main.py --process
```

## 📈 الأداء المتوقع / Expected Performance

### على GPU 40GB مع RAM 256GB:

- **السرعة**: ~10-20 ملف PDF/دقيقة (حسب حجم الملف)
- **الدقة**: 92-98% للنصوص العربية الواضحة
- **الذاكرة**: ~2-4 GB لكل worker
- **الوقت المقدر لـ 100K ملف**: 3-7 أيام بمعالجة مستمرة

### العوامل المؤثرة:
- جودة المستندات الأصلية
- عدد الصفحات لكل ملف
- تعقيد التخطيط (جداول، صور، أعمدة متعددة)
- سرعة الإنترنت (للتنزيل من Drive)

## 🔍 حل المشاكل / Troubleshooting

### مشكلة: Out of Memory
```python
# في config.py قلل:
NUM_WORKERS = 2
BATCH_SIZE = 8
PADDLE_GPU_MEM = 4000
```

### مشكلة: دقة منخفضة
```python
# في config.py زد:
IMAGE_DPI = 400
ENHANCE_IMAGE = True
OCR_ENGINE = "ensemble"  # استخدام عدة محركات
```

### مشكلة: بطء المعالجة
```python
# تحقق من:
PADDLE_USE_GPU = True        # تأكد من تفعيل GPU
PADDLE_ENABLE_MKLDNN = True  # تسريع CPU
CLEAR_TEMP_FILES = True      # حذف الملفات المؤقتة
```

## 📝 الملاحظات / Notes

### للمستندات القانونية:
- ✅ احتفظ بالتشكيل (`REMOVE_DIACRITICS = False`)
- ✅ فعّل التحقق من الصحة (`VALIDATE_ARABIC = True`)
- ✅ احفظ البيانات الوصفية (`SAVE_METADATA = True`)
- ✅ استخرج أرقام المواد (`EXTRACT_ARTICLE_NUMBERS = True`)

### للأداء الأمثل:
- استخدم SSD للتخزين المؤقت
- ضع الملفات المؤقتة على قرص منفصل
- راقب استخدام GPU memory
- نظف temp directory دورياً

## 🤝 المساهمة / Contributing

المساهمات مرحب بها! يرجى:
1. Fork المشروع
2. إنشاء فرع للميزة الجديدة
3. Commit التغييرات
4. Push للفرع
5. فتح Pull Request

## 📄 الترخيص / License

MIT License - انظر ملف LICENSE للتفاصيل

## 🆘 الدعم / Support

للأسئلة والدعم:
- افتح Issue على GitHub
- راجع ملفات السجلات في `logs/`
- تحقق من قاعدة البيانات للإحصائيات

## 🙏 شكر وتقدير / Acknowledgments

- **PaddleOCR** - محرك OCR الممتاز
- **PyMuPDF** - معالجة PDF السريعة
- **OpenCV** - معالجة الصور
- **Google Drive API** - التكامل السحابي

---

**ملاحظة هامة**: هذا النظام مصمم خصيصاً للمستندات القانونية العربية ويتطلب موارد حاسوبية كبيرة لمعالجة 100K+ ملف. تأكد من توفر الموارد اللازمة قبل البدء.

**Important Note**: This system is specifically designed for Arabic legal documents and requires significant computational resources to process 100K+ files. Ensure you have the necessary resources before starting.
