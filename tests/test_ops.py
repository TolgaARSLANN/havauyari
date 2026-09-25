"""Günlük tahmin işi ve canlı izleme testleri (ağ yok: sahte sağlayıcı + küçük model)."""

import json
from datetime import timedelta

import numpy as np
import pandas as pd
from conftest import NOW, FakeProvider

from havauyari.ops.daily import (
    LOG_COLUMNS,
    append,
    fill_actuals,
    load_log,
    monitor,
    run,
    summary_markdown,
)
from havauyari.serving.service import ForecastService, load_artifacts


def _service(models_dir, clock, provider=None):
    return ForecastService(load_artifacts(models_dir), provider or FakeProvider(),
                           clock=lambda: clock["now"])


def test_two_days_log_then_evaluate(models_dir, tmp_path):
    log_path, status_path = tmp_path / "kayit.csv", tmp_path / "durum.json"
    clock = {"now": NOW}
    s1 = run(_service(models_dir, clock), log_path, status_path)
    assert s1["stations_ok"] == ["s1", "s2"] and s1["evaluated"] == 0
    day1 = load_log(log_path)
    assert list(day1.columns) == LOG_COLUMNS and len(day1) == 2
    assert day1["actual"].isna().all()                        # hedef saat henüz gelmedi

    run(_service(models_dir, clock), log_path, status_path)   # aynı saat: kopya yok
    assert len(load_log(log_path)) == 2

    clock["now"] = NOW + timedelta(hours=24)                  # ertesi gün
    s2 = run(_service(models_dir, clock), log_path, status_path)
    log = load_log(log_path)
    assert len(log) == 4
    first = log[log["issued_at"] == pd.Timestamp(NOW)]
    assert first["actual"].notna().all()                      # dünkü tahminler değerlendirildi
    assert np.allclose(first["abs_error"], (first["pm25"] - first["actual"]).abs(), atol=0.01)
    assert s2["evaluated"] == 2 and s2["mae"] >= 0
    assert json.loads(status_path.read_text(encoding="utf-8"))["log_rows"] == 4


def test_failed_station_is_reported_not_logged(models_dir, tmp_path):
    clock = {"now": NOW}
    status = run(_service(models_dir, clock, FakeProvider(gap_for={"s1"})),
                 tmp_path / "k.csv", tmp_path / "d.json")
    assert status["stations_ok"] == ["s2"] and "s1" in status["stations_failed"]
    assert set(load_log(tmp_path / "k.csv")["station"]) == {"s2"}
    assert "⚠ s1" in summary_markdown(status)


def _log(errors, days_ago=1):
    t = pd.Timestamp(NOW) - timedelta(days=days_ago)
    rows = [{"issued_at": t - timedelta(hours=24 + i), "target_time": t - timedelta(hours=i),
             "station": "s1", "pm25": 20.0 + e, "low": 10.0, "high": 30.0, "category": "Orta",
             "decision_threshold": 28.5, "is_alert": False, "risk": False, "actual": 20.0,
             "abs_error": abs(e)} for i, e in enumerate(errors)]
    return pd.DataFrame(rows, columns=LOG_COLUMNS)


def test_monitor_drift_needs_enough_evidence():
    small = monitor(_log([30.0] * 10), NOW, 6.78, min_n=40)
    assert not small["drift"] and "yetersiz" in small["reason"]
    good = monitor(_log([5.0, -5.0] * 30), NOW, 6.78, min_n=40)
    assert not good["drift"] and good["mae"] == 5.0 and good["bias"] == 0.0
    bad = monitor(_log([15.0] * 60), NOW, 6.78, min_n=40)
    assert bad["drift"] and "1.5 katını" in bad["reason"].replace(",", ".")
    assert bad["coverage_80"] == 1.0                          # 35 > 30 değil: 20 aralıkta
    old = monitor(_log([15.0] * 60, days_ago=30), NOW, 6.78, min_n=40)
    assert old["evaluated"] == 0 and not old["drift"]         # pencere dışı kayıtlar sayılmaz


def test_live_monitor_panel_states():
    from havauyari.ui.components import live_monitor_html

    assert "henüz başlamadı" in live_monitor_html(None, None)
    pending = _log([1.0, 2.0])
    pending.loc[:, ["actual", "abs_error"]] = np.nan
    assert "2 tahmin kaydedildi" in live_monitor_html(pending, {"evaluated": 0})
    status = monitor(_log([5.0, -5.0] * 30), NOW, 6.78, min_n=40)
    panel = live_monitor_html(_log([5.0, -5.0] * 30), status)
    assert "Canlı ortalama hata" in panel and "5,00" in panel and "Yok" in panel


def test_fill_actuals_only_open_rows_with_measurement():
    log = _log([1.0, 2.0])
    log.loc[:, ["actual", "abs_error"]] = np.nan
    t0 = pd.Timestamp(log.at[0, "target_time"])
    out = fill_actuals(log, {"s1": [{"time": t0, "pm25": 18.0},
                                    {"time": t0 - timedelta(hours=1), "pm25": None}]})
    assert out.at[0, "actual"] == 18.0 and out.at[0, "abs_error"] == 3.0
    assert np.isnan(out.at[1, "actual"])                      # ölçüm yok: açık kalır
    assert append(out, out).shape[0] == 2                     # tekrar eklemede kopya yok
