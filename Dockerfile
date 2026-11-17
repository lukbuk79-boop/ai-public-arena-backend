FROM python:3.10-slim

# Pracovní adresář
WORKDIR /app

# Instalace systémových závislostí VČETNĚ knihoven pro WeasyPrint (Cairo, Pango, atd.)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Kopírování requirements a instalace Python závislostí
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopírování zbytku aplikace
COPY . .

# Expozice portu pro Streamlit (Cloud Run vyžaduje port 8080)
EXPOSE 8080

# Spuštění Streamlitu
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0", "--server.headless=true"]
