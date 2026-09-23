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
    assert {"ölçüm", "tahmin", "önceki tahminler", "%80 aralık"} <= names
    assert len(explanation_figure(forecast["explanation"]).data[0].x) == 5
    m = map_figure([{"name": "a", "lat": 40, "lon": 29, "pm25": 20, "category": "Orta",
                     "is_alert": False, "risk": True}])
    stations = next(tr for tr in m.data if tr.name == "istasyonlar")
    assert stations.marker.color[0] == CATEGORY_COLORS["Orta"]


def test_theme_tokens_and_contrast():
    """Metin/yüzey kontrastı her iki temada ≥ 4.5:1 (WCAG AA)."""
    from havauyari.ui.theme import DARK, LIGHT

    def lum(hex_color):
        rgb = [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
        return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]

    def contrast(a, b):
        hi, lo = sorted([lum(a), lum(b)], reverse=True)
        return (hi + 0.05) / (lo + 0.05)

    for t in (LIGHT, DARK):
        for fg in (t.text, t.muted):
            for bg in (t.bg, t.surface, t.surface_alt):
                assert contrast(fg, bg) >= 4.5, (t.name, fg, bg)
    for cat, bg in CATEGORY_COLORS.items():                 # rozet metni
        from havauyari.ui.components import CATEGORY_TEXT_COLORS
        assert contrast(CATEGORY_TEXT_COLORS[cat], bg) >= 4.5, cat


def test_css_keeps_icon_font():
    """Yazı tipi kuralı Streamlit'in ikon öğelerini ezmemeli (ikon adı metin olarak görünür)."""
    from havauyari.ui.theme import LIGHT, css

    c = css(LIGHT)
    assert 'span:not([data-testid="stIconMaterial"])' in c
    assert "'Material Symbols Rounded' !important" in c
    assert '[class*="st-"]' not in c                  # eski, ikonları da ezen geniş seçici


def test_html_fragments_escape_and_label():
    from havauyari.ui.components import category_chip, flags_html, range_html

    assert "Uyarı yok" in flags_html(False, False) and "Risk" in flags_html(False, True)
    assert "&lt;" in category_chip("<x>")                  # kullanıcı metni kaçışlanır
    r = range_html(20, 10, 40, 30)
    assert 'role="img"' in r and "eşik 35,5" in r


def test_streamlit_app_renders_with_fake_service(service, monkeypatch):
    from streamlit.testing.v1 import AppTest

    import havauyari.ui.state as ui_state

    monkeypatch.setattr(ui_state, "SERVICE_FACTORY", lambda: service)
    at = AppTest.from_file(str(APP), default_timeout=60)
    at.run()
    assert not at.exception, at.exception
    labels = [t.label for t in at.tabs]
    for expected, label in zip(["Genel bakış", "İstasyon detayı", "Model performansı",
                                "Hakkında"], labels, strict=True):
        assert label.endswith(expected), label
    body = " ".join(m.value for m in at.markdown)
    for text in ("HavaUyarı", "Hedef zaman", "Uyarı riski", "hu-station", "için tahmin",
                 "Bu tahmin neden böyle?"):
        assert text in body, text
    assert at.selectbox[0].options                      # istasyon seçimi dolu
