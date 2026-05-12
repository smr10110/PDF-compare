import os
import json
import re
import fitz
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"
MAX_TEXT_CHARS = 20000
KEYWORD_COUNT = 100


def extract_text(pdf_bytes: bytes) -> str:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text[:MAX_TEXT_CHARS]


def get_keywords(text: str, filename: str) -> list[str]:
    prompt = (
        f"Extract exactly {KEYWORD_COUNT} key concepts, terms, and keywords from the following document. "
        "Return ONLY a JSON array of strings, nothing else. No explanation, no markdown, just the JSON array.\n\n"
        f"Document:\n{text}"
    )
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=2000,
    )
    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    try:
        keywords = json.loads(raw)
        return [str(k).lower().strip() for k in keywords if k]
    except Exception:
        words = re.findall(r'"([^"]+)"', raw)
        return [w.lower().strip() for w in words[:KEYWORD_COUNT]]


def jaccard_similarity(set_a: set, set_b: set) -> float:
    if not set_a and not set_b:
        return 0.0
    union = set_a | set_b
    intersection = set_a & set_b
    return len(intersection) / len(union) * 100


def similarity_label(pct: float) -> str:
    if pct >= 60:
        return "Altamente relacionados"
    elif pct >= 30:
        return "Medianamente relacionados"
    elif pct >= 10:
        return "Muy poco relacionados"
    return "No relacionados"


def direct_llm_comparison(texts: list[str], filenames: list[str]) -> dict:
    docs_block = "\n\n".join(
        f"=== DOCUMENTO {i+1}: {filenames[i]} ===\n{text}"
        for i, text in enumerate(texts)
    )
    prompt = (
        "You are an expert academic document analyst. Analyze the following documents and determine their thematic relationship.\n\n"
        f"{docs_block}\n\n"
        "Respond ONLY with a JSON object (no markdown, no explanation) with this exact structure:\n"
        '{"affinity_pct": <number 0-100>, "label": "<Altamente relacionados|Medianamente relacionados|Muy poco relacionados|No relacionados>", '
        '"explanation": "<2-3 sentences in Spanish explaining the relationship>"}'
    )
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=500,
    )
    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    try:
        result = json.loads(raw)
        result["affinity_pct"] = float(result.get("affinity_pct", 0))
        return result
    except Exception:
        pct_match = re.search(r'\d+(?:\.\d+)?', raw)
        pct = float(pct_match.group()) if pct_match else 0.0
        return {
            "affinity_pct": pct,
            "label": similarity_label(pct),
            "explanation": raw[:300],
        }


@app.get("/")
def index():
    return FileResponse("static/index.html")


@app.post("/compare")
async def compare(files: list[UploadFile] = File(...)):
    if len(files) < 2:
        raise HTTPException(status_code=400, detail="Se requieren al menos 2 archivos PDF.")

    texts = []
    filenames = []
    for f in files:
        content = await f.read()
        try:
            text = extract_text(content)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error leyendo {f.filename}: {e}")
        texts.append(text)
        filenames.append(f.filename)

    all_keywords = []
    for i, text in enumerate(texts):
        kws = get_keywords(text, filenames[i])
        all_keywords.append(kws)

    sets = [set(kws) for kws in all_keywords]
    if len(sets) == 2:
        intersection = list(sets[0] & sets[1])
        only_a = list(sets[0] - sets[1])
        only_b = list(sets[1] - sets[0])
        sim_pct = jaccard_similarity(sets[0], sets[1])
    else:
        common = sets[0]
        for s in sets[1:]:
            common = common & s
        intersection = list(common)
        all_union = sets[0]
        for s in sets[1:]:
            all_union = all_union | s
        sim_pct = (len(common) / len(all_union) * 100) if all_union else 0.0
        only_a = list(sets[0] - common)
        only_b = list(sets[1] - common) if len(sets) > 1 else []

    strategy2 = direct_llm_comparison(texts, filenames)

    return JSONResponse({
        "filenames": filenames,
        "strategy1": {
            "keywords": all_keywords,
            "intersection": intersection,
            "only_a": only_a[:50],
            "only_b": only_b[:50],
            "similarity_pct": round(sim_pct, 1),
            "label": similarity_label(sim_pct),
        },
        "strategy2": strategy2,
    })
