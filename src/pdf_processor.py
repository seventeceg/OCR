"""
PDF Processor with advanced image enhancement
Optimized for Arabic legal documents with high accuracy requirements
"""
import fitz  # PyMuPDF
from pdf2image import convert_from_path
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional
from loguru import logger
import config


class PDFProcessor:
    """Process PDF files and convert to high-quality images for OCR"""
    
    def __init__(self, dpi: int = None, enhance: bool = True):
        """
        Initialize PDF processor
        
        Args:
            dpi: DPI for image conversion (uses config value if None)
            enhance: Whether to apply image enhancements
        """
        self.dpi = dpi or config.IMAGE_DPI
        self.enhance = enhance
    
    def get_page_count(self, pdf_path: Path) -> int:
        """Get number of pages in PDF"""
        try:
            doc = fitz.open(str(pdf_path))
            count = doc.page_count
            doc.close()
            return count
        except Exception as e:
            logger.error(f"Error getting page count from {pdf_path}: {e}")
            raise
    
    def pdf_to_images(self, pdf_path: Path, output_dir: Optional[Path] = None) -> List[np.ndarray]:
        """
        Convert PDF to high-quality images
        
        Args:
            pdf_path: Path to PDF file
            output_dir: Optional directory to save images
            
        Returns:
            List of images as numpy arrays
        """
        logger.info(f"Converting PDF to images: {pdf_path.name}")
        
        try:
            # Convert PDF to images using pdf2image (high quality)
            images = convert_from_path(
                str(pdf_path),
                dpi=self.dpi,
                fmt=config.IMAGE_FORMAT.lower(),
                thread_count=4,  # Parallel conversion
                use_pdftocairo=True  # Better quality
            )
            
            logger.info(f"✓ Converted {len(images)} pages to images")
            
            # Convert PIL images to numpy arrays
            image_arrays = []
            for idx, img in enumerate(images):
                # Convert to numpy array
                img_array = np.array(img)
                
                # Apply enhancements if enabled
                if self.enhance:
                    img_array = self.enhance_image(img_array, page_num=idx+1)
                
                image_arrays.append(img_array)
                
                # Optionally save images
                if output_dir and config.SAVE_IMAGES:
                    output_path = output_dir / f"page_{idx+1:04d}.{config.IMAGE_FORMAT.lower()}"
                    Image.fromarray(img_array).save(output_path)
            
            return image_arrays
            
        except Exception as e:
            logger.error(f"Error converting PDF to images: {e}")
            raise
    
    def enhance_image(self, image: np.ndarray, page_num: int = 0) -> np.ndarray:
        """
        Apply image enhancement techniques for better OCR
        
        Args:
            image: Input image as numpy array
            page_num: Page number (for logging)
            
        Returns:
            Enhanced image as numpy array
        """
        try:
            # Convert to grayscale if color
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                gray = image.copy()
            
            # 1. Denoise
            if config.DENOISE:
                gray = cv2.fastNlMeansDenoising(gray, None, h=10, templateWindowSize=7, searchWindowSize=21)
            
            # 2. Deskew (straighten rotated text)
            if config.DESKEW:
                gray = self.deskew_image(gray)
            
            # 3. Contrast enhancement
            if config.CONTRAST_ENHANCEMENT:
                gray = self.enhance_contrast(gray)
            
            # 4. Binarization (convert to black and white)
            if config.BINARIZATION:
                gray = self.adaptive_threshold(gray)
            
            logger.debug(f"Enhanced page {page_num}")
            return gray
            
        except Exception as e:
            logger.warning(f"Error enhancing image page {page_num}: {e}")
            return image  # Return original if enhancement fails
    
    def deskew_image(self, image: np.ndarray) -> np.ndarray:
        """
        Detect and correct image skew
        
        Args:
            image: Grayscale image
            
        Returns:
            Deskewed image
        """
        try:
            # Detect edges
            edges = cv2.Canny(image, 50, 150, apertureSize=3)
            
            # Detect lines using Hough Transform
            lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)
            
            if lines is not None and len(lines) > 0:
                # Calculate average angle
                angles = []
                for rho, theta in lines[:, 0]:
                    angle = np.degrees(theta) - 90
                    if -45 < angle < 45:  # Filter extreme angles
                        angles.append(angle)
                
                if angles:
                    # Use median angle to avoid outliers
                    skew_angle = np.median(angles)
                    
                    # Only deskew if angle is significant
                    if abs(skew_angle) > 0.5:
                        # Rotate image
                        (h, w) = image.shape[:2]
                        center = (w // 2, h // 2)
                        M = cv2.getRotationMatrix2D(center, skew_angle, 1.0)
                        image = cv2.warpAffine(image, M, (w, h), 
                                              flags=cv2.INTER_CUBIC, 
                                              borderMode=cv2.BORDER_REPLICATE)
                        logger.debug(f"Deskewed by {skew_angle:.2f} degrees")
            
            return image
            
        except Exception as e:
            logger.debug(f"Deskew failed: {e}")
            return image
    
    def enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """
        Enhance image contrast using CLAHE
        
        Args:
            image: Grayscale image
            
        Returns:
            Contrast-enhanced image
        """
        try:
            # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(image)
            return enhanced
        except Exception as e:
            logger.debug(f"Contrast enhancement failed: {e}")
            return image
    
    def adaptive_threshold(self, image: np.ndarray) -> np.ndarray:
        """
        Apply adaptive thresholding for binarization
        
        Args:
            image: Grayscale image
            
        Returns:
            Binarized image
        """
        try:
            # Use Gaussian adaptive thresholding
            binary = cv2.adaptiveThreshold(
                image,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                blockSize=11,
                C=2
            )
            return binary
        except Exception as e:
            logger.debug(f"Binarization failed: {e}")
            return image
    
    def remove_borders(self, image: np.ndarray, border_size: int = 10) -> np.ndarray:
        """
        Remove borders from scanned documents
        
        Args:
            image: Input image
            border_size: Border size to remove (pixels)
            
        Returns:
            Image with borders removed
        """
        h, w = image.shape[:2]
        return image[border_size:h-border_size, border_size:w-border_size]
    
    def detect_tables(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect table regions in image
        
        Args:
            image: Grayscale image
            
        Returns:
            List of table bounding boxes (x, y, w, h)
        """
        tables = []
        
        try:
            # Detect horizontal and vertical lines
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
            
            # Detect horizontal lines
            horizontal_lines = cv2.morphologyEx(image, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
            
            # Detect vertical lines
            vertical_lines = cv2.morphologyEx(image, cv2.MORPH_OPEN, vertical_kernel, iterations=2)
            
            # Combine lines
            table_mask = cv2.addWeighted(horizontal_lines, 0.5, vertical_lines, 0.5, 0.0)
            
            # Find contours
            contours, _ = cv2.findContours(table_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filter contours by size
            min_area = 5000  # Minimum table area
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > min_area:
                    x, y, w, h = cv2.boundingRect(contour)
                    tables.append((x, y, w, h))
            
            if tables:
                logger.info(f"Detected {len(tables)} table(s)")
            
        except Exception as e:
            logger.debug(f"Table detection failed: {e}")
        
        return tables
    
    def extract_text_regions(self, pdf_path: Path) -> List[Dict]:
        """
        Extract text regions and metadata from PDF
        Useful for understanding document structure
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of text blocks with position info
        """
        regions = []
        
        try:
            doc = fitz.open(str(pdf_path))
            
            for page_num in range(doc.page_count):
                page = doc[page_num]
                blocks = page.get_text("dict")["blocks"]
                
                for block in blocks:
                    if "lines" in block:  # Text block
                        bbox = block["bbox"]
                        text = " ".join([span["text"] for line in block["lines"] 
                                       for span in line["spans"]])
                        
                        regions.append({
                            'page': page_num + 1,
                            'bbox': bbox,
                            'text': text,
                            'type': 'text'
                        })
                    elif "image" in block:  # Image block
                        regions.append({
                            'page': page_num + 1,
                            'bbox': block["bbox"],
                            'type': 'image'
                        })
            
            doc.close()
            logger.info(f"Extracted {len(regions)} text/image regions")
            
        except Exception as e:
            logger.warning(f"Text region extraction failed: {e}")
        
        return regions


def process_pdf_file(pdf_path: Path, output_dir: Optional[Path] = None) -> List[np.ndarray]:
    """
    Convenience function to process a single PDF file
    
    Args:
        pdf_path: Path to PDF file
        output_dir: Optional output directory for images
        
    Returns:
        List of processed images
    """
    processor = PDFProcessor()
    return processor.pdf_to_images(pdf_path, output_dir)


if __name__ == "__main__":
    # Test with a sample PDF
    import sys
    
    if len(sys.argv) > 1:
        pdf_path = Path(sys.argv[1])
        if pdf_path.exists():
            processor = PDFProcessor()
            images = processor.pdf_to_images(pdf_path)
            print(f"✓ Processed {len(images)} pages")
        else:
            print(f"Error: File not found: {pdf_path}")
    else:
        print("Usage: python pdf_processor.py <pdf_file>")
