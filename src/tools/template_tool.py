from langchain.tools import StructuredTool
from pydantic import BaseModel, Field
from typing import Literal

class TemplateInput(BaseModel):
    tipo: Literal["sincrona", "asincrona", "cenacron"] = Field(description="Tipo de plantilla")

class GenerateTemplateTool:
    TEMPLATES = {
        "sincrona": "📋 TELECOLPOSCOPÍA SÍNCRONA - CENATE\nHORA: _____\n☐ CONSENTIMIENTO INFORMADO\n...",
        "asincrona": "📋 TELECOLPOSCOPÍA ASÍNCRONA - CENATE\nFECHA: _____\n...",
        "cenacron": "📋 ATENCIÓN PACIENTES CRÓNICOS\nFECHA: _____\n☐ CONSENTIMIENTO VERBAL\n..."
    }

    def generar(self, tipo: str) -> str:
        return self.TEMPLATES.get(tipo.lower(), "❌ Tipo inválido")

    def as_tool(self):
        return StructuredTool.from_function(
            func=self.generar,
            name="generar_plantilla_hce",
            description="Genera plantillas de HCE: sincrona, asincrona, cenacron",
            args_schema=TemplateInput
        )

if __name__ == "__main__":
    print("🧪 TEST TEMPLATE TOOL")
    tool = GenerateTemplateTool()
    result = tool.generar("sincrona")
    print(result)
