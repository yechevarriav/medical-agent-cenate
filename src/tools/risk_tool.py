from langchain.tools import StructuredTool
from pydantic import BaseModel, Field
from typing import Optional
import json

class RiskInput(BaseModel):
    a1c: Optional[float] = Field(default=None, description="A1C en %")
    pa_sistolica: Optional[int] = Field(default=None, description="PA sistólica mmHg")
    pa_diastolica: Optional[int] = Field(default=None, description="PA diastólica mmHg")
    ldl: Optional[int] = Field(default=None, description="LDL mg/dL")
    phq9: Optional[int] = Field(default=None, description="PHQ-9 score")
    gad7: Optional[int] = Field(default=None, description="GAD-7 score")

class RiskStratificationTool:
    def estratificar(self,
                     a1c: Optional[float] = None,
                     pa_sistolica: Optional[int] = None,
                     pa_diastolica: Optional[int] = None,
                     ldl: Optional[int] = None,
                     phq9: Optional[int] = None,
                     gad7: Optional[int] = None) -> str:

        resultado = {"evaluacion": {}, "recomendaciones": []}

        # Diabetes
        if a1c is not None:
            if a1c < 7:
                resultado["evaluacion"]["diabetes"] = "Bajo"
                resultado["recomendaciones"].append("Monitoreo trimestral")
            elif 7 <= a1c <= 8:
                resultado["evaluacion"]["diabetes"] = "Moderado"
                resultado["recomendaciones"].append("Monitoreo mensual")
            else:
                resultado["evaluacion"]["diabetes"] = "Alto"
                resultado["recomendaciones"].append("Derivar a endocrinología")

        # Hipertensión
        if pa_sistolica and pa_diastolica:
            if pa_sistolica < 140 and pa_diastolica < 90:
                resultado["evaluacion"]["hipertension"] = "Bajo"
            elif pa_sistolica < 160 or pa_diastolica < 100:
                resultado["evaluacion"]["hipertension"] = "Moderado"
            else:
                resultado["evaluacion"]["hipertension"] = "Alto"
                resultado["recomendaciones"].append("Derivar a cardiología")

        # Dislipidemia
        if ldl is not None:
            if ldl < 70:
                resultado["evaluacion"]["dislipidemia"] = "Bajo"
            elif ldl <= 100:
                resultado["evaluacion"]["dislipidemia"] = "Moderado"
            else:
                resultado["evaluacion"]["dislipidemia"] = "Alto"

        # Psicológico
        if phq9 and gad7:
            if phq9 < 5 and gad7 < 5:
                resultado["evaluacion"]["psicologico"] = "Bajo"
            elif phq9 <= 9 or gad7 <= 9:
                resultado["evaluacion"]["psicologico"] = "Moderado"
            else:
                resultado["evaluacion"]["psicologico"] = "Alto"
                resultado["recomendaciones"].append("Derivar a psiquiatría")

        resultado["fuente"] = "PM.2.1.2 Anexo 10"
        return json.dumps(resultado, ensure_ascii=False, indent=2)

    def as_tool(self):
        return StructuredTool.from_function(
            func=self.estratificar,
            name="estratificar_riesgo_cronico",
            description="Clasifica riesgo de pacientes crónicos (Bajo/Moderado/Alto)",
            args_schema=RiskInput
        )

if __name__ == "__main__":
    print("🧪 TEST RISK TOOL")
    tool = RiskStratificationTool()
    result = tool.estratificar(a1c=8.5, pa_sistolica=150, pa_diastolica=95, ldl=110)
    print(result)
