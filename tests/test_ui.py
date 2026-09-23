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
    assert "tahminî ortalama rüzgârı" in s and "−3,1" in s
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


def test_turkish_date_and_percent_formats():
    """TDK: saat ile dakika arasında nokta; ay adı yazıyla; yüzde işareti sayıdan önce."""
    from havauyari.ui.components import tr_datetime, tr_pct, tr_short

    assert tr_datetime("2026-09-24 14:00") == "24 Eylül 2026, 14.00"
    assert tr_datetime("2026-01-05 09:30", year=False) == "5 Ocak, 09.30"
    assert tr_short("2026-09-24 14:00") == "24.09, 14.00"
    assert tr_pct(0.824) == "%82" and tr_pct(0.829, 1) == "%82,9"


def test_pr_figure_uses_turkish_percent_ticks():
    from havauyari.ui.components import pr_figure

    curves = {"pr": {"lgbm_gercekci": {"threshold": [30.0], "recall": [0.8],
                                       "precision": [0.6]}},
              "points": {"persistence": {"recall": 0.5, "precision": 0.5}}}
    fig = pr_figure(curves, {"recall": 0.8, "precision": 0.55})
    assert list(fig.layout.xaxis.ticktext)[4] == "%80"
    assert fig.data[0].customdata[0][1] == "%80"


def test_figures_build(forecast):
    fig = forecast_figure(forecast)
    names = {t.name for t in fig.data}
    assert {"ölçüm", "tahmin", "önceki tahminler", "%80'lik aralık"} <= names
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

    assert "Uyarı yok" in flags_html(False, False)
    assert "Uyarı riski" in flags_html(False, True)
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
    for text in ("HavaUyarı", "Tahmin edilen saat", "Uyarı riski", "hu-station", "için tahmin",
                 "Bu tahmin neden böyle?", "hu-rank-row", "hu-hours", 'lang="tr"'):
        assert text in body, text

    # Kart düğmesi: istasyonu seçer, detay sekmesini açar ve adresi günceller
    at.button(key="go-s2").click().run()
    assert not at.exception, at.exception
    assert at.session_state["istasyon"] == "s2"
    assert at.session_state["nav"].endswith("İstasyon detayı")
    assert at.query_params["istasyon"] == ["s2"]


def test_new_overview_fragments(forecast):
    from havauyari.ui.components import (
        hero_html,
        hourly_strip_html,
        mae_bars_html,
        pipeline_html,
        ranking_html,
        skeleton_html,
        sparkline_svg,
    )

    rows = [{"name": "A", "pm25": 40.0, "low": 30.0, "high": 55.0,
             "category": "Hassas gruplar için sağlıksız", "is_alert": True, "risk": True},
            {"name": "B", "pm25": 12.0, "low": 5.0, "high": 20.0, "category": "Orta",
             "is_alert": False, "risk": False}]
    hero = hero_html(rows, "2026-09-24 16:00")
    assert "1 istasyonda uyarı var" in hero and "24 Eylül, 16.00" in hero
    assert 'role="heading"' in hero
    rank = ranking_html(rows)
    assert rank.count('class="hu-rank-row"') == 2 and "uyarı" in rank   # erişilebilir etiket
    svg = sparkline_svg(forecast)
    assert svg.startswith("<svg") and 'aria-hidden="true"' in svg
    strip = hourly_strip_html(forecast)
    assert strip.count('class="hu-hour"') == 24 and "zirvesi" in strip
    assert mae_bars_html().count("hu-bar-row") == 7 and "hu-bar-ours" in mae_bars_html()
    assert pipeline_html().count("hu-step") >= 5
    assert 'role="status"' in skeleton_html()


def test_station_code_and_particles_are_stable():
    from havauyari.ui.components import particles_svg, station_code

    assert station_code("İzmir - Konak") == "İZM · KNK"
    assert station_code("Ankara - Keçiören Sanatoryum") == "ANK · KÇR"
    assert station_code("Kocaeli") == "KOC"
    a = particles_svg(7, 25.0, 13.0, 39.0, 50.0, "#D4A53A", "#1C1B19")
    particles_svg.cache_clear()
    b = particles_svg(7, 25.0, 13.0, 39.0, 50.0, "#D4A53A", "#1C1B19")
    assert a == b                                            # her çizimde aynı noktalar
    assert a.count("<circle") > particles_svg(7, 5.0, 1.0, 9.0, 50.0, "#D4A53A", "x").count(
        "<circle")                                           # yoğunluk değerle artar


def test_uppercase_labels_protect_micro_sign(service, monkeypatch):
    """CSS büyük harf dönüşümü µ'yü Yunanca Mu'ya çevirir ("MG/M³"): büyük harfli etiketlerde
    birim .hu-u ile korunmalı."""
    import re

    from streamlit.testing.v1 import AppTest

    import havauyari.ui.state as ui_state

    monkeypatch.setattr(ui_state, "SERVICE_FACTORY", lambda: service)
    at = AppTest.from_file(str(APP), default_timeout=60)
    at.run()
    body = " ".join(m.value for m in at.markdown)
    upper = re.findall(r'class="(?:hu-label|hu-eyebrow|hu-kpi-label|hu-mono)"[^>]*>(.*?)</div>',
                       body)
    for label in upper:
        assert "µ" not in re.sub(r'<span class="hu-u">.*?</span>', "", label), label


def test_map_declutters_nearby_stations():
    """Yakın istasyonlar (İstanbul, Bursa, Ankara ikilileri) üst üste binip değer gizlememeli;
    değerler panonun serif rakamıyla yazılır."""
    import math

    from havauyari.ui.components import MIN_SEP_DEG, _merc, declutter, map_figure

    pts = [(28.87, 41.10), (29.10, 41.03), (29.93, 40.77), (29.06, 40.19), (29.07, 40.20),
           (32.86, 39.97), (32.67, 39.95), (27.13, 38.42), (29.0, 41.0)]
    out = declutter(pts)
    for i in range(len(out)):
        for j in range(i + 1, len(out)):
            d = math.hypot(out[i][0] - out[j][0], _merc(out[i][1]) - _merc(out[j][1]))
            assert d >= MIN_SEP_DEG * 0.999, (i, j, d)
    assert declutter(pts) == out                              # her çizimde aynı yerleşim

    rows = [{"name": n, "lat": la, "lon": lo, "pm25": v, "category": "Orta",
             "is_alert": False, "risk": False}
            for n, (lo, la), v in zip("ab", pts[:2], (16, 10), strict=True)]
    fig = map_figure(rows)
    stations = next(tr for tr in fig.data if tr.name == "istasyonlar")
    assert list(stations.text) == ["16", "10"]
    assert "Instrument Serif" in stations.textfont.family
    assert any(tr.name == "öncü" for tr in fig.data)          # gerçek konuma bağlayan çizgi
