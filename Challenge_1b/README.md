# Adobe Hackathon Round 1B: Persona-Driven Document Intelligence System

An AI-powered document intelligence system that processes PDF collections and generates structured insights tailored to specific user personas and their job-to-be-done tasks.

## 🎯 Overview

This system analyzes 3-10 PDF documents per collection, extracts relevant content based on user personas (Travel Planner, HR Professional, Food Contractor), and outputs structured JSON with ranked sections and subsection analysis.

### Key Features

- **Persona-Driven Analysis**: Tailored content extraction based on user roles and requirements
- **Semantic Similarity**: Lightweight keyword-based TF-IDF approach for content relevance
- **Fast Processing**: Under 60 seconds per collection (3.78s - 13.21s typical)
- **Structured Output**: JSON format with metadata, extracted_sections, and subsection_analysis
- **Docker Support**: Containerized deployment for consistent execution

## 🏗️ Architecture

```
Document Intelligence System
├── PDF Processing (pdfplumber)
├── Semantic Analysis (keyword-based TF-IDF)
├── Persona Analysis (enhanced ranking)
├── Content Ranking (multi-factor scoring)
└── JSON Output Generation
```

### Core Components

- **`main_semantic.py`**: Enhanced main entry point with semantic analysis
- **`document_analyzer.py`**: Core document processing pipeline
- **`pdf_parser.py`**: PDF content extraction using pdfplumber
- **`embedder.py`**: Lightweight keyword-based embeddings
- **`retriever.py`**: Relevance scoring and content retrieval
- **`enhanced_ranking.py`**: Persona-specific ranking logic
- **`config.py`**: Configuration management

## Build Docker Image

```bash
# Build optimized Docker image
docker build -t adobe-document-intelligence:latest .
```

## Run Docker Container

```bash
 docker run --rm   -v $(pwd)/Challenge_1b:/app/Challenge_1b   adobe-document-intelligence:latest   python main_semantic.py --all
```


## 📁 Project Structure

```
Challenge_1b/
├── Collection 1/                    # Travel Planning
│   ├── PDFs/                       # South of France guides
│   ├── challenge1b_input.json      # Input configuration
│   └── challenge1b_output.json     # Analysis results
├── Collection 2/                    # Adobe Acrobat Learning
│   ├── PDFs/                       # Acrobat tutorials
│   ├── challenge1b_input.json      # Input configuration
│   └── challenge1b_output.json     # Analysis results
├── Collection 3/                    # Recipe Collection
│   ├── PDFs/                       # Cooking guides
│   ├── challenge1b_input.json      # Input configuration
│   └── challenge1b_output.json     # Analysis results
└── README.md
├── main_semantic.py                 # Enhanced main entry point
├── document_analyzer.py             # Core analysis pipeline
├── pdf_parser.py                   # PDF processing
├── embedder.py                     # Keyword embeddings
├── retriever.py                    # Content retrieval
├── enhanced_ranking.py             # Persona-specific ranking
├── config.py                       # Configuration
├── Dockerfile                      # Docker container config
├── pyproject.toml                  # Python dependencies
└── README.md                       # This file
```

## ⚙️ Configuration

### Input Format

Each collection requires a `challenge1b_input.json` file:

```json
{
  "challenge_info": {
    "challenge_id": "round_1b_XXX",
    "test_case_name": "specific_test_case"
  },
  "documents": [{"filename": "doc.pdf", "title": "Title"}],
  "persona": {"role": "User Persona"},
  "job_to_be_done": {"task": "Use case description"}
}
```

### Output Format

Generated `challenge1b_output.json`:

```json
{
  "metadata": {
    "input_documents": ["list"],
    "persona": "User Persona",
    "job_to_be_done": "Task description"
  },
  "extracted_sections": [
    {
      "document": "source.pdf",
      "section_title": "Title",
      "importance_rank": 1,
      "page_number": 1
    }
  ],
  "subsection_analysis": [
    {
      "document": "source.pdf",
      "refined_text": "Content",
      "page_number": 1
    }
  ]
}
```

## 🎭 Persona-Specific Logic

### Travel Planner
**Priority Order**: Cities/Destinations → Activities → Food → Tips → Entertainment

**Keywords**: destinations, coastal adventures, culinary experiences, nightlife, travel tips

### HR Professional  
**Priority Order**: Form Creation → Bulk Operations → Conversion → Workflow → Signatures

**Keywords**: fillable forms, bulk operations, workflow management, e-signatures

### Food Contractor
**Priority Order**: Protein Sources → Substantial Sides → Appetizers → Variety → Buffet

**Keywords**: vegetarian recipes, protein sources, gluten-free options, corporate catering


## 🐛 Troubleshooting

### Common Issues

1. **PDF Not Found**
   ```bash
   # Ensure PDFs are in correct directory structure
   ls -la Challenge_1b/Collection\ 1/PDFs/
   ```

2. **Low Relevance Scores**
   ```python
   # Adjust relevance threshold in config.py
   relevance_threshold=0.001  # Lower for more results
   ```

3. **Memory Issues**
   ```bash
   # Increase Docker memory limit
   docker run --memory=4g ...
   ```

4. **Permission Errors**
   ```bash
   # Fix file permissions
   chmod -R 755 Challenge_1b/
   chown -R $USER:$USER output/
   ```


## 📊 Performance Benchmarks

| Collection | Documents | Processing Time | Relevant Chunks | Sections |
|------------|-----------|----------------|-----------------|----------|
| Collection 1 | 7 PDFs | 3.78s | 37 chunks | 5 sections |
| Collection 2 | 15 PDFs | 13.21s | 50+ chunks | 5 sections |
| Collection 3 | 9 PDFs | 10.35s | 4 chunks | 4 sections |

### System Requirements

- **Memory**: 2GB minimum, 4GB recommended
- **CPU**: 1 core minimum, 2+ cores recommended
- **Storage**: 1GB for system, additional space for documents
- **Python**: 3.11+ (handled by Docker)


### Adding New Personas

1. Update `enhanced_ranking.py` with new persona logic
2. Add persona-specific keywords to query generation
3. Test with sample documents
4. Update documentation

## 📋 Dependencies

### Core Dependencies
- **pdfplumber==0.10.3**: PDF text extraction
- **Python 3.11+**: Runtime environment

### Development Dependencies
- **black**: Code formatting
- **pytest**: Testing framework
- **memory_profiler**: Performance monitoring

## 🏆 Competition Alignment

This system is specifically designed for the Adobe India Hackathon Round 1B, focusing on:

- ✅ **Processing Speed**: Sub-60 second requirement met
- ✅ **Output Format**: Exact JSON structure matching expected format
- ✅ **Persona Alignment**: Enhanced ranking logic for each persona type
- ✅ **Scalability**: Docker deployment for consistent execution
- ✅ **Accuracy**: Keyword-based semantic similarity optimized for challenge data
