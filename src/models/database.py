"""
Database models for tracking OCR processing progress
Handles 100K+ files with resume capability
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import config

Base = declarative_base()


class PDFFile(Base):
    """Model for tracking PDF file processing"""
    __tablename__ = 'pdf_files'
    
    id = Column(Integer, primary_key=True)
    file_id = Column(String(255), unique=True, nullable=False, index=True)
    filename = Column(String(500), nullable=False)
    drive_path = Column(String(1000))
    file_size = Column(Integer)  # in bytes
    num_pages = Column(Integer)
    
    # Processing Status
    status = Column(String(50), default='pending', index=True)
    # Status options: pending, downloading, processing, completed, failed, quarantine
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    last_retry_at = Column(DateTime)
    
    # Processing Info
    retry_count = Column(Integer, default=0)
    processing_time = Column(Float)  # in seconds
    worker_id = Column(String(100))
    
    # Quality Metrics
    confidence_score = Column(Float)
    avg_page_confidence = Column(Float)
    low_confidence_pages = Column(Text)  # JSON array of page numbers
    
    # Output
    output_path_txt = Column(String(1000))
    output_path_docx = Column(String(1000))
    output_path_pdf = Column(String(1000))
    
    # Error Info
    error_message = Column(Text)
    error_type = Column(String(100))
    
    # Flags
    needs_manual_review = Column(Boolean, default=False)
    has_tables = Column(Boolean, default=False)
    has_images = Column(Boolean, default=False)
    is_multilingual = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<PDFFile(id={self.id}, filename={self.filename}, status={self.status})>"


class ProcessingStats(Base):
    """Model for overall processing statistics"""
    __tablename__ = 'processing_stats'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Counts
    total_files = Column(Integer, default=0)
    pending_files = Column(Integer, default=0)
    processing_files = Column(Integer, default=0)
    completed_files = Column(Integer, default=0)
    failed_files = Column(Integer, default=0)
    
    # Performance
    avg_processing_time = Column(Float)
    total_processing_time = Column(Float)
    avg_confidence = Column(Float)
    
    # Throughput
    files_per_hour = Column(Float)
    pages_per_hour = Column(Float)
    
    def __repr__(self):
        return f"<ProcessingStats(completed={self.completed_files}/{self.total_files})>"


class ErrorLog(Base):
    """Model for detailed error logging"""
    __tablename__ = 'error_logs'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    file_id = Column(String(255), index=True)
    filename = Column(String(500))
    error_type = Column(String(100), index=True)
    error_message = Column(Text)
    stack_trace = Column(Text)
    retry_attempt = Column(Integer)
    
    def __repr__(self):
        return f"<ErrorLog(file={self.filename}, type={self.error_type})>"


# Database initialization
engine = create_engine(config.DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(engine)
    print("✓ Database initialized successfully")


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_processing_stats(db):
    """Get current processing statistics"""
    from sqlalchemy import func
    
    total = db.query(PDFFile).count()
    pending = db.query(PDFFile).filter(PDFFile.status == 'pending').count()
    processing = db.query(PDFFile).filter(PDFFile.status == 'processing').count()
    completed = db.query(PDFFile).filter(PDFFile.status == 'completed').count()
    failed = db.query(PDFFile).filter(PDFFile.status == 'failed').count()
    
    avg_confidence = db.query(func.avg(PDFFile.confidence_score)).filter(
        PDFFile.status == 'completed'
    ).scalar() or 0
    
    avg_time = db.query(func.avg(PDFFile.processing_time)).filter(
        PDFFile.status == 'completed'
    ).scalar() or 0
    
    return {
        'total': total,
        'pending': pending,
        'processing': processing,
        'completed': completed,
        'failed': failed,
        'avg_confidence': round(avg_confidence, 2),
        'avg_processing_time': round(avg_time, 2),
        'completion_rate': round((completed / total * 100) if total > 0 else 0, 2)
    }


if __name__ == "__main__":
    init_db()
