import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
import time
from collections import defaultdict

from pdf_parser import PDFParser
from embedder import DocumentEmbedder
from retriever import RelevanceRetriever
from config import Config

logger = logging.getLogger(__name__)


class DocumentAnalyzer:
    """Main document analysis orchestrator."""
    
    def __init__(self, config: Config):
        self.config = config
        self.pdf_parser = PDFParser(config)
        self.embedder = DocumentEmbedder(config)
        self.retriever = RelevanceRetriever(config)
        
    def analyze_documents(self, pdf_paths: List[Path], query: str) -> Tuple[List[Dict], List[Dict]]:
        """
        Analyze a collection of PDF documents and return ranked sections and subsections.
        
        Args:
            pdf_paths: List of paths to PDF files
            query: Analysis query combining persona and job-to-be-done
            
        Returns:
            Tuple of (section_rankings, subsection_analysis)
        """
        logger.info(f"Starting analysis of {len(pdf_paths)} documents")
        
        # Step 1: Parse all documents and extract structured content
        all_chunks = []
        document_metadata = {}
        
        for pdf_path in pdf_paths:
            logger.info(f"Parsing document: {pdf_path.name}")
            chunks, metadata = self.pdf_parser.parse_document(pdf_path)
            
            # Add document source to each chunk and filter None chunks
            valid_chunks = []
            for chunk in chunks:
                if chunk is not None:
                    chunk['source_document'] = pdf_path.name
                    valid_chunks.append(chunk)
            
            all_chunks.extend(valid_chunks)
            document_metadata[pdf_path.name] = metadata
            
        logger.info(f"Extracted {len(all_chunks)} text chunks from all documents")
        
        if not all_chunks:
            logger.warning("No valid chunks extracted from documents")
            return [], []
        
        # Step 2: Generate keyword representations for all chunks and the query
        logger.info("Generating keyword representations...")
        chunk_embeddings = self.embedder.embed_chunks([chunk['text'] for chunk in all_chunks])
        query_embedding = self.embedder.embed_query(query)
        
        # Step 3: Retrieve most relevant chunks
        logger.info("Computing relevance scores...")
        relevant_chunks = self.retriever.retrieve_relevant_chunks(
            all_chunks, chunk_embeddings, query_embedding
        )
        
        logger.info(f"Retrieved {len(relevant_chunks)} relevant chunks")
        
        # Step 4: Aggregate section-level importance scores
        section_scores = self._aggregate_section_scores(relevant_chunks)
        
        # Step 5: Generate section rankings
        section_rankings = self._generate_section_rankings(section_scores, document_metadata)
        
        # Step 6: Generate subsection analysis
        subsection_analysis = self._generate_subsection_analysis(relevant_chunks)
        
        return section_rankings, subsection_analysis
    
    def _aggregate_section_scores(self, relevant_chunks: List[Dict]) -> Dict[str, Dict]:
        """Aggregate relevance scores at the section level."""
        section_scores = {}
        
        for chunk in relevant_chunks:
            section_key = f"{chunk['source_document']}:{chunk.get('section_title', 'Unknown Section')}"
            
            if section_key not in section_scores:
                section_scores[section_key] = {
                    'total_score': 0.0,
                    'chunk_count': 0,
                    'document': chunk['source_document'],
                    'section_title': chunk.get('section_title', 'Unknown Section'),
                    'page_numbers': set(),
                    'chunks': []
                }
            
            section_data = section_scores[section_key]
            section_data['total_score'] += chunk['relevance_score']
            section_data['chunk_count'] += 1
            section_data['page_numbers'].add(chunk.get('page_number', 1))
            section_data['chunks'].append(chunk)
        
        # Calculate average scores
        for section_data in section_scores.values():
            if section_data['chunk_count'] > 0:
                section_data['avg_score'] = section_data['total_score'] / section_data['chunk_count']
            else:
                section_data['avg_score'] = 0.0
        
        return section_scores
    
    def _generate_section_rankings(self, section_scores: Dict, document_metadata: Dict) -> List[Dict]:
        """Generate final section rankings with enhanced persona-specific logic."""
        # Sort sections by average score
        sorted_sections = sorted(
            section_scores.items(),
            key=lambda x: x[1]['avg_score'],
            reverse=True
        )
        
        rankings = []
        for rank, (section_key, section_data) in enumerate(sorted_sections[:self.config.max_sections], 1):
            # Get the full section title from the best chunk
            best_chunk = max(section_data['chunks'], key=lambda x: x['relevance_score'])
            full_section_title = self._extract_clean_section_title(best_chunk['text'])
            
            ranking = {
                'document': section_data['document'],
                'section_title': full_section_title,
                'importance_rank': rank,
                'page_number': list(section_data['page_numbers'])[0] if section_data['page_numbers'] else 1
            }
            rankings.append(ranking)
        
        logger.info(f"Generated {len(rankings)} section rankings")
        return rankings
    
    def _extract_clean_section_title(self, text: str) -> str:
        """Extract a clean, descriptive section title from text content."""
        lines = text.strip().split('\n')
        
        # Look for the first meaningful line that could be a title
        for line in lines[:3]:  # Check first 3 lines
            line = line.strip()
            if len(line) > 10 and len(line) < 100:
                # Check if it looks like a title
                if (line.istitle() or 
                    line.isupper() or 
                    any(keyword in line.lower() for keyword in ['guide', 'introduction', 'overview', 'chapter'])):
                    return line
        
        # If no clear title found, use first substantial line
        for line in lines:
            line = line.strip()
            if len(line) > 20 and len(line) < 80:
                return line
        
        # Fallback to first line or truncated text
        if lines:
            return lines[0][:60] + "..." if len(lines[0]) > 60 else lines[0]
        
        return "Untitled Section"
    
    def _generate_subsection_analysis(self, relevant_chunks: List[Dict]) -> List[Dict]:
        """Generate subsection analysis with refined text."""
        subsections = []
        
        # Take top chunks for subsection analysis
        top_chunks = relevant_chunks[:self.config.max_subsections]
        
        for chunk in top_chunks:
            # Refine the text to be more concise
            refined_text = self._refine_text(chunk['text'])
            
            subsection = {
                'document': chunk['source_document'],
                'refined_text': refined_text,
                'page_number': chunk.get('page_number', 1)
            }
            
            subsections.append(subsection)
        
        logger.info(f"Generated {len(subsections)} subsection analyses")
        return subsections
    
    def _refine_text(self, text: str) -> str:
        """Refine text to be more concise and focused."""
        # Normalize whitespace by replacing newlines and multiple spaces with a single space
        text = ' '.join(text.split())

        # Truncate if too long
        if len(text) > self.config.max_refined_text_length:
            # Try to find a good stopping point (end of sentence)
            truncated = text[:self.config.max_refined_text_length]
            last_period = truncated.rfind('.')
            
            if last_period > self.config.max_refined_text_length * 0.7:
                return truncated[:last_period + 1]
            else:
                return truncated + "..."
        
        return text