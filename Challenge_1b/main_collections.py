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


def validate_pdf_files(documents: List[Dict], pdf_dir: Path) -> List[Path]:
    """Validate that all PDF files exist and return their paths."""
    pdf_paths = []
    
    for doc in documents:
        filename = doc.get('filename', '')
        if not filename:
            raise ValueError("Document missing filename")
        
        pdf_path = pdf_dir / filename
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        pdf_paths.append(pdf_path)
        logger.info(f"Found PDF: {pdf_path}")
    
    return pdf_paths


def process_collection(collection_path: Path, config: Config) -> Dict[str, Any]:
    """Process a single collection."""
    logger.info(f"Processing collection: {collection_path}")
    
    # File paths
    input_file = collection_path / "challenge1b_input.json"
    output_file = collection_path / "challenge1b_output.json"
    pdf_dir = collection_path / "PDFs"
    
    # Validate paths
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    if not pdf_dir.exists():
        raise FileNotFoundError(f"PDF directory not found: {pdf_dir}")
    
    # Load input configuration
    input_data = load_input_json(input_file)
    
    # Validate PDF files
    pdf_paths = validate_pdf_files(input_data['documents'], pdf_dir)
    
    # Initialize analyzer
    analyzer = DocumentAnalyzer(config)
    
    # Run analysis
    start_time = time.time()
    logger.info(f"Starting analysis of {len(pdf_paths)} documents...")
    
    try:
        # Create query combining persona and task
        query = f"As a {input_data['persona']['role']}: {input_data['job_to_be_done']['task']}"
        
        # Analyze documents
        section_rankings, subsection_analysis = analyzer.analyze_documents(
            pdf_paths=pdf_paths,
            query=query
        )
        
        # Format results into expected JSON structure
        results = {
            'metadata': {
                'input_documents': [doc['filename'] for doc in input_data['documents']],
                'persona': input_data['persona']['role'],
                'job_to_be_done': input_data['job_to_be_done']['task']
            },
            'extracted_sections': section_rankings,
            'subsection_analysis': subsection_analysis
        }
        
        processing_time = time.time() - start_time
        
        # Add processing metadata
        results['metadata']['processing_timestamp'] = datetime.now().isoformat()
        results['metadata']['processing_time_seconds'] = round(processing_time, 2)
        results['metadata']['collection_path'] = str(collection_path)
        
        # Save results
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
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
        description='Adobe Hackathon Challenge 1B - Multi-Collection PDF Analysis System'
    )
    parser.add_argument(
        '--collection', '-c',
        type=str,
        help='Path to specific collection directory to process'
    )
    parser.add_argument(
        '--all', '-a',
        action='store_true',
        help='Process all collections in Challenge_1b directory'
    )
    parser.add_argument(
        '--base-dir', '-b',
        type=str,
        default='Challenge_1b',
        help='Base directory containing collections (default: Challenge_1b)'
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize configuration
        config = Config()
        logger.info("Initialized system configuration")
        
        results = []
        
        if args.collection:
            # Process single collection
            collection_path = Path(args.collection)
            result = process_collection(collection_path, config)
            results.append(result)
            
        elif args.all:
            # Process all collections
            base_dir = Path(args.base_dir)
            if not base_dir.exists():
                raise FileNotFoundError(f"Base directory not found: {base_dir}")
            
            collection_dirs = [d for d in base_dir.iterdir() if d.is_dir() and d.name.startswith('Collection')]
            collection_dirs.sort()  # Process in order
            
            if not collection_dirs:
                raise FileNotFoundError(f"No collection directories found in {base_dir}")
            
            logger.info(f"Found {len(collection_dirs)} collections to process")
            
            for collection_dir in collection_dirs:
                result = process_collection(collection_dir, config)
                results.append(result)
        
        else:
            # Backward compatibility - process legacy format
            logger.info("No collection specified, using backward compatibility mode")
            
            # Try to find input files in attached_assets
            input_files = [
                Path("attached_assets/challenge1b_collection1_input_1753641058463.json"),
                Path("attached_assets/collection1_challenge1b_input_1753641550727.json")
            ]
            
            input_data = None
            for input_file in input_files:
                if input_file.exists():
                    try:
                        input_data = load_input_json(input_file)
                        break
                    except Exception as e:
                        logger.warning(f"Failed to load {input_file}: {e}")
                        continue
            
            if input_data is None:
                raise FileNotFoundError("No valid input configuration found. Use --help for usage.")
            
            # Process using attached_assets
            analyzer = DocumentAnalyzer(config)
            start_time = time.time()
            
            # Validate PDF files in attached_assets
            pdf_paths = []
            for doc in input_data['documents']:
                filename = doc.get('filename', '')
                # Try to find the actual file with the original logic
                for asset_file in Path('attached_assets').glob('*.pdf'):
                    if filename.replace('.pdf', '') in asset_file.name:
                        pdf_paths.append(asset_file)
                        break
                else:
                    # Try exact filename match
                    exact_path = Path('attached_assets') / filename
                    if exact_path.exists():
                        pdf_paths.append(exact_path)
            
            if not pdf_paths:
                raise FileNotFoundError("No PDF files found in attached_assets")
            
            # Create query and analyze
            query = f"As a {input_data['persona']['role']}: {input_data['job_to_be_done']['task']}"
            section_rankings, subsection_analysis = analyzer.analyze_documents(
                pdf_paths=pdf_paths,
                query=query
            )
            
            # Format results
            results_data = {
                'metadata': {
                    'input_documents': [doc['filename'] for doc in input_data['documents']],
                    'persona': input_data['persona']['role'],
                    'job_to_be_done': input_data['job_to_be_done']['task']
                },
                'extracted_sections': section_rankings,
                'subsection_analysis': subsection_analysis
            }
            
            processing_time = time.time() - start_time
            results_data['metadata']['processing_timestamp'] = datetime.now().isoformat()
            results_data['metadata']['processing_time_seconds'] = round(processing_time, 2)
            
            # Save results
            output_file = "challenge1b_output.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results_data, f, indent=2, ensure_ascii=False)
            
            results.append({
                'collection': 'attached_assets',
                'success': True,
                'processing_time': processing_time,
                'documents_count': len(input_data['documents']),
                'sections_count': len(results_data.get('extracted_sections', [])),
                'subsections_count': len(results_data.get('subsection_analysis', []))
            })
        
        # Print summary
        print("\n" + "="*50)
        print("ANALYSIS SUMMARY")
        print("="*50)
        
        successful_results = [r for r in results if r.get('success', False)]
        failed_results = [r for r in results if not r.get('success', False)]
        
        if successful_results:
            total_time = sum(r['processing_time'] for r in successful_results)
            total_docs = sum(r['documents_count'] for r in successful_results)
            total_sections = sum(r['sections_count'] for r in successful_results)
            total_subsections = sum(r['subsections_count'] for r in successful_results)
            
            print(f"Successful Collections: {len(successful_results)}")
            for result in successful_results:
                print(f"\n  {result['collection']}:")
                print(f"    Processing Time: {result['processing_time']:.2f}s")
                print(f"    Documents: {result['documents_count']}")
                print(f"    Sections: {result['sections_count']}")
                print(f"    Subsections: {result['subsections_count']}")
            
            print(f"\nTOTAL:")
            print(f"  Processing Time: {total_time:.2f} seconds")
            print(f"  Documents: {total_docs}")
            print(f"  Sections: {total_sections}")
            print(f"  Subsections: {total_subsections}")
        
        if failed_results:
            print(f"\nFailed Collections: {len(failed_results)}")
            for result in failed_results:
                print(f"  {result['collection']}: {result.get('error', 'Unknown error')}")
        
        print("="*50)
        
        # Exit with appropriate code
        sys.exit(0 if not failed_results else 1)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()