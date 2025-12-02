from langchain.tools import StructuredTool
from pydantic import BaseModel, Field
from typing import Optional, List

class RiskInput(BaseModel):
    a1c: Optional[float] = Field(default=None, description="Hemoglobina A1C (%)")
    pa_sistolica: Optional[int] = Field(default=None, description="Presión arterial sistólica (mmHg)")
    pa_diastolica: Optional[int] = Field(default=None, description="Presión arterial diastólica (mmHg)")
    ldl: Optional[int] = Field(default=None, description="Colesterol LDL (mg/dL)")
    phq9: Optional[int] = Field(default=None, description="Escala PHQ-9 (0-27)")
    gad7: Optional[int] = Field(default=None, description="Escala GAD-7 (0-21)")

class RiskStratificationTool:
    def __init__(self):
        self.fuente = "PM.2.1.2 Anexo 10 - Criterios de Estandarización de Riesgo"

    def estratificar(
        self,
        a1c: Optional[float] = None,
        pa_sistolica: Optional[int] = None,
        pa_diastolica: Optional[int] = None,
        ldl: Optional[int] = None,
        phq9: Optional[int] = None,
        gad7: Optional[int] = None
    ) -> dict:
        """Estratifica riesgo según criterios PM.2.1.2 Anexo 10"""

        evaluacion = {}
        recomendaciones = []

        # DIABETES (A1C)
        if a1c is not None:
            if a1c < 7:
                evaluacion["diabetes"] = "Bajo"
            elif 7 <= a1c <= 8:
                evaluacion["diabetes"] = "Moderado"
            else:  # a1c > 8
                evaluacion["diabetes"] = "Alto"
                recomendaciones.append("Derivar a endocrinología")

        # HIPERTENSIÓN
        if pa_sistolica is not None and pa_diastolica is not None:
            if pa_sistolica < 140 and pa_diastolica < 90:
                evaluacion["hipertension"] = "Controlado"
            elif (140 <= pa_sistolica < 160) or (90 <= pa_diastolica < 100):
                evaluacion["hipertension"] = "Moderado"
            else:  # PA >= 160/100
                evaluacion["hipertension"] = "Alto"
                recomendaciones.append("Derivar a cardiología")

        # DISLIPIDEMIA (LDL)
        if ldl is not None:
            if ldl < 70:
                evaluacion["dislipidemia"] = "Bajo"
            elif 70 <= ldl <= 100:
                evaluacion["dislipidemia"] = "Moderado"
            else:  # ldl > 100
                evaluacion["dislipidemia"] = "Alto"

        # SALUD MENTAL
        if phq9 is not None or gad7 is not None:
            scores = [s for s in [phq9, gad7] if s is not None]
            max_score = max(scores)

            if max_score < 5:
                evaluacion["psicologico"] = "Bajo"
            elif 5 <= max_score <= 9:
                evaluacion["psicologico"] = "Moderado"
            else:  # >= 10
                evaluacion["psicologico"] = "Alto"
                recomendaciones.append("Derivar a psiquiatría")

        # Determinar frecuencia de monitoreo
        niveles_alto = [v for v in evaluacion.values() if v == "Alto"]
        if niveles_alto:
            recomendaciones.append("Control mensual requerido")
        else:
            recomendaciones.append("Control trimestral")

        return {
            "evaluacion": evaluacion,
            "recomendaciones": recomendaciones,
            "fuente": self.fuente
        }

    def as_tool(self):
        return StructuredTool.from_function(
            func=self.estratificar,
            name="estratificar_riesgo_cronico",
            description="Estratifica riesgo de pacientes crónicos según PM.2.1.2 Anexo 10: diabetes (A1C), hipertensión (PA), dislipidemia (LDL), salud mental (PHQ-9/GAD-7)",
            args_schema=RiskInput
        )

if __name__ == "__main__":
    print("=" * 80)
    print("🧪 TEST: ESTRATIFICACIÓN DE RIESGO")
    print("=" * 80)

    tool = RiskStratificationTool()

    # Test: Paciente con múltiples factores de riesgo alto
    print("\n--- Test: Paciente Alto Riesgo ---")
    result = tool.estratificar(
        a1c=11,
        pa_sistolica=122,
        pa_diastolica=98,
        ldl=112,
        phq9=10,
        gad7=21
    )

    print(f"📊 Evaluación:")
    for categoria, nivel in result["evaluacion"].items():
        print(f"   {categoria.capitalize()}: {nivel}")

    print(f"\n⚠️  Recomendaciones:")
    for rec in result["recomendaciones"]:
        print(f"   - {rec}")

    print(f"\n📄 Fuente: {result['fuente']}")

    print("\n" + "=" * 80)
