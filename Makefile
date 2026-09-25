.PHONY: install data quality process train baselines test lint \
        sim-survey sim-data forecasts stations train-station final api ui \
        daily docker up

# Günlük tahmin ve canlı izleme (GitHub Actions her gün çalıştırır) -> izleme/
daily:
	python -m havauyari.ops.daily

# API + pano konteynerde: http://localhost:8000/docs, http://localhost:8501
docker:
	docker build -t havauyari .

up:
	docker compose up --build

final:
	python -m havauyari.models.final

api:
	uvicorn havauyari.serving.app:app --reload

ui:
	streamlit run src/havauyari/ui/app.py

sim-survey:
	python -m havauyari.data.fetch_sim survey

sim-data:
	python -m havauyari.data.fetch_sim fetch

forecasts:
	python -m havauyari.data.fetch_forecasts

stations:
	python -m havauyari.data.stations

train-station:
	python -m havauyari.models.train_station

install:
	pip install -e ".[dev,api,ui]"

data:
	python -m havauyari.data.fetch_openmeteo

quality:
	python -m havauyari.data.quality

process:
	python -m havauyari.data.clean

train:
	python -m havauyari.models.train --horizon 24

baselines:
	python -m havauyari.models.train --horizon 24 --baselines-only

test:
	pytest -q

lint:
	ruff check src tests
