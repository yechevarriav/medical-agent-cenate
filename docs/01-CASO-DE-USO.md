# Caso de Uso: Asistente Virtual Inteligente para Procedimientos de Telemedicina en CENATE

## 1. Contexto y Problemática

### 1.1 Situación Actual

El Centro Nacional de Telemedicina (CENATE) de EsSalud atiende diariamente más de 100 consultas relacionadas con procedimientos médicos estandarizados, específicamente:

- **PM.2.1.2**: Procedimiento de Atención de Pacientes Crónicos (CENACRON)
- **PM.2.2.2**: Procedimiento de Teleinterconsulta de Telecolposcopía Síncrona y Asíncrona

**Problemas identificados:**

1. **Tiempo desperdiciado en tareas repetitivas**: El personal médico invierte entre 15-30 minutos por paciente consultando manualmente los procedimientos PM.2.1.2 y PM.2.2.2 para:
   - Estratificar riesgo de pacientes crónicos según criterios del Anexo 10
   - Validar elegibilidad para telecolposcopía según público objetivo
   - Generar plantillas de Historia Clínica Electrónica

2. **Inconsistencia en criterios de evaluación**: Diferentes médicos interpretan los criterios de forma variable, resultando en:
   - 12% de errores en estratificación de riesgo
   - Variabilidad en derivaciones a especialistas
   - Falta de estandarización en reportes

3. **Barrera de acceso a información**: Los procedimientos están en documentos PDF de 20-30 páginas, dificultando:
   - Búsqueda rápida de criterios específicos
   - Actualización cuando cambian los protocolos
   - Capacitación de nuevo personal médico

4. **Carga cognitiva del personal**: Los médicos deben memorizar múltiples criterios:
   - Rangos de A1C para diabetes (3 niveles de riesgo)
   - Umbrales de presión arterial (3 categorías)
   - Criterios de elegibilidad para telecolposcopía (edad, PAP, VPH)
   - Escalas psicológicas PHQ-9 y GAD-7

### 1.2 Impacto Cuantificado

**Análisis de tiempo perdido:**
- 100 consultas/día × 20 minutos promedio = 2,000 minutos/día (33.3 horas/día)
- 250 días laborables/año = 8,333 horas/año de tiempo médico
- Valor hora médica: ~$10 USD → **$83,330 USD/año en tiempo desperdiciado**

**Errores en criterios:**
- 12% de casos con estratificación incorrecta
- 8% de derivaciones innecesarias a especialistas
- 5% de casos que deberían derivarse pero no se detectan

---

## 2. Solución Propuesta

### 2.1 Descripción General

Desarrollo de un **Asistente Virtual Inteligente** basado en IA que automatiza los procesos críticos de consulta y aplicación de procedimientos médicos de CENATE mediante:

1. **Retrieval-Augmented Generation (RAG)**: Sistema que lee directamente los documentos oficiales PM.2.1.2 y PM.2.2.2 para garantizar información actualizada y trazable.

2. **Herramientas Especializadas**: 4 tools médicas implementadas:
   - Estratificación de riesgo de pacientes crónicos
   - Validación de elegibilidad para telecolposcopía
   - Generación de plantillas HCE
   - Búsqueda semántica en procedimientos

3. **Arquitectura Híbrida**: Combina validación lógica rápida (50ms) con verificación contra documentos fuente vía RAG (200ms adicionales).

### 2.2 Componentes Técnicos

**Backend:**
- LLM: GPT-4o-mini (OpenAI)
- Framework: LangChain 0.3.0
- Vector Store: FAISS con embeddings OpenAI text-embedding-3-small
- API: FastAPI 0.109.0

**Infraestructura:**
- Deployment: Railway (orchestrator)
- Serverless: AWS Lambda (tools serverless)
- CI/CD: GitHub Actions
- Monitoreo: CloudWatch

**Frontend:**
- HTML/CSS/JavaScript vanilla
- Interfaz web responsive
- Validación de datos en tiempo real

---

## 3. Público Objetivo

### 3.1 Usuarios Directos

**Personal médico de CENATE:**
- Médicos generales que atienden pacientes crónicos
- Especialistas en ginecología (telecolposcopía)
- Médicos de atención primaria en red asistencial
- **Perfil técnico**: Familiarizado con sistemas HIS, acceso a internet, uso básico de aplicaciones web

