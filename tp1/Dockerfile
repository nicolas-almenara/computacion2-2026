# Imagen base liviana con Python 3.11.
FROM python:3.11-slim

# Directorio de trabajo dentro del contenedor.
WORKDIR /app

# Instalar dependencias primero (mejor uso del cache de capas).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código.
COPY . .

# El monitor lee /proc del propio contenedor. Se ejecuta la TUI como
# proceso principal; los analizadores se levantan desde main.py.
CMD ["python", "src/main.py"]
