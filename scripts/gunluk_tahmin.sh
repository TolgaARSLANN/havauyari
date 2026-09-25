#!/usr/bin/env bash
# Günlük tahmin işi (Faz 7.3): yerel makinede çalışır, çünkü SİM (sim.csb.gov.tr) yurt dışı
# IP'lerine kapalı; GitHub Actions sunucuları erişemiyor.
#
# Windows Görev Zamanlayıcı her gün 08.17'de ve oturum açılışında çalıştırır
# (scripts/gorev_kur.ps1). Ayrı bir klonda çalışır: geliştirme kopyasına dokunmaz. Aynı gün
# başarılı bir çalıştırma zaten varsa hiçbir şey yapmaz (--zorla ile yine de çalışır).
# Sonuç depoya gönderilir; "Canlı izleme" iş akışı sapma ve kesintiyi bulutta denetler.
#
# Günlük: ~/.havauyari-gunluk.log
set -euo pipefail

REPO_URL="${HAVAUYARI_REPO:-git@github.com:TolgaARSLANN/havauyari.git}"
WORK="${HAVAUYARI_GUNLUK_DIR:-$HOME/.havauyari-gunluk}"
LOG="$WORK.log"
FORCE="${1:-}"

exec >>"$LOG" 2>&1
echo "=== $(date '+%F %T') ==="

if [ ! -d "$WORK/.git" ]; then
    git clone -q "$REPO_URL" "$WORK"
fi
cd "$WORK"
# İş klonu yalnızca izleme/ yazar; her seferinde uzak depoyla birebir eşitlenir
git fetch -q origin main
git reset -q --hard origin/main

today=$(TZ=Europe/Istanbul date +%F)
if [ "$FORCE" != "--zorla" ] && grep -q "\"run_at\": \"$today" izleme/durum.json 2>/dev/null; then
    echo "Bugün ($today) zaten çalıştı; çıkılıyor."
    exit 0
fi

if [ ! -x .venv/bin/python ]; then
    python3 -m venv .venv
fi
.venv/bin/pip install -q --disable-pip-version-check -e .

.venv/bin/python -m havauyari.ops.daily

git add izleme/
if git diff --cached --quiet; then
    echo "Değişiklik yok."
    exit 0
fi
git commit -q -m "Gunluk tahmin: $today"
git push -q origin HEAD:main
echo "Gönderildi: $(git log --oneline -1)"
