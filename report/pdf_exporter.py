"""
report/pdf_exporter.py
Markdown → PDF (fpdf2)
Türkçe karakter desteği + içerik korunumu
"""

import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

# Türkçe → Latin-1 dönüşüm tablosu (fpdf2 font yüklenemezse fallback)
TR_MAP = str.maketrans(
    "çğışöüÇĞİŞÖÜ",
    "cgisouCGISOu"
)


def export_pdf(markdown_text: str, output_path: str) -> str:
    try:
        from fpdf import FPDF, XPos, YPos

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=20)
        pdf.add_page()
        pdf.set_margins(20, 20, 20)

        # Unicode font dene
        font_loaded = _try_load_unicode_font(pdf)

        _render_markdown(pdf, markdown_text, font_loaded)

        pdf.output(output_path)
        logger.info(f"PDF oluşturuldu: {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"PDF hatası: {e}")
        return _export_simple(markdown_text, output_path)


def _try_load_unicode_font(pdf) -> bool:
    """Unicode font yüklemeyi dene. Başarısızsa False döndür."""
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for path in font_paths:
        if Path(path).exists():
            try:
                pdf.add_font("Unicode", "", path, uni=True)
                bold_path = path.replace("Sans.ttf", "Sans-Bold.ttf")
                if Path(bold_path).exists():
                    pdf.add_font("Unicode", "B", bold_path, uni=True)
                else:
                    pdf.add_font("Unicode", "B", path, uni=True)
                return True
            except Exception:
                continue
    return False


def _render_markdown(pdf, markdown_text: str, unicode_font: bool):
    """Markdown metni PDF'e render et."""

    def set_font(style="", size=10):
        if unicode_font:
            pdf.set_font("Unicode", style, size)
        else:
            pdf.set_font("Helvetica", style, size)

    def safe_text(text: str) -> str:
        """Font desteklemiyorsa Türkçe karakterleri dönüştür."""
        if not unicode_font:
            return text.translate(TR_MAP)
        return text

    def clean_inline(text: str) -> str:
        """**bold** ve *italic* işaretlerini kaldır."""
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        text = re.sub(r'`(.*?)`', r'\1', text)
        return text.strip()

    lines = markdown_text.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i].rstrip()

        # H1
        if line.startswith("# "):
            set_font("B", 16)
            pdf.set_text_color(26, 58, 92)
            pdf.multi_cell(0, 10, safe_text(clean_inline(line[2:])), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_draw_color(26, 58, 92)
            pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
            pdf.ln(4)

        # H2
        elif line.startswith("## "):
            set_font("B", 13)
            pdf.set_text_color(44, 95, 138)
            pdf.ln(3)
            pdf.multi_cell(0, 8, safe_text(clean_inline(line[3:])), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(2)

        # H3
        elif line.startswith("### "):
            set_font("B", 11)
            pdf.set_text_color(60, 60, 60)
            pdf.ln(2)
            pdf.multi_cell(0, 7, safe_text(clean_inline(line[4:])), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Bullet
        elif line.startswith("- ") or line.startswith("• ") or line.startswith("* "):
            set_font("", 10)
            pdf.set_text_color(40, 40, 40)
            text = safe_text(clean_inline(line[2:]))
            # Girintili bullet
            x = pdf.get_x()
            pdf.set_x(pdf.l_margin + 5)
            pdf.multi_cell(0, 6, f"• {text}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Numaralı liste
        elif re.match(r'^\d+\.', line):
            set_font("", 10)
            pdf.set_text_color(40, 40, 40)
            text = safe_text(clean_inline(line))
            pdf.set_x(pdf.l_margin + 3)
            pdf.multi_cell(0, 6, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Alt madde (iki boşluklu)
        elif line.startswith("   ") or line.startswith("\t"):
            set_font("", 9)
            pdf.set_text_color(80, 80, 80)
            text = safe_text(clean_inline(line.strip()))
            if text.startswith("-") or text.startswith("•"):
                text = text[1:].strip()
            pdf.set_x(pdf.l_margin + 12)
            pdf.multi_cell(0, 5, f"◦ {text}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Yatay çizgi
        elif line.startswith("---") or line.startswith("___"):
            pdf.ln(3)
            pdf.set_draw_color(200, 200, 200)
            pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
            pdf.ln(3)

        # Boş satır
        elif line.strip() == "":
            pdf.ln(3)

        # Normal metin
        else:
            set_font("", 10)
            pdf.set_text_color(40, 40, 40)
            text = safe_text(clean_inline(line))
            if text:
                pdf.multi_cell(0, 6, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        i += 1


def _export_simple(markdown_text: str, output_path: str) -> str:
    """Minimum fallback — saf metin, Türkçe dönüştürülmüş."""
    from fpdf import FPDF, XPos, YPos

    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(20, 20, 20)
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_font("Helvetica", size=10)

    for line in markdown_text.split("\n"):
        clean = re.sub(r'[*#`]', '', line).strip().translate(TR_MAP)
        if clean:
            try:
                pdf.multi_cell(0, 6, clean, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            except Exception:
                pass
        else:
            pdf.ln(3)

    pdf.output(output_path)
    return output_path