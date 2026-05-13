"""Módulo de integración con el LLM de Groq para análisis temático de documentos."""

import os
import json
import re

from groq import Groq
from dotenv import load_dotenv

from app.config import MODEL, KEYWORD_COUNT
from app.similarity import etiqueta_similitud

load_dotenv()

# Validación temprana: falla al importar si la key no está configurada
_api_key = os.environ.get("GROQ_API_KEY")
if not _api_key:
    raise RuntimeError(
        "GROQ_API_KEY no está definida. "
        "Crea un archivo .env con GROQ_API_KEY=tu_key o configúrala en las variables de entorno."
    )

_cliente = Groq(api_key=_api_key)


def _limpiar_json(raw: str) -> str:
    """Elimina bloques de código markdown que el LLM puede agregar alrededor del JSON.

    Args:
        raw: Texto crudo devuelto por el LLM.

    Returns:
        Texto limpio listo para parsear como JSON.
    """
    raw = re.sub(r"^```(?:json)?\s*", "", raw.strip())
    raw = re.sub(r"\s*```$", "", raw)
    return raw


def extraer_keywords(texto: str) -> list[str]:
    """Extrae las keywords más relevantes de un texto usando el LLM (Estrategia 1).

    Le pide al modelo que devuelva exactamente KEYWORD_COUNT conceptos clave
    en formato JSON. Si el parseo falla, intenta recuperar palabras del texto crudo.

    Args:
        texto: Contenido textual del documento PDF.

    Returns:
        Lista de keywords en minúsculas, sin espacios sobrantes.
    """
    prompt = (
        f"Extract exactly {KEYWORD_COUNT} key concepts, terms, and keywords "
        "from the following document. "
        "Return ONLY a JSON array of strings, nothing else. "
        "No explanation, no markdown, just the JSON array.\n\n"
        f"Document:\n{texto}"
    )
    respuesta = _cliente.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=2000,
    )
    raw = _limpiar_json(respuesta.choices[0].message.content)

    try:
        keywords = json.loads(raw)
        return [str(k).lower().strip() for k in keywords if k]
    except Exception:
        # Fallback: extrae strings entre comillas si el JSON está malformado
        palabras = re.findall(r'"([^"]+)"', raw)
        return [p.lower().strip() for p in palabras[:KEYWORD_COUNT]]


def comparacion_directa(textos: list[str], nombres: list[str]) -> dict:
    """Consulta directamente al LLM sobre la afinidad temática entre documentos (Estrategia 2).

    Envía el contenido de todos los documentos en un solo prompt y pide al modelo
    que evalúe su relación temática con un porcentaje y una explicación.

    Args:
        textos: Lista con el contenido textual de cada documento.
        nombres: Lista con los nombres de archivo correspondientes.

    Returns:
        Diccionario con:
            - affinity_pct: porcentaje de afinidad (0–100).
            - label: etiqueta cualitativa de la relación.
            - explanation: explicación en español del análisis.
    """
    bloque_docs = "\n\n".join(
        f"=== DOCUMENTO {i + 1}: {nombres[i]} ===\n{texto}"
        for i, texto in enumerate(textos)
    )
    prompt = (
        "You are an expert academic document analyst. "
        "Analyze the following documents and determine their thematic relationship.\n\n"
        f"{bloque_docs}\n\n"
        "Respond ONLY with a JSON object (no markdown, no explanation) "
        "with this exact structure:\n"
        '{"affinity_pct": <number 0-100>, '
        '"label": "<Altamente relacionados|Medianamente relacionados|Muy poco relacionados|No relacionados>", '
        '"explanation": "<2-3 sentences in Spanish explaining the relationship>"}'
    )
    respuesta = _cliente.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=500,
    )
    raw = _limpiar_json(respuesta.choices[0].message.content)

    try:
        resultado = json.loads(raw)
        resultado["affinity_pct"] = float(resultado.get("affinity_pct", 0))
        return resultado
    except Exception:
        # Fallback: intenta extraer al menos el porcentaje del texto crudo
        match = re.search(r"\d+(?:\.\d+)?", raw)
        pct = float(match.group()) if match else 0.0
        return {
            "affinity_pct": pct,
            "label": etiqueta_similitud(pct),
            "explanation": raw[:300],
        }
