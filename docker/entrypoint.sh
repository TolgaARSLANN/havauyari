#!/bin/sh
# Konteyner açılışı: DATABASE_URL tanımlıysa önce migration'lar, sonra verilen komut (uvicorn).
set -e

if [ -n "$DATABASE_URL" ]; then
    python -m havauyari.storage.migrate
else
    echo "DATABASE_URL tanımlı değil: API veritabanı olmadan çalışacak."
fi

exec "$@"
