# Documentación Técnica - CENATE Medical Assistant

## Índice
1. [Guía de Instalación](#1-guía-de-instalación)
2. [Configuración](#2-configuración)
3. [Uso de la API](#3-uso-de-la-api)
4. [Arquitectura de Tools](#4-arquitectura-de-tools)
5. [Vector Store y RAG](#5-vector-store-y-rag)
6. [Testing](#6-testing)
7. [Troubleshooting](#7-troubleshooting)
8. [Best Practices](#8-best-practices)
9. [FAQ](#9-faq)

---

## 1. Guía de Instalación

### 1.1 Instalación Local (Desarrollo)

#### Prerrequisitos
- Python 3.12 o superior
- pip 23.0+
- Git
- OpenAI API Key (obtener en https://platform.openai.com/api-keys)

#### Pasos

**1. Clonar el repositorio:**
```bash
git clone https://github.com/yechevarriav/medical-agent-cenate.git
cd medical-agent-cenate
```

**2. Crear entorno virtual:**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

**3. Instalar dependencias:**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Si encuentras errores de dependencias**, instala en este orden:
```bash
# Desinstalar versiones conflictivas
pip uninstall -y langchain langchain-openai langchain-community langchain-core

# Reinstalar con versiones compatibles
pip install langchain==0.3.0 langchain-openai==0.2.0 langchain-community==0.3.0
pip install openai>=1.10.0
pip install faiss-cpu>=1.8.0
```

**4. Configurar variables de entorno:**
```bash
# Copiar template
cp .env.example .env

# Editar .env con tu editor favorito
nano .env  # o code .env, vim .env, etc.
```

Contenido de `.env`:
```bash
OPENAI_API_KEY=sk-proj-XXXXXXXXXXXXXXXXXXXXXXXX
PORT=8000
ENVIRONMENT=development
```

**5. Copiar PDFs a data/raw/ (si tienes los documentos):**
```bash
# Copiar tus PDFs PM.2.1.2 y PM.2.2.2
cp /ruta/a/tus/pdfs/*.pdf data/raw/
```

**6. Crear vector store:**
```bash
python src/vectorstore.py
```

Salida esperada:
```
================================================================================
🚀 INICIANDO PROCESAMIENTO DE DOCUMENTOS
================================================================================
📄 Procesando: PM.2.1.2 ...
   ✅ 50391 caracteres extraídos
📄 Procesando: PM.2.2.2 ...
   ✅ 43421 caracteres extraídos
🔄 Creando embeddings para 133 chunks...
✅ Vectorstore creado y guardado en data/faiss_index
```

**7. Ejecutar servidor de desarrollo:**
```bash
python src/main.py
```

Salida esperada:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**8. Verificar instalación:**

Abre tu navegador en:
- Frontend: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- Health check: http://localhost:8000/health

---

### 1.2 Instalación con Docker

**1. Build de la imagen:**
```bash
docker build -t cenate-medical-assistant:latest .
```

**2. Ejecutar container:**
```bash
docker run -d \
  --name cenate-app \
  -p 8000:8000 \
  -e OPENAI_API_KEY=sk-proj-... \
  -e PORT=8000 \
  -e ENVIRONMENT=production \
  cenate-medical-assistant:latest
```

**3. Ver logs:**
```bash
docker logs -f cenate-app
```

**4. Detener container:**
```bash
docker stop cenate-app
docker rm cenate-app
```

---

## 2. Configuración

### 2.1 Variables de Entorno

| Variable | Requerida | Default | Descripción |
|----------|-----------|---------|-------------|
| `OPENAI_API_KEY` | ✅ Sí | - | API key de OpenAI |
| `PORT` | ❌ No | 8000 | Puerto del servidor |
| `ENVIRONMENT` | ❌ No | development | `development` o `production` |

### 2.2 Configuración de OpenAI

El sistema usa dos modelos de OpenAI:

**LLM (GPT-4o-mini):**
```python
# src/agent.py o cualquier tool que use LLM
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,  # Determinístico para evaluaciones médicas
    max_tokens=1000
)
```

**Embeddings (text-embedding-3-small):**
```python
# src/vectorstore.py
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    dimensions=1536
)
```

### 2.3 Configuración de FAISS

```python
# src/vectorstore.py
from langchain_text_splitters import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,      # Tamaño de cada chunk
    chunk_overlap=200,    # 20% de overlap
    length_function=len,
    is_separator_regex=False
)
```

**Ajustar para tus documentos:**
- `chunk_size`: 500-2000 caracteres
  - Más pequeño: búsquedas más precisas, menos contexto
  - Más grande: más contexto, búsquedas menos precisas
- `chunk_overlap`: 10-30% del chunk_size
  - Mayor overlap: menos pérdida de contexto entre chunks
  - Menor overlap: más chunks únicos

---

## 3. Uso de la API

### 3.1 Endpoints Disponibles

#### **GET /**
Servir frontend HTML

**Response:** HTML page

---

#### **GET /health**
Health check del servicio

**Response:**
```json
{
  "status": "healthy"
}
```

---

#### **POST /risk**
Estratificar riesgo de paciente crónico

**Request Body:**
```json
{
  "a1c": 8.5,              // float, optional - Hemoglobina A1C (%)
  "pa_sistolica": 155,     // int, optional - Presión sistólica (mmHg)
  "pa_diastolica": 98,     // int, optional - Presión diastólica (mmHg)
  "ldl": 115,              // int, optional - Colesterol LDL (mg/dL)
  "phq9": 10,              // int, optional - Escala PHQ-9 (0-27)
  "gad7": 21               // int, optional - Escala GAD-7 (0-21)
}
```

**Response 200:**
```json
{
  "result": {
    "evaluacion": {
      "diabetes": "Alto",
      "hipertension": "Moderado",
      "dislipidemia": "Elevado",
      "psicologico": "Severo",
      "psicologico_detalle": "PHQ-9: Moderado, GAD-7: Severo"
    },
    "recomendaciones": [
      "Derivar a endocrinología (A1C >8%)",
      "Derivar a psiquiatría (ansiedad severa, GAD-7 ≥15)",
      "Control mensual requerido (alto riesgo)"
    ],
    "fuente": "PM.2.1.2 Anexo 10 - Criterios de Estandarización de Riesgo"
  }
}
```

**Ejemplo con Python:**
```python
import requests

response = requests.post(
    "http://localhost:8000/risk",
    json={
        "a1c": 8.5,
        "pa_sistolica": 155,
        "pa_diastolica": 98,
        "ldl": 115,
        "phq9": 10,
        "gad7": 21
    }
)

print(response.json())
```

---

#### **POST /validate**
Validar elegibilidad para telecolposcopía

**Request Body:**
```json
{
  "edad": 45,                     // int, required - Edad del paciente
  "pap_resultado": "ASC-H",       // string, optional - Resultado PAP
  "vph_positivo": true            // boolean, optional - VPH positivo
}
```

**Valores válidos para `pap_resultado`:**
- `"AGC"`, `"ASC-H"`, `"LIE-AG"`, `"CARCINOMA"`, `"NEGATIVO"`

**Response 200:**
```json
{
  "result": {
    "elegible": true,
    "criterios_cumplidos": [
      "Edad válida: 45 años (rango 25-65)",
      "PAP positivo: ASC-H",
      "VPH de alto riesgo positivo"
    ],
    "detalles": "Cumple todos los criterios",
    "fuente": "PM.2.2.2 - Público Objetivo (Verificado con RAG - Score: 0.85)",
    "contexto_pdf": "...público objetivo: mujeres de 25 a 65 años..."
  }
}
```

**Ejemplo con cURL:**
```bash
curl -X POST http://localhost:8000/validate \
  -H "Content-Type: application/json" \
  -d '{
    "edad": 45,
    "pap_resultado": "ASC-H",
    "vph_positivo": true
  }'
```

---

#### **GET /template/{tipo}**
Generar plantilla HCE

**Path Parameters:**
- `tipo`: `sincrona` | `asincrona` | `cenacron`

**Query Parameters:**
- `formato`: `texto` | `html` | `hl7` (default: `texto`)

**Response 200:**
```json
{
  "result": {
    "tipo": "sincrona",
    "formato": "texto",
    "plantilla": "📋 PROTOCOLO TELECOLPOSCOPÍA SÍNCRONA - CENATE\n\nFECHA: ___/___/_____ HORA: _____\n\n☐ CONSENTIMIENTO INFORMADO FIRMADO...",
    "fuente": "PM.2.2.2 Anexo 2"
  }
}
```

**Ejemplo con JavaScript:**
```javascript
fetch('http://localhost:8000/template/sincrona?formato=texto')
  .then(res => res.json())
  .then(data => console.log(data.result.plantilla));
```

---

## 4. Arquitectura de Tools

### 4.1 Tool: Risk Stratification

**Archivo:** `src/tools/risk_tool.py`

**Clase:** `RiskStratificationTool`

**Criterios de evaluación:**

```python
# Diabetes (A1C)
if a1c < 7:    → "Bajo"
if 7 <= a1c <= 8:  → "Moderado"
if a1c > 8:    → "Alto" + derivar_endocrinologia

# Hipertensión (PA)
if PA < 140/90:  → "Controlado"
if 140/90 <= PA < 160/100:  → "Moderado"
if PA >= 160/100:  → "Alto" + derivar_cardiologia

# Dislipidemia (LDL)
if ldl < 70:   → "Óptimo"
if 70 <= ldl <= 100:  → "Aceptable"
if ldl > 100:  → "Elevado"

# Salud Mental (PHQ-9 y GAD-7 - INDEPENDIENTES)
PHQ-9 (Depresión):
  0-4:   Mínimo
  5-9:   Leve
  10-14: Moderado
  ≥15:   Severo → derivar_psiquiatria

GAD-7 (Ansiedad):
  0-4:   Mínimo
  5-9:   Leve
  10-14: Moderado
  ≥15:   Severo → derivar_psiquiatria

# Nivel general = MAX(PHQ-9, GAD-7)
```

**Uso programático:**
```python
from tools.risk_tool import RiskStratificationTool

tool = RiskStratificationTool()
result = tool.estratificar(
    a1c=8.5,
    pa_sistolica=155,
    pa_diastolica=98,
    ldl=115,
    phq9=10,
    gad7=21
)

print(result)
# {
#   "evaluacion": {...},
#   "recomendaciones": [...],
#   "fuente": "..."
# }
```

---

### 4.2 Tool: Validate Eligibility

**Archivo:** `src/tools/validate_tool.py`

**Clase:** `ValidateTelecolposcopiaTool`

**Arquitectura Híbrida:**

```
┌─────────────────────────────────────┐
│   Paso 1: Validación Lógica (50ms) │
│   - Edad ∈ [25, 65]                │
│   - PAP ∈ {AGC, ASC-H, LIE-AG, ...}│
│   - VPH = true/false                │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│   Paso 2: Verificación RAG (200ms) │
│   - Query vector store              │
│   - Retornar contexto PDF           │
│   - Score de relevancia             │
└─────────────────────────────────────┘
```

**Criterios:**
```python
# Elegibilidad
elegible = edad_valida AND (pap_positivo OR vph_positivo)

# Donde:
edad_valida = 25 <= edad <= 65
pap_positivo = pap_resultado in ["AGC", "ASC-H", "LIE-AG", "CARCINOMA"]
vph_positivo = vph_positivo == True
```

**Uso programático:**
```python
from tools.validate_tool import ValidateTelecolposcopiaTool

tool = ValidateTelecolposcopiaTool()
result = tool.validar(
    edad=45,
    pap_resultado="ASC-H",
    vph_positivo=True
)

if result["elegible"]:
    print("Paciente ELEGIBLE")
    print(f"Criterios: {result['criterios_cumplidos']}")
    print(f"Contexto PDF: {result.get('contexto_pdf', 'N/A')}")
else:
    print("Paciente NO ELEGIBLE")
    print(f"Razón: {result['detalles']}")
```

---

### 4.3 Tool: Template Generator

**Archivo:** `src/tools/template_tool.py`

**Clase:** `GenerateTemplateTool`

**Plantillas disponibles:**
- `sincrona`: Telecolposcopía en tiempo real
- `asincrona`: Telecolposcopía diferida (store-and-forward)
- `cenacron`: Atención de pacientes crónicos

**Formatos:**
- `texto`: Texto plano con formato
- `html`: Formulario HTML interactivo (pendiente)
- `hl7`: HL7 FHIR R4 (pendiente)

**Uso programático:**
```python
from tools.template_tool import GenerateTemplateTool

tool = GenerateTemplateTool()

# Formato texto
result = tool.generar("sincrona", "texto")
print(result["plantilla"])

# Guardar en archivo
with open("plantilla_sincrona.txt", "w", encoding="utf-8") as f:
    f.write(result["plantilla"])
```

---

### 4.4 Tool: Semantic Search

**Archivo:** `src/tools/search_tool.py`

**Clase:** `SearchMedicalTool`

**Proceso:**
```
Query → Embedding → FAISS Search → Top-K Chunks → Format Results
```

**Uso programático:**
```python
from tools.search_tool import SearchMedicalTool

tool = SearchMedicalTool()
results = tool.search("criterios de elegibilidad telecolposcopía")

for i, result in enumerate(results, 1):
    print(f"Resultado {i}:")
    print(f"  Fuente: {result['fuente']}")
    print(f"  Score: {result['score']}")
    print(f"  Contenido: {result['contenido'][:200]}...")
    print()
```

---

## 5. Vector Store y RAG

### 5.1 Crear Vector Store desde cero

**Script:** `src/vectorstore.py`

```bash
# Ejecutar con PDFs en data/raw/
python src/vectorstore.py
```

**Proceso interno:**
1. Lee todos los PDFs de `data/raw/`
2. Extrae texto con `pypdf`
3. Divide en chunks de 1000 caracteres (overlap 200)
4. Genera embeddings con OpenAI text-embedding-3-small
5. Crea índice FAISS
6. Guarda en `data/faiss_index/`

**Archivos generados:**
```
data/faiss_index/
├── index.faiss      # Índice FAISS binario
└── index.pkl        # Metadata de documentos
```

### 5.2 Cargar Vector Store existente

```python
from vectorstore import MedicalVectorStore

# Cargar
vs = MedicalVectorStore()
vs.load()  # Lee de data/faiss_index/

# Búsqueda
results = vs.search("diabetes descontrolada", k=3)

for doc, score in results:
    print(f"Score: {score:.3f}")
    print(f"Contenido: {doc.page_content[:200]}...")
    print(f"Fuente: {doc.metadata['source']}")
    print()
```

### 5.3 Agregar nuevos documentos

```python
from vectorstore import MedicalVectorStore
from langchain.schema import Document

vs = MedicalVectorStore()
vs.load()

# Crear nuevos documentos
nuevos_docs = [
    Document(
        page_content="Contenido del nuevo procedimiento...",
        metadata={"source": "PM.3.1.5", "page": 1}
    ),
    # ... más documentos
]

# Agregar al vector store
vs.add_documents(nuevos_docs)

# Guardar
vs.save()
```

### 5.4 Actualizar Vector Store

Cuando los PDFs cambien:

```bash
# 1. Copiar nuevos PDFs a data/raw/
cp nuevos_pdfs/*.pdf data/raw/

# 2. Eliminar índice anterior
rm -rf data/faiss_index/

# 3. Recrear
python src/vectorstore.py
```

---

## 6. Testing

### 6.1 Test Manual de Tools

**Risk Tool:**
```bash
python src/tools/risk_tool.py
```

**Validate Tool:**
```bash
python src/tools/validate_tool.py
```

**Template Tool:**
```bash
python src/tools/template_tool.py
```

**Search Tool:**
```bash
python src/tools/search_tool.py
```

### 6.2 Test de Endpoints con cURL

```bash
# Health check
curl http://localhost:8000/health

# Risk
curl -X POST http://localhost:8000/risk \
  -H "Content-Type: application/json" \
  -d '{"a1c": 8.5, "pa_sistolica": 155}'

# Validate
curl -X POST http://localhost:8000/validate \
  -H "Content-Type: application/json" \
  -d '{"edad": 45, "pap_resultado": "ASC-H"}'

# Template
curl http://localhost:8000/template/sincrona
```

### 6.3 Test del Vector Store

```python
# test_vectorstore.py
from vectorstore import MedicalVectorStore

def test_vectorstore():
    vs = MedicalVectorStore()
    vs.load()
    
    # Test 1: Búsqueda diabetes
    results = vs.search("criterios diabetes A1C", k=3)
    assert len(results) == 3
    assert results[0][1] > 0.5  # Score > 0.5
    
    # Test 2: Búsqueda telecolposcopía
    results = vs.search("elegibilidad telecolposcopía", k=3)
    assert "PM.2.2.2" in results[0][0].metadata["source"]
    
    print("✅ Todos los tests pasaron")

if __name__ == "__main__":
    test_vectorstore()
```

---

## 7. Troubleshooting

### 7.1 Error: "Vectorstore no inicializado"

**Causa:** No se ha creado el vector store

**Solución:**
```bash
# Verificar que existan PDFs
ls data/raw/

# Crear vector store
python src/vectorstore.py
```

---

### 7.2 Error: "Incorrect API key"

**Causa:** API key de OpenAI inválida o no configurada

**Solución:**
```bash
# Verificar .env
cat .env | grep OPENAI_API_KEY

# Si está mal, editar
nano .env

# Reiniciar servidor
python src/main.py
```

---

### 7.3 Error: Conflictos de dependencias LangChain

**Síntoma:**
```
ImportError: cannot import name 'Tool' from 'langchain.tools'
```

**Solución:**
```bash
# Desinstalar todo LangChain
pip uninstall -y langchain langchain-openai langchain-community langchain-core

# Reinstalar versiones compatibles
pip install langchain==0.3.0
pip install langchain-openai==0.2.0
pip install langchain-community==0.3.0
pip install openai>=1.10.0
```

---

### 7.4 Error: "Module 'faiss' has no attribute 'IndexFlatL2'"

**Causa:** Versión incorrecta de FAISS

**Solución:**
```bash
pip uninstall faiss-cpu faiss-gpu
pip install faiss-cpu>=1.8.0
```

---

### 7.5 Frontend no carga

**Síntoma:** Navegador muestra error 404

**Solución:**
```bash
# Verificar que frontend.html existe
ls src/frontend.html

# Verificar que main.py sirve frontend
grep "frontend.html" src/main.py

# Verificar puerto correcto
echo $PORT  # Linux/Mac
echo %PORT%  # Windows
```

---

### 7.6 Latencia alta (>3 segundos)

**Diagnóstico:**
```python
# Agregar prints de tiempo en main.py
import time

@app.post("/risk")
async def estratificar_riesgo(req: RiskRequest):
    start = time.time()
    result = risk_tool.estratificar(...)
    elapsed = time.time() - start
    print(f"⏱️  Risk tool: {elapsed:.2f}s")
    return {"result": result}
```

**Causas comunes:**
- OpenAI API lenta (>1s)
- RAG con muchos documentos
- Cold start (primera llamada)

**Soluciones:**
- Implementar caching con Redis
- Reducir k en búsquedas RAG
- Pre-calentar modelos al inicio

---

## 8. Best Practices

### 8.1 Seguridad

**❌ NUNCA hagas esto:**
```python
# NO hardcodear API keys
OPENAI_API_KEY = "sk-proj-..."  # ❌ MAL

# NO subir .env a Git
git add .env  # ❌ MAL
```

**✅ Hacer esto:**
```python
# Usar variables de entorno
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")  # ✅ BIEN
```

### 8.2 Manejo de Errores

**❌ NUNCA hagas esto:**
```python
result = tool.estratificar(...)  # ❌ Sin try-catch
```

**✅ Hacer esto:**
```python
try:
    result = tool.estratificar(...)
except ValueError as e:
    logger.error(f"Error de validación: {e}")
    return {"error": "Datos inválidos"}
except Exception as e:
    logger.error(f"Error inesperado: {e}")
    return {"error": "Error interno del servidor"}
```

### 8.3 Logging

**❌ NUNCA hagas esto:**
```python
print("Procesando request...")  # ❌ print en producción
```

**✅ Hacer esto:**
```python
import logging

logger = logging.getLogger(__name__)
logger.info("Procesando request de estratificación")
logger.debug(f"Parámetros: a1c={a1c}, pa={pa}")
```

### 8.4 Performance

**Optimizaciones recomendadas:**

1. **Caching de embeddings:**
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_embedding(text: str):
    return embeddings.embed_query(text)
```

2. **Connection pooling OpenAI:**
```python
from openai import OpenAI

client = OpenAI(
    max_retries=3,
    timeout=30.0
)
```

3. **Batch processing:**
```python
# En lugar de procesar 1 por 1
for paciente in pacientes:
    result = tool.estratificar(**paciente)  # ❌ Lento

# Procesar en batch
results = tool.estratificar_batch(pacientes)  # ✅ Rápido
```

---

## 9. FAQ

### 9.1 ¿Puedo usar otros modelos LLM?

Sí, el sistema es agnóstico al LLM. Para cambiar:

```python
# Usar Gemini en lugar de GPT-4o-mini
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0
)
```

### 9.2 ¿Cuánto cuesta ejecutar el sistema?

**Costos mensuales estimados (100 consultas/día):**
- OpenAI API: $0.38 (2.5M tokens)
- Railway: $5.00 (1 instancia)
- **Total: $5.38/mes**

### 9.3 ¿Cómo agregar un nuevo procedimiento médico?

1. Copiar PDF a `data/raw/`
2. Recrear vector store: `python src/vectorstore.py`
3. (Opcional) Crear tool específica en `src/tools/`

### 9.4 ¿El sistema funciona offline?

**Parcialmente:**
- ✅ Risk Tool: Sí (lógica local)
- ✅ Validate Tool (lógica): Sí
- ❌ Validate Tool (RAG): No (requiere OpenAI)
- ❌ Search Tool: No (requiere OpenAI embeddings)

### 9.5 ¿Cómo exportar/importar el vector store?

**Exportar:**
```bash
# Comprimir
tar -czf faiss_index.tar.gz data/faiss_index/
```

**Importar:**
```bash
# Descomprimir
tar -xzf faiss_index.tar.gz -C data/
```

### 9.6 ¿Puedo usar el sistema sin internet?

No completamente. Requieres internet para:
- Llamadas a OpenAI API (embeddings, LLM)
- Si deploys en Railway

Para uso offline total, necesitarías:
- Modelo LLM local (Llama, Mistral con Ollama)
- Embeddings locales (sentence-transformers)
- Deployment local (Docker)

---

**Autor**: Yvonne Echevarria  
**Última actualización**: Diciembre 2024  
**Versión**: 1.0
