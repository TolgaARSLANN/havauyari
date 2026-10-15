.PHONY: install data quality process train baselines test lint \
        sim-survey sim-data forecasts stations train-station final api ui \
        db-up db-down migrate test-db compose-up compose-down collect

# Yerel PostgreSQL (docker compose'daki postgres servisi). Değerler .env.example ile aynı.
DATABASE_URL ?= postgresql://havauyari:havauyari@localhost:5432/havauyari
TEST_DATABASE_URL ?= postgresql://havauyari:havauyari@localhost:5432/havauyari_test

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
	pip install -e ".[dev,api,ui,db]"

# --- veritabanı ve Docker ---------------------------------------------------------------
db-up:            ## yalnızca postgres; test veritabanını (havauyari_test) da oluşturur
	docker compose up -d --wait postgres
	docker compose exec -T postgres sh -c 'createdb -U "$$POSTGRES_USER" havauyari_test 2>/dev/null || true'

db-down:
	docker compose stop postgres

migrate:          ## şemayı en son migration'a taşır
	DATABASE_URL=$(DATABASE_URL) python -m havauyari.storage.migrate

test-db: db-up    ## DB entegrasyon testleri dahil tüm testler
	TEST_DATABASE_URL=$(TEST_DATABASE_URL) pytest -q

compose-up:       ## api + postgres (migration'lar api açılışında çalışır)
	docker compose up -d --build --wait

compose-down:
	docker compose down

collect: db-up    ## tüm istasyonların bu saatki tahmini + ölçümleri DB'ye (zamanlanmış iş)
	DATABASE_URL=$(DATABASE_URL) python -m havauyari.jobs.collect

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
