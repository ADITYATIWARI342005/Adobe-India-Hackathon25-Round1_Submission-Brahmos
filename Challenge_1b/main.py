import json
import sys
import time
import logging
from pathlib import Path
from typing import Dict, Any, List
import traceback

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


def validate_pdf_files(documents: List[Dict], base_path: Path) -> List[Path]:
    """Validate that all PDF files exist and return their paths."""
    pdf_paths = []
    
    for doc in documents:
        filename = doc.get('filename', '')
        if not filename:
            raise ValueError("Document missing filename")
        
        # Try different possible locations for PDF files
        # Handle both original names and the actual file names with prefixes
        actual_filename = None
        for asset_file in Path('attached_assets').glob('*.pdf'):
            if filename.replace('.pdf', '') in asset_file.name:
                actual_filename = asset_file.name
                break
        
        possible_paths = [
            base_path / filename,
            base_path / 'attached_assets' / filename,
            Path('attached_assets') / filename,
            Path(filename)
        ]
        
        if actual_filename:
            possible_paths.extend([
                base_path / 'attached_assets' / actual_filename,
                Path('attached_assets') / actual_filename
            ])
        
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


def create_analysis_query(persona: Dict, job_to_be_done: Dict) -> str:
    """Create an enriched query for semantic analysis."""
    role = persona.get('role', 'User')
    task = job_to_be_done.get('task', 'Find relevant information')
    
    # Create a rich query that combines persona and task context
    if 'travel planner' in role.lower() and 'college friends' in task.lower():
        query = (
            f"As a {role}, I need to find information to help me {task.lower()}. "
            "I am looking for fun activities, nightlife, entertainment, dining options, "
            "budget-friendly recommendations, group activities, cultural experiences, "
            "and practical travel tips suitable for young adults and college students."
        )
    else:
        query = f"As a {role}, I need to find information to help me {task.lower()}."
    
    logger.info(f"Created analysis query: {query}")
    return query


def generate_output_json(
    input_data: Dict,
    section_rankings: List[Dict],
    subsection_analysis: List[Dict],
    processing_time: float
) -> Dict[str, Any]:
    """Generate the final output JSON in the required format."""
    
    # Extract document names from input
    doc_names = [doc['filename'] for doc in input_data['documents']]
    
    output = {
        "metadata": {
            "input_documents": doc_names,
            "persona": input_data['persona']['role'],
            "job_to_be_done": input_data['job_to_be_done']['task'],
            "processing_timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3],
            "processing_time_seconds": round(processing_time, 2)
        },
        "extracted_sections": section_rankings,
        "subsection_analysis": subsection_analysis
    }
    
    return output


def main():
    """Main execution function."""
    start_time = time.time()
    
    try:
        # Configuration
        config = Config()
        
        # Determine input file path
        if len(sys.argv) > 1:
            input_path = Path(sys.argv[1])
        else:
            # Look for input files in common locations
            possible_inputs = [
                Path('challenge1b_input.json'),
                Path('attached_assets/challenge1b_collection1_input_1753639458907.json'),
                Path('input.json')
            ]
            
            input_path = None
            for path in possible_inputs:
                if path.exists():
                    input_path = path
                    break
            
            if input_path is None:
                raise FileNotFoundError("No input JSON file found")
        
        logger.info(f"Using input file: {input_path}")
        
        # Load input data
        input_data = load_input_json(input_path)
        
        # Validate PDF files
        pdf_paths = validate_pdf_files(input_data['documents'], input_path.parent)
        
        # Create analysis query
        query = create_analysis_query(input_data['persona'], input_data['job_to_be_done'])
        
        # Initialize document analyzer
        logger.info("Initializing document analyzer...")
        analyzer = DocumentAnalyzer(config)
        
        # Process documents
        logger.info("Processing documents...")
        section_rankings, subsection_analysis = analyzer.analyze_documents(pdf_paths, query)
        
        # Generate output
        processing_time = time.time() - start_time
        output = generate_output_json(input_data, section_rankings, subsection_analysis, processing_time)
        
        # Write output
        output_path = Path('challenge1b_output.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Analysis completed in {processing_time:.2f} seconds")
        logger.info(f"Output written to: {output_path}")
        logger.info(f"Found {len(section_rankings)} relevant sections")
        logger.info(f"Generated {len(subsection_analysis)} subsection analyses")
        
        # Print summary
        print(f"\n=== ANALYSIS COMPLETE ===")
        print(f"Processing time: {processing_time:.2f} seconds")
        print(f"Documents processed: {len(pdf_paths)}")
        print(f"Sections identified: {len(section_rankings)}")
        print(f"Output file: {output_path}")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
