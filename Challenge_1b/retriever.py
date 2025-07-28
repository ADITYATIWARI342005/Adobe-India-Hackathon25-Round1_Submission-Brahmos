import logging
from typing import List, Dict, Any
import math

from config import Config

logger = logging.getLogger(__name__)


class RelevanceRetriever:
    """Retrieves and ranks relevant content based on keyword similarity."""
    
    def __init__(self, config: Config):
        self.config = config
    
    def retrieve_relevant_chunks(
        self,
        chunks: List[Dict],
        chunk_embeddings: List[Dict[str, float]],
        query_embedding: Dict[str, float]
    ) -> List[Dict]:
        """
        Retrieve and rank chunks by relevance to the query.
        
        Args:
            chunks: List of text chunks with metadata
            chunk_embeddings: Keyword vectors for all chunks
            query_embedding: Keyword vector for the query
            
        Returns:
            List of chunks ranked by relevance, with relevance scores added
        """
        if len(chunks) == 0 or len(chunk_embeddings) == 0:
            return []
        
        logger.info(f"Computing relevance for {len(chunks)} chunks")
        
        # Compute similarity between query and all chunks
        similarities = []
        for chunk_vector in chunk_embeddings:
            similarity = self._cosine_similarity(query_embedding, chunk_vector)
            similarities.append(similarity)
        
        # Add relevance scores to chunks
        scored_chunks = []
        for i, chunk in enumerate(chunks):
            if chunk is None:  # Skip None chunks from filtering
                continue
                
            chunk_with_score = chunk.copy()
            chunk_with_score['relevance_score'] = similarities[i]
            scored_chunks.append(chunk_with_score)
        
        # Sort by relevance score (descending)
        scored_chunks.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        # Apply relevance threshold filter
        filtered_chunks = [
            chunk for chunk in scored_chunks
            if chunk['relevance_score'] >= self.config.relevance_threshold
        ]
        
        # Take top N chunks
        top_chunks = filtered_chunks[:self.config.max_retrieved_chunks]
        
        logger.info(f"Retrieved {len(top_chunks)} relevant chunks")
        
        if top_chunks:
            logger.info(f"Top relevance score: {top_chunks[0]['relevance_score']:.4f}")
            logger.info(f"Lowest relevance score: {top_chunks[-1]['relevance_score']:.4f}")
        
        return top_chunks
    
    def _cosine_similarity(self, vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
        """Calculate cosine similarity between two keyword vectors."""
        if not vec1 or not vec2:
            return 0.0
        
        # Find common terms
        common_terms = set(vec1.keys()) & set(vec2.keys())
        
        if not common_terms:
            return 0.0
        
        # Calculate dot product
        dot_product = sum(vec1[term] * vec2[term] for term in common_terms)
        
        # Calculate magnitudes
        magnitude1 = math.sqrt(sum(val**2 for val in vec1.values()))
        magnitude2 = math.sqrt(sum(val**2 for val in vec2.values()))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def compute_section_relevance(self, chunks_in_section: List[Dict]) -> float:
        """
        Compute overall relevance score for a section based on its chunks.
        
        Args:
            chunks_in_section: List of chunks belonging to the same section
            
        Returns:
            Aggregated relevance score for the section
        """
        if not chunks_in_section:
            return 0.0
        
        scores = [chunk['relevance_score'] for chunk in chunks_in_section]
        
        # Use weighted average: higher weight for top scores
        weights = [1.0 / (i + 1) for i in range(len(scores))]
        weights_sum = sum(weights)
        
        if weights_sum == 0:
            return 0.0
        
        weighted_sum = sum(score * weight for score, weight in zip(scores, weights))
        return weighted_sum / weights_sum
    
    def diversify_results(self, chunks: List[Dict], max_per_document: int = None) -> List[Dict]:
        """
        Diversify results to avoid over-representation from single documents.
        
        Args:
            chunks: List of ranked chunks
            max_per_document: Maximum chunks to take from each document
            
        Returns:
            Diversified list of chunks
        """
        if max_per_document is None:
            max_per_document = self.config.max_chunks_per_document or 10
        
        diversified = []
        doc_counts = {}
        
        for chunk in chunks:
            doc_name = chunk.get('source_document', 'unknown')
            current_count = doc_counts.get(doc_name, 0)
            
            if current_count < max_per_document:
                diversified.append(chunk)
                doc_counts[doc_name] = current_count + 1
            
            if len(diversified) >= self.config.max_retrieved_chunks:
                break
        
        logger.info(f"Diversified results: {len(diversified)} chunks from {len(doc_counts)} documents")
        return diversified