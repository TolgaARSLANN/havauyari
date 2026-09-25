"""Günlük tahmin işi ve canlı izleme (Faz 7.3, 7.4).

Her çalıştırmada:
1. Tüm istasyonlar için 24 saat sonrasının tahmini üretilir ve `izleme/tahmin_kaydi.csv`
   dosyasına eklenir (istasyon + tahmin zamanı başına tek satır; tekrar çalıştırma kopya
   üretmez).
2. Hedef saati geçmiş kayıtlar, servisin getirdiği son 72 saatlik ölçümlerle eşleştirilir:
   gerçekleşen değer ve mutlak hata yazılır. Bir istasyon bir gün ölçüm vermezse kaydı
   açık kalır ve sonraki çalıştırmalarda (72 saat boyunca) yeniden denenir.
3. Son `WINDOW_DAYS` günün canlı hatası geri testle karşılaştırılır. Ortalama hata geri
   testin `DRIFT_RATIO` katını aşarsa (en az `MIN_EVALUATED` değerlendirilmiş tahminle)
   "sapma" işaretlenir; GitHub Actions bu durumda bir konu (issue) açar.

Çalıştırma:
    python -m havauyari.ops.daily [--summary DOSYA]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import requests

from havauyari.config import ROOT
from havauyari.serving.service import DataUnavailable, ForecastService

MONITOR_DIR = ROOT / "izleme"
LOG_PATH = MONITOR_DIR / "tahmin_kaydi.csv"
STATUS_PATH = MONITOR_DIR / "durum.json"

WINDOW_DAYS = 14
MIN_EVALUATED = 40          # 8 istasyon × ~5 gün: daha azıyla karar verilmez
DRIFT_RATIO = 1.5           # canlı MAE > 1,5 × geri test MAE -> sapma

LOG_COLUMNS = ["issued_at", "target_time", "station", "pm25", "low", "high", "category",
               "decision_threshold", "is_alert", "risk", "actual", "abs_error"]


def forecast_rows(forecasts: dict[str, dict]) -> pd.DataFrame:
    """Servis çıktılarından kayıt satırları (gerçekleşen değer henüz boş)."""
    rows = [{
        "issued_at": pd.Timestamp(f["issued_at"]),
        "target_time": pd.Timestamp(f["target_time"]),
        "station": slug,
        "pm25": f["pm25"],
        "low": f["interval_80"]["low"],
        "high": f["interval_80"]["high"],
        "category": f["category"],
        "decision_threshold": f["alert"]["decision_threshold"],
        "is_alert": f["alert"]["is_alert"],
        "risk": f["alert"]["risk"],
        "actual": float("nan"),
        "abs_error": float("nan"),
    } for slug, f in forecasts.items()]
    return pd.DataFrame(rows, columns=LOG_COLUMNS)


def load_log(path: Path = LOG_PATH) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=LOG_COLUMNS)
    log = pd.read_csv(path, parse_dates=["issued_at", "target_time"])
    return log[LOG_COLUMNS]


def append(log: pd.DataFrame, new: pd.DataFrame) -> pd.DataFrame:
    """Yeni satırları ekler; aynı istasyon ve tahmin zamanı varsa eski satır korunur."""
    frames = [f for f in (log, new) if not f.empty]
    if not frames:
        return pd.DataFrame(columns=LOG_COLUMNS)
    out = pd.concat(frames, ignore_index=True)
    out = out.drop_duplicates(subset=["station", "issued_at"], keep="first")
    return out.sort_values(["issued_at", "station"]).reset_index(drop=True)


def fill_actuals(log: pd.DataFrame, histories: dict[str, list[dict]]) -> pd.DataFrame:
    """Hedef saati ölçülmüş, henüz değerlendirilmemiş satırlara gerçekleşen değeri yazar."""
    log = log.copy()
    for slug, history in histories.items():
        measured = {pd.Timestamp(h["time"]): h["pm25"] for h in history if h["pm25"] is not None}
        open_rows = log.index[(log["station"] == slug) & log["actual"].isna()]
        for i in open_rows:
            value = measured.get(pd.Timestamp(log.at[i, "target_time"]))
            if value is not None:
                log.at[i, "actual"] = value
                log.at[i, "abs_error"] = round(abs(log.at[i, "pm25"] - value), 2)
    return log


def monitor(log: pd.DataFrame, now: datetime, backtest_mae: float,
            window_days: int = WINDOW_DAYS, min_n: int = MIN_EVALUATED,
            ratio: float = DRIFT_RATIO) -> dict:
    """Son `window_days` günün canlı başarımı ve sapma kararı."""
    done = log.dropna(subset=["actual"])
    since = pd.Timestamp(now) - timedelta(days=window_days)
    recent = done[pd.to_datetime(done["target_time"]) > since]
    n = len(recent)
    status: dict = {"window_days": window_days, "evaluated": n, "backtest_mae": backtest_mae,
                    "drift": False, "reason": None}
    if n:
        err = recent["pm25"] - recent["actual"]
        status.update({
            "mae": round(float(err.abs().mean()), 2),
            "bias": round(float(err.mean()), 2),                # + : olduğundan yüksek tahmin
            "coverage_80": round(float(((recent["actual"] >= recent["low"])
                                        & (recent["actual"] <= recent["high"])).mean()), 3),
        })
    if n < min_n:
        status["reason"] = f"Karar için yetersiz kayıt ({n} < {min_n})"
    elif status["mae"] > ratio * backtest_mae:
        status["drift"] = True
        status["reason"] = (f"Son {window_days} günün ortalama hatası {status['mae']:.2f} µg/m³; "
                            f"geri testin ({backtest_mae:.2f}) {ratio:g} katını aşıyor")
    return status


def run(service: ForecastService, log_path: Path = LOG_PATH,
        status_path: Path = STATUS_PATH) -> dict:
    forecasts, errors = {}, {}
    slugs = list(service.a.stations)
    for i, slug in enumerate(slugs):
        try:
            forecasts[slug] = service.forecast(slug)
        except DataUnavailable as e:
            errors[slug] = str(e)
        except (requests.ConnectionError, requests.Timeout) as e:
            # Kaynağa hiç bağlanılamıyor: kalan istasyonlar için ayrı ayrı zaman aşımı beklenmez
            msg = f"Veri kaynağına bağlanılamadı ({type(e).__name__}: {_host(e)})"
            errors.update({s: msg for s in slugs[i:]})
            break
        except requests.RequestException as e:
            errors[slug] = f"Veri kaynağı hatası ({type(e).__name__})"

    log = append(load_log(log_path), forecast_rows(forecasts))
    log = fill_actuals(log, {s: f["history"] for s, f in forecasts.items()})
    now = service.clock()
    status = monitor(log, now, service.a.card.get("backtest_12m", {}).get("mae", float("nan")))
    status.update({
        "run_at": now.isoformat(),
        "stations_ok": sorted(forecasts),
        "stations_failed": errors,
        "log_rows": len(log),
        "alerts": sorted(s for s, f in forecasts.items() if f["alert"]["is_alert"]),
        "risks": sorted(s for s, f in forecasts.items()
                        if f["alert"]["risk"] and not f["alert"]["is_alert"]),
    })

    log_path.parent.mkdir(parents=True, exist_ok=True)
    out = log.copy()
    for col in ("issued_at", "target_time"):
        out[col] = pd.to_datetime(out[col]).dt.strftime("%Y-%m-%dT%H:%M:%S")
    out.to_csv(log_path, index=False)
    status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    return status


def _host(e: requests.RequestException) -> str:
    url = getattr(getattr(e, "request", None), "url", None) or ""
    return url.split("/")[2] if url.count("/") >= 2 else "bilinmeyen adres"


def summary_markdown(status: dict) -> str:
    """GitHub Actions özet sayfası için kısa Markdown."""
    ok, failed = status["stations_ok"], status["stations_failed"]
    lines = [f"## HavaUyarı günlük tahmin · {status['run_at'][:16].replace('T', ' ')}", "",
             f"- Tahmin üretilen istasyon: **{len(ok)} / {len(ok) + len(failed)}**",
             f"- Uyarı: {', '.join(status['alerts']) or 'yok'} · "
             f"Uyarı riski: {', '.join(status['risks']) or 'yok'}"]
    if status["evaluated"]:
        lines.append(f"- Son {status['window_days']} gün: {status['evaluated']} tahmin "
                     f"değerlendirildi, ortalama hata **{status['mae']:.2f} µg/m³** "
                     f"(geri test {status['backtest_mae']:.2f}), %80'lik aralık kapsaması "
                     f"%{status['coverage_80'] * 100:.0f}")
    lines.append(f"- Sapma: **{'VAR' if status['drift'] else 'yok'}**"
                 + (f" ({status['reason']})" if status["reason"] else ""))
    for slug, msg in failed.items():
        lines.append(f"- ⚠ {slug}: {msg}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Günlük tahmin ve canlı izleme")
    parser.add_argument("--summary", type=Path, help="Markdown özetin ekleneceği dosya")
    args = parser.parse_args(argv)

    from havauyari.serving.data import LiveProvider
    from havauyari.serving.service import load_artifacts

    status = run(ForecastService(load_artifacts(), LiveProvider()))
    text = summary_markdown(status)
    print(text)
    if args.summary:
        with args.summary.open("a", encoding="utf-8") as fh:
            fh.write(text)
    # Hiçbir istasyonda tahmin üretilemediyse iş başarısız sayılır (veri kaynağı sorunu)
    return 0 if status["stations_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
