# pdf-compare

**Estudiante:** Angelo Huaiquil

Plataforma web que utiliza inteligencia artificial para comparar temáticamente dos o tres documentos PDF y determinar su grado de afinidad mediante dos estrategias distintas.

## ¿Qué hace?

Dado un conjunto de PDFs, el sistema aplica dos estrategias de análisis:

**Estrategia 1 — Extracción de keywords (Jaccard)**
Extrae las palabras clave más relevantes de cada documento usando un LLM y calcula el porcentaje de coincidencia entre los conjuntos mediante el índice de Jaccard. Para 3 PDFs, calcula la similitud por pares (A↔B, A↔C, B↔C).

**Estrategia 2 — Consulta directa al LLM**
Envía el contenido completo de los documentos al modelo y le pregunta directamente qué tan relacionados están, obteniendo un porcentaje de afinidad y una explicación en español.

Los resultados se visualizan con un **diagrama de Venn dinámico**: los círculos se solapan proporcionalmente al grado de similitud y se separan cuando no hay relación.

## Tecnologías

- **Backend:** Python, FastAPI, PyMuPDF
- **LLM:** Groq API (`llama-3.3-70b-versatile`)
- **Similitud:** Índice de Jaccard
- **Frontend:** HTML + CSS + JavaScript, D3.js, venn.js
- **Despliegue:** Render

## Estructura del proyecto

```
pdf-compare/
├── main.py              # Rutas FastAPI
├── requirements.txt
├── render.yaml          # Configuración de despliegue
├── app/
│   ├── config.py        # Constantes (modelo, límites)
│   ├── extractor.py     # Extracción de texto desde PDF
│   ├── similarity.py    # Jaccard y comparación de conjuntos
│   └── llm.py           # Integración con Groq
└── static/
    └── index.html       # Frontend completo
```

## Levantar localmente

### 1. Requisitos
- Python 3.10+
- Cuenta gratuita en [console.groq.com](https://console.groq.com) para obtener una API key

### 2. Clonar e instalar dependencias

```bash
git clone https://github.com/TU_USUARIO/pdf-compare.git
cd pdf-compare
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

```bash
cp .env.example .env
```

Edita `.env` y reemplaza el valor con tu API key de Groq:

```
GROQ_API_KEY=tu_api_key_aqui
```

### 4. Iniciar el servidor

```bash
uvicorn main:app --reload --port 8080
```

Abre `http://localhost:8080` en el navegador.

## Uso

1. Arrastra o selecciona entre 2 y 3 archivos PDF
2. Haz clic en **Analizar documentos**
3. Espera el análisis (~10-20 segundos)
4. Revisa los resultados: porcentajes de ambas estrategias y diagrama de Venn

## Grados de relación

| Porcentaje | Etiqueta |
|---|---|
| 60–100% | Altamente relacionados |
| 30–59% | Medianamente relacionados |
| 10–29% | Muy poco relacionados |
| 0–9% | No relacionados |
