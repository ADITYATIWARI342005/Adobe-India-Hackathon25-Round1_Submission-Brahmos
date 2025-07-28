# PDF Outline Extraction System - Round 1A

A high-performance PDF outline extraction model built for the Adobe India Hackathon 2025, Round 1A challenge.

## Overview

The system extracts structured document outlines (title and hierarchical headings H1-H3) from PDF files using a sophisticated multi-pass analysis approach with PyMuPDF.

## Features

- **Multi-pass Analysis**: Document profiling → Candidate identification → Hierarchy classification → JSON generation
- **Robust Heading Detection**: Uses font size, styling, spacing, and numbering patterns (not just font size)
- **High Performance**: Optimized for ≤10 seconds processing time for 50-page PDFs
- **Multilingual Support**: Handles various document types and languages
- **Offline Operation**: No internet access required during runtime

## Technical Approach

### Pass 1: Document Profiling
- Extracts all text blocks with detailed metadata (font, size, position, styling)
- Identifies body text baseline using font frequency analysis
- Calculates document-wide statistics (spacing, positioning patterns)

### Pass 2: Heading Candidate Identification
Filters potential headings using multiple criteria:
- Font size relative to body text
- Bold styling and formatting
- Text length and positioning
- Vertical spacing patterns
- Numbering detection (regex-based)

### Pass 3: Hierarchical Classification
- Groups candidates by style characteristics
- Uses numbering patterns for definitive level assignment
- Applies font-based ranking for style groups
- Handles title identification (largest, most prominent text)

### Pass 4: JSON Output Generation
- Formats results into required JSON structure
- Ensures proper ordering and page numbering
- Handles edge cases and empty documents

## Requirements Met

- ✅ Execution time ≤ 10 seconds for 50-page PDF
- ✅ Model size ≤ 200MB (uses PyMuPDF only, no ML models)
- ✅ CPU-only operation (AMD64 architecture)
- ✅ No internet access required
- ✅ Memory efficient (within 16GB limit)
- ✅ Processes all PDFs from `/app/sample_dataset/pdfs` automatically
- ✅ Generates `filename.json` for each `filename.pdf`

## Validation Checklist
- ✅ All PDFs in input directory are processed
- ✅ JSON output files are generated for each PDF
- ✅ Output format matches required structure
- ✅ Output conforms to schema in sample_dataset/schema/output_schema.json
- ✅ Processing completes within 10 seconds for 50-page PDFs
- ✅ Solution works without internet access
- ✅ Memory usage stays within 16GB limit
- ✅ Compatible with AMD64 architecture

## Technology Stack

- **Language**: Python 3.10+
- **PDF Processing**: PyMuPDF (fitz) - chosen for speed and rich metadata
- **Container**: Docker with python:3.10-slim-bullseye
- **Text Processing**: Built-in regex and string processing

## Usage

### Building the Docker Image

```bash
docker build --platform linux/amd64 -t pdf-processor .
```

### Running the Container

```bash
docker run --rm \
  -v "$(pwd)/sample_dataset/pdfs:/app/input:ro" \
  -v "$(pwd)/sample_dataset/outputs:/app/output" \
  --network none \
  pdf-processor
```

### Input/Output Structure

### Input/Output Structure

**Input**: PDF files in `/app/sample_dataset/pdfs/` directory
- Contains sample PDF documents for processing

**Output**: JSON files in `/app/sample_dataset/outputs/` directory with the same base filename
- Generated outline extraction results
- Format defined in schema/output_schema.json


#### Expected JSON Output Format

```json
{  
}  
"title": "Understanding AI",  
"outline": [  
{ "level": "H1", "text": "Introduction", "page": 1 },  
{ "level": "H2", "text": "What is AI?", "page": 2 },  
{ "level": "H3", "text": "History of AI", "page": 3 }  
]  
```

## Performance Benchmarks

- **Processing Speed**: < 10 seconds for 50-page documents
- **Memory Usage**: Optimized for 16GB RAM limit
- **Accuracy**: High precision heading detection across various document formats

## Architecture

```
PDF Input → Document Profiling → Candidate Identification → 
Hierarchy Classification → JSON Output Generation → Result Export
```

## Development Notes

- No machine learning models required
- Relies on sophisticated heuristics and document structure analysis
- Optimized for hackathon constraints and evaluation criteria
- Handles edge cases including documents without clear hierarchical structure
