# Adobe-India-Hackathon25-Round1_Submission-Brahmos
This is the submission repository for Round 1 of Adobe India Hackathon 2025,  Connecting the Dots Challenge, It has submission for Round 1A and 1B

# Adobe India Hackathon 2025 - "Connecting the Dots" Challenge

## 🎯 Project Overview

**Rethink Reading. Rediscover Knowledge**

This repository contains complete solutions for Adobe India Hackathon 2025's "Connecting the Dots" Challenge, reimagining PDF documents as intelligent, interactive experiences that understand structure, surface insights, and respond like trusted research companions.

### Challenge Vision
What if every time you opened a PDF, it didn't just sit there—it spoke to you, connected ideas, and narrated meaning across your entire library? That's the future we're building.

## 🏆 Achievements & Constraints Passed

### ✅ Round 1A: PDF Outline Extraction
- **Execution Time**: ≤ 10 seconds for 50-page PDFs ✓
- **Model Size**: ≤ 200MB (No ML models used, PyMuPDF only) ✓
- **Network**: No internet access required ✓
- **Architecture**: AMD64 compatibility ✓
- **Memory**: Within 16GB RAM limit ✓
- **Processing**: Automatic batch processing from input directory ✓
- **Output Format**: Valid JSON with title, H1/H2/H3 headings ✓
- **Multilingual**: Bonus multilingual handling support ✓

### ✅ Round 1B: Persona-Driven Document Intelligence
#### the challenge1b_output.json has been left unpopulated initially and the output will be generated when docker is run
- **Processing Time**: ≤ 60 seconds for document collections ✓
- **Model Size**: ≤ 1GB ✓
- **CPU Only**: No GPU dependencies ✓
- **Network**: Offline operation ✓
- **Output Format**: Structured JSON with metadata, sections, and subsections ✓
- **Persona Support**: Travel Planner, HR Professional, Food Contractor ✓
- **Collection Processing**: 3-10 PDFs per collection ✓

## 🚀 Project Structure

```
Adobe-India-Hackathon-2025/
├── Challenge_1a/                   # Round 1A: PDF Outline Extraction
│   ├── sample_dataset/
│   │   ├── outputs/               # Generated JSON outputs
│   │   ├── pdfs/                  # Input PDF files
│   │   └── schema/                # Output schema definition
│   ├── Dockerfile                 # Docker container config
│   ├── process_pdfs.py            # Main processing script
│   └── README.md                  # Challenge 1A documentation
├── Challenge_1b/                   # Round 1B: Persona-Driven Intelligence
│   ├── Collection 1/              # Travel Planning (7 PDFs)
│   ├── Collection 2/              # Adobe Acrobat Learning (15 PDFs)
│   ├── Collection 3/              # Recipe Collection (9 PDFs)
│   ├── main_semantic.py           # Enhanced main entry point
│   ├── document_analyzer.py       # Core analysis pipeline
│   ├── pdf_parser.py             # PDF content extraction
│   ├── embedder.py               # Keyword-based embeddings
│   ├── retriever.py              # Content retrieval system
│   ├── enhanced_ranking.py       # Persona-specific ranking
│   ├── Dockerfile                # Docker configuration
│   └── README.md                 # Challenge 1B documentation
└── README.md                      # This file
```

## 🎯 Challenge Solutions

### Round 1A: Understand Your Document
**Mission**: Extract structured outlines (title, H1/H2/H3 headings) from PDFs with machine-like precision.

**Key Features**:
- Multi-pass analysis: Document profiling → Candidate identification → Hierarchy classification
- Robust heading detection using font size, styling, spacing, and numbering patterns
- High-performance processing optimized for hackathon constraints
- Multilingual document support

**Technical Approach**:
1. **Document Profiling**: Extract text blocks with detailed metadata
2. **Candidate Identification**: Filter potential headings using multiple criteria
3. **Hierarchical Classification**: Group candidates and assign heading levels
4. **JSON Generation**: Format results into required structure

### Round 1B: Persona-Driven Document Intelligence
**Mission**: Build an intelligent document analyst that extracts and prioritizes relevant sections based on specific personas and their job-to-be-done.

**Key Features**:
- Persona-driven content analysis (Travel Planner, HR Professional, Food Contractor)
- Semantic similarity using lightweight TF-IDF approach
- Multi-collection document processing (3-10 PDFs)
- Structured output with importance ranking

**Supported Personas**:
- **Travel Planner**: Focus on destinations, activities, food, tips, entertainment
- **HR Professional**: Prioritize forms, workflows, bulk operations, signatures
- **Food Contractor**: Emphasize protein sources, sides, appetizers, buffet planning

## 🐳 Docker Deployment

### Challenge 1A
```bash
# Build
docker build --platform linux/amd64 -t pdf-processor .

# Run
docker run --rm \
  -v "$(pwd)/sample_dataset/pdfs:/app/input:ro" \
  -v "$(pwd)/sample_dataset/outputs:/app/output" \
  --network none \
  pdf-processor
```

### Challenge 1B
```bash
# Build
docker build -t adobe-document-intelligence:latest .

# Run
docker run --rm \
  -v $(pwd)/Challenge_1b:/app/Challenge_1b \
  adobe-document-intelligence:latest \
  python main_semantic.py --all
```

## 📊 Performance Benchmarks

### Round 1A Performance
- **Processing Speed**: < 10 seconds for 50-page documents
- **Memory Usage**: Optimized for 16GB RAM limit
- **Architecture**: AMD64 compatible, no ML models required
- **Accuracy**: High precision heading detection across document formats

### Round 1B Performance
| Collection | Documents | Processing Time | Status |
|------------|-----------|----------------|---------|
| Collection 1 (Travel) | 7 PDFs | 3.78s | ✅ |
| Collection 2 (HR) | 15 PDFs | 13.21s | ✅ |
| Collection 3 (Food) | 9 PDFs | 10.35s | ✅ |

## 🛠️ Technology Stack

### Round 1A
- **Language**: Python 3.10+
- **PDF Processing**: PyMuPDF (fitz) - chosen for speed and rich metadata
- **Container**: Docker with python:3.10-slim-bullseye
- **Processing**: Built-in regex and string processing (no ML models)

### Round 1B
- **Language**: Python 3.11+
- **PDF Processing**: pdfplumber for detailed text extraction
- **Semantic Analysis**: Keyword-based TF-IDF approach
- **Container**: Docker with optimized Python environment
- **Architecture**: Modular pipeline design

## 📋 Validation Checklist

### Round 1A ✅
- [x] All PDFs in input directory processed automatically
- [x] JSON output files generated for each PDF
- [x] Output format matches required structure
- [x] Processing completes within 10 seconds for 50-page PDFs
- [x] Solution works without internet access
- [x] Memory usage stays within 16GB limit
- [x] Compatible with AMD64 architecture
- [x] Output conforms to schema requirements

### Round 1B ✅
- [x] Processing time under 60 seconds per collection
- [x] CPU-only operation (no GPU dependencies)
- [x] Model size within 1GB limit
- [x] Offline operation (no internet access)
- [x] Structured JSON output with required format
- [x] Persona-specific
