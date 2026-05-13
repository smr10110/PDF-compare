"""Módulo de extracción de texto desde archivos PDF."""

import fitz  # PyMuPDF
from app.config import MAX_TEXT_CHARS


def extraer_texto(pdf_bytes: bytes) -> str:
    """Extrae el texto completo de un PDF dado como bytes.

    Recorre todas las páginas del documento y concatena su contenido
    textual. El resultado se trunca a MAX_TEXT_CHARS para no exceder
    el contexto del LLM.

    Args:
        pdf_bytes: Contenido binario del archivo PDF.

    Returns:
        Texto extraído del PDF, truncado a MAX_TEXT_CHARS caracteres.
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    texto = ""
    for pagina in doc:
        texto += pagina.get_text()
    return texto[:MAX_TEXT_CHARS]
