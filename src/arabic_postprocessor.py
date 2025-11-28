"""
Arabic Text Post-Processor for Legal Documents
Handles text correction, formatting, and Arabic-specific issues
"""
import re
from typing import List, Dict, Tuple
from loguru import logger
import config

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    HAS_BIDI = True
except ImportError:
    HAS_BIDI = False
    logger.warning("python-bidi not available. Some Arabic text processing features disabled.")


class ArabicPostProcessor:
    """Post-processor for Arabic legal documents"""
    
    def __init__(self):
        """Initialize Arabic post-processor"""
        self.arabic_digits = '٠١٢٣٤٥٦٧٨٩'
        self.english_digits = '0123456789'
        
        # Common OCR errors in Arabic
        self.common_errors = {
            'آ': ['أ', 'ا'],
            'إ': ['ا'],
            'أ': ['ا'],
            'ة': ['ه'],
            'ى': ['ي'],
            'ئ': ['ي'],
            'ؤ': ['و'],
        }
        
        # Legal terminology patterns
        self.legal_patterns = {
            'article': r'(?:المادة|ماده|ماده)\s*(?:رقم)?\s*(\d+)',
            'clause': r'(?:البند|بند)\s*(?:رقم)?\s*(\d+)',
            'paragraph': r'(?:الفقرة|فقرة|فقره)\s*(?:رقم)?\s*(\d+)',
            'date': r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
        }
    
    def process(self, text: str) -> str:
        """
        Main processing pipeline for Arabic text
        
        Args:
            text: Raw OCR text
            
        Returns:
            Processed and corrected text
        """
        if not text:
            return ''
        
        # 1. Fix spacing
        if config.FIX_SPACING:
            text = self.fix_spacing(text)
        
        # 2. Normalize numbers
        if config.NORMALIZE_NUMBERS:
            text = self.normalize_numbers(text)
        
        # 3. Fix Arabic ligatures
        if config.FIX_ARABIC_LIGATURES:
            text = self.fix_ligatures(text)
        
        # 4. Correct common OCR errors
        if config.CORRECT_COMMON_ERRORS:
            text = self.correct_common_errors(text)
        
        # 5. Normalize whitespace
        text = self.normalize_whitespace(text)
        
        # 6. Remove diacritics if configured
        if config.REMOVE_DIACRITICS:
            text = self.remove_diacritics(text)
        
        return text.strip()
    
    def fix_spacing(self, text: str) -> str:
        """
        Fix spacing issues common in Arabic OCR
        
        Args:
            text: Input text
            
        Returns:
            Text with fixed spacing
        """
        # Remove spaces before punctuation
        text = re.sub(r'\s+([،؛:.؟!])', r'\1', text)
        
        # Add space after punctuation if missing
        text = re.sub(r'([،؛:.؟!])([^\s\d])', r'\1 \2', text)
        
        # Fix spaces around parentheses
        text = re.sub(r'\(\s+', '(', text)
        text = re.sub(r'\s+\)', ')', text)
        
        # Fix spaces around quotes
        text = re.sub(r'"\s+', '"', text)
        text = re.sub(r'\s+"', '"', text)
        
        return text
    
    def normalize_numbers(self, text: str) -> str:
        """
        Normalize Arabic and English numbers
        
        Args:
            text: Input text
            
        Returns:
            Text with normalized numbers
        """
        # Convert Arabic-Indic digits to Arabic (Eastern) digits
        arabic_indic = '٠١٢٣٤٥٦٧٨٩'
        arabic = '0123456789'
        
        trans_table = str.maketrans(arabic_indic, arabic)
        text = text.translate(trans_table)
        
        # Also handle Persian/Urdu digits
        persian_digits = '۰۱۲۳۴۵۶۷۸۹'
        trans_table = str.maketrans(persian_digits, arabic)
        text = text.translate(trans_table)
        
        return text
    
    def fix_ligatures(self, text: str) -> str:
        """
        Fix Arabic ligature issues from OCR
        
        Args:
            text: Input text
            
        Returns:
            Text with fixed ligatures
        """
        # Common ligature replacements
        replacements = {
            'ﻻ': 'لا',
            'ﻷ': 'لأ',
            'ﻹ': 'لإ',
            'ﻵ': 'لآ',
            'ﷲ': 'الله',
            'ﷺ': 'صلى الله عليه وسلم',
        }
        
        for ligature, replacement in replacements.items():
            text = text.replace(ligature, replacement)
        
        return text
    
    def correct_common_errors(self, text: str) -> str:
        """
        Correct common OCR errors in Arabic text
        
        Args:
            text: Input text
            
        Returns:
            Corrected text
        """
        # Fix common character confusions
        corrections = {
            # Hamza variations
            r'أ(?=[^ء])': 'ا',  # alef with hamza -> alef (context dependent)
            
            # Taa marbuta
            r'ه\b': 'ة',  # heh at end of word -> taa marbuta
            
            # Yaa variations
            r'ى\b': 'ي',  # alef maksura at end -> yaa
        }
        
        for pattern, replacement in corrections.items():
            text = re.sub(pattern, replacement, text)
        
        return text
    
    def remove_diacritics(self, text: str) -> str:
        """
        Remove Arabic diacritical marks
        
        Args:
            text: Input text
            
        Returns:
            Text without diacritics
        """
        # Arabic diacritics Unicode range
        diacritics = re.compile(r'[\u064B-\u065F\u0670]')
        return diacritics.sub('', text)
    
    def normalize_whitespace(self, text: str) -> str:
        """
        Normalize whitespace in text
        
        Args:
            text: Input text
            
        Returns:
            Text with normalized whitespace
        """
        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)
        
        # Replace multiple newlines with double newline
        text = re.sub(r'\n\n+', '\n\n', text)
        
        # Remove trailing spaces
        lines = [line.rstrip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        return text
    
    def extract_article_numbers(self, text: str) -> List[Dict]:
        """
        Extract article/clause numbers from legal text
        
        Args:
            text: Input text
            
        Returns:
            List of extracted articles with positions
        """
        articles = []
        
        for pattern_type, pattern in self.legal_patterns.items():
            for match in re.finditer(pattern, text):
                articles.append({
                    'type': pattern_type,
                    'text': match.group(0),
                    'number': match.group(1) if match.groups() else None,
                    'position': match.span()
                })
        
        return articles
    
    def extract_dates(self, text: str) -> List[str]:
        """
        Extract dates from text
        
        Args:
            text: Input text
            
        Returns:
            List of extracted dates
        """
        # Date patterns (various formats)
        date_patterns = [
            r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}',  # DD/MM/YYYY or DD-MM-YYYY
            r'\d{4}[-/]\d{1,2}[-/]\d{1,2}',    # YYYY/MM/DD
            r'\d{1,2}\s+(?:يناير|فبراير|مارس|أبريل|مايو|يونيو|يوليو|أغسطس|سبتمبر|أكتوبر|نوفمبر|ديسمبر)\s+\d{4}',
        ]
        
        dates = []
        for pattern in date_patterns:
            dates.extend(re.findall(pattern, text))
        
        return dates
    
    def format_for_display(self, text: str) -> str:
        """
        Format Arabic text for proper display (bidirectional text)
        
        Args:
            text: Input text
            
        Returns:
            Formatted text for display
        """
        if not HAS_BIDI:
            return text
        
        try:
            # Reshape Arabic text for proper connection
            reshaped_text = arabic_reshaper.reshape(text)
            
            # Apply bidirectional algorithm
            bidi_text = get_display(reshaped_text)
            
            return bidi_text
        except Exception as e:
            logger.warning(f"Error formatting text for display: {e}")
            return text
    
    def validate_arabic_text(self, text: str) -> Dict:
        """
        Validate Arabic text quality
        
        Args:
            text: Input text
            
        Returns:
            Dictionary with validation metrics
        """
        if not text:
            return {
                'is_valid': False,
                'has_arabic': False,
                'arabic_ratio': 0.0,
                'has_numbers': False,
                'has_dates': False
            }
        
        # Count Arabic characters
        arabic_chars = len(re.findall(r'[\u0600-\u06FF]', text))
        total_chars = len(re.findall(r'\S', text))
        
        arabic_ratio = arabic_chars / total_chars if total_chars > 0 else 0.0
        
        # Check for numbers
        has_numbers = bool(re.search(r'\d', text))
        
        # Check for dates
        has_dates = bool(self.extract_dates(text))
        
        # Check for legal markers
        has_legal_markers = bool(re.search(
            r'(?:المادة|البند|الفقرة|القانون|العقد|الاتفاقية)',
            text
        ))
        
        return {
            'is_valid': arabic_ratio > 0.3,  # At least 30% Arabic
            'has_arabic': arabic_chars > 0,
            'arabic_ratio': round(arabic_ratio, 2),
            'has_numbers': has_numbers,
            'has_dates': has_dates,
            'has_legal_markers': has_legal_markers,
            'word_count': len(text.split())
        }
    
    def split_into_articles(self, text: str) -> List[Dict]:
        """
        Split legal document into articles/sections
        
        Args:
            text: Full document text
            
        Returns:
            List of articles with metadata
        """
        articles = []
        
        # Find article markers
        article_pattern = r'(?:المادة|ماده)\s*(?:رقم)?\s*(\d+)'
        matches = list(re.finditer(article_pattern, text))
        
        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            
            article_text = text[start:end].strip()
            article_num = match.group(1)
            
            articles.append({
                'number': article_num,
                'text': article_text,
                'start': start,
                'end': end
            })
        
        return articles


def process_text(text: str) -> str:
    """
    Convenience function to process Arabic text
    
    Args:
        text: Raw OCR text
        
    Returns:
        Processed text
    """
    processor = ArabicPostProcessor()
    return processor.process(text)


if __name__ == "__main__":
    # Test processor
    processor = ArabicPostProcessor()
    
    sample_text = "المادة  ١٢:  يجب  على  الطرف  الأول  ..."
    processed = processor.process(sample_text)
    
    print("Original:", sample_text)
    print("Processed:", processed)
    
    validation = processor.validate_arabic_text(processed)
    print("Validation:", validation)
