"""Canlı izleme bekçisi (bulutta çalışır; SİM ya da ek paket gerektirmez).

Günlük tahmin işi SİM'e yalnızca Türkiye'deki bir makineden erişebildiği için yerelde
çalışır ve sonucu `izleme/` klasörüne işler (scripts/gunluk_tahmin.sh). GitHub Actions bu
modülle iki durumu denetler:

- **kesinti:** `izleme/durum.json` `STALE_HOURS` saatten eski (bilgisayar kapalı kalmış ya da
  iş hata vermiş olabilir),
- **sapma:** günlük iş canlı hatanın geri testin çok üstünde olduğunu işaretlemiş.

Her bulgu için etiketli bir GitHub konusu açılır; aynı etiketle açık konu varsa ona yorum
eklenir (her gün yeni konu açılmaz).

Çalıştırma (depo kökünden):
    PYTHONPATH=src python -m havauyari.ops.check            # yalnızca raporla
    PYTHONPATH=src python -m havauyari.ops.check --github   # konu aç / yorum ekle (gh CLI)
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

STATUS_PATH = Path(__file__).resolve().parents[3] / "izleme" / "durum.json"
TIMEZONE = "Europe/Istanbul"
STALE_HOURS = 30

LABELS = {"kesinti": ("B45309", "Günlük tahmin işi zamanında çalışmadı"),
          "sapma": ("C4401A", "Canlı hata geri testin çok üstünde")}


def findings(status: dict | None, now: datetime, stale_hours: float = STALE_HOURS) -> list[dict]:
    """Durum dosyasından açılması gereken konular: [{label, title, body}]."""
    if status is None:
        return [{"label": "kesinti", "title": "Günlük tahmin kaydı bulunamadı",
                 "body": "izleme/durum.json yok; günlük tahmin işi hiç çalışmamış olabilir."}]
    out = []
    run_at = datetime.fromisoformat(status["run_at"])
    age = (now - run_at).total_seconds() / 3600
    if age > stale_hours:
        out.append({
            "label": "kesinti", "title": "Günlük tahmin işi çalışmadı",
            "body": (f"Son çalıştırma {run_at:%d.%m.%Y %H.%M} ({age:.0f} saat önce). "
                     "Bilgisayar kapalı kalmış ya da iş hata vermiş olabilir; günlük: "
                     "~/.havauyari-gunluk.log")})
    if status.get("drift"):
        out.append({"label": "sapma", "title": "Canlı tahmin hatası arttı (sapma)",
                    "body": f"{status.get('reason')}. Ayrıntılar: izleme/durum.json"})
    return out


def _gh(*args: str) -> str:
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout


def report_to_github(items: list[dict], stamp: str) -> None:
    for f in items:
        color, desc = LABELS[f["label"]]
        _gh("label", "create", f["label"], "--color", color, "--description", desc, "--force")
        existing = _gh("issue", "list", "--label", f["label"], "--state", "open",
                       "--json", "number", "-q", ".[0].number").strip()
        if existing:
            _gh("issue", "comment", existing, "--body", f"{stamp}: {f['body']}")
        else:
            _gh("issue", "create", "--title", f["title"], "--label", f["label"],
                "--body", f["body"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Canlı izleme bekçisi")
    parser.add_argument("--github", action="store_true", help="GitHub konusu aç / yorum ekle")
    args = parser.parse_args(argv)

    status = (json.loads(STATUS_PATH.read_text(encoding="utf-8"))
              if STATUS_PATH.exists() else None)
    now = datetime.now(ZoneInfo(TIMEZONE)).replace(tzinfo=None)
    items = findings(status, now)
    for f in items:
        print(f"[{f['label']}] {f['title']}: {f['body']}")
    if not items:
        print("Sorun yok: kayıt güncel, sapma yok.")
    if args.github and items:
        report_to_github(items, now.strftime("%d.%m.%Y %H.%M"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
