"""
Arabic Legal Documents OCR System
Main application entry point for processing 100K+ PDF files
"""
import sys
import os
import argparse
from pathlib import Path
from datetime import datetime
import json
import time
from multiprocessing import Pool, cpu_count
from typing import List, Dict, Optional
import gc

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from loguru import logger
from tqdm import tqdm
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn

import config
from src.google_drive_handler import GoogleDriveHandler
from src.pdf_processor import PDFProcessor
from src.ocr_engine import OCREngine
from src.arabic_postprocessor import ArabicPostProcessor
from src.models.database import init_db, SessionLocal, PDFFile, get_processing_stats

console = Console()


class OCRProcessor:
    """Main OCR processing orchestrator"""
    
    def __init__(self, num_workers: int = None):
        """
        Initialize OCR processor
        
        Args:
            num_workers: Number of parallel workers (uses config if None)
        """
        self.num_workers = num_workers or config.NUM_WORKERS
        self.drive_handler = None
        self.pdf_processor = PDFProcessor()
        self.ocr_engine = OCREngine()
        self.arabic_processor = ArabicPostProcessor()
        
        # Initialize database
        init_db()
        
        # Configure logging
        self._setup_logging()
        
        logger.info(f"OCR Processor initialized with {self.num_workers} workers")
    
    def _setup_logging(self):
        """Setup logging configuration"""
        logger.remove()  # Remove default handler
        
        # Console logging
        if config.ENABLE_CONSOLE_LOG:
            logger.add(
                sys.stderr,
                level=config.LOG_LEVEL,
                format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
            )
        
        # File logging
        logger.add(
            config.LOG_FILE,
            rotation=config.LOG_ROTATION,
            retention=config.LOG_RETENTION,
            level=config.LOG_LEVEL,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}"
        )
        
        # Error logging
        logger.add(
            config.ERROR_LOG_FILE,
            level="ERROR",
            rotation=config.LOG_ROTATION,
            retention=config.LOG_RETENTION
        )
    
    def initialize_google_drive(self):
        """Initialize Google Drive connection"""
        logger.info("Initializing Google Drive connection...")
        self.drive_handler = GoogleDriveHandler()
        logger.info("✓ Google Drive connection established")
    
    def sync_files_from_drive(self) -> int:
        """
        Sync PDF files list from Google Drive to database
        
        Returns:
            Number of files synced
        """
        if not self.drive_handler:
            self.initialize_google_drive()
        
        logger.info("Syncing files from Google Drive...")
        db = SessionLocal()
        
        try:
            synced_count = 0
            
            # Stream files in chunks to avoid memory issues
            for file_chunk in self.drive_handler.stream_file_list(chunk_size=100):
                for file_info in file_chunk:
                    file_id = file_info['id']
                    
                    # Check if file already exists in database
                    existing = db.query(PDFFile).filter(PDFFile.file_id == file_id).first()
                    
                    if not existing:
                        pdf_file = PDFFile(
                            file_id=file_id,
                            filename=file_info['name'],
                            file_size=int(file_info.get('size', 0)),
                            drive_path=file_info.get('parents', [''])[0] if file_info.get('parents') else '',
                            status='pending'
                        )
                        db.add(pdf_file)
                        synced_count += 1
                    
                    # Commit in batches
                    if synced_count % 100 == 0:
                        db.commit()
                        logger.info(f"Synced {synced_count} files...")
            
            db.commit()
            logger.info(f"✓ Synced {synced_count} new files from Google Drive")
            return synced_count
            
        except Exception as e:
            logger.error(f"Error syncing files: {e}")
            db.rollback()
            raise
        finally:
            db.close()
    
    def process_single_file(self, pdf_record: PDFFile) -> Dict:
        """
        Process a single PDF file
        
        Args:
            pdf_record: PDFFile database record
            
        Returns:
            Processing result dictionary
        """
        start_time = time.time()
        db = SessionLocal()
        
        try:
            # Update status
            pdf_record.status = 'processing'
            pdf_record.started_at = datetime.utcnow()
            db.merge(pdf_record)
            db.commit()
            
            logger.info(f"Processing: {pdf_record.filename}")
            
            # 1. Download file from Google Drive
            if not self.drive_handler:
                self.initialize_google_drive()
            
            pdf_path = self.drive_handler.download_file(
                pdf_record.file_id,
                pdf_record.filename,
                config.TEMP_DIR
            )
            
            # 2. Convert PDF to images
            images = self.pdf_processor.pdf_to_images(pdf_path)
            pdf_record.num_pages = len(images)
            
            # 3. Run OCR on images
            ocr_results = self.ocr_engine.process_batch(images)
            
            # 4. Post-process Arabic text
            processed_texts = []
            for result in ocr_results:
                processed_text = self.arabic_processor.process(result['text'])
                processed_texts.append(processed_text)
            
            # Combine all pages
            full_text = '\n\n--- Page Break ---\n\n'.join(processed_texts)
            
            # 5. Calculate confidence metrics
            metrics = self.ocr_engine.extract_confidence_metrics(ocr_results)
            pdf_record.confidence_score = metrics['avg_confidence']
            pdf_record.avg_page_confidence = metrics['avg_confidence']
            pdf_record.low_confidence_pages = json.dumps(metrics['low_confidence_pages'])
            pdf_record.needs_manual_review = metrics['needs_review']
            
            # 6. Save outputs
            output_base = config.OUTPUT_DIR / pdf_record.filename.replace('.pdf', '')
            
            # Save as TXT
            if 'txt' in config.OUTPUT_FORMATS:
                txt_path = output_base.with_suffix('.txt')
                txt_path.write_text(full_text, encoding='utf-8')
                pdf_record.output_path_txt = str(txt_path)
            
            # Save as DOCX
            if 'docx' in config.OUTPUT_FORMATS:
                try:
                    from docx import Document
                    docx_path = output_base.with_suffix('.docx')
                    doc = Document()
                    doc.add_paragraph(full_text)
                    doc.save(str(docx_path))
                    pdf_record.output_path_docx = str(docx_path)
                except Exception as e:
                    logger.warning(f"Could not create DOCX: {e}")
            
            # Update status
            processing_time = time.time() - start_time
            pdf_record.status = 'completed'
            pdf_record.completed_at = datetime.utcnow()
            pdf_record.processing_time = processing_time
            
            db.merge(pdf_record)
            db.commit()
            
            # Clean up temp file
            if config.CLEAR_TEMP_FILES:
                pdf_path.unlink()
            
            logger.info(f"✓ Completed: {pdf_record.filename} ({processing_time:.1f}s, confidence: {metrics['avg_confidence']:.2f})")
            
            return {
                'success': True,
                'filename': pdf_record.filename,
                'pages': len(images),
                'confidence': metrics['avg_confidence'],
                'processing_time': processing_time
            }
            
        except Exception as e:
            logger.error(f"Error processing {pdf_record.filename}: {e}")
            
            # Update error status
            pdf_record.status = 'failed'
            pdf_record.error_message = str(e)
            pdf_record.retry_count += 1
            pdf_record.last_retry_at = datetime.utcnow()
            
            db.merge(pdf_record)
            db.commit()
            
            return {
                'success': False,
                'filename': pdf_record.filename,
                'error': str(e)
            }
            
        finally:
            db.close()
            # Force garbage collection
            gc.collect()
    
    def process_batch(self, batch_size: int = None, limit: int = None):
        """
        Process a batch of PDF files
        
        Args:
            batch_size: Number of files to process in parallel
            limit: Maximum number of files to process (None for all)
        """
        batch_size = batch_size or config.BATCH_SIZE
        
        db = SessionLocal()
        
        try:
            # Get pending files
            query = db.query(PDFFile).filter(PDFFile.status == 'pending')
            
            if limit:
                query = query.limit(limit)
            
            pending_files = query.all()
            total_files = len(pending_files)
            
            if total_files == 0:
                logger.info("No pending files to process")
                return
            
            logger.info(f"Starting batch processing of {total_files} files")
            
            # Process with progress bar
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeRemainingColumn(),
                console=console
            ) as progress:
                
                task = progress.add_task(f"[cyan]Processing PDFs...", total=total_files)
                
                for i in range(0, total_files, batch_size):
                    batch = pending_files[i:i + batch_size]
                    
                    for pdf_file in batch:
                        result = self.process_single_file(pdf_file)
                        progress.update(task, advance=1)
                        
                        # Run GC every 100 files
                        if (i + 1) % config.AUTO_GC_INTERVAL == 0:
                            gc.collect()
            
            logger.info(f"✓ Batch processing completed")
            
            # Show statistics
            self.show_statistics()
            
        finally:
            db.close()
    
    def show_statistics(self):
        """Display processing statistics"""
        db = SessionLocal()
        
        try:
            stats = get_processing_stats(db)
            
            table = Table(title="Processing Statistics")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("Total Files", str(stats['total']))
            table.add_row("Pending", str(stats['pending']))
            table.add_row("Processing", str(stats['processing']))
            table.add_row("Completed", str(stats['completed']))
            table.add_row("Failed", str(stats['failed']))
            table.add_row("Completion Rate", f"{stats['completion_rate']}%")
            table.add_row("Avg Confidence", f"{stats['avg_confidence']:.2f}")
            table.add_row("Avg Processing Time", f"{stats['avg_processing_time']:.2f}s")
            
            console.print(table)
            
        finally:
            db.close()
    
    def retry_failed_files(self, max_retries: int = None):
        """Retry processing failed files"""
        max_retries = max_retries or config.MAX_RETRIES
        
        db = SessionLocal()
        
        try:
            failed_files = db.query(PDFFile).filter(
                PDFFile.status == 'failed',
                PDFFile.retry_count < max_retries
            ).all()
            
            logger.info(f"Retrying {len(failed_files)} failed files")
            
            for pdf_file in failed_files:
                # Reset status to pending
                pdf_file.status = 'pending'
                db.merge(pdf_file)
            
            db.commit()
            
            # Process them
            self.process_batch()
            
        finally:
            db.close()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Arabic Legal Documents OCR System')
    parser.add_argument('--sync', action='store_true', help='Sync files from Google Drive')
    parser.add_argument('--process', action='store_true', help='Process pending files')
    parser.add_argument('--stats', action='store_true', help='Show processing statistics')
    parser.add_argument('--retry', action='store_true', help='Retry failed files')
    parser.add_argument('--limit', type=int, help='Limit number of files to process')
    parser.add_argument('--workers', type=int, help='Number of parallel workers')
    parser.add_argument('--batch-size', type=int, help='Batch size for processing')
    
    args = parser.parse_args()
    
    # Show config
    console.print("\n[bold cyan]Arabic Legal Documents OCR System[/bold cyan]")
    console.print(f"OCR Engine: {config.OCR_ENGINE}")
    console.print(f"GPU Enabled: {config.PADDLE_USE_GPU}")
    console.print(f"Workers: {args.workers or config.NUM_WORKERS}")
    console.print(f"Batch Size: {args.batch_size or config.BATCH_SIZE}\n")
    
    # Initialize processor
    processor = OCRProcessor(num_workers=args.workers)
    
    try:
        if args.sync:
            processor.sync_files_from_drive()
        
        if args.process:
            processor.process_batch(
                batch_size=args.batch_size,
                limit=args.limit
            )
        
        if args.retry:
            processor.retry_failed_files()
        
        if args.stats or (not args.sync and not args.process and not args.retry):
            processor.show_statistics()
    
    except KeyboardInterrupt:
        logger.warning("\n⚠ Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"✗ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
