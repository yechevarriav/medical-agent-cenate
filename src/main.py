from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from tools.risk_tool import RiskStratificationTool
from tools.validate_tool import ValidateTelecolposcopiaTool
from tools.template_tool import GenerateTemplateTool
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="CENATE Medical Tools API",
    description="API de herramientas médicas - Proyecto 3",
    version="1.0.0"
)

# Inicializar tools
risk_tool = RiskStratificationTool()
validate_tool = ValidateTelecolposcopiaTool()
template_tool = GenerateTemplateTool()

@app.get("/")
async def root():
    return {
        "message": "CENATE Medical Tools API",
        "status": "operational",
        "available_endpoints": ["/risk", "/validate", "/template", "/health"]
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

# Endpoint de estratificación de riesgo
class RiskRequest(BaseModel):
    a1c: float = None
    pa_sistolica: int = None
    pa_diastolica: int = None
    ldl: int = None
    phq9: int = None
    gad7: int = None

@app.post("/risk")
async def estratificar_riesgo(req: RiskRequest):
    """Estratifica riesgo de paciente crónico"""
    try:
        result = risk_tool.estratificar(
            a1c=req.a1c,
            pa_sistolica=req.pa_sistolica,
            pa_diastolica=req.pa_diastolica,
            ldl=req.ldl,
            phq9=req.phq9,
            gad7=req.gad7
        )
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint de validación
class ValidateRequest(BaseModel):
    edad: int
    pap_resultado: str = None
    vph_positivo: bool = None

@app.post("/validate")
async def validar_telecolposcopia(req: ValidateRequest):
    """Valida elegibilidad para telecolposcopía"""
    try:
        result = validate_tool.validar(
            edad=req.edad,
            pap_resultado=req.pap_resultado,
            vph_positivo=req.vph_positivo
        )
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint de plantilla
@app.get("/template/{tipo}")
async def generar_plantilla(tipo: str):
    """Genera plantilla HCE: sincrona, asincrona, cenacron"""
    try:
        result = template_tool.generar(tipo)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
