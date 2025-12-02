from langchain.tools import StructuredTool
from pydantic import BaseModel, Field
from typing import List, Dict
import sys
import os

# Añadir path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vectorstore import MedicalVectorStore

class SearchInput(BaseModel):
    query: str = Field(description="Consulta médica en lenguaje natural")

class SearchMedicalTool:
    def __init__(self):
        self.vectorstore = MedicalVectorStore()

    def search(self, query: str) -> str:
        """Busca en procedimientos médicos de CENATE"""
        try:
            results = self.vectorstore.search(query, n_results=3)

            if not results:
                return "❌ No se encontraron procedimientos relevantes."

            response = "📋 Información encontrada:\n\n"

            for i, result in enumerate(results, 1):
                source = result['metadata']['source']
                score = result['score']
                content = result['content']

                response += f"📄 Fuente {i}: {source} (Score: {score:.2%})\n"
                response += f"{content[:300]}...\n\n---\n\n"

            return response

        except Exception as e:
            return f"❌ Error: {str(e)}"

    def as_tool(self):
        return StructuredTool.from_function(
            func=self.search,
            name="search_medical_procedures",
            description="""Busca información en procedimientos de telemedicina de CENATE.
            Usa cuando necesites info sobre: pacientes crónicos, telecolposcopía, protocolos.""",
            args_schema=SearchInput
        )

if __name__ == "__main__":
    print("="*80)
    print("🧪 TEST DE SEARCH TOOL")
    print("="*80)

    tool = SearchMedicalTool()
    result = tool.search("¿Cómo atender pacientes crónicos con diabetes?")
    print(result)
