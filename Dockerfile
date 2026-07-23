# Imagem para deploy híbrido (Streamlit Community Cloud / GCP Cloud Run).
FROM python:3.12-slim

WORKDIR /app

# Dependências de sistema: pdftotext (leitura de PDF FWD) e LuaLaTeX + tex-gyre
# (geração de relatório PDF com fontes OpenType/CFF, sem Type 1).
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       poppler-utils \
       texlive-luatex texlive-latex-recommended \
       texlive-fonts-recommended texlive-fonts-extra texlive-science \
    && rm -rf /var/lib/apt/lists/*

# Dependências primeiro (cache de camadas).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código.
COPY . .

ENV PYTHONPATH=/app/src:/app/app
EXPOSE 8501

# Cloud Run injeta $PORT; localmente usa 8501.
CMD streamlit run app/streamlit_app.py \
    --server.headless true \
    --server.address 0.0.0.0 \
    --server.port ${PORT:-8501}
