# AWS Lambda Deployment Guide - CENATE Medical Assistant

## Índice

1. [Overview](#1-overview)
2. [Preparación](#2-preparación)
3. [Deploy risk-lambda](#3-deploy-risk-lambda)
4. [Deploy validate-lambda](#4-deploy-validate-lambda)
5. [Integración con FastAPI](#5-integración-con-fastapi)
6. [Testing](#6-testing)
7. [Monitoring](#7-monitoring)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. Overview

### 1.1 ¿Qué funciones Lambda tenemos?

| Función             | Propósito                 | Memory | Timeout | Trigger        |
| ------------------- | ------------------------- | ------ | ------- | -------------- |
| **risk-lambda**     | Estratificación de riesgo | 512MB  | 30s     | FastAPI invoke |
| **validate-lambda** | Validación elegibilidad   | 256MB  | 10s     | FastAPI invoke |

### 1.2 ¿Por qué estas 2 y no las 4?

**Migradas a Lambda:**

- ✅ **risk**: Alto uso, cálculos complejos, requiere escalado
- ✅ **validate**: Alto uso, validación crítica, requiere escalado

**Permanecen en Railway:**

- ❌ **template**: Bajo uso, operación simple (string formatting)
- ❌ **search**: Requiere FAISS local, complejo migrar vector store

### 1.3 Arquitectura de invocación

```
Cliente
   ↓
FastAPI (Railway)
   ├──→ boto3.invoke() → risk-lambda (AWS)
   ├──→ boto3.invoke() → validate-lambda (AWS)
   ├──→ template_tool (local)
   └──→ search_tool (local)
```

---

## 2. Preparación

### 2.1 Prerrequisitos

- AWS Account
- AWS CLI instalado y configurado
- Python 3.12
- Credenciales AWS con permisos Lambda

```bash
# Instalar AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configurar credenciales
aws configure
# AWS Access Key ID: AKIA...
# AWS Secret Access Key: ...
# Default region: us-east-1
# Default output format: json

# Verificar
aws sts get-caller-identity
```

### 2.2 Crear IAM Role para Lambda

```bash
# Crear trust policy
cat > lambda-trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "Service": "lambda.amazonaws.com"
    },
    "Action": "sts:AssumeRole"
  }]
}
EOF

# Crear role
aws iam create-role \
  --role-name cenate-lambda-execution-role \
  --assume-role-policy-document file://lambda-trust-policy.json

# Agregar políticas
aws iam attach-role-policy \
  --role-name cenate-lambda-execution-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# Obtener ARN del role (guardarlo)
aws iam get-role --role-name cenate-lambda-execution-role --query 'Role.Arn'
# Output: arn:aws:iam::123456789012:role/cenate-lambda-execution-role
```

### 2.3 Estructura del proyecto

```
medical-agent-cenate/
├── lambda/
│   ├── risk_lambda/
│   │   ├── lambda_function.py
│   │   ├── requirements.txt
│   │   └── package/  (generado)
│   └── validate_lambda/
│       ├── lambda_function.py
│       ├── requirements.txt
│       └── package/  (generado)
└── src/
    └── tools/
        ├── risk_tool.py
        └── validate_tool.py
```

---

## 3. Deploy risk-lambda

### 3.1 Crear archivos Lambda

**`lambda/risk_lambda/lambda_function.py`:**

```python
import json
import sys
import os

# Agregar layer path
sys.path.insert(0, '/opt/python')

# Import tool
from risk_tool import RiskStratificationTool

def handler(event, context):
    """
    Lambda handler para estratificación de riesgo

    Args:
        event (dict): {
            "a1c": float (optional),
            "pa_sistolica": int (optional),
            "pa_diastolica": int (optional),
            "ldl": int (optional),
            "phq9": int (optional),
            "gad7": int (optional)
        }
        context: Lambda context object

    Returns:
        dict: {
            "statusCode": 200,
            "body": json string con resultado
        }
    """
    print(f"Received event: {json.dumps(event)}")

    try:
        # Inicializar tool
        tool = RiskStratificationTool()

        # Estratificar
        result = tool.estratificar(
            a1c=event.get('a1c'),
            pa_sistolica=event.get('pa_sistolica'),
            pa_diastolica=event.get('pa_diastolica'),
            ldl=event.get('ldl'),
            phq9=event.get('phq9'),
            gad7=event.get('gad7')
        )

        print(f"Result: {json.dumps(result)}")

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'result': result})
        }

    except ValueError as e:
        print(f"Validation error: {str(e)}")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': f'Validation error: {str(e)}'})
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
```

**`lambda/risk_lambda/requirements.txt`:**

```txt
pydantic==2.7.4
```

### 3.2 Empaquetar función

```bash
cd lambda/risk_lambda

# Crear directorio package
mkdir -p package

# Instalar dependencias
pip install -r requirements.txt -t package/

# Copiar código de la tool
cp ../../src/tools/risk_tool.py package/

# Copiar lambda handler
cp lambda_function.py package/

# Crear ZIP
cd package
zip -r ../risk-lambda.zip .
cd ..

# Verificar tamaño
ls -lh risk-lambda.zip
# Debería ser ~5MB
```

### 3.3 Crear función Lambda

```bash
aws lambda create-function \
  --function-name risk-lambda \
  --runtime python3.12 \
  --role arn:aws:iam::123456789012:role/cenate-lambda-execution-role \
  --handler lambda_function.handler \
  --zip-file fileb://risk-lambda.zip \
  --timeout 30 \
  --memory-size 512 \
  --environment Variables={ENVIRONMENT=production} \
  --description "Estratificación de riesgo para pacientes crónicos - CENATE"

# Output: ARN de la función
# arn:aws:lambda:us-east-1:123456789012:function:risk-lambda
```

### 3.4 Test inicial

```bash
# Crear payload de test
cat > test-risk-event.json << EOF
{
  "a1c": 8.5,
  "pa_sistolica": 155,
  "pa_diastolica": 98,
  "ldl": 115,
  "phq9": 10,
  "gad7": 21
}
EOF

# Invocar Lambda
aws lambda invoke \
  --function-name risk-lambda \
  --payload file://test-risk-event.json \
  --cli-binary-format raw-in-base64-out \
  response.json

# Ver respuesta
cat response.json | jq
# {
#   "statusCode": 200,
#   "body": "{\"result\": {\"evaluacion\": {...}, \"recomendaciones\": [...]}}"
# }
```

---

## 4. Deploy validate-lambda

### 4.1 Crear archivos Lambda

**`lambda/validate_lambda/lambda_function.py`:**

```python
import json
import sys

sys.path.insert(0, '/opt/python')

from validate_tool import ValidateTelecolposcopiaTool

def handler(event, context):
    """
    Lambda handler para validación de elegibilidad

    Args:
        event (dict): {
            "edad": int (required),
            "pap_resultado": str (optional),
            "vph_positivo": bool (optional)
        }
    """
    print(f"Received event: {json.dumps(event)}")

    try:
        tool = ValidateTelecolposcopiaTool()

        result = tool.validar(
            edad=event.get('edad'),
            pap_resultado=event.get('pap_resultado'),
            vph_positivo=event.get('vph_positivo')
        )

        print(f"Result: {json.dumps(result)}")

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'result': result})
        }

    except ValueError as e:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': f'Validation error: {str(e)}'})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
```

**`lambda/validate_lambda/requirements.txt`:**

```txt
pydantic==2.7.4
```

### 4.2 Empaquetar y deployar

```bash
cd lambda/validate_lambda

mkdir -p package
pip install -r requirements.txt -t package/
cp ../../src/tools/validate_tool.py package/
cp lambda_function.py package/

cd package
zip -r ../validate-lambda.zip .
cd ..

aws lambda create-function \
  --function-name validate-lambda \
  --runtime python3.12 \
  --role arn:aws:iam::123456789012:role/cenate-lambda-execution-role \
  --handler lambda_function.handler \
  --zip-file fileb://validate-lambda.zip \
  --timeout 10 \
  --memory-size 256 \
  --description "Validación de elegibilidad para telecolposcopía - CENATE"
```

### 4.3 Test

```bash
cat > test-validate-event.json << EOF
{
  "edad": 45,
  "pap_resultado": "ASC-H",
  "vph_positivo": true
}
EOF

aws lambda invoke \
  --function-name validate-lambda \
  --payload file://test-validate-event.json \
  --cli-binary-format raw-in-base64-out \
  response.json

cat response.json | jq
```

---

## 5. Integración con FastAPI

### 5.1 Actualizar main.py

```python
# src/main.py
import boto3
import json
import os
from fastapi import FastAPI, HTTPException
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="CENATE Medical Tools API")

# Cliente Lambda
lambda_client = boto3.client(
    'lambda',
    region_name=os.getenv('AWS_REGION', 'us-east-1')
)

# ARNs de Lambda
LAMBDA_RISK_ARN = os.getenv('LAMBDA_RISK_ARN')
LAMBDA_VALIDATE_ARN = os.getenv('LAMBDA_VALIDATE_ARN')

@app.post("/risk")
async def estratificar_riesgo(req: RiskRequest):
    """Estratifica riesgo invocando Lambda"""
    logger.info(f"Invoking risk-lambda with: {req.dict()}")

    try:
        response = lambda_client.invoke(
            FunctionName=LAMBDA_RISK_ARN,
            InvocationType='RequestResponse',
            Payload=json.dumps(req.dict())
        )

        payload = json.loads(response['Payload'].read())
        logger.info(f"Lambda response status: {response['StatusCode']}")

        if response['StatusCode'] == 200:
            body = json.loads(payload['body'])
            return body
        else:
            logger.error(f"Lambda error: {payload}")
            raise HTTPException(status_code=500, detail="Lambda invocation failed")

    except Exception as e:
        logger.error(f"Error invoking risk-lambda: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/validate")
async def validar_telecolposcopia(req: ValidateRequest):
    """Valida elegibilidad invocando Lambda"""
    logger.info(f"Invoking validate-lambda with: {req.dict()}")

    try:
        response = lambda_client.invoke(
            FunctionName=LAMBDA_VALIDATE_ARN,
            InvocationType='RequestResponse',
            Payload=json.dumps(req.dict())
        )

        payload = json.loads(response['Payload'].read())

        if response['StatusCode'] == 200:
            body = json.loads(payload['body'])
            return body
        else:
            raise HTTPException(status_code=500, detail="Lambda invocation failed")

    except Exception as e:
        logger.error(f"Error invoking validate-lambda: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### 5.2 Configurar variables de entorno en Railway

En Railway → Variables:

```bash
AWS_REGION=us-east-1
LAMBDA_RISK_ARN=arn:aws:lambda:us-east-1:123456789012:function:risk-lambda
LAMBDA_VALIDATE_ARN=arn:aws:lambda:us-east-1:123456789012:function:validate-lambda

# Credenciales AWS (para boto3)
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
```

### 5.3 Agregar boto3 a requirements.txt

```txt
# ... dependencias existentes ...
boto3==1.34.0
```

---

## 6. Testing

### 6.1 Test local de invocación Lambda

```python
# test_lambda_invoke.py
import boto3
import json

lambda_client = boto3.client('lambda', region_name='us-east-1')

# Test risk-lambda
def test_risk_lambda():
    response = lambda_client.invoke(
        FunctionName='risk-lambda',
        InvocationType='RequestResponse',
        Payload=json.dumps({
            "a1c": 8.5,
            "pa_sistolica": 155,
            "pa_diastolica": 98
        })
    )

    payload = json.loads(response['Payload'].read())
    print(json.dumps(payload, indent=2))

    assert response['StatusCode'] == 200
    assert 'result' in json.loads(payload['body'])

# Test validate-lambda
def test_validate_lambda():
    response = lambda_client.invoke(
        FunctionName='validate-lambda',
        InvocationType='RequestResponse',
        Payload=json.dumps({
            "edad": 45,
            "pap_resultado": "ASC-H",
            "vph_positivo": True
        })
    )

    payload = json.loads(response['Payload'].read())
    print(json.dumps(payload, indent=2))

    assert response['StatusCode'] == 200

if __name__ == "__main__":
    test_risk_lambda()
    test_validate_lambda()
    print("✅ All tests passed")
```

### 6.2 Test end-to-end

```bash
# Desde Railway URL
curl -X POST https://medical-agent-cenate-production.up.railway.app/risk \
  -H "Content-Type: application/json" \
  -d '{"a1c": 8.5, "pa_sistolica": 155, "pa_diastolica": 98}'

# Debe retornar resultado de Lambda
```

---

## 7. Monitoring

### 7.1 CloudWatch Logs

```bash
# Ver logs de risk-lambda
aws logs tail /aws/lambda/risk-lambda --follow

# Ver logs de validate-lambda
aws logs tail /aws/lambda/validate-lambda --follow

# Filtrar errores
aws logs filter-log-events \
  --log-group-name /aws/lambda/risk-lambda \
  --filter-pattern "ERROR"
```

### 7.2 Métricas CloudWatch

```bash
# Ver invocaciones últimas 24h
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=risk-lambda \
  --start-time $(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Sum

# Ver errores
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=risk-lambda \
  --start-time $(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Sum
```

---

## 8. Troubleshooting

### 8.1 Error: "Task timed out after 3.00 seconds"

**Causa:** Timeout muy corto

**Solución:**

```bash
aws lambda update-function-configuration \
  --function-name risk-lambda \
  --timeout 30
```

### 8.2 Error: "Unable to import module 'lambda_function'"

**Causa:** Estructura del ZIP incorrecta

**Solución:**

```bash
# El ZIP debe tener lambda_function.py en la raíz
cd package
zip -r ../function.zip .  # ✅ Correcto
cd ..
zip -r function.zip package/  # ❌ Incorrecto
```

### 8.3 Cold start muy lento (>2 segundos)

**Solución 1: Provisioned Concurrency**

```bash
aws lambda put-provisioned-concurrency-config \
  --function-name risk-lambda \
  --provisioned-concurrent-executions 1
```

**Solución 2: CloudWatch Events (keep-warm)**

```bash
# Crear regla que invoca Lambda cada 10 min
aws events put-rule \
  --name keep-risk-lambda-warm \
  --schedule-expression "rate(10 minutes)"

aws events put-targets \
  --rule keep-risk-lambda-warm \
  --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:123:function:risk-lambda"
```

### 8.4 Error: "Module not found: pydantic"

**Causa:** Dependencias no incluidas en el ZIP

**Solución:**

```bash
# Reinstalar en package/
cd lambda/risk_lambda
rm -rf package/
mkdir package
pip install -r requirements.txt -t package/
# Luego recrear ZIP
```

---

## 9. Actualización de Funciones

### 9.1 Actualizar código

```bash
# Modificar lambda_function.py o tool
# Recrear ZIP
cd lambda/risk_lambda/package
zip -r ../risk-lambda.zip .
cd ..

# Actualizar función
aws lambda update-function-code \
  --function-name risk-lambda \
  --zip-file fileb://risk-lambda.zip

# Esperar a que termine
aws lambda wait function-updated \
  --function-name risk-lambda

# Test
aws lambda invoke \
  --function-name risk-lambda \
  --payload file://test-risk-event.json \
  response.json
```

### 9.2 Actualizar configuración

```bash
# Cambiar timeout
aws lambda update-function-configuration \
  --function-name risk-lambda \
  --timeout 45

# Cambiar memory
aws lambda update-function-configuration \
  --function-name risk-lambda \
  --memory-size 1024

# Cambiar variables de entorno
aws lambda update-function-configuration \
  --function-name risk-lambda \
  --environment Variables={ENVIRONMENT=production,LOG_LEVEL=DEBUG}
```

---

## 10. Costos y Optimización

### 10.1 Calculadora de costos

**Escenario: 100 consultas/día (3,000/mes)**

```
risk-lambda (1,500 invocations):
- Duration promedio: 200ms
- Memory: 512MB
- Compute: 1,500 × 0.2s × (512/1024) GB × $0.0000166667/GB-s = $0.0025
- Requests: 1,500 × $0.0000002 = $0.0003

validate-lambda (1,500 invocations):
- Duration promedio: 100ms
- Memory: 256MB
- Compute: 1,500 × 0.1s × (256/1024) GB × $0.0000166667/GB-s = $0.0006
- Requests: 1,500 × $0.0000002 = $0.0003

Total: $0.0037/mes ≈ $0.04/año

Free Tier (permanente):
- 1M requests/mes
- 400,000 GB-segundos/mes
→ Proyecto cubre dentro de Free Tier
```

### 10.2 Optimizaciones

**Reducir cold start:**

- Minimizar dependencias
- Usar Layers para librerías comunes
- Provisioned Concurrency para funciones críticas

**Reducir costo:**

- Ajustar memory al mínimo necesario
- Optimizar código para reducir duration
- Usar batch processing para múltiples requests

---

**Autor**: Yvonne Echevarria
**Última actualización**: Diciembre 2025
**Versión**: 1.0
