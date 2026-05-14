"""Constantes de configuración globales del proyecto."""

# Modelo de lenguaje a utilizar en Groq
# MODEL = "llama-3.3-70b-versatile"
MODEL = "llama-3.3-70b-versatile"

# Máximo de caracteres extraídos por PDF antes de enviarlo al LLM
# Reducido para respetar el límite de 6K tokens/minuto de llama-3.1-8b-instant
MAX_TEXT_CHARS = 4_000

# Número de keywords a extraer por documento en la Estrategia 1
KEYWORD_COUNT = 50
