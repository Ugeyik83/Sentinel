"""
report/pdf_exporter.py — Markdown → PDF (fpdf2)
WeasyPrint Streamlit Cloud'da çalışmıyor (sistem bağımlılığı).
fpdf2 saf Python — her ortamda çalışır.
"""

import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)


def export_pdf(markdown_text: str, output_path: str) -> str:
    try:
        from fpdf import FPDF

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_margins(20, 20, 20)

        # Unicode font
        pdf.add_font("DejaVu", "", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", uni=True)
        pdf.add_font("DejaVu", "B", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", uni=True)
    except Exception:
        # Font bulunamazsa Latin-1 fallback
        return _export_pdf_basic(markdown_text, output_path)

    try:
        lines = markdown_text.split("\n")
        for line in lines:
            line = line.rstrip()

            if line.startswith("# "):
                pdf.set_font("DejaVu", "B", 16)
                pdf.set_text_color(26, 58, 92)
                pdf.multi_cell(0, 10, line[2:])
                pdf.ln(2)

            elif line.startswith("## "):
                pdf.set_font("DejaVu", "B", 13)
                pdf.set_text_color(44, 95, 138)
                pdf.multi_cell(0, 8, line[3:])
                pdf.ln(1)

            elif line.startswith("### "):
                pdf.set_font("DejaVu", "B", 11)
                pdf.set_text_color(60, 60, 60)
                pdf.multi_cell(0, 7, line[4:])

            elif line.startswith("- ") or line.startswith("• "):
                pdf.set_font("DejaVu", "", 10)
                pdf.set_text_color(40, 40, 40)
                text = line[2:].strip()
                text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
                pdf.multi_cell(0, 6, f"  • {text}")

            elif re.match(r'^\d+\.', line):
                pdf.set_font("DejaVu", "", 10)
                pdf.set_text_color(40, 40, 40)
                text = re.sub(r'\*\*(.*?)\*\*', r'\1', line)
                pdf.multi_cell(0, 6, f"  {text}")

            elif line.startswith("---"):
                pdf.set_draw_color(200, 200, 200)
                pdf.line(20, pdf.get_y(), 190, pdf.get_y())
                pdf.ln(3)

            elif line.strip() == "":
                pdf.ln(3)

            else:
                pdf.set_font("DejaVu", "", 10)
                pdf.set_text_color(40, 40, 40)
                text = re.sub(r'\*\*(.*?)\*\*', r'\1', line)
                text = re.sub(r'\*(.*?)\*', r'\1', text)
                pdf.multi_cell(0, 6, text)

        pdf.output(output_path)
        logger.info(f"PDF oluşturuldu: {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"PDF hata: {e}")
        return _export_pdf_basic(markdown_text, output_path)


def _export_pdf_basic(markdown_text: str, output_path: str) -> str:
    """Latin-1 fallback — Türkçe karakter desteği sınırlı."""
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(20, 20, 20)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Helvetica", size=10)

    # Türkçe karakterleri ASCII'ye çevir
    tr_map = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")

    lines = markdown_text.split("\n")
    for line in lines:
        line = line.rstrip().translate(tr_map)
        clean = re.sub(r'[*#`]', '', line).strip()
        if clean:
            try:
                pdf.multi_cell(0, 6, clean)
            except Exception:
                pass
        else:
            pdf.ln(3)

    pdf.output(output_path)
    return output_path