import logging
from typing import List, Dict, Set
import re
from collections import Counter

from config import Config

logger = logging.getLogger(__name__)


class DocumentEmbedder:
    """Generates text representations using keyword-based similarity matching."""
    
    def __init__(self, config: Config):
        self.config = config
        self.vocabulary = set()
        self.document_vectors = []
        
    def embed_chunks(self, texts: List[str]) -> List[Dict[str, float]]:
        """
        Generate keyword-based representations for text chunks.
        
        Args:
            texts: List of text strings to process
            
        Returns:
            List of dictionaries representing keyword frequencies
        """
        if not texts:
            return []
        
        logger.info(f"Generating keyword representations for {len(texts)} text chunks")
        
        # Build vocabulary from all texts
        all_words = set()
        for text in texts:
            words = self._extract_keywords(text)
            all_words.update(words)
        
        self.vocabulary = all_words
        logger.info(f"Built vocabulary with {len(self.vocabulary)} unique terms")
        
        # Create vectors for each text
        vectors = []
        for text in texts:
            vector = self._create_vector(text)
            vectors.append(vector)
        
        self.document_vectors = vectors
        return vectors
    
    def embed_query(self, query: str) -> Dict[str, float]:
        """
        Generate keyword representation for a single query string.
        
        Args:
            query: Query string to process
            
        Returns:
            Dictionary representing keyword frequencies
        """
        logger.info(f"Generating query representation for: {query[:100]}...")
        return self._create_vector(query)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text."""
        # Convert to lowercase and remove punctuation
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        
        # Split into words
        words = text.split()
        
        # Filter out common stop words and short words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 
            'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her',
            'its', 'our', 'their', 'can', 'may', 'might', 'must', 'shall', 'get',
            'go', 'come', 'take', 'make', 'see', 'know', 'think', 'say', 'tell',
            'give', 'use', 'find', 'want', 'need', 'try', 'ask', 'work', 'seem',
            'feel', 'leave', 'put', 'mean', 'keep', 'let', 'begin', 'start'
        }
        
        # Filter and return meaningful keywords
        keywords = [
            word for word in words 
            if len(word) > 2 and word not in stop_words and word.isalpha()
        ]
        
        return keywords
    
    def _create_vector(self, text: str) -> Dict[str, float]:
        """Create a keyword frequency vector for text."""
        keywords = self._extract_keywords(text)
        word_counts = Counter(keywords)
        
        # Calculate TF (term frequency) scores
        total_words = len(keywords)
        if total_words == 0:
            return {}
        
        # Normalize by text length
        vector = {}
        for word, count in word_counts.items():
            tf = count / total_words
            vector[word] = tf
        
        return vector