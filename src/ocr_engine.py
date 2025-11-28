"""
OCR Engine optimized for Arabic legal documents
Supports PaddleOCR, EasyOCR, and Tesseract with GPU acceleration
"""
import os
import numpy as np
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from loguru import logger
import config

# Set GPU device
os.environ['CUDA_VISIBLE_DEVICES'] = config.CUDA_VISIBLE_DEVICES


class OCREngine:
    """Main OCR engine with multiple backend support"""
    
    def __init__(self, engine: str = None, use_gpu: bool = True):
        """
        Initialize OCR engine
        
        Args:
            engine: OCR engine to use (paddleocr, easyocr, tesseract, ensemble)
            use_gpu: Whether to use GPU acceleration
        """
        self.engine_name = engine or config.OCR_ENGINE
        self.use_gpu = use_gpu and config.PADDLE_USE_GPU
        self.ocr = None
        
        logger.info(f"Initializing OCR engine: {self.engine_name} (GPU: {self.use_gpu})")
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Initialize the selected OCR engine"""
        if self.engine_name == "paddleocr":
            self._init_paddleocr()
        elif self.engine_name == "easyocr":
            self._init_easyocr()
        elif self.engine_name == "tesseract":
            self._init_tesseract()
        elif self.engine_name == "ensemble":
            self._init_ensemble()
        else:
            raise ValueError(f"Unknown OCR engine: {self.engine_name}")
    
    def _init_paddleocr(self):
        """Initialize PaddleOCR (Best for Arabic)"""
        try:
            from paddleocr import PaddleOCR
            
            self.ocr = PaddleOCR(
                use_angle_cls=True,  # Enable angle classification
                lang='arabic',  # Arabic language model
                use_gpu=self.use_gpu,
                gpu_mem=config.PADDLE_GPU_MEM,
                enable_mkldnn=config.PADDLE_ENABLE_MKLDNN,
                use_tensorrt=config.PADDLE_USE_TENSORRT,
                det_db_thresh=config.PADDLE_DET_DB_THRESH,
                det_db_box_thresh=config.PADDLE_DET_DB_BOX_THRESH,
                rec_batch_num=config.PADDLE_REC_BATCH_NUM,
                show_log=False
            )
            
            logger.info("✓ PaddleOCR initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize PaddleOCR: {e}")
            raise
    
    def _init_easyocr(self):
        """Initialize EasyOCR"""
        try:
            import easyocr
            
            self.ocr = easyocr.Reader(
                lang_list=['ar', 'en'],
                gpu=self.use_gpu,
                verbose=False
            )
            
            logger.info("✓ EasyOCR initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize EasyOCR: {e}")
            raise
    
    def _init_tesseract(self):
        """Initialize Tesseract"""
        try:
            import pytesseract
            
            # Check if Tesseract is installed
            try:
                pytesseract.get_tesseract_version()
                self.ocr = pytesseract
                logger.info("✓ Tesseract initialized successfully")
            except:
                raise RuntimeError("Tesseract not installed. Install it first.")
                
        except Exception as e:
            logger.error(f"Failed to initialize Tesseract: {e}")
            raise
    
    def _init_ensemble(self):
        """Initialize ensemble of multiple OCR engines"""
        logger.info("Initializing ensemble OCR (PaddleOCR + EasyOCR)")
        self._init_paddleocr()
        
        try:
            import easyocr
            self.ocr_secondary = easyocr.Reader(['ar', 'en'], gpu=self.use_gpu, verbose=False)
        except:
            logger.warning("Could not initialize secondary OCR engine")
            self.ocr_secondary = None
    
    def process_image(self, image: np.ndarray) -> Dict:
        """
        Process a single image and extract text
        
        Args:
            image: Image as numpy array
            
        Returns:
            Dictionary with extracted text and metadata
        """
        if self.engine_name == "paddleocr":
            return self._process_paddleocr(image)
        elif self.engine_name == "easyocr":
            return self._process_easyocr(image)
        elif self.engine_name == "tesseract":
            return self._process_tesseract(image)
        elif self.engine_name == "ensemble":
            return self._process_ensemble(image)
    
    def _process_paddleocr(self, image: np.ndarray) -> Dict:
        """Process image with PaddleOCR"""
        try:
            result = self.ocr.ocr(image, cls=True)
            
            if not result or not result[0]:
                return {
                    'text': '',
                    'lines': [],
                    'confidence': 0.0
                }
            
            lines = []
            all_confidences = []
            
            for line in result[0]:
                bbox = line[0]
                text = line[1][0]
                confidence = line[1][1]
                
                lines.append({
                    'text': text,
                    'bbox': bbox,
                    'confidence': confidence
                })
                all_confidences.append(confidence)
            
            # Sort lines by vertical position (top to bottom)
            lines.sort(key=lambda x: x['bbox'][0][1])
            
            # Combine all text
            full_text = '\n'.join([line['text'] for line in lines])
            
            # Calculate average confidence
            avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
            
            return {
                'text': full_text,
                'lines': lines,
                'confidence': avg_confidence,
                'engine': 'paddleocr'
            }
            
        except Exception as e:
            logger.error(f"PaddleOCR processing error: {e}")
            return {'text': '', 'lines': [], 'confidence': 0.0}
    
    def _process_easyocr(self, image: np.ndarray) -> Dict:
        """Process image with EasyOCR"""
        try:
            result = self.ocr.readtext(image)
            
            if not result:
                return {
                    'text': '',
                    'lines': [],
                    'confidence': 0.0
                }
            
            lines = []
            all_confidences = []
            
            for detection in result:
                bbox = detection[0]
                text = detection[1]
                confidence = detection[2]
                
                lines.append({
                    'text': text,
                    'bbox': bbox,
                    'confidence': confidence
                })
                all_confidences.append(confidence)
            
            # Sort lines by vertical position
            lines.sort(key=lambda x: x['bbox'][0][1])
            
            # Combine text
            full_text = '\n'.join([line['text'] for line in lines])
            
            avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
            
            return {
                'text': full_text,
                'lines': lines,
                'confidence': avg_confidence,
                'engine': 'easyocr'
            }
            
        except Exception as e:
            logger.error(f"EasyOCR processing error: {e}")
            return {'text': '', 'lines': [], 'confidence': 0.0}
    
    def _process_tesseract(self, image: np.ndarray) -> Dict:
        """Process image with Tesseract"""
        try:
            import pytesseract
            from PIL import Image
            
            # Convert numpy array to PIL Image
            if len(image.shape) == 2:
                pil_image = Image.fromarray(image, mode='L')
            else:
                pil_image = Image.fromarray(image)
            
            # Get text with confidence
            data = pytesseract.image_to_data(
                pil_image,
                lang='ara+eng',
                output_type=pytesseract.Output.DICT
            )
            
            lines = []
            all_confidences = []
            
            for i in range(len(data['text'])):
                text = data['text'][i].strip()
                if text:
                    conf = float(data['conf'][i])
                    if conf > 0:
                        lines.append({
                            'text': text,
                            'confidence': conf / 100.0
                        })
                        all_confidences.append(conf / 100.0)
            
            full_text = pytesseract.image_to_string(pil_image, lang='ara+eng')
            
            avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
            
            return {
                'text': full_text,
                'lines': lines,
                'confidence': avg_confidence,
                'engine': 'tesseract'
            }
            
        except Exception as e:
            logger.error(f"Tesseract processing error: {e}")
            return {'text': '', 'lines': [], 'confidence': 0.0}
    
    def _process_ensemble(self, image: np.ndarray) -> Dict:
        """Process with ensemble (multiple engines and voting)"""
        # Primary: PaddleOCR
        result_paddle = self._process_paddleocr(image)
        
        # If confidence is high enough, return immediately
        if result_paddle['confidence'] > 0.9:
            return result_paddle
        
        # If low confidence, try secondary engine
        if self.ocr_secondary:
            result_easy = self._process_easyocr(image)
            
            # Return result with higher confidence
            if result_easy['confidence'] > result_paddle['confidence']:
                return result_easy
        
        return result_paddle
    
    def process_batch(self, images: List[np.ndarray]) -> List[Dict]:
        """
        Process multiple images in batch (GPU optimized)
        
        Args:
            images: List of images as numpy arrays
            
        Returns:
            List of OCR results
        """
        results = []
        batch_size = config.BATCH_SIZE
        
        for i in range(0, len(images), batch_size):
            batch = images[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1} ({len(batch)} images)")
            
            for img in batch:
                result = self.process_image(img)
                results.append(result)
        
        return results
    
    def extract_confidence_metrics(self, results: List[Dict]) -> Dict:
        """
        Extract confidence metrics from OCR results
        
        Args:
            results: List of OCR results
            
        Returns:
            Dictionary with confidence metrics
        """
        if not results:
            return {
                'avg_confidence': 0.0,
                'min_confidence': 0.0,
                'max_confidence': 0.0,
                'low_confidence_pages': []
            }
        
        confidences = [r['confidence'] for r in results]
        low_conf_pages = [i+1 for i, c in enumerate(confidences) 
                         if c < config.MIN_CONFIDENCE_THRESHOLD]
        
        return {
            'avg_confidence': sum(confidences) / len(confidences),
            'min_confidence': min(confidences),
            'max_confidence': max(confidences),
            'low_confidence_pages': low_conf_pages,
            'needs_review': len(low_conf_pages) > 0
        }


def test_ocr_engine():
    """Test OCR engine with sample image"""
    try:
        engine = OCREngine()
        logger.info("✓ OCR Engine test successful")
        return True
    except Exception as e:
        logger.error(f"✗ OCR Engine test failed: {e}")
        return False


if __name__ == "__main__":
    test_ocr_engine()
