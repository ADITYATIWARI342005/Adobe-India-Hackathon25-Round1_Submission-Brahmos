"""
PDF Outline Extraction System for Adobe Hackathon Round 1A

This system extracts hierarchical document structure (title and headings H1-H3)
from PDF files using a multi-pass analysis approach with PyMuPDF.

Performance targets:
- ≤10 seconds for 50-page PDF
- ≤200MB memory usage
- CPU-only operation
- Offline execution
"""

import fitz  # PyMuPDF
import json
import re
import os
from pathlib import Path
from collections import Counter, defaultdict
from typing import List, Dict, Tuple, Optional, Any
import sys


class PDFOutlineExtractor:
    """High-performance PDF outline extraction using multi-pass analysis."""
    
    def __init__(self, input_dir=None, output_dir=None):
        # Use provided directories or default to Docker container paths
        self.input_dir = Path(input_dir) if input_dir else Path("/app/input")
        self.output_dir = Path(output_dir) if output_dir else Path("/app/output")
        
        # For local testing, use Challenge_1a structure
        if not self.input_dir.exists():
            self.input_dir = Path("sample_dataset/pdfs")
            self.output_dir = Path("sample_dataset/outputs")
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def extract_text_blocks(self, doc: fitz.Document) -> List[Dict[str, Any]]:
        """
        Pass 1: Extract all text blocks with detailed metadata.
        
        Returns list of text blocks with font info, coordinates, and styling.
        """
        text_blocks = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Get text as dictionary with detailed formatting info
            text_dict = page.get_text("dict")
            
            for block in text_dict["blocks"]:
                if "lines" not in block:  # Skip image blocks
                    continue
                    
                for line in block["lines"]:
                    for span in line["spans"]:
                        # Extract text and clean it
                        text = span["text"].strip()
                        if not text:
                            continue
                            
                        # Get font properties
                        font_size = span["size"]
                        font_name = span["font"]
                        bbox = span["bbox"]
                        flags = span["flags"]
                        
                        # Determine if text is bold
                        is_bold = bool(flags & 2**4)  # Bold flag in PyMuPDF
                        
                        text_block = {
                            "text": text,
                            "page": page_num + 1,  # 1-indexed pages
                            "bbox": bbox,
                            "font_size": font_size,
                            "font_name": font_name,
                            "is_bold": is_bold,
                            "flags": flags,
                            "x_pos": bbox[0],  # Left position for indentation analysis
                            "y_pos": bbox[1],  # Top position for spacing analysis
                            "width": bbox[2] - bbox[0],
                            "height": bbox[3] - bbox[1]
                        }
                        
                        text_blocks.append(text_block)
        
        return text_blocks
    
    def analyze_document_profile(self, text_blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Pass 1: Analyze document to identify body text and establish baseline.
        
        Returns document profile with body text size, font statistics, etc.
        """
        if not text_blocks:
            return {"body_text_size": 12, "font_sizes": [], "avg_line_spacing": 15}
        
        # Collect font size statistics
        font_sizes = [block["font_size"] for block in text_blocks]
        font_size_counter = Counter(font_sizes)
        
        # Most common font size is likely body text
        body_text_size = font_size_counter.most_common(1)[0][0]
        
        # Calculate average line spacing for the document
        y_positions = [block["y_pos"] for block in text_blocks]
        y_positions.sort()
        
        line_spacings = []
        for i in range(1, len(y_positions)):
            spacing = y_positions[i] - y_positions[i-1]
            if 5 < spacing < 50:  # Reasonable line spacing range
                line_spacings.append(spacing)
        
        avg_line_spacing = sum(line_spacings) / len(line_spacings) if line_spacings else 15
        
        return {
            "body_text_size": body_text_size,
            "font_sizes": sorted(set(font_sizes), reverse=True),
            "avg_line_spacing": avg_line_spacing,
            "font_size_distribution": dict(font_size_counter)
        }
    
    def identify_heading_candidates(self, text_blocks: List[Dict[str, Any]], 
                                  profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Pass 2: Identify potential heading candidates using multiple criteria.
        
        Filters text blocks that are likely headings based on font size,
        styling, spacing, line length, and numbering patterns.
        """
        candidates = []
        body_text_size = profile["body_text_size"]
        
        # Merge adjacent text blocks that might be split heading text
        merged_blocks = self._merge_split_headings(text_blocks)
        
        # Sort blocks by page and vertical position
        merged_blocks.sort(key=lambda x: (x["page"], x["y_pos"]))
        
        # Identify distinct font styles and their characteristics
        font_styles = self._analyze_font_styles(merged_blocks)
        
        for block in merged_blocks:
            text = block["text"].strip()
            font_size = block["font_size"]
            
            # Skip very small text or single characters
            if len(text) < 3:
                continue
            
            # Skip obvious non-headings
            if self._is_non_heading(text, block, body_text_size):
                continue
            
            # Check for numbering patterns (strong heading indicator)
            has_numbering = bool(re.match(r"^\d+(\.\d+)*\.?\s+", text))
            
            # Check if this text block has heading characteristics
            is_heading_candidate = self._evaluate_heading_candidate(
                block, text, body_text_size, font_styles, has_numbering
            )
            
            # Additional heuristics for title detection
            is_potential_title = (
                block["page"] == 1 and  # On first page
                font_size > body_text_size * 1.3 and  # Significantly larger
                block["y_pos"] < 300 and  # Near top of page
                len(text) <= 100 and  # Reasonable title length
                not has_numbering  # Titles usually don't have numbering
            )
            
            if is_heading_candidate or is_potential_title:
                candidate = block.copy()
                candidate["has_numbering"] = has_numbering
                candidate["numbering_level"] = self._get_numbering_level(text) if has_numbering else None
                candidate["is_potential_title"] = is_potential_title
                candidates.append(candidate)
        
        return candidates
    
    def _merge_split_headings(self, text_blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge adjacent text blocks that are likely split parts of a single heading."""
        if not text_blocks:
            return []
        
        merged = []
        current_block = text_blocks[0].copy()
        
        for i in range(1, len(text_blocks)):
            block = text_blocks[i]
            
            # Check if this block should be merged with the current one
            should_merge = (
                block["page"] == current_block["page"] and
                abs(block["y_pos"] - current_block["y_pos"]) < 5 and  # Same line
                abs(block["font_size"] - current_block["font_size"]) < 1 and  # Same font size
                block["is_bold"] == current_block["is_bold"] and  # Same bold status
                block["x_pos"] > current_block["x_pos"]  # To the right
            )
            
            if should_merge:
                # Merge the text
                current_block["text"] += " " + block["text"].strip()
                # Update bounding box
                current_block["bbox"] = [
                    current_block["bbox"][0],  # Keep left x
                    current_block["bbox"][1],  # Keep top y
                    block["bbox"][2],          # Update right x
                    max(current_block["bbox"][3], block["bbox"][3])  # Update bottom y
                ]
                current_block["width"] = current_block["bbox"][2] - current_block["bbox"][0]
            else:
                merged.append(current_block)
                current_block = block.copy()
        
        merged.append(current_block)
        return merged
    
    def _analyze_font_styles(self, text_blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze font styles in the document to understand hierarchy."""
        font_stats = {}
        
        for block in text_blocks:
            font_key = block["font_name"]
            if font_key not in font_stats:
                font_stats[font_key] = {"count": 0, "sizes": [], "bold_count": 0}
            
            font_stats[font_key]["count"] += 1
            font_stats[font_key]["sizes"].append(block["font_size"])
            if block["is_bold"]:
                font_stats[font_key]["bold_count"] += 1
        
        # Calculate average sizes and boldness ratios
        for font_key in font_stats:
            sizes = font_stats[font_key]["sizes"]
            font_stats[font_key]["avg_size"] = sum(sizes) / len(sizes)
            font_stats[font_key]["max_size"] = max(sizes)
            font_stats[font_key]["bold_ratio"] = font_stats[font_key]["bold_count"] / font_stats[font_key]["count"]
        
        return font_stats
    
    def _is_non_heading(self, text: str, block: Dict[str, Any], body_text_size: float) -> bool:
        """Check if text is obviously not a heading."""
        text_lower = text.lower()
        
        # Skip revision history entries
        if re.match(r"^\d+\.\d+\s+\d{1,2}\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)", text_lower):
            return True
            
        # Skip version numbers
        if re.match(r"^version\s+\d+\.\d+", text_lower):
            return True
            
        # Skip copyright and page references
        if any(word in text_lower for word in ["copyright", "©", "page", "version 2014"]):
            return True
            
        # Skip very small text
        if block["font_size"] < body_text_size * 0.85:
            return True
            
        # Skip decorative separators
        if re.match(r"^[-=_*•]+$", text.strip()):
            return True
            
        return False
    
    def _evaluate_heading_candidate(self, block: Dict[str, Any], text: str, 
                                   body_text_size: float, font_styles: Dict, 
                                   has_numbering: bool) -> bool:
        """Evaluate if a text block is likely a heading candidate."""
        font_size = block["font_size"]
        is_bold = block["is_bold"]
        
        # Strong indicators
        if has_numbering:
            return True
            
        # Font size significantly larger than body text
        if font_size > body_text_size * 1.3:
            return True
            
        # Bold text that's larger than body text
        if is_bold and font_size > body_text_size * 1.1:
            return True
            
        # Check for specific heading patterns in text
        heading_patterns = [
            r"^\d+\.\s+[A-Z]",  # "1. Introduction"
            r"^[A-Z][a-z]+(\s+[A-Z][a-z]+)*\s*$",  # Title case like "Introduction to Something"
            r"^[A-Z\s]+$",  # ALL CAPS (but not too long)
        ]
        
        for pattern in heading_patterns:
            if re.match(pattern, text) and len(text) <= 80:
                return True
                
        return False
    
    def _get_numbering_level(self, text: str) -> Optional[int]:
        """Extract numbering level from numbered heading (e.g., '1.2.3' -> 3)."""
        match = re.match(r"^(\d+(?:\.\d+)*)\.?\s+", text)
        if match:
            numbers = match.group(1)
            return numbers.count('.') + 1  # Count dots + 1 for level
        return None
    
    def classify_heading_hierarchy(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Pass 3: Classify candidates into title, H1, H2, H3 hierarchy.
        
        Uses font size, numbering patterns, and indentation to determine levels.
        """
        if not candidates:
            return []
        
        # Separate title candidates from heading candidates
        title_candidates = [c for c in candidates if c.get("is_potential_title", False)]
        heading_candidates = [c for c in candidates if not c.get("is_potential_title", False)]
        
        # Identify title (largest, earliest, most prominent)
        title = None
        if title_candidates:
            title = max(title_candidates, key=lambda x: (x["font_size"], -x["y_pos"]))
        elif heading_candidates:
            # If no clear title candidates, use the first large heading
            first_page_headings = [c for c in heading_candidates if c["page"] == 1]
            if first_page_headings:
                title = max(first_page_headings, key=lambda x: x["font_size"])
        
        # Remove title from heading candidates
        if title:
            heading_candidates = [c for c in heading_candidates if c != title]
        
        # Group headings by style characteristics
        style_groups = defaultdict(list)
        for candidate in heading_candidates:
            # Create style key based on font size and bold status
            style_key = (candidate["font_size"], candidate["is_bold"])
            style_groups[style_key].append(candidate)
        
        # Sort style groups by font size (descending)
        sorted_styles = sorted(style_groups.keys(), key=lambda x: x[0], reverse=True)
        
        # Assign heading levels
        classified_headings = []
        
        for candidate in heading_candidates:
            level = self._determine_heading_level(candidate, sorted_styles, style_groups)
            
            if level:
                classified_headings.append({
                    "level": level,
                    "text": candidate["text"],
                    "page": candidate["page"]
                })
        
        # Sort by page and position
        classified_headings.sort(key=lambda x: (x["page"], 
                                              next(c["y_pos"] for c in heading_candidates 
                                                   if c["text"] == x["text"])))
        
        result = []
        if title:
            result.append({
                "title": title["text"],
                "headings": classified_headings
            })
        else:
            result.append({
                "title": "",
                "headings": classified_headings
            })
        
        return result
    
    def _determine_heading_level(self, candidate: Dict[str, Any], 
                               sorted_styles: List[Tuple], 
                               style_groups: Dict) -> Optional[str]:
        """Determine the heading level (H1, H2, H3) for a candidate."""
        
        # Use numbering level if available (most reliable)
        if candidate.get("has_numbering") and candidate.get("numbering_level"):
            numbering_level = candidate["numbering_level"]
            if numbering_level == 1:
                return "H1"
            elif numbering_level == 2:
                return "H2"
            elif numbering_level >= 3:
                return "H3"
        
        # Use font-based classification
        candidate_style = (candidate["font_size"], candidate["is_bold"])
        
        try:
            style_rank = sorted_styles.index(candidate_style)
            
            # Map style rank to heading level
            if style_rank == 0:
                return "H1"
            elif style_rank == 1:
                return "H2"
            elif style_rank <= 3:  # Allow some flexibility for H3
                return "H3"
        except ValueError:
            pass
        
        # Fallback: use relative font size
        font_size = candidate["font_size"]
        if font_size >= 18:
            return "H1"
        elif font_size >= 14:
            return "H2"
        elif font_size >= 12:
            return "H3"
        
        return None
    
    def generate_json_output(self, result: List[Dict[str, Any]], output_path: Path):
        """
        Pass 4: Generate the final JSON output in the required format.
        """
        if not result:
            output_data = {"title": "", "outline": []}
        else:
            title = result[0].get("title", "")
            headings = result[0].get("headings", [])
            
            output_data = {
                "title": title,
                "outline": headings
            }
        
        # Write JSON output
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    def process_single_pdf(self, pdf_path: Path) -> bool:
        """Process a single PDF file and generate JSON output."""
        try:
            print(f"Processing: {pdf_path.name}")
            
            # Open PDF document
            doc = fitz.open(pdf_path)
            
            if len(doc) == 0:
                print(f"Warning: {pdf_path.name} is empty")
                return False
            
            # Multi-pass analysis
            print("  Pass 1: Extracting text blocks...")
            text_blocks = self.extract_text_blocks(doc)
            
            print("  Pass 1: Analyzing document profile...")
            profile = self.analyze_document_profile(text_blocks)
            
            print("  Pass 2: Identifying heading candidates...")
            candidates = self.identify_heading_candidates(text_blocks, profile)
            
            print("  Pass 3: Classifying hierarchy...")
            result = self.classify_heading_hierarchy(candidates)
            
            # Generate output file path
            output_file = self.output_dir / f"{pdf_path.stem}.json"
            
            print("  Pass 4: Generating JSON output...")
            self.generate_json_output(result, output_file)
            
            doc.close()
            print(f"  ✓ Generated: {output_file.name}")
            return True
            
        except Exception as e:
            print(f"Error processing {pdf_path.name}: {str(e)}")
            return False
    
    def process_all_pdfs(self):
        """Process all PDF files in the input directory."""
        if not self.input_dir.exists():
            print(f"Error: Input directory {self.input_dir} does not exist")
            return
        
        # Find all PDF files
        pdf_files = list(self.input_dir.glob("*.pdf"))
        
        if not pdf_files:
            print(f"No PDF files found in {self.input_dir}")
            return
        
        print(f"Found {len(pdf_files)} PDF file(s) to process")
        
        successful = 0
        for pdf_file in pdf_files:
            if self.process_single_pdf(pdf_file):
                successful += 1
        
        print(f"\nProcessing complete: {successful}/{len(pdf_files)} files processed successfully")


def main():
    """Main entry point for the PDF outline extraction system."""
    print("PDF Outline Extraction System - Adobe Hackathon Round 1A")
    print("=" * 60)
    
    extractor = PDFOutlineExtractor()
    extractor.process_all_pdfs()


if __name__ == "__main__":
    main()
