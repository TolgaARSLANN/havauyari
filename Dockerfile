# HavaUyarı API imajı. Python sürümü pyproject.toml'daki requires-python (>=3.11) ve CI ile aynı.
#   docker build -t havauyari-api .
# Model dosyası (models/lgbm_station_h24.txt) git dışı olduğu için imaja girmez; compose
# models/ klasörünü salt okunur bağlar (bkz. docker-compose.yml).

FROM python:3.11-slim AS build
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /src
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip wheel --wheel-dir /wheels ".[api,db]"

FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
# LightGBM çalışma anında OpenMP (libgomp) ister
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*
# Wheel'ler katman olarak kopyalanmaz, yalnızca kurulum sırasında bağlanır (imaj ~0,5 GB küçük)
RUN --mount=type=bind,from=build,source=/wheels,target=/wheels     pip install --no-index --find-links /wheels "havauyari[api,db]"

RUN useradd --create-home --uid 10001 app
WORKDIR /app
# Paket site-packages'ta; depo kökü (models/ klasörü) HAVAUYARI_ROOT ile gösterilir
COPY --chown=app:app models/*.json ./models/
COPY --chown=app:app docker/entrypoint.sh ./entrypoint.sh
USER app

ENV HAVAUYARI_ROOT=/app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4).status != 200)"

ENTRYPOINT ["./entrypoint.sh"]
CMD ["uvicorn", "havauyari.serving.app:app", "--host", "0.0.0.0", "--port", "8000"]
