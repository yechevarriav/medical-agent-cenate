from langchain.tools import StructuredTool
from pydantic import BaseModel, Field
from typing import Literal

class TemplateInput(BaseModel):
    tipo: Literal["sincrona", "asincrona", "cenacron"] = Field(description="Tipo de plantilla")

class GenerateTemplateTool:
    def __init__(self):
        self.plantillas = {
            "sincrona": """📋 PROTOCOLO TELECOLPOSCOPÍA SÍNCRONA - CENATE

FECHA: ___/___/_____ HORA: _____

☐ CONSENTIMIENTO INFORMADO FIRMADO

DATOS DEL PACIENTE:
- Nombre: _________________________________
- Edad: _____ DNI: _______________________
- Resultado PAP: _________________________
- Resultado VPH: _________________________

EVALUACIÓN COLPOSCÓPICA EN TIEMPO REAL:
☐ Cuello uterino visible
☐ Unión escamo-columnar visible
☐ Zona de transformación tipo: ___

HALLAZGOS:
☐ Normal
☐ Cambios menores (LIE-BG)
☐ Cambios mayores (LIE-AG)
☐ Sospecha de invasión

INTERCONSULTA CON ESPECIALISTA:
Médico consultor: _________________________
Recomendación: ___________________________
_________________________________________

PLAN:
☐ Control en ___ meses
☐ Biopsia dirigida
☐ Tratamiento: ___________________________

Médico solicitante: _______________________
Médico consultor: ________________________

Fuente: PM.2.2.2 Anexo 2""",

            "asincrona": """📋 PROTOCOLO TELECOLPOSCOPÍA ASÍNCRONA - CENATE

FECHA CAPTURA: ___/___/_____
FECHA EVALUACIÓN: ___/___/_____

☐ CONSENTIMIENTO INFORMADO FIRMADO

DATOS DEL PACIENTE:
- Nombre: _________________________________
- Edad: _____ DNI: _______________________
- Resultado PAP: _________________________
- Resultado VPH: _________________________

IMÁGENES CAPTURADAS:
☐ Sin ácido acético (mínimo 3)
☐ Con ácido acético 5% (mínimo 3)
☐ Con Lugol (mínimo 2)
☐ Calidad de imágenes: ☐ Óptima ☐ Aceptable ☐ Deficiente

EVALUACIÓN DIFERIDA POR ESPECIALISTA:
Médico evaluador: _________________________
Fecha evaluación: _________________________

HALLAZGOS:
☐ Examen satisfactorio
☐ Cambios benignos
☐ LIE-BG (Bajo Grado)
☐ LIE-AG (Alto Grado)
☐ Sospecha de cáncer

RECOMENDACIÓN:
☐ Control en ___ meses
☐ Biopsia dirigida
☐ LEEP/Cono
☐ Referencia a oncología

Observaciones: ____________________________
_________________________________________

Médico solicitante: _______________________
Médico evaluador: ________________________

Fuente: PM.2.2.2 Anexo 3""",

            "cenacron": """📋 ATENCIÓN PACIENTES CRÓNICOS - CENACRON

FECHA: ___/___/_____ HORA: _____

☐ CONSENTIMIENTO VERBAL REGISTRADO

DATOS DEL PACIENTE:
- Nombre: _________________________________
- Edad: _____ DNI: _______________________
- Diagnósticos: ___________________________

ESTRATIFICACIÓN DE RIESGO:
DIABETES:
☐ A1C <7% (Bajo riesgo)
☐ A1C 7-8% (Riesgo moderado)
☐ A1C >8% (Alto riesgo → derivar endocrinología)

HIPERTENSIÓN:
☐ PA <140/90 (Controlado)
☐ PA 140-159/90-99 (Riesgo moderado)
☐ PA ≥160/100 (Alto riesgo → derivar cardiología)

DISLIPIDEMIA:
☐ LDL <70 (Óptimo)
☐ LDL 70-100 (Aceptable)
☐ LDL >100 (Elevado)

SALUD MENTAL:
☐ PHQ-9 <5 / GAD-7 <5 (Bajo)
☐ PHQ-9 5-9 / GAD-7 5-9 (Moderado)
☐ PHQ-9 ≥10 / GAD-7 ≥10 (Alto → derivar psiquiatría)

FRECUENCIA DE MONITOREO:
☐ Control trimestral (bajo riesgo)
☐ Control mensual (alto riesgo)

DERIVACIONES NECESARIAS:
☐ Endocrinología
☐ Cardiología
☐ Psiquiatría/Psicología
☐ Ninguna

PLAN DE ACCIÓN:
- Ajuste de medicación: ___________________
- Exámenes solicitados: ___________________
- Educación al paciente: ___________________
- Próxima cita: ___/___/_____

Médico tratante: __________________________

Fuente: PM.2.1.2 Anexo 10"""
        }

    def generar(self, tipo: str) -> dict:
        """Genera plantilla según tipo"""
        tipo = tipo.lower()

        if tipo not in self.plantillas:
            return {
                "error": f"Tipo '{tipo}' no válido",
                "tipos_disponibles": ["sincrona", "asincrona", "cenacron"],
                "fuente": "N/A"
            }

        fuente_map = {
            "sincrona": "PM.2.2.2 Anexo 2",
            "asincrona": "PM.2.2.2 Anexo 3",
            "cenacron": "PM.2.1.2 Anexo 10"
        }

        return {
            "tipo": tipo,
            "plantilla": self.plantillas[tipo],
            "fuente": fuente_map[tipo]
        }

    def as_tool(self):
        return StructuredTool.from_function(
            func=self.generar,
            name="generar_plantilla_hce",
            description="Genera plantillas de Historia Clínica Electrónica: sincrona (telecolposcopía en tiempo real), asincrona (telecolposcopía diferida), cenacron (pacientes crónicos)",
            args_schema=TemplateInput
        )

if __name__ == "__main__":
    print("=" * 80)
    print("🧪 TEST: GENERAR PLANTILLA HCE")
    print("=" * 80)

    tool = GenerateTemplateTool()

    # Test 1: Plantilla síncrona
    print("\n--- Test 1: Telecolposcopía Síncrona ---")
    result = tool.generar("sincrona")
    print(f"✅ Tipo: {result['tipo']}")
    print(f"📄 Fuente: {result['fuente']}")
    print(f"📋 Plantilla:\n{result['plantilla'][:200]}...")

    # Test 2: Plantilla asíncrona
    print("\n--- Test 2: Telecolposcopía Asíncrona ---")
    result = tool.generar("asincrona")
    print(f"✅ Tipo: {result['tipo']}")
    print(f"📄 Fuente: {result['fuente']}")

    # Test 3: Plantilla CENACRON
    print("\n--- Test 3: CENACRON ---")
    result = tool.generar("cenacron")
    print(f"✅ Tipo: {result['tipo']}")
    print(f"📄 Fuente: {result['fuente']}")

    # Test 4: Tipo inválido
    print("\n--- Test 4: Tipo Inválido ---")
    result = tool.generar("invalido")
    print(f"❌ Error: {result.get('error')}")
    print(f"💡 Tipos disponibles: {result.get('tipos_disponibles')}")

    print("\n" + "=" * 80)
    print("✅ TESTS COMPLETADOS")
    print("=" * 80)
