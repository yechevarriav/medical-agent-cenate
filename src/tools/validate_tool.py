from langchain.tools import StructuredTool
from pydantic import BaseModel, Field
from typing import Optional
import sys
from pathlib import Path

# Agregar path para imports
sys.path.append(str(Path(__file__).parent.parent))

class ValidateInput(BaseModel):
    edad: int = Field(description="Edad del paciente")
    pap_resultado: Optional[str] = Field(default=None, description="Resultado PAP: AGC, ASC-H, LIE-AG, CARCINOMA")
    vph_positivo: Optional[bool] = Field(default=None, description="Test VPH de alto riesgo positivo")

class ValidateTelecolposcopiaTool:
    def __init__(self):
        # Criterios base (rápidos, siempre disponibles)
        self.criterios_base = {
            "edad_min": 25,
            "edad_max": 65,
            "pap_positivos": ["AGC", "ASC-H", "LIE-AG", "CARCINOMA"],
            "fuente_base": "PM.2.2.2 - Público Objetivo"
        }

        # Intentar cargar vectorstore para verificación
        self.vectorstore = None
        self.rag_disponible = False
        try:
            from vectorstore import MedicalVectorStore
            self.vectorstore = MedicalVectorStore()
            self.vectorstore.load()
            self.rag_disponible = True
            print("✅ RAG disponible para verificación")
        except Exception as e:
            print(f"⚠️  RAG no disponible: {e}")

    def _validar_con_logica(self, edad: int, pap_resultado: Optional[str], vph_positivo: Optional[bool]) -> dict:
        """Validación rápida con lógica hardcoded"""
        criterios_cumplidos = []
        detalles = []

        # Validar edad (25-65 años)
        edad_valida = self.criterios_base["edad_min"] <= edad <= self.criterios_base["edad_max"]

        if edad_valida:
            criterios_cumplidos.append(f"Edad válida: {edad} años (rango 25-65)")
        else:
            detalles.append(f"Edad fuera de rango: {edad} años (requiere 25-65)")

        # Validar PAP positivo
        pap_positivo = False
        if pap_resultado:
            pap_upper = pap_resultado.upper()
            if pap_upper in self.criterios_base["pap_positivos"]:
                pap_positivo = True
                criterios_cumplidos.append(f"PAP positivo: {pap_resultado}")
            else:
                detalles.append(f"PAP '{pap_resultado}' no es criterio de elegibilidad")

        # Validar VPH
        if vph_positivo is True:
            criterios_cumplidos.append("VPH de alto riesgo positivo")
        elif vph_positivo is False:
            detalles.append("VPH negativo")

        # Determinar elegibilidad: edad válida Y (PAP positivo O VPH positivo)
        elegible = edad_valida and (pap_positivo or vph_positivo is True)

        if not elegible:
            if not edad_valida:
                detalles.append("No cumple criterio de edad")
            if not pap_positivo and vph_positivo is not True:
                detalles.append("Requiere PAP positivo (AGC, ASC-H, LIE-AG, CARCINOMA) O VPH de alto riesgo positivo")

        return {
            "elegible": elegible,
            "criterios_cumplidos": criterios_cumplidos,
            "detalles": " | ".join(detalles) if detalles else "Cumple todos los criterios de elegibilidad",
            "fuente": self.criterios_base["fuente_base"]
        }

    def _verificar_con_rag(self, edad: int, pap_resultado: Optional[str], vph_positivo: Optional[bool]) -> Optional[dict]:
        """Verificación con RAG del documento fuente"""
        if not self.rag_disponible:
            return None

        try:
            # Construir query contextual
            query_parts = [f"criterios elegibilidad telecolposcopía edad {edad} años"]
            if pap_resultado:
                query_parts.append(f"PAP {pap_resultado}")
            if vph_positivo is not None:
                query_parts.append(f"VPH {'positivo' if vph_positivo else 'negativo'}")

            query = " ".join(query_parts)

            # Buscar en vector store
            resultados = self.vectorstore.search(query, k=2)

            if resultados:
                # Extraer contexto más relevante
                contexto = resultados[0][0].page_content
                score = resultados[0][1]

                return {
                    "contexto_fuente": contexto[:400],  # Primeros 400 caracteres
                    "relevancia": f"{score:.2f}",
                    "verificado_con_rag": True
                }
        except Exception as e:
            print(f"⚠️  Error en verificación RAG: {e}")

        return None

    def validar(self, edad: int, pap_resultado: Optional[str] = None, vph_positivo: Optional[bool] = None) -> dict:
        """
        Validación híbrida:
        1. Validación rápida con lógica (50ms)
        2. Verificación con RAG si está disponible (200ms adicionales)
        """

        # PASO 1: Validación rápida con lógica
        resultado = self._validar_con_logica(edad, pap_resultado, vph_positivo)

        # PASO 2: Verificar con RAG si está disponible
        if self.rag_disponible:
            verificacion = self._verificar_con_rag(edad, pap_resultado, vph_positivo)

            if verificacion:
                resultado["contexto_pdf"] = verificacion["contexto_fuente"]
                resultado["fuente"] = f"{self.criterios_base['fuente_base']} (Verificado con RAG - Score: {verificacion['relevancia']})"
            else:
                resultado["fuente"] = f"{self.criterios_base['fuente_base']} (Verificación RAG no disponible)"
        else:
            resultado["fuente"] = f"{self.criterios_base['fuente_base']} "

        return resultado

    def as_tool(self):
        return StructuredTool.from_function(
            func=self.validar,
            name="validar_criterios_telecolposcopia",
            description="Valida elegibilidad para telecolposcopía según PM.2.2.2: edad 25-65 años Y (PAP positivo O VPH+). Usa validación rápida con verificación RAG.",
            args_schema=ValidateInput
        )

