"""
report/pdf_exporter.py — Markdown → PDF (WeasyPrint)
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def export_pdf(markdown_text: str, output_path: str) -> str:
    try:
        import markdown
        from weasyprint import HTML

        html_body = markdown.markdown(markdown_text, extensions=["tables", "fenced_code"])
        html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  body {{ font-family: Arial, sans-serif; margin: 40px; font-size: 13px; }}
  h1 {{ color: #1a3a5c; border-bottom: 2px solid #1a3a5c; }}
  h2 {{ color: #2c5f8a; }}
  table {{ border-collapse: collapse; width: 100%; }}
  th, td {{ border: 1px solid #ccc; padding: 6px 10px; }}
  th {{ background: #f0f4f8; }}
</style>
</head><body>{html_body}</body></html>"""

        HTML(string=html).write_pdf(output_path)
        logger.info(f"PDF oluşturuldu: {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"PDF hatası: {e}")
        raise
