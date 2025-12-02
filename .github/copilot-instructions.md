# AI Copilot Instructions - CENATE Medical Agent

## Project Overview
**CENATE Medical Tools API** is a FastAPI-based telemedicine platform built for EsSalud (Peru) that provides:
- **Risk stratification** for chronic disease patients using clinical parameters (A1C, blood pressure, lipids, mental health scores)
- **Eligibility validation** for telecolposcopy procedures based on PAP results and HPV status
- **Medical template generation** for electronic health records (sincrona, asincrona, cenacron)
- **RAG-powered search** over medical procedures (PM.2.1.2, PM.2.2.2) using LangChain + FAISS vector store
- **ReAct agent** that coordinates tools for complex clinical queries

## Architecture & Data Flow

### Component Layers
1. **API Layer** (`src/main.py`): FastAPI endpoints exposing clinical tools directly
2. **Agent Layer** (`src/agent.py`): LangChain ReAct agent with tool orchestration
3. **Vector Search Layer** (`src/vectorstore.py`): FAISS-backed semantic search over medical procedures
4. **Tool Layer** (`src/tools/`): Four specialized medical decision tools

### Key Data Flow
```
User Query → Agent (ReAct) → Multiple Tools (search, risk, validate, template)
              ↓
         LLM (GPT-4o-mini)
              ↓
         Tool Results → Final Answer
```

**Critical Pattern**: Tools return JSON strings (not objects) to ensure LLM-friendliness. See `risk_tool.py` line 45-46 and `validate_tool.py` line 36.

### Vector Store Setup
- **Location**: `data/faiss_index/` (persisted locally)
- **Source**: PDFs in `data/raw/` processed via `PDFProcessor` (pypdf extraction)
- **Embedding**: OpenAI `text-embedding-3-small`
- **Flow**: `vectorstore.py` handles creation/loading; `search_tool.py` wraps search for agent
- **Key Detail**: Loads existing index if present; otherwise creates from PDFs

## Tool Patterns & Conventions

### All Tools Implement Dual Interface
Each tool class (`RiskStratificationTool`, `ValidateTelecolposcopiaTool`, etc.) has:
1. **Direct method** (e.g., `estratificar()`) - used by FastAPI endpoints directly
2. **LangChain wrapper** (`as_tool()`) - used by the agent
- This enables both REST API and agent-driven workflows

### Tool Output Format
- **Return type**: Always `str` (JSON serialized)
- **Structure**: JSON with `result`, `evaluacion`, `recomendaciones`, `fuente` (procedural reference)
- **Source citing**: Tools include `"fuente": "PM.X.X.X"` to maintain clinical traceability

### New Tool Template
```python
from langchain.tools import StructuredTool
from pydantic import BaseModel, Field

class MyInput(BaseModel):
    param: str = Field(description="Human-readable param description")

class MyTool:
    def execute(self, param: str) -> str:
        result = {"data": "...", "fuente": "PM.X.X.X"}
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    def as_tool(self):
        return StructuredTool.from_function(
            func=self.execute,
            name="tool_name",
            description="What this tool does for medical teams",
            args_schema=MyInput
        )
```

## Environment & Deployment

### Local Development
- **Python**: 3.12 (Docker uses `python:3.12-slim`)
- **Start API**: `python src/main.py` (uvicorn on port 8000)
- **Start agent**: `python src/agent.py` (test script with 4 demo queries)
- **Process vectors**: `python src/vectorstore.py` (processes PDFs from `data/raw/`)
- **Required**: `.env` file with `OPENAI_API_KEY` and `PORT` (default 8000)

### Deployment
- **Docker**: Railway deployment via `Dockerfile` + `railway.json`
- **Critical**: Ensure `data/faiss_index/` persisted in deployment volume
- **Restart policy**: ON_FAILURE (max 10 retries)

## LangChain Agent Configuration
- **ReAct Prompt**: Located in `agent.py` (lines 26-60) - in Spanish, references PM procedures
- **LLM**: `gpt-4o-mini` with `temperature=0` (deterministic medical decisions)
- **Max iterations**: 5 (prevents infinite loops)
- **Parsing**: `handle_parsing_errors=True` (graceful failure)
- **Tools registered**: search_tool, risk_tool, validate_tool, template_tool

## Medical Data Standards
- **Clinical scoring**: PHQ-9 (depression), GAD-7 (anxiety) - categorical thresholds in risk_tool
- **Blood pressure categories**: Follows hypertension guidelines (systolic/diastolic boundaries)
- **PAP results**: ASC-H, AGC, LIE-AG, CARCINOMA trigger telecolposcopy eligibility
- **Age eligibility**: Telecolposcopy restricted to 25-65 years (validate_tool.py line 17)
- **Procedure codes**: PM.2.1.2 (chronic patients), PM.2.2.2 (telecolposcopy) referenced throughout

## Developer Workflows

### Adding a New Medical Tool
1. Create `src/tools/new_tool.py` with class implementing `as_tool()` method
2. Import in `agent.py` and add to `self.tools` list
3. Add endpoint in `main.py` for direct REST access if needed
4. Test via `python src/tools/new_tool.py`

### Updating Vector Store
1. Place new PDFs in `data/raw/`
2. Run `python src/vectorstore.py` (rebuilds index)
3. Agent automatically uses updated search results

### Testing the Agent
- Run `python src/agent.py` - includes 4 documented test queries (risk, procedure search, eligibility, template)
- Agent prints `verbose=True` output showing ReAct reasoning chain

## Code Organization Notes
- All Spanish variable/function names (medical domain convention in Peru) - preserve this
- Tools use relative imports; `search_tool.py` has custom sys.path insertion (line 7)
- Error handling: tools catch exceptions and return error JSON strings (never raise exceptions to agent)
