# ==========================================
# FÁZE 1: Builder (těžké nástroje pro instalaci)
# ==========================================
FROM python:3.12-slim-bookworm AS builder

WORKDIR /app

# Instalace buildovacích nástrojů POUZE sem (do finálního image se nedostanou)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Vytvoření virtuálního prostředí
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

# Instalace POUZE nutných běhových knihoven (žádné gcc ani make)
RUN apt-get update && apt-get install -y --no-install-recommends \
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

# Spuštění s pevným portem 8080, který Cloud Run spolehlivě očekává
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0", "--server.headless=true"]