### 3.2 Usuarios Indirectos

**Pacientes de EsSalud:**
- Pacientes crónicos con diabetes, hipertensión, dislipidemia
- Mujeres de 25-65 años elegibles para screening cervical
- **Beneficio**: Atención más rápida y estandarizada

**Administración de CENATE:**
- Jefatura médica
- Área de calidad
- **Beneficio**: Métricas de performance, auditoría de criterios

### 3.3 Stakeholders

- Dirección de Telesalud de EsSalud
- Ministerio de Salud (MINSA)
- Oficina de Transformación Digital

---

## 4. Beneficios y Valor

### 4.1 Beneficios Cuantitativos

| Métrica | Antes | Con IA | Mejora |
|---------|-------|--------|--------|
| Tiempo por estratificación de riesgo | 10 min | 15 seg | 97% más rápido |
| Tiempo validación elegibilidad | 5 min | 3 seg | 99% más rápido |
| Errores en criterios | 12% | <1% | 92% reducción |
| Costo por consulta | $8 | $0.001 | 99.9% más barato |
| Tiempo de capacitación nuevo personal | 2 semanas | 1 día | 93% reducción |

**ROI Proyectado:**
- Ahorro anual: $83,330 USD (tiempo médico)
- Costo anual IA: $375 USD (OpenAI API)
- **ROI: 22,186%** en el primer año

### 4.2 Beneficios Cualitativos

**Para médicos:**
- ✅ Reducción de carga cognitiva
- ✅ Decisiones respaldadas por procedimientos oficiales
- ✅ Trazabilidad completa (cita PM.2.X.X Anexo Y)
- ✅ Confianza en derivaciones

**Para pacientes:**
- ✅ Atención más rápida (reducción de tiempos de espera)
- ✅ Criterios consistentes (sin variabilidad inter-médico)
- ✅ Detección temprana de riesgos altos

**Para la institución:**
- ✅ Cumplimiento estricto de protocolos
- ✅ Auditoría facilitada (logs completos)
- ✅ Escalabilidad (mismo costo para 10 o 10,000 usuarios)
- ✅ Actualización instantánea (cambiar PDF, no reentrenar)

---

## 5. Casos de Uso Específicos

### 5.1 Caso de Uso 1: Estratificación de Riesgo de Paciente Crónico

**Actor**: Médico de atención primaria  
**Objetivo**: Determinar nivel de riesgo y frecuencia de monitoreo

**Flujo normal:**
1. Médico ingresa datos del paciente:
   - A1C: 8.5%
   - PA: 155/98 mmHg
   - LDL: 115 mg/dL
   - PHQ-9: 10
2. Sistema consulta criterios PM.2.1.2 Anexo 10 vía RAG
3. Sistema retorna en 250ms:
   - Diabetes: Alto riesgo → Derivar endocrinología
   - Hipertensión: Moderado
   - Dislipidemia: Elevado
   - Psicológico: Moderado
4. Sistema recomienda: Control mensual + derivación
5. Médico documenta en HCE con trazabilidad completa

**Resultado**: Decisión en 15 segundos vs 10 minutos manual

---

### 5.2 Caso de Uso 2: Validación de Elegibilidad para Telecolposcopía

**Actor**: Médico ginecólogo  
**Objetivo**: Determinar si paciente califica para telecolposcopía

**Flujo normal:**
1. Médico ingresa:
   - Edad: 45 años
   - PAP: ASC-H
   - VPH: Positivo
2. Sistema valida con lógica rápida (50ms)
3. Sistema verifica contra PM.2.2.2 vía RAG (200ms)
4. Sistema retorna:
   - ELEGIBLE ✅
   - Criterios cumplidos: Edad válida, PAP positivo, VPH+
   - Contexto del PDF: "...mujeres de 25-65 años con PAP..."
5. Sistema genera plantilla HCE pre-llenada

**Resultado**: Validación en 3 segundos vs 5 minutos manual

---

### 5.3 Caso de Uso 3: Capacitación de Personal Nuevo

**Actor**: Médico recién contratado  
**Objetivo**: Aprender criterios de CENATE

**Flujo normal:**
1. Médico accede a sistema de entrenamiento
2. Sistema presenta casos simulados
3. Médico ingresa su evaluación
4. Sistema compara con criterios oficiales PM.2.X.X
5. Sistema explica discrepancias citando documento fu