import re
import json
import logging
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)


def clean_text(text: str) -> str:
    """Clean and normalize text content."""
    if not text:
        return ""
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove excessive punctuation
    text = re.sub(r'[.]{3,}', '...', text)
    
    # Clean up common PDF artifacts
    text = re.sub(r'\x0c', ' ', text)  # Form feed
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)  # Control chars
    
    return text.strip()


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to maximum length with suffix."""
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def extract_filename_without_extension(path: Path) -> str:
    """Extract filename without extension from path."""
    return path.stem


def format_section_title(title: str) -> str:
    """Format section title for consistent display."""
    if not title:
        return "Untitled Section"
    
    # Remove extra whitespace
    title = ' '.join(title.split())
    
    # Ensure proper capitalization
    if title.isupper() and len(title) > 5:
        title = title.title()
    elif title.islower():
        title = title.capitalize()
    
    return title


def safe_json_dump(data: Any, filepath: Path, indent: int = 2) -> bool:
    """Safely dump data to JSON file with error handling."""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False, default=str)
        return True
    except Exception as e:
        logger.error(f"Failed to write JSON to {filepath}: {e}")
        return False


def load_json_file(filepath: Path) -> Dict[str, Any]:
    """Load JSON file with error handling."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load JSON from {filepath}: {e}")
        return {}


def get_current_timestamp() -> str:
    """Get current timestamp in ISO format."""
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]


def validate_pdf_path(path: Path) -> bool:
    """Validate that a path points to a valid PDF file."""
    if not path.exists():
        return False
    
    if not path.is_file():
        return False
    
    if path.suffix.lower() != '.pdf':
        return False
    
    return True


def estimate_reading_time(text: str, wpm: int = 200) -> float:
    """Estimate reading time for text in minutes."""
    word_count = len(text.split())
    return word_count / wpm


def create_document_summary(chunks: List[Dict]) -> Dict[str, Any]:
    """Create a summary of document processing results."""
    if not chunks:
        return {
            'total_chunks': 0,
            'total_characters': 0,
            'sections': [],
            'documents': []
        }
    
    total_chars = sum(len(chunk.get('text', '')) for chunk in chunks)
    sections = list(set(chunk.get('section_title', 'Unknown') for chunk in chunks))
    documents = list(set(chunk.get('source_document', 'Unknown') for chunk in chunks))
    
    return {
        'total_chunks': len(chunks),
        'total_characters': total_chars,
        'sections': sorted(sections),
        'documents': sorted(documents),
        'estimated_reading_time_minutes': estimate_reading_time(' '.join(chunk.get('text', '') for chunk in chunks))
    }


def filter_chunks_by_length(chunks: List[Dict], min_length: int = 50, max_length: int = 2000) -> List[Dict]:
    """Filter chunks by text length."""
    filtered = []
    
    for chunk in chunks:
        text_length = len(chunk.get('text', ''))
        if min_length <= text_length <= max_length:
            filtered.append(chunk)
    
    logger.info(f"Filtered chunks: {len(filtered)}/{len(chunks)} within length range [{min_length}, {max_length}]")
    return filtered


def deduplicate_chunks(chunks: List[Dict], similarity_threshold: float = 0.95) -> List[Dict]:
    """Remove near-duplicate chunks based on text similarity."""
    if len(chunks) <= 1:
        return chunks
    
    # Simple deduplication based on text length and first N characters
    seen_signatures = set()
    deduplicated = []
    
    for chunk in chunks:
        text = chunk.get('text', '')
        signature = (len(text), text[:100] if len(text) > 100 else text)
        
        if signature not in seen_signatures:
            seen_signatures.add(signature)
            deduplicated.append(chunk)
    
    logger.info(f"Deduplicated chunks: {len(deduplicated)}/{len(chunks)} unique")
    return deduplicated
