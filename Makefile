.PHONY: install data quality process train baselines test lint \
        sim-survey sim-data forecasts stations train-station

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
	pip install -e ".[dev,ml,serve]"

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
