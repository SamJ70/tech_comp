# backend/app/services/enhanced_document_generator.py
from docx import Document
from docx.shared import Inches, Pt
import os
from datetime import datetime
from ..config import REPORTS_DIR
import textwrap
import json

class ImprovedDocumentGenerator:
    def __init__(self):
        os.makedirs(REPORTS_DIR, exist_ok=True)
        self.reports_dir = REPORTS_DIR

    def generate_document(self, country1, country2, domain, combined_analysis: dict, filepath: str, include_charts: bool = True):
        doc = Document()
        doc.styles['Normal'].font.name = 'Calibri'
        doc.styles['Normal'].font.size = Pt(11)

        # Cover
        doc.add_heading(f"{country1} vs {country2} — {domain}", level=0)
        doc.add_paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        doc.add_paragraph("Executive summary:")
        doc.add_paragraph(combined_analysis.get("overall_analysis", "")[:1200])

        # Dual-use
        doc.add_heading("Dual-Use Analysis", level=1)
        dual = combined_analysis.get("dual_use_analysis", {})
        for c in (country1, country2):
            info = dual.get(c, {})
            doc.add_heading(c, level=2)
            doc.add_paragraph(f"Risk Level: {info.get('risk_level')}")
            doc.add_paragraph(f"Compliance Status: {info.get('compliance_status')}")
            doc.add_paragraph(f"Wassenaar Category (guessed): {info.get('wassenaar_category')}")
            doc.add_paragraph("Notes:")
            doc.add_paragraph(info.get("compliance_notes", "")[:1000])
            if info.get("military_indicators"):
                doc.add_paragraph("Top Indicators:")
                for ind in info["military_indicators"][:10]:
                    doc.add_paragraph(f"- {ind.get('matched_text')[:200]} (score {ind.get('score')})")

        # Chronological
        doc.add_heading("Chronological Tracking", level=1)
        chrono = combined_analysis.get("chronological_tracking", {})
        for c in (country1, country2):
            data = chrono.get(c, {"timeline": []})
            doc.add_heading(f"{c} timeline", level=2)
            for item in data.get("timeline", [])[:50]:
                doc.add_paragraph(f"{item['year']}: {item['total_events']} events")
                for h in item.get("highlights", [])[:3]:
                    doc.add_paragraph(f"  - {h}")

            plot_path = data.get("plot_path")
            if include_charts and plot_path and os.path.exists(plot_path):
                try:
                    doc.add_picture(plot_path, width=Inches(6))
                except Exception:
                    pass

        # Top items (table)
        doc.add_heading("Top Items (sample)", level=1)
        rows = []
        for c in (country1, country2):
            data = combined_analysis.get("chronological_tracking", {}).get(c, {})
            for y in data.get("timeline", [])[:3]:
                for it in y.get("items", [])[:3]:
                    rows.append((c, y.get("year"), it.get("title")[:180], it.get("source"), it.get("url", "")))
        if rows:
            table = doc.add_table(rows=1, cols=5)
            hdr = table.rows[0].cells
            hdr[0].text = "Country"
            hdr[1].text = "Year"
            hdr[2].text = "Title"
            hdr[3].text = "Source"
            hdr[4].text = "URL"
            for r in rows:
                row_cells = table.add_row().cells
                row_cells[0].text = str(r[0])
                row_cells[1].text = str(r[1])
                row_cells[2].text = r[2]
                row_cells[3].text = r[3]
                row_cells[4].text = r[4] or ""

        doc.add_heading("Recommendations", level=1)
        recs = []
        for c in (country1, country2):
            recs.extend(dual.get(c, {}).get("recommendations", []))
        for r in list(dict.fromkeys(recs))[:20]:
            doc.add_paragraph(f"- {r}")

        doc.add_heading("Metadata & Sources", level=1)
        meta = combined_analysis.get("metadata", {})
        doc.add_paragraph(json.dumps(meta, ensure_ascii=False, indent=2)[:2000])

        # Save
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        doc.save(filepath)
        return filepath
