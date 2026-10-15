#!/usr/bin/env bash
# Saatlik toplama işinin sarmalayıcısı: Windows Görev Zamanlayıcı bunu WSL'de çağırır
# (bkz. scripts/windows/register_collect_task.ps1). Elle de çalıştırılabilir:
#     scripts/collect.sh            -> çıktı logs/collect.log dosyasına eklenir
#
# 1. .env varsa okunur (DATABASE_URL, POSTGRES_* değerleri).
# 2. Postgres konteyneri başlatılır (Docker Desktop kapalıysa iş burada durur ve loga yazar).
# 3. python -m havauyari.jobs.collect çalışır; çıkış kodu aynen döner.
set -u
cd "$(dirname "$0")/.."

mkdir -p logs
LOG=logs/collect.log
# Log 5 MB'ı geçerse bir önceki dosya olarak saklanır (en fazla ~10 MB yer kaplar)
if [ -f "$LOG" ] && [ "$(stat -c %s "$LOG")" -gt 5242880 ]; then
    mv "$LOG" "$LOG.1"
fi
exec >>"$LOG" 2>&1

echo "=== $(date '+%Y-%m-%d %H:%M:%S') ==="
set -a
[ -f .env ] && . ./.env
set +a
: "${DATABASE_URL:=postgresql://${POSTGRES_USER:-havauyari}:${POSTGRES_PASSWORD:-havauyari}@localhost:${POSTGRES_PORT:-5432}/${POSTGRES_DB:-havauyari}}"
export DATABASE_URL

if ! docker compose up -d --wait postgres >/dev/null 2>&1; then
    echo "HATA: Postgres başlatılamadı. Docker Desktop açık mı, WSL entegrasyonu etkin mi?"
    exit 1
fi

.venv/bin/python -m havauyari.jobs.collect
status=$?
echo "çıkış kodu: $status"
exit $status
