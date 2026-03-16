"""
Infraestrutura de relatórios.
"""
from __future__ import annotations

from infrastructure.reporting.pdf_generator import (
    build_relatorio_pdf_bytes,
    build_relatorio_prospeccao_pdf_bytes,
    default_pdf_filename,
    save_pdf_copy,
)

__all__ = [
    "build_relatorio_pdf_bytes",
    "build_relatorio_prospeccao_pdf_bytes",
    "default_pdf_filename",
    "save_pdf_copy",
]
