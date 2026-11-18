FROM python:3.12-slim-bookworm

WORKDIR /app

# Instalace nezbytných systémových knihoven pro grafiku, PDF a fonty v jedné vrstvě
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf-2.0-0 \
    libglib2.0-0 \
    libffi8 \
    shared-mime-info \
    fonts-liberation \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Instalace Python závislostí bez ukládání mezipaměti (zůstane bezpečně pod 500 MB)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Zkopírování zdrojových kódů aplikace
COPY . .

EXPOSE 8080

# Čisté spuštění Streamlitu, port si Cloud Run řádně obslouží sám
CMD streamlit run app.py --server.address=0.0.0.0 --server.headless=true
