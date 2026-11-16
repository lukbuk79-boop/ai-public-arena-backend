FROM python:3.12-slim

# 1. Instalace systémových knihoven pro WeasyPrint (Pango, Cairo atd.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    libharfbuzz0b \
    libcairo2 \
    shared-mime-info \
    fonts-liberation \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# 2. Nastavení pracovního adresáře
WORKDIR /app

# 3. Instalace Python závislostí
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Zkopírování zbytku aplikace
COPY . .

# 5. Spuštění Streamlitu na portu 8080 (který Cloud Run očekává)
EXPOSE 8080
CMD streamlit run app.py --server.port=8080 --server.address=0.0.0.0
