FROM python:3.10-slim

# Pracovní adresář
WORKDIR /app

# Instalace systémových závislostí (pokud jsou potřeba, např. pro PDF nebo git)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Kopírování requirements a instalace závislostí
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopírování zbytku aplikace
COPY . .

# Expozice portu, který Streamlit očekává (Cloud Run vyžaduje port 8080)
EXPOSE 8080

# Spuštění Streamlitu s vazbou na port 8080 a vypnutím sběru metrik
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0", "--server.headless=true"]