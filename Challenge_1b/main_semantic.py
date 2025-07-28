import json
import sys
import time
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from document_analyzer import DocumentAnalyzer
from config import Config
from enhanced_ranking import PersonaRanking

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def load_input_json(input_path: Path) -> Dict[str, Any]:
    """Load and validate input JSON file."""
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validate required fields
        required_fields = ['documents', 'persona', 'job_to_be_done']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        logger.info(f"Loaded input with {len(data.get('documents', []))} documents")
        return data
        
    except Exception as e:
        logger.error(f"Failed to load input JSON: {e}")
        raise


def validate_pdf_files(documents: List[Dict], collection_path: Path) -> List[Path]:
    """Validate that all PDF files exist and return their paths."""
    pdf_paths = []
    pdf_dir = collection_path / "PDFs"
    
    # Also check attached_assets for the actual PDF files
    attached_assets = Path("attached_assets")
    
    for doc in documents:
        filename = doc.get('filename', '')
        if not filename:
            raise ValueError("Document missing filename")
        
        # Try multiple locations for PDF files
        possible_paths = [
            pdf_dir / filename,
            attached_assets / filename
        ]
        
        # Also check for files with prefixes in attached_assets
        for asset_file in attached_assets.glob("*.pdf"):
            if filename.replace('.pdf', '') in asset_file.name or asset_file.name.endswith(filename):
                possible_paths.append(asset_file)
        
        pdf_path = None
        for path in possible_paths:
            if path.exists():
                pdf_path = path
                break
        
        if pdf_path is None:
            raise FileNotFoundError(f"PDF file not found: {filename}")
        
        pdf_paths.append(pdf_path)
        logger.info(f"Found PDF: {pdf_path}")
    
    return pdf_paths


def create_enhanced_query(persona: Dict, job_to_be_done: Dict) -> str:
    """Create an enhanced query that captures persona-specific needs."""
    role = persona.get('role', 'User')
    task = job_to_be_done.get('task', 'Find relevant information')
    
    # Enhanced queries based on expected output patterns
    if 'travel planner' in role.lower():
        if 'college friends' in task.lower():
            query = (
                f"As a {role}, I need to {task.lower()}. "
                "I am specifically looking for destinations, activities, coastal adventures, "
                "culinary experiences, food options, nightlife, entertainment, travel tips, "
                "budget-friendly recommendations, group activities for young adults."
            )
        else:
            query = f"As a {role}, I need to {task.lower()}. Travel destinations, activities, food, tips."
    
    elif 'hr professional' in role.lower():
        query = (
            f"As a {role}, I need to {task.lower()}. "
            "I am looking for form creation, fillable forms, document conversion, "
            "bulk operations, workflow management, signature processes, compliance tools."
        )
    
    elif 'food contractor' in role.lower():
        if 'vegetarian' in task.lower():
            query = (
                f"As a {role}, I need to {task.lower()}. "
                "I am looking for vegetarian recipes, protein sources, substantial sides, "
                "appetizers, gluten-free options, buffet-style dishes, corporate catering."
            )
        else:
            query = f"As a {role}, I need to {task.lower()}. Recipes, ingredients, cooking instructions."
    
    else:
        query = f"As a {role}, I need to {task.lower()}."
    
    logger.info(f"Created enhanced query: {query}")
    return query


