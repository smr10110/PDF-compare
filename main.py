"""Punto de entrada de la aplicación: define la app FastAPI y sus rutas."""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.extractor import extraer_texto
from app.similarity import comparar_conjuntos
from app.llm import extraer_keywords, comparacion_directa

app = FastAPI(title="PDF Compare", version="1.0.0")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def index():
    """Sirve el frontend principal sin caché para que los cambios se reflejen de inmediato."""
    return FileResponse(
        "static/index.html",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )


@app.post("/compare")
async def compare(files: list[UploadFile] = File(...)):
    """Compara temáticamente dos o más PDFs usando dos estrategias de IA.

    Estrategia 1: Extrae keywords de cada documento con el LLM y calcula
    la similitud mediante el índice de Jaccard.

    Estrategia 2: Envía el contenido completo al LLM y le pregunta
    directamente el porcentaje de afinidad temática.

    Args:
        files: Lista de archivos PDF subidos (mínimo 2).

    Returns:
        JSON con los resultados de ambas estrategias y datos para el diagrama de Venn.
    """
    if len(files) < 2:
        raise HTTPException(status_code=400, detail="Se requieren al menos 2 archivos PDF.")

    textos, nombres = [], []
    for f in files:
        contenido = await f.read()
        try:
            texto = extraer_texto(contenido)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error leyendo {f.filename}: {e}")
        textos.append(texto)
        nombres.append(f.filename)

    # Estrategia 1: extracción de keywords + Jaccard
    lista_keywords = [extraer_keywords(t) for t in textos]
    metricas = comparar_conjuntos(lista_keywords)

    # Estrategia 2: consulta directa al LLM
    resultado_llm = comparacion_directa(textos, nombres)

    return JSONResponse({
        "filenames": nombres,
        "strategy1": {
            "keywords": lista_keywords,
            "intersection": metricas["intersection"],
            "only_a": metricas["only_a"],
            "only_b": metricas["only_b"],
            "only_c": metricas["only_c"],
            "similarity_pct": metricas["sim_pct"],
            "label": metricas["label"],
        },
        "strategy2": resultado_llm,
    })
