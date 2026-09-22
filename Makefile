.PHONY: install data quality process train baselines test lint

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