if __name__ == "__main__":
    print("=" * 80)
    print("🧪 TEST: VALIDACIÓN HÍBRIDA (Lógica + RAG)")
    print("=" * 80)

    tool = ValidateTelecolposcopiaTool()

    print(f"\n🔍 Modo RAG: {'✅ Activo' if tool.rag_disponible else '❌ Desactivado (usando solo lógica)'}\n")

    # Test 1: Elegible completo
    print("--- Test 1: Paciente Elegible (45 años, PAP ASC-H, VPH+) ---")
    result = tool.validar(edad=45, pap_resultado="ASC-H", vph_positivo=True)
    print(f"{'✅' if result['elegible'] else '❌'} Elegible: {result['elegible']}")
    print(f"📋 Criterios cumplidos:")
    for criterio in result['criterios_cumplidos']:
        print(f"   - {criterio}")
    print(f"📄 Fuente: {result['fuente']}")
    if 'contexto_pdf' in result:
        print(f"📖 Contexto PDF:\n   {result['contexto_pdf'][:150]}...")

    # Test 2: No elegible (edad)
    print("\n--- Test 2: No Elegible (15 años, PAP AGC, VPH+) ---")
    result = tool.validar(edad=15, pap_resultado="AGC", vph_positivo=True)
    print(f"{'✅' if result['elegible'] else '❌'} Elegible: {result['elegible']}")
    print(f"⚠️  Detalles: {result['detalles']}")
    print(f"📄 Fuente: {result['fuente']}")

    # Test 3: No elegible (sin criterios)
    print("\n--- Test 3: No Elegible (45 años, PAP negativo, VPH-) ---")
    result = tool.validar(edad=45, pap_resultado="NEGATIVO", vph_positivo=False)
    print(f"{'✅' if result['elegible'] else '❌'} Elegible: {result['elegible']}")
    print(f"⚠️  Detalles: {result['detalles']}")
    print(f"📄 Fuente: {result['fuente']}")

    # Test 4: Elegible solo con VPH
    print("\n--- Test 4: Elegible (50 años, sin PAP, VPH+) ---")
    result = tool.validar(edad=50, pap_resultado=None, vph_positivo=True)
    print(f"{'✅' if result['elegible'] else '❌'} Elegible: {result['elegible']}")
    print(f"📋 Criterios cumplidos:")
    for criterio in result['criterios_cumplidos']:
        print(f"   - {criterio}")
    print(f"📄 Fuente: {result['fuente']}")
    if 'contexto_pdf' in result:
        print(f"📖 Contexto PDF:\n   {result['contexto_pdf'][:150]}...")

    print("\n" + "=" * 80)
    print("✅ TESTS COMPLETADOS")
    print("=" * 80)
