# HavaUyarı: tahmin API'si ve pano için tek imaj (Faz 7.1).
# docker-compose.yml aynı imajı iki servis olarak çalıştırır: api (8000) ve ui (8501).
#
#   docker build -t havauyari .
#   docker run -p 8000:8000 havauyari                          # API: /docs
#   docker run -p 8501:8501 havauyari \
#       streamlit run src/havauyari/ui/app.py --server.address 0.0.0.0   # pano
FROM python:3.11-slim

# libgomp1: LightGBM'in OpenMP kitaplığı. curl: sağlık kontrolü.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 curl \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Paket düzenlenebilir kipte kurulur: config.ROOT dosya konumundan hesaplanır ve models/,
# reports/ klasörlerini /app altında bulur (site-packages'a kurulsaydı bulamazdı).
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install -e ".[api,ui]"

COPY models ./models
COPY reports ./reports
COPY izleme ./izleme
COPY .streamlit ./.streamlit

RUN useradd --create-home --uid 1000 app && chown -R app:app /app
USER app

EXPOSE 8000 8501
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || curl -fsS http://localhost:8501/_stcore/health || exit 1

CMD ["uvicorn", "havauyari.serving.app:app", "--host", "0.0.0.0", "--port", "8000"]