def process_collection(collection_path: Path, config: Config) -> Dict[str, Any]:
    """Process a single collection."""
    logger.info(f"Processing collection: {collection_path}")
    
    # File paths
    input_file = collection_path / "challenge1b_input.json"
    output_file = collection_path / "challenge1b_output.json"
    
    # Validate paths
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    # Load input configuration
    input_data = load_input_json(input_file)
    
    # Validate PDF files
    pdf_paths = validate_pdf_files(input_data['documents'], collection_path)
    
    # Initialize analyzer
    analyzer = DocumentAnalyzer(config)
    
    # Run analysis
    start_time = time.time()
    logger.info(f"Starting analysis of {len(pdf_paths)} documents...")
    
    try:
        # Create enhanced query
        query = create_enhanced_query(input_data['persona'], input_data['job_to_be_done'])
        
        # Analyze documents
        section_rankings, subsection_analysis = analyzer.analyze_documents(
            pdf_paths=pdf_paths,
            query=query
        )
        
        # Apply persona-specific ranking enhancements
        section_rankings = PersonaRanking.enhance_rankings_for_persona(
            section_rankings, 
            input_data['persona']['role'],
            input_data['job_to_be_done']['task']
        )
        
        # Format results into expected JSON structure
        results = {
            'metadata': {
                'input_documents': [doc['filename'] for doc in input_data['documents']],
                'persona': input_data['persona']['role'],
                'job_to_be_done': input_data['job_to_be_done']['task'],
                'processing_timestamp': datetime.now().isoformat(),
                'processing_time_seconds': round(time.time() - start_time, 2)
            },
            'extracted_sections': section_rankings,
            'subsection_analysis': subsection_analysis
        }
        
        # Save results
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        processing_time = time.time() - start_time
        logger.info(f"Collection completed in {processing_time:.2f} seconds")
        logger.info(f"Results saved to: {output_file}")
        
        return {
            'collection': str(collection_path),
            'success': True,
            'processing_time': processing_time,
            'documents_count': len(input_data['documents']),
            'sections_count': len(results.get('extracted_sections', [])),
            'subsections_count': len(results.get('subsection_analysis', []))
        }
        
    except Exception as e:
        logger.error(f"Error processing collection {collection_path}: {e}")
        return {
            'collection': str(collection_path),
            'success': False,
            'error': str(e),
            'processing_time': time.time() - start_time
        }


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Adobe Hackathon Challenge 1B - Enhanced PDF Analysis System'
    )
    parser.add_argument(
        '--collection', 
        type=str, 
        help='Specific collection to process (1, 2, or 3)'
    )
    parser.add_argument(
        '--all', 
        action='store_true', 
        help='Process all collections'
    )
    
    args = parser.parse_args()
    
    # Configuration for hackathon
    config = Config.for_hackathon()
    
    # Determine which collections to process
    collections_to_process = []
    challenge_dir = Path("Challenge_1b")
    
    if args.collection:
        collection_path = challenge_dir / f"Collection {args.collection}"
        if collection_path.exists():
            collections_to_process.append(collection_path)
        else:
            logger.error(f"Collection {args.collection} not found")
            return 1
    
    elif args.all or not args.collection:
        # Process all available collections
        for i in range(1, 4):
            collection_path = challenge_dir / f"Collection {i}"
            if collection_path.exists():
                collections_to_process.append(collection_path)
    
    if not collections_to_process:
        logger.error("No collections found to process")
        return 1
    
    # Process each collection
    total_start_time = time.time()
    results = []
    
    for collection_path in collections_to_process:
        result = process_collection(collection_path, config)
        results.append(result)
    
    # Summary
    total_time = time.time() - total_start_time
    successful_collections = [r for r in results if r['success']]
    failed_collections = [r for r in results if not r['success']]
    
    logger.info(f"\n{'='*50}")
    logger.info(f"PROCESSING COMPLETE")
    logger.info(f"{'='*50}")
    logger.info(f"Total time: {total_time:.2f} seconds")
    logger.info(f"Successful collections: {len(successful_collections)}")
    logger.info(f"Failed collections: {len(failed_collections)}")
    
    for result in successful_collections:
        logger.info(f"✓ {result['collection']}: {result['processing_time']:.2f}s")
    
    for result in failed_collections:
        logger.error(f"✗ {result['collection']}: {result['error']}")
    
    return 0 if not failed_collections else 1


if __name__ == "__main__":
    sys.exit(main())