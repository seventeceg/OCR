"""
Configuration for Arabic Legal Documents OCR System
Optimized for 100K+ PDF files with GPU acceleration
"""
import os
from pathlib import Path

# Base Directories
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
INPUT_DIR = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"
TEMP_DIR = DATA_DIR / "temp"
LOGS_DIR = BASE_DIR / "logs"
MODELS_DIR = BASE_DIR / "models"

# Create directories
for dir_path in [INPUT_DIR, OUTPUT_DIR, TEMP_DIR, LOGS_DIR, MODELS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Google Drive Configuration
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "1ErvlZ739ZMK8gMj-0xkIujtjnpWSs1H2")
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "client.json")
GOOGLE_TOKEN_PATH = "token.pickle"

# OCR Engine Settings
OCR_ENGINE = "paddleocr"  # Options: paddleocr, easyocr, tesseract, ensemble
OCR_LANGUAGES = ['ar', 'en']  # Arabic + English for mixed documents

# PaddleOCR Settings (Best for Arabic)
PADDLE_USE_GPU = True
PADDLE_GPU_MEM = 8000  # MB per process
PADDLE_ENABLE_MKLDNN = True
PADDLE_USE_TENSORRT = False
PADDLE_DET_DB_THRESH = 0.3
PADDLE_DET_DB_BOX_THRESH = 0.5
PADDLE_REC_BATCH_NUM = 32  # Increased for GPU utilization

# Image Processing Settings
IMAGE_DPI = 300  # DPI for PDF to image conversion (300-400 for legal docs)
IMAGE_FORMAT = "PNG"
ENHANCE_IMAGE = True
DENOISE = True
DESKEW = True
BINARIZATION = True
CONTRAST_ENHANCEMENT = True

# Performance Settings
NUM_WORKERS = 4  # Number of parallel workers
BATCH_SIZE = 16  # Files processed per batch
MAX_PAGES_PER_PDF = 1000  # Safety limit
PREFETCH_COUNT = 20  # Files to prefetch from Drive

# GPU Settings
CUDA_VISIBLE_DEVICES = "0"  # GPU device ID
GPU_MEMORY_FRACTION = 0.9  # Use 90% of GPU memory
ENABLE_MIXED_PRECISION = True

# Database Settings
DATABASE_URL = f"sqlite:///{BASE_DIR}/ocr_tracking.db"
TRACK_PROGRESS = True
AUTO_RESUME = True

# Queue Settings (for distributed processing)
USE_QUEUE = True
QUEUE_BACKEND = "sqlite"  # Options: sqlite, redis
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0

# Retry Settings
MAX_RETRIES = 3
RETRY_DELAY = 60  # seconds
RETRY_BACKOFF = 2  # exponential backoff multiplier

# Output Settings
OUTPUT_FORMATS = ["txt", "docx", "searchable_pdf"]  # Formats to generate
SAVE_IMAGES = False  # Save intermediate images (consumes storage)
SAVE_METADATA = True  # Save processing metadata
PRESERVE_LAYOUT = True  # Maintain document structure

# Legal Document Specific Settings
EXTRACT_ARTICLE_NUMBERS = True  # Extract article/clause numbers
EXTRACT_DATES = True  # Extract and format dates
EXTRACT_TABLES = True  # Special handling for tables
VALIDATE_ARABIC = True  # Validate Arabic text correctness
FIX_ARABIC_LIGATURES = True  # Fix Arabic ligature issues

# Text Post-Processing
REMOVE_DIACRITICS = False  # Keep diacritics for legal accuracy
NORMALIZE_NUMBERS = True  # Normalize Arabic/English numbers
FIX_SPACING = True  # Fix spacing issues
CORRECT_COMMON_ERRORS = True  # Fix common OCR errors

# Logging Settings
LOG_LEVEL = "INFO"
LOG_FILE = LOGS_DIR / "ocr_processing.log"
LOG_ROTATION = "100 MB"
LOG_RETENTION = "30 days"
ENABLE_CONSOLE_LOG = True

# Performance Monitoring
TRACK_PROCESSING_TIME = True
TRACK_ACCURACY_METRICS = True
GENERATE_REPORT = True

# Error Handling
CONTINUE_ON_ERROR = True  # Continue processing even if some files fail
ERROR_LOG_FILE = LOGS_DIR / "errors.log"
QUARANTINE_FAILED_FILES = True
QUARANTINE_DIR = DATA_DIR / "quarantine"

# Memory Management
CLEAR_TEMP_FILES = True  # Clear temp files after processing
MAX_MEMORY_PER_PROCESS = 8  # GB
AUTO_GC_INTERVAL = 100  # Run garbage collection every N files

# Quality Assurance
MIN_CONFIDENCE_THRESHOLD = 0.7  # Minimum OCR confidence score
FLAG_LOW_CONFIDENCE = True  # Flag files with low confidence
MANUAL_REVIEW_THRESHOLD = 0.5  # Threshold for manual review queue

# Print Configuration Summary
def print_config():
    print("=" * 60)
    print("OCR Configuration Summary")
    print("=" * 60)
    print(f"OCR Engine: {OCR_ENGINE}")
    print(f"GPU Enabled: {PADDLE_USE_GPU}")
    print(f"Number of Workers: {NUM_WORKERS}")
    print(f"Batch Size: {BATCH_SIZE}")
    print(f"Image DPI: {IMAGE_DPI}")
    print(f"Output Formats: {', '.join(OUTPUT_FORMATS)}")
    print(f"Database: {DATABASE_URL}")
    print(f"Queue Backend: {QUEUE_BACKEND}")
    print("=" * 60)

if __name__ == "__main__":
    print_config()
