"""Pano testleri: saf bileşenler + sahte servisle Streamlit uygulamasının duman testi."""

from pathlib import Path

import pytest

from havauyari.alerts.aqi import CATEGORIES
from havauyari.ui.components import (
    ADVICE,
    CATEGORY_COLORS,
    explanation_figure,
    explanation_sentence,
    feature_label,
    forecast_figure,
    map_figure,
)

APP = Path(__file__).resolve().parents[1] / "src" / "havauyari" / "ui" / "app.py"


def test_every_category_has_color_and_advice():
    assert set(CATEGORIES) == set(CATEGORY_COLORS) == set(ADVICE)


def test_explanation_sentence_names_strongest_factors():
    e = {"top_features": [
        {"feature": "station_pm25", "contribution": 4.1},
        {"feature": "fc_win_wind_mean", "contribution": -3.1},
        {"feature": "hour_cos", "contribution": 0.5}]}
    s = explanation_sentence(e)
    assert "istasyonun şu anki ölçümü" in s and "+4,1" in s
    assert "tahmini ortalama rüzgârı" in s and "−3,1" in s
    assert explanation_sentence({"top_features": []}).startswith("Belirgin")
    assert feature_label("bilinmeyen_ozellik") == "bilinmeyen_ozellik"


@pytest.fixture
def forecast(service):
    return service.forecast("s1")


def test_tr_num():
    from havauyari.ui.components import tr_num

    assert tr_num(6.78, 2) == "6,78"
    assert tr_num(0.9, sign=True) == "+0,9" and tr_num(-2.84, sign=True) == "−2,8"
    assert tr_num(-5, 0) == "−5"


def test_figures_build(forecast):
    fig = forecast_figure(forecast)
    names = {t.name for t in fig.data}
    assert {"ölçüm", "önümüzdeki 24 saat tahmini", "%80 aralık"} <= names
    assert len(explanation_figure(forecast["explanation"]).data[0].x) == 5
    m = map_figure([{"name": "a", "lat": 40, "lon": 29, "pm25": 20, "category": "Orta",
                     "is_alert": False, "risk": True}])
    assert m.data[0].marker.color[0] == CATEGORY_COLORS["Orta"]


def test_streamlit_app_renders_with_fake_service(service, monkeypatch):
    from streamlit.testing.v1 import AppTest

    import havauyari.ui.state as ui_state

    monkeypatch.setattr(ui_state, "SERVICE_FACTORY", lambda: service)
    at = AppTest.from_file(str(APP), default_timeout=60)
    at.run()
    assert not at.exception, at.exception
    assert [t.label for t in at.tabs] == ["Genel bakış", "İstasyon", "Model performansı",
                                          "Hakkında"]
    assert any("Uyarı verilen istasyon" in m.label for m in at.metric)
    assert at.selectbox[0].options                      # istasyon seçimi dolu
