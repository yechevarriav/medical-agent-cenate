FROM python:3.12-slim

WORKDIR /app

# Copiar requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY src/ ./src/
COPY data/ ./data/

# Exponer puerto
EXPOSE 8000

# Comando de inicio
CMD ["python", "src/main.py"]
