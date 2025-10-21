from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from typing import Dict
from datetime import datetime

class DocumentGenerator:
    def __init__(self):
        pass
    
    def generate_document(
        self, 
        country1: str, 
        country2: str, 
        domain: str, 
        analysis: Dict, 
        filepath: str
    ):
        doc = Document()
        
        self._add_title(doc, f"Comparative Analysis: {country1} vs {country2}")
        self._add_subtitle(doc, f"Technology Domain: {domain}")
        self._add_metadata(doc)
        
        doc.add_paragraph()
        
        self._add_section_header(doc, "Executive Summary")
        doc.add_paragraph(analysis.get("overall_analysis", "Analysis not available."))
        
        doc.add_page_break()
        
        self._add_section_header(doc, "Key Metrics Comparison")
        metrics = analysis.get("metrics", {})
        if metrics:
            table = doc.add_table(rows=1, cols=3)
            table.style = 'Light Grid Accent 1'
            
            header_cells = table.rows[0].cells
            header_cells[0].text = "Metric"
            header_cells[1].text = country1
            header_cells[2].text = country2
            
            for header_cell in header_cells:
                for paragraph in header_cell.paragraphs:
                    paragraph.runs[0].font.bold = True
            
            metrics1 = metrics.get(country1, {})
            metrics2 = metrics.get(country2, {})
            
            metric_labels = {
                "total_companies_mentioned": "Organizations Mentioned",
                "recent_developments_count": "Recent Developments",
                "normalized_activity_score": "Activity Score (normalized)",
                "text_coverage": "Data Coverage (chars)"
            }
            
            for key, label in metric_labels.items():
                row = table.add_row()
                row.cells[0].text = label
                row.cells[1].text = str(metrics1.get(key, "N/A"))
                row.cells[2].text = str(metrics2.get(key, "N/A"))
        
        doc.add_paragraph()
        
        self._add_section_header(doc, f"{country1} - Detailed Analysis")
        summary1 = analysis.get("summary", {}).get(country1, "No data available.")
        doc.add_paragraph(summary1)
        
        self._add_subsection_header(doc, "Key Organizations and Entities")
        resources1 = analysis.get("resources", {}).get(country1, [])
        if resources1:
            for resource in resources1:
                doc.add_paragraph(resource, style='List Bullet')
        else:
            doc.add_paragraph("Information not available.")
        
        doc.add_paragraph()
        
        self._add_section_header(doc, f"{country2} - Detailed Analysis")
        summary2 = analysis.get("summary", {}).get(country2, "No data available.")
        doc.add_paragraph(summary2)
        
        self._add_subsection_header(doc, "Key Organizations and Entities")
        resources2 = analysis.get("resources", {}).get(country2, [])
        if resources2:
            for resource in resources2:
                doc.add_paragraph(resource, style='List Bullet')
        else:
            doc.add_paragraph("Information not available.")
        
        doc.add_page_break()
        
        self._add_section_header(doc, "Comparative Analysis by Category")
        
        comparison = analysis.get("comparison", {})
        if comparison:
            table = doc.add_table(rows=1, cols=2)
            table.style = 'Light Grid Accent 1'
            
            header_cells = table.rows[0].cells
            header_cells[0].text = "Category"
            header_cells[1].text = "Analysis"
            
            for header_cell in header_cells:
                for paragraph in header_cell.paragraphs:
                    paragraph.runs[0].font.bold = True
            
            for category, result in comparison.items():
                row_cells = table.add_row().cells
                row_cells[0].text = category.replace("_", " ").title()
                row_cells[1].text = result
        else:
            doc.add_paragraph("Comparison data not available.")
        
        doc.add_paragraph()
        
        self._add_section_header(doc, "Recent Developments and News")
        news_items = analysis.get("news", [])
        if news_items:
            for item in news_items:
                p = doc.add_paragraph(style='List Bullet')
                source = item.get("source", "Unknown Source")
                headline = item.get("headline", "No headline available")
                year_indicator = " [Recent]" if item.get("recent", False) else ""
                p.add_run(f"{source}{year_indicator}: ").bold = True
                p.add_run(headline)
        else:
            doc.add_paragraph("No recent news items found.")
        
        doc.add_page_break()
        
        self._add_section_header(doc, "Methodology & Data Quality")
        methodology_text = (
            f"This report was generated through autonomous data collection and analysis from publicly available sources. "
            f"The analysis includes web scraping of Wikipedia articles related to {domain} in both {country1} and {country2}. "
            f"\n\n**Analysis Approach:**\n"
            f"- Normalized keyword frequency analysis (per 10,000 characters) to ensure fair comparison regardless of source text length\n"
            f"- Extraction of numerical data including funding amounts, company counts, and growth metrics\n"
            f"- Focus on recent developments (2020-{datetime.now().year}) to capture current state\n"
            f"- Entity recognition to identify key organizations and institutions\n"
            f"\n**Important Notes:**\n"
            f"- This analysis is based on publicly available Wikipedia data and may not reflect complete or classified information\n"
            f"- Comparisons are normalized to account for data availability differences between countries\n"
            f"- Results should be considered as indicative trends based on documented information rather than definitive metrics\n"
            f"- Some countries may have more comprehensive Wikipedia coverage, which is accounted for in normalization"
        )
        doc.add_paragraph(methodology_text)
        
        doc.save(filepath)
    
    def _add_title(self, doc: Document, text: str):
        title = doc.add_heading(text, level=0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in title.runs:
            run.font.size = Pt(24)
            run.font.color.rgb = RGBColor(0, 51, 102)
    
    def _add_subtitle(self, doc: Document, text: str):
        subtitle = doc.add_paragraph(text)
        subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in subtitle.runs:
            run.font.size = Pt(14)
            run.font.italic = True
            run.font.color.rgb = RGBColor(64, 64, 64)
    
    def _add_metadata(self, doc: Document):
        metadata = doc.add_paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
        metadata.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in metadata.runs:
            run.font.size = Pt(10)
            run.font.color.rgb = RGBColor(128, 128, 128)
    
    def _add_section_header(self, doc: Document, text: str):
        heading = doc.add_heading(text, level=1)
        for run in heading.runs:
            run.font.color.rgb = RGBColor(0, 51, 102)
    
    def _add_subsection_header(self, doc: Document, text: str):
        heading = doc.add_heading(text, level=2)
        for run in heading.runs:
            run.font.color.rgb = RGBColor(51, 102, 153)
