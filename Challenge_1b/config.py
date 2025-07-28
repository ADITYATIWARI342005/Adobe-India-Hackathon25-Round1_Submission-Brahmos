"""
Configuration settings for the document analysis system
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Configuration parameters for the document analysis system."""
    
    # Model configuration
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_batch_size: int = 32
    
    # Text processing
    min_chunk_length: int = 50
    max_chunk_length: int = 2000
    max_refined_text_length: int = 500
    
    # Retrieval parameters
    relevance_threshold: float = 0.1
    max_retrieved_chunks: int = 100
    max_chunks_per_document: int = 20
    
    # Output configuration
    max_sections: int = 10
    max_subsections: int = 15
    
    # Performance settings
    max_processing_time: int = 60  # seconds
    memory_limit_mb: int = 1024
    
    # File paths
    model_cache_dir: str = "models"
    temp_dir: str = "temp"
    
    def __post_init__(self):
        """Post-initialization validation and environment variable overrides."""
        
        # Override with environment variables if available
        self.model_name = os.getenv("MODEL_NAME", self.model_name)
        self.relevance_threshold = float(os.getenv("RELEVANCE_THRESHOLD", self.relevance_threshold))
        self.max_sections = int(os.getenv("MAX_SECTIONS", self.max_sections))
        self.max_subsections = int(os.getenv("MAX_SUBSECTIONS", self.max_subsections))
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self):
        """Validate configuration parameters."""
        if self.min_chunk_length >= self.max_chunk_length:
            raise ValueError("min_chunk_length must be less than max_chunk_length")
        
        if self.relevance_threshold < 0 or self.relevance_threshold > 1:
            raise ValueError("relevance_threshold must be between 0 and 1")
        
        if self.max_sections <= 0 or self.max_subsections <= 0:
            raise ValueError("max_sections and max_subsections must be positive")
        
        if self.embedding_batch_size <= 0:
            raise ValueError("embedding_batch_size must be positive")
    
    @classmethod
    def for_hackathon(cls) -> 'Config':
        """Create configuration optimized for hackathon constraints."""
        return cls(
            max_sections=5,
            max_subsections=10,
            max_retrieved_chunks=50,
            relevance_threshold=0.01,  # Much lower threshold for keyword-based matching
            embedding_batch_size=32,
            max_processing_time=50  # Leave buffer for 60s limit
        )