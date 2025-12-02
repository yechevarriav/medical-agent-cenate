from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from tools.search_tool import SearchMedicalTool
from tools.risk_tool import RiskStratificationTool
from tools.validate_tool import ValidateTelecolposcopiaTool
from tools.template_tool import GenerateTemplateTool
import os
from dotenv import load_dotenv

load_dotenv()

class MedicalAssistantAgent:
    def __init__(self):
        # Inicializar LLM
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            api_key=os.getenv("OPENAI_API_KEY")
        )

        # Inicializar tools
        search_tool_obj = SearchMedicalTool()
        risk_tool_obj = RiskStratificationTool()
        validate_tool_obj = ValidateTelecolposcopiaTool()
        template_tool_obj = GenerateTemplateTool()

        self.tools = [
            search_tool_obj.as_tool(),
            risk_tool_obj.as_tool(),
            validate_tool_obj.as_tool(),
            template_tool_obj.as_tool()
        ]

        # Prompt ReAct
        self.prompt = PromptTemplate.from_template("""
Eres un asistente médico especializado en procedimientos de telemedicina de CENATE (EsSalud - Perú).

Tu rol es ayudar al personal médico y administrativo a:
1. Consultar procedimientos de telemedicina (PM.2.1.2 y PM.2.2.2)
2. Estratificar riesgo de pacientes crónicos
3. Validar criterios de elegibilidad para telecolposcopía
4. Generar plantillas de Historia Clínica Electrónica

REGLAS IMPORTANTES:
- SIEMPRE usa las herramientas disponibles para obtener información precisa
- NO inventes información - solo usa lo que devuelven las herramientas
- Cita la fuente cuando uses información de procedimientos (ej: "Según PM.2.1.2...")
- Sé preciso, profesional y conciso
- Si no encuentras información, dilo claramente

Tienes acceso a estas herramientas:
{tools}

Nombres de herramientas: {tool_names}

Usa el siguiente formato ReAct:

Question: la pregunta del usuario
Thought: analiza qué necesitas hacer
Action: la herramienta a usar [{tool_names}]
Action Input: el input para la herramienta
Observation: resultado de la herramienta
... (puedes repetir Thought/Action/Action Input/Observation varias veces)
Thought: ahora tengo suficiente información para responder
Final Answer: tu respuesta final al usuario

Comienza!

Question: {input}
Thought: {agent_scratchpad}
""")

        # Crear agente
        self.agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )

        # Crear executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5,
            return_intermediate_steps=True
        )

    def query(self, question: str) -> dict:
        """Procesa una consulta y retorna la respuesta"""
        try:
            result = self.agent_executor.invoke({"input": question})

            return {
                "output": result.get("output", ""),
                "intermediate_steps": result.get("intermediate_steps", []),
                "tool_calls": len(result.get("intermediate_steps", []))
            }

        except Exception as e:
            return {
                "output": f"❌ Error al procesar la consulta: {str(e)}",
                "tool_calls": 0,
                "error": str(e)
            }

# Test del agente
if __name__ == "__main__":
    print("="*80)
    print("🤖 INICIANDO AGENTE DE TELEMEDICINA CENATE")
    print("="*80)

    agent = MedicalAssistantAgent()

    # Test 1: Búsqueda de procedimientos
    print("\n" + "="*80)
    print("📋 TEST 1: Consulta sobre procedimientos")
    print("="*80)
    query1 = "¿Cuáles son los pasos para atender un paciente crónico con diabetes por telemedicina?"
    print(f"\n❓ Pregunta: {query1}\n")
    result1 = agent.query(query1)
    print(f"\n✅ Respuesta:\n{result1['output']}")
    print(f"\n📊 Tool calls: {result1['tool_calls']}")

    # Test 2: Estratificación de riesgo
    print("\n\n" + "="*80)
    print("📊 TEST 2: Estratificación de riesgo")
    print("="*80)
    query2 = "Tengo un paciente con A1C de 8.5%, presión arterial 155/98 y LDL de 115. ¿Cuál es su nivel de riesgo?"
    print(f"\n❓ Pregunta: {query2}\n")
    result2 = agent.query(query2)
    print(f"\n✅ Respuesta:\n{result2['output']}")
    print(f"\n📊 Tool calls: {result2['tool_calls']}")

    # Test 3: Validación telecolposcopía
    print("\n\n" + "="*80)
    print("✔️ TEST 3: Validación de elegibilidad")
    print("="*80)
    query3 = "¿Una paciente de 45 años con PAP resultado ASC-H es elegible para telecolposcopía?"
    print(f"\n❓ Pregunta: {query3}\n")
    result3 = agent.query(query3)
    print(f"\n✅ Respuesta:\n{result3['output']}")
    print(f"\n📊 Tool calls: {result3['tool_calls']}")

    # Test 4: Generación de plantilla
    print("\n\n" + "="*80)
    print("📄 TEST 4: Generación de plantilla")
    print("="*80)
    query4 = "Genera una plantilla de HCE para atención de pacientes crónicos"
    print(f"\n❓ Pregunta: {query4}\n")
    result4 = agent.query(query4)
    print(f"\n✅ Respuesta:\n{result4['output']}")
    print(f"\n📊 Tool calls: {result4['tool_calls']}")

    print("\n" + "="*80)
    print("✅ TESTS COMPLETADOS")
    print("="*80)
