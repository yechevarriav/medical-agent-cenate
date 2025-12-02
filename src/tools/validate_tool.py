from langchain.tools import StructuredTool
from pydantic import BaseModel, Field
from typing import Optional
import json

class ValidateInput(BaseModel):
    edad: int = Field(description="Edad del paciente")
    pap_resultado: Optional[str] = Field(default=None, description="PAP: AGC, ASC-H, LIE-AG")
    vph_positivo: Optional[bool] = Field(default=None, description="VPH positivo")

class ValidateTelecolposcopiaTool:
    def validar(self, edad: int, pap_resultado: Optional[str] = None, vph_positivo: Optional[bool] = None) -> str:
        resultado = {
            "elegible": False,
            "criterios": {"edad_valida": False, "pap_positivo": False, "vph_positivo": False},
            "detalles": []
        }

        # Edad 25-65
        if 25 <= edad <= 65:
            resultado["criterios"]["edad_valida"] = True
            resultado["detalles"].append(f"✅ Edad válida: {edad} años")
        else:
            resultado["detalles"].append(f"❌ Edad fuera de rango: {edad}")

        # PAP
        if pap_resultado:
            pap_upper = pap_resultado.upper()
            if pap_upper in ["AGC", "ASC-H", "LIE-AG", "CARCINOMA"]:
                resultado["criterios"]["pap_positivo"] = True
                resultado["detalles"].append(f"✅ PAP positivo: {pap_resultado}")

        # VPH
        if vph_positivo:
            resultado["criterios"]["vph_positivo"] = True
            resultado["detalles"].append("✅ VPH positivo")

        # Elegibilidad
        if resultado["criterios"]["edad_valida"]:
            if resultado["criterios"]["pap_positivo"] or resultado["criterios"]["vph_positivo"]:
                resultado["elegible"] = True

        resultado["fuente"] = "PM.2.2.2 - Público Objetivo"
        return json.dumps(resultado, ensure_ascii=False, indent=2)

    def as_tool(self):
        return StructuredTool.from_function(
            func=self.validar,
            name="validar_criterios_telecolposcopia",
            description="Valida si paciente cumple criterios para telecolposcopía",
            args_schema=ValidateInput
        )

if __name__ == "__main__":
    print("🧪 TEST VALIDATE TOOL")
    tool = ValidateTelecolposcopiaTool()
    result = tool.validar(edad=45, pap_resultado="ASC-H", vph_positivo=True)
    print(result)
