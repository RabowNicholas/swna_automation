import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import os
from config.settings import AR_ACK_SIGNATURE
from src.logger import SWNALogger

class DocumentProcessor:
    """Handle PDF text extraction and AR Ack document identification."""
    
    def __init__(self, logger=None):
        self.logger = logger or SWNALogger()
    
    def extract_text_from_pdf(self, pdf_path):
        """
        Extract text from scanned PDF using OCR.
        Returns extracted text string or None if extraction fails.
        """
        # All files are scanned images - go directly to OCR
        self.logger.debug(f"[OCR] Processing scanned PDF with OCR: {pdf_path}")
        try:
            text = self._extract_with_ocr(pdf_path)
            if text and len(text.strip()) > 0:
                self.logger.debug(f"[OCR] OCR extracted {len(text)} characters")
                return text
        except Exception as e:
            self.logger.debug(f"OCR extraction failed for {pdf_path}: {str(e)}")
        
        return None
    
    
    def _extract_with_ocr(self, pdf_path):
        """Extract text using OCR (Tesseract) for scanned PDFs."""
        text = ""
        
        try:
            self.logger.debug(f"[OCR] Converting PDF to images: {pdf_path}")
            
            # Convert PDF pages to images
            images = convert_from_path(pdf_path, dpi=300, first_page=1, last_page=3)  # Limit to first 3 pages for speed
            
            self.logger.debug(f"[OCR] Processing {len(images)} pages with Tesseract")
            
            for i, image in enumerate(images):
                try:
                    # Use Tesseract to extract text from image
                    page_text = pytesseract.image_to_string(image, config='--psm 6')
                    
                    if page_text and page_text.strip():
                        text += page_text + "\n"
                        self.logger.debug(f"[OCR] Page {i+1}: extracted {len(page_text)} characters")
                    else:
                        self.logger.debug(f"[OCR] Page {i+1}: no text extracted")
                        
                except Exception as e:
                    self.logger.debug(f"[OCR] Failed to process page {i+1}: {str(e)}")
                    continue
            
            self.logger.debug(f"[OCR] Total OCR text extracted: {len(text)} characters")
            return text
            
        except Exception as e:
            self.logger.error(f"[OCR] OCR processing failed: {str(e)}")
            raise
    
    def is_ar_acknowledgment(self, text):
        """
        Check if the document is an AR Acknowledgment letter.
        Returns True if AR Ack signature text is found.
        """
        if not text:
            self.logger.debug("[DEBUG] No text provided to AR Ack checker")
            return False
        
        # Clean text for comparison (remove extra whitespace, normalize)
        clean_text = " ".join(text.split())
        clean_signature = " ".join(AR_ACK_SIGNATURE.split())
        
        self.logger.debug(f"[DEBUG] Looking for signature text (length: {len(clean_signature)})")
        self.logger.debug(f"[DEBUG] Signature starts with: '{clean_signature[:100]}...'")
        
        # Check if signature text exists in document
        found = clean_signature in clean_text
        
        if found:
            self.logger.debug("[DEBUG] ✅ AR Ack signature text FOUND!")
        else:
            self.logger.debug("[DEBUG] ❌ AR Ack signature text NOT found")
            # Look for partial matches to help debug
            signature_words = clean_signature.split()[:10]  # First 10 words
            partial_signature = " ".join(signature_words)
            if partial_signature in clean_text:
                self.logger.debug(f"[DEBUG] 🔍 Found partial match: '{partial_signature}'")
            else:
                self.logger.debug(f"[DEBUG] 🔍 Even partial signature not found: '{partial_signature}'")
        
        return found
    
    def process_document(self, pdf_path):
        """
        Process a PDF document and return extracted text if it's an AR Ack.
        Returns (is_ar_ack, extracted_text) tuple.
        """
        try:
            # Extract text from PDF
            text = self.extract_text_from_pdf(pdf_path)
            
            if not text:
                self.logger.debug(f"No text could be extracted from {pdf_path}")
                return False, None
            
            # DEBUG: Log the first 500 characters of extracted text
            self.logger.debug(f"[DEBUG] Extracted text from {pdf_path}:")
            self.logger.debug(f"[DEBUG] First 500 chars: {text[:500]}")
            self.logger.debug(f"[DEBUG] Text length: {len(text)} characters")
            
            # Check if it's an AR Acknowledgment
            is_ar_ack = self.is_ar_acknowledgment(text)
            
            if is_ar_ack:
                self.logger.log_ar_ack_identified(pdf_path)
                return True, text
            else:
                self.logger.debug(f"Document is not an AR Ack: {pdf_path}")
                self.logger.debug(f"[DEBUG] Looking for signature text in document...")
                return False, None
                
        except Exception as e:
            self.logger.error(f"Document processing failed for {pdf_path}: {str(e)}")
            return False, None