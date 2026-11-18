# ==========================================
# FÁZE 1: Builder (těžké nástroje pro instalaci)
# ==========================================
FROM python:3.12-slim-bookworm AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ==========================================
# FÁZE 2: Runtime (lehký čistý image pro Cloud Run)
# ==========================================
FROM python:3.12-slim-bookworm AS runtime

WORKDIR /app

# Instalace běhových knihoven VČETNĚ Panga pro PDF/Cairo/WeasyPrint
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

# Zkopírování hotového virtuálního prostředí z builderu
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Zkopírování zbytku aplikace
COPY . .

EXPOSE 8080

# Spuštění s dynamickým portem Cloud Runu přes shell
CMD sh -c "streamlit run app.py --server.port=${PORT:-8080} --server.address=0.0.0.0 --server.headless=true"
