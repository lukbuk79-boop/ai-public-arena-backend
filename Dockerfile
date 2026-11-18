# ==========================================
# FÁZE 1: Builder (příprava závislostí)
# ==========================================
FROM python:3.12-slim AS builder

WORKDIR /app

# Instalace systémových závislostí potřebných POUZE pro build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Vytvoření virtuálního prostředí a instalace Python balíčků
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ==========================================
# FÁZE 2: Runtime (finální, minimální image)
# ==========================================
FROM python:3.12-slim AS runtime

WORKDIR /app

# Instalace POUZE běhových systémových knihoven (bez build-essential)
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
CMD streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true
