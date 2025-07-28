import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
import re

# Use pdfplumber for PDF processing (already available)
import pdfplumber
fitz = None

from config import Config

logger = logging.getLogger(__name__)


class PDFParser:
    """Extracts structured text content from PDF documents."""
    
    def __init__(self, config: Config):
        self.config = config
        
    def parse_document(self, pdf_path: Path) -> Tuple[List[Dict], Dict]:
        """
        Parse a PDF document and extract structured text chunks.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Tuple of (text_chunks, document_metadata)
        """
        logger.info(f"Parsing PDF: {pdf_path}")
        
        # Use pdfplumber since PyMuPDF is not available
        return self._parse_with_pdfplumber(pdf_path)
    
    def _parse_with_pymupdf(self, pdf_path: Path) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Parse using PyMuPDF (not available in this environment)."""
        # PyMuPDF is not available, fallback to pdfplumber
        return self._parse_with_pdfplumber(pdf_path)
    
    def _parse_with_pdfplumber(self, pdf_path: Path) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Fallback parsing using pdfplumber."""
        try:
            chunks = []
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                
                document_metadata = {
                    'filename': pdf_path.name,
                    'total_pages': total_pages,
                    'title': pdf_path.stem
                }
                
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if text and text.strip():
                        # Simple paragraph-based chunking for pdfplumber
                        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
                        
                        for para in paragraphs:
                            if len(para) >= self.config.min_chunk_length:
                                chunk = {
                                    'text': para,
                                    'section_title': self._infer_section_title(para),
                                    'page_number': page_num,
                                    'source_document': pdf_path.name
                                }
                                chunks.append(chunk)
            
            logger.info(f"Extracted {len(chunks)} chunks from {pdf_path.name} using pdfplumber")
            return chunks, document_metadata
            
        except Exception as e:
            logger.error(f"Failed to parse {pdf_path} with pdfplumber: {e}")
            raise
    
    def _extract_page_chunks_pymupdf(self, page, page_number: int, document_name: str) -> List[Dict]:
        """PyMuPDF not available - this method is unused."""
        return []
    
    def _create_text_chunk(self, text: str, section_title: str, page_number: int, document_name: str) -> Dict[str, Any] | None:
        """Create a standardized text chunk dictionary."""
        # Clean the text
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Skip very short chunks
        if len(text) < self.config.min_chunk_length:
            return None
        
        # Truncate very long chunks
        if len(text) > self.config.max_chunk_length:
            text = text[:self.config.max_chunk_length] + "..."
        
        return {
            'text': text,
            'section_title': section_title,
            'page_number': page_number,
            'source_document': document_name
        }
    
    def _infer_section_title(self, text: str) -> str:
        """Infer section title from text content (fallback method)."""
        # Extract first sentence or phrase
        sentences = text.split('. ')
        if sentences:
            first_sentence = sentences[0].strip()
            if len(first_sentence) < 100:
                return first_sentence
        
        # Fallback to first few words
        words = text.split()[:5]
        return ' '.join(words) + "..." if len(words) == 5 else ' '.join(words)