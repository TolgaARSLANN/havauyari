"""Panonun saf (Streamlit'ten bağımsız, test edilebilir) parçaları: metinler, HTML kartları,
Plotly grafikleri. Görsel kararlar ui/theme.py'deki tasarım sisteminden gelir."""

from __future__ import annotations

from html import escape

import pandas as pd
import plotly.graph_objects as go

from havauyari.alerts.aqi import CATEGORIES, PM25_BREAKPOINTS, aqi_category
from havauyari.ui.theme import LIGHT, Tokens, plotly_layout, svg

OFFICIAL_ALERT = 35.5

# AQI renkleri: US EPA tonlarının ekranda daha dengeli görünen karşılıkları (aynı renk ailesi,
# aynı sıra). Metin rengi kontrastı her kategori için ≥ 4.5:1 (testlerde doğrulanır).
CATEGORY_COLORS = {
    "İyi": "#22C55E",
    "Orta": "#FACC15",
    "Hassas gruplar için sağlıksız": "#F97316",
    "Sağlıksız": "#EF4444",
    "Çok sağlıksız": "#9333EA",
    "Tehlikeli": "#9F1239",
}
CATEGORY_TEXT_COLORS = {c: ("#ffffff" if c in ("Çok sağlıksız", "Tehlikeli") else "#0F172A")
                        for c in CATEGORIES}
CATEGORY_SHORT = {"Hassas gruplar için sağlıksız": "Hassas gruplar"}

# Genel bilgilendirme (US EPA AQI rehberinden özetlenmiştir; tıbbi tavsiye değildir).
# Yazım: TDK Yazım Kılavuzu (olağan dışı, mekân, resmî, tahminî).
ADVICE = {
    "İyi": "Hava kalitesi iyi. Açık havadaki etkinlikler için uygun bir gün.",
    "Orta": "Hava kalitesi kabul edilebilir düzeyde. Kirliliğe olağan dışı duyarlı kişiler, "
            "açık havada uzun süreli ve yoğun fiziksel etkinliği azaltmayı düşünebilir.",
    "Hassas gruplar için sağlıksız": "Astım, kalp ya da akciğer hastalığı olanlar, yaşlılar "
            "ve çocuklar açık havada uzun süreli ve yoğun fiziksel etkinliği azaltmalıdır.",
    "Sağlıksız": "Herkes açık havada uzun süreli ve yoğun fiziksel etkinliği azaltmalıdır; "
            "hassas gruplar bu tür etkinliklerden kaçınmalıdır.",
    "Çok sağlıksız": "Herkes açık havada fiziksel etkinlikten kaçınmalıdır; hassas gruplar "
            "mümkünse kapalı alanda kalmalıdır.",
    "Tehlikeli": "Herkes açık havadaki etkinliklerden kaçınmalı ve mümkünse kapalı alanda "
            "kalmalıdır.",
}
DISCLAIMER = ("Bu tahminler bir makine öğrenmesi modeli tarafından üretilir ve yalnızca "
              "bilgilendirme amaçlıdır; resmî hava kalitesi uyarılarının ve tıbbi tavsiyenin "
              "yerine geçmez.")

TR_MONTHS = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos",
             "Eylül", "Ekim", "Kasım", "Aralık"]

CITY_LABELS = {"istanbul": "İstanbul", "ankara": "Ankara", "izmir": "İzmir", "bursa": "Bursa",
               "kocaeli": "Kocaeli"}

# Sık görülen özelliklerin okunur adları
FEATURE_LABELS = {
    "station_pm25": "istasyonun şu anki ölçümü",
    "station_pm25_lag1": "bir saat önceki ölçüm",
    "station_pm25_lag2": "iki saat önceki ölçüm",
    "station_pm25_lag3": "üç saat önceki ölçüm",
    "station_pm25_lag24": "24 saat önceki ölçüm",
    "station_pm25_lag168": "bir hafta önceki ölçüm",
    "station_pm25_tgt_day_ago": "hedef saatin bir gün önceki ölçümü",
    "station_pm25_tgt_week_ago": "hedef saatin bir hafta önceki ölçümü",
    "station_pm25_rollmean24": "son 24 saatin ortalaması",
    "station_pm25_rollmean168": "son bir haftanın ortalaması",
    "station_pm25_rollmax24": "son 24 saatin en yüksek değeri",
    "station_pm25_rollstd168": "son bir haftadaki dalgalanma",
    "station_pm10": "istasyonun PM10 ölçümü",
    "fc_win_wind_mean": "önümüzdeki 24 saatin tahminî ortalama rüzgârı",
    "fc_win_wind_min": "önümüzdeki 24 saatin tahminî en zayıf rüzgârı",
    "fc_win_calm_hours": "önümüzdeki 24 saatteki tahminî durgun saat sayısı",
    "fc_win_precip_sum": "önümüzdeki 24 saatin tahminî yağışı",
    "fc_win_temp_range": "önümüzdeki 24 saatin tahminî sıcaklık farkı",
    "fc_win_temp_min": "önümüzdeki 24 saatin tahminî en düşük sıcaklığı",
    "fc_win_cloud_mean": "önümüzdeki 24 saatin tahminî bulutluluğu",
    "fc_tgt_humidity": "hedef saatteki tahminî nem",
    "fc_tgt_wind_speed": "hedef saatteki tahminî rüzgâr hızı",
    "fc_tgt_wind_u": "hedef saatteki tahminî rüzgâr yönü (doğu-batı)",
    "fc_tgt_wind_v": "hedef saatteki tahminî rüzgâr yönü (kuzey-güney)",
    "fc_tgt_temperature": "hedef saatteki tahminî sıcaklık",
    "fc_tgt_temp_change": "tahminî sıcaklık değişimi",
    "fc_tgt_pressure_change": "tahminî basınç değişimi",
    "fc_tgt_cloud_cover": "hedef saatteki tahminî bulutluluk",
    "surface_pressure": "şu anki hava basıncı",
    "heating_degree_rollmean24": "son 24 saatteki ısınma ihtiyacı",
    "calm_hours24": "son 24 saatteki durgun saat sayısı",
    "wind_speed_rollmean24": "son 24 saatin ortalama rüzgârı",
    "hour_sin": "günün saati", "hour_cos": "günün saati",
    "tgt_hour_sin": "hedef saat", "tgt_hour_cos": "hedef saat",
    "month_sin": "mevsim", "month_cos": "mevsim",
    "dayofweek": "haftanın günü", "tgt_dayofweek": "hedef günün haftanın hangi günü olduğu",
    "station_code": "istasyonun kendine özgü seviyesi",
    "city_code": "şehrin kendine özgü seviyesi",
}

MODEL_LABELS = {"lgbm_gercekci": "HavaUyarı", "lgbm_iyimser": "HavaUyarı (üst sınır)",
                "persistence": "Yarın da bugün gibi", "cams_raw": "Ham CAMS",
                "cams_scaled": "Ölçeklenmiş CAMS"}

# 12 aylık geri testte ortalama mutlak hata (µg/m³); kaynak: reports/backtest_istasyon_h24.md
BACKTEST_MAE = [
    ("HavaUyarı", 6.78),
    ("24 saatlik hareketli ortalama", 9.09),
    ("Yarın da bugün gibi", 9.09),
    ("Klimatoloji", 10.30),
    ("Ölçeklenmiş CAMS", 11.15),
    ("Bir hafta önceki aynı saat", 11.61),
    ("Ham CAMS", 12.95),
]


# ---------------------------------------------------------------------------------------------
# Metin yardımcıları
# ---------------------------------------------------------------------------------------------
def feature_label(name: str) -> str:
    return FEATURE_LABELS.get(name, name)


def tr_num(x: float, digits: int = 1, sign: bool = False) -> str:
    """Türkçe ondalık biçimi: 6.78 -> '6,78'; sign=True: '+0,9' / '−2,8'."""
    s = f"{abs(x):.{digits}f}".replace(".", ",")
    if sign:
        return ("+" if x > 0 else "−" if x < 0 else "") + s
    return ("−" if x < 0 else "") + s


def tr_datetime(ts, year: bool = True) -> str:
    """TDK'ye uygun tarih-saat: '24 Eylül 2026, 14.00' (saat ile dakika arasında nokta)."""
    ts = pd.Timestamp(ts)
    y = f" {ts.year}" if year else ""
    return f"{ts.day} {TR_MONTHS[ts.month - 1]}{y}, {ts:%H.%M}"


def tr_short(ts) -> str:
    """Kısa biçim (kartlar için): '24.09, 14.00'."""
    return f"{pd.Timestamp(ts):%d.%m, %H.%M}"


def tr_pct(x: float, digits: int = 0) -> str:
    """Türkçede yüzde işareti sayıdan önce gelir: 0.824 -> '%82' (digits=1: '%82,4')."""
    return "%" + tr_num(x * 100, digits)


def category_color(category: str) -> str:
    return CATEGORY_COLORS.get(category, "#94A3B8")


def tint(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


def short_label(category: str) -> str:
    return CATEGORY_SHORT.get(category, category)


def explanation_sentence(explanation: dict, markup: str = "md") -> str:
    """Katkılardan sade Türkçe özet cümle. markup: "md" (**kalın**) ya da "html" (<b>)."""

    def bold(s: str) -> str:
        return f"<b>{escape(s)}</b>" if markup == "html" else f"**{s}**"

    feats = explanation["top_features"]
    up = [f for f in feats if f["contribution"] > 0]
    down = [f for f in feats if f["contribution"] < 0]
    parts = []
    if up:
        top = max(up, key=lambda f: f["contribution"])
        parts.append(f"Tahmini en çok {bold(feature_label(top['feature']))} yükseltiyor "
                     f"({tr_num(top['contribution'], sign=True)} µg/m³)")
    if down:
        top = min(down, key=lambda f: f["contribution"])
        parts.append(f"en çok {bold(feature_label(top['feature']))} düşürüyor "
                     f"({tr_num(top['contribution'], sign=True)} µg/m³)")
    if not parts:
        return "Belirgin bir etken yok; tahmin, ortalamaya yakın."
    sentence = "; ".join(parts) + "."
    return sentence[0].upper() + sentence[1:]


def status_of(rows: list[dict]) -> str:
    """Genel durum: 'alert' (en az bir uyarı), 'risk' ya da 'ok'."""
    if any(r["is_alert"] for r in rows):
        return "alert"
    if any(r["risk"] for r in rows):
        return "risk"
    return "ok"


# ---------------------------------------------------------------------------------------------
# HTML parçaları (renk her zaman metin ve/veya ikonla birlikte)
# ---------------------------------------------------------------------------------------------
def header_html(issued: pd.Timestamp | None, stale: bool, t: Tokens = LIGHT) -> str:
    if issued is None:
        status = (f'<span class="hu-dot" style="background:{t.muted}"></span>'
                  "Veri bekleniyor")
    else:
        color, label = (t.warn, "Veri gecikmeli") if stale else (t.ok, "Canlı")
        pulse = "" if stale else " hu-dot-live"
        status = (f'<span class="hu-dot{pulse}" style="background:{color};color:{color}">'
                  f"</span><strong style='color:{color}'>{label}</strong>"
                  f'<span class="hu-status-sep" aria-hidden="true"></span>'
                  f"Son güncelleme: {tr_datetime(issued)}")
    # lang="tr": CSS ile büyük harfe çevrilen metinlerde i → İ dönüşümü doğru yapılır
    return (f'<header class="hu-header" lang="tr"><div class="hu-brand">'
            f'<div class="hu-logo">{svg("wind", 22, "#ffffff")}</div><div>'
            f'<h1 class="hu-title">HavaUyarı</h1>'
            f'<p class="hu-subtitle">PM2.5 için 24 saat önceden tahmin ve erken uyarı · '
            f'5 şehir, 8 istasyon</p></div></div>'
            f'<div class="hu-status" role="status">{status}</div></header>')


def skeleton_html() -> str:
    """Yükleme iskeleti: özet bant, harita/sıralama ve kartların yer tutucuları."""
    cards = "".join('<div class="hu-skel" style="height:190px"></div>' for _ in range(4))
    return ('<div class="hu-skeleton" lang="tr" role="status" aria-live="polite">'
            '<span class="hu-sr">Canlı ölçümler ve hava tahmini alınıyor, tahminler '
            'hesaplanıyor…</span>'
            '<div class="hu-skel-note">Canlı ölçümler ve hava tahmini alınıyor…</div>'
            '<div class="hu-skel" style="height:190px;border-radius:22px"></div>'
            '<div class="hu-skel-row"><div class="hu-skel" style="height:420px"></div>'
            '<div class="hu-skel" style="height:420px"></div></div>'
            f'<div class="hu-skel-cards">{cards}</div></div>')


def kpi_html(label: str, value: str, sub: str = "", icon: str | None = None) -> str:
    ic = f'<span class="hu-kpi-icon">{svg(icon, 16)}</span>' if icon else ""
    sub_html = f'<div class="hu-kpi-sub">{sub}</div>' if sub else ""
    return (f'<div class="hu-card hu-kpi" lang="tr"><div class="hu-kpi-label">{ic}'
            f'{escape(label)}</div><div class="hu-kpi-value">{value}</div>{sub_html}</div>')


def category_chip(category: str, solid: bool = False, t: Tokens = LIGHT,
                  suffix: str = "") -> str:
    label = escape(short_label(category) + suffix)
    if solid:
        return (f'<span class="hu-chip" style="background:{category_color(category)};'
                f'color:{CATEGORY_TEXT_COLORS.get(category, "#000")}" '
                f'title="{escape(category)}">{label}</span>')
    return (f'<span class="hu-chip" style="background:{tint(category_color(category), .16)};'
            f'color:{t.text}" title="{escape(category)}"><span class="hu-chip-swatch" '
            f'style="background:{category_color(category)}"></span>{label}</span>')


def flags_html(is_alert: bool, risk: bool, t: Tokens = LIGHT) -> str:
    if is_alert:
        return (f'<span class="hu-flag" style="color:{t.danger};'
                f'background:{tint(t.danger, .10)}">{svg("alert", 14)}Uyarı</span>')
    if risk:
        return (f'<span class="hu-flag" style="color:{t.warn};background:{tint(t.warn, .10)}">'
                f'{svg("eye", 14)}Uyarı riski</span>')
    return (f'<span class="hu-flag hu-flag-quiet" style="color:{t.ok}">{svg("shield", 14)}'
            "Uyarı yok</span>")


def hero_html(rows: list[dict], target_time, t: Tokens = LIGHT) -> str:
    """Özet bant: genel durum başlığı, kategori dağılımı ve üç temel sayı.

    rows: name, pm25, category, is_alert, risk (tahmine göre azalan sırada)."""
    n = len(rows)
    n_alert = sum(r["is_alert"] for r in rows)
    n_risk = sum(r["risk"] and not r["is_alert"] for r in rows)
    status = status_of(rows)
    top = rows[0]
    if status == "alert":
        headline = f"{n_alert} istasyonda uyarı var"
        tone, icon = t.danger, "alert"
    elif status == "risk":
        headline = "Uyarı yok; uyarı riski izleniyor"
        tone, icon = t.warn, "eye"
    else:
        headline = "Uyarı yok: Hava kalitesi kabul edilebilir düzeyde"
        tone, icon = t.ok, "shield"
    lead = (f"En yüksek tahmin <b>{escape(top['name'])}</b> istasyonunda: "
            f"<b>{tr_num(top['pm25'], 0)} µg/m³</b> ({escape(short_label(top['category']))}).")
    if status == "risk":
        lead += (f" {n_risk} istasyonda %80'lik aralığın üst sınırı resmî eşiği "
                 "(35,5 µg/m³) aşıyor.")

    counts = {c: sum(r["category"] == c for r in rows) for c in CATEGORIES}
    segs = "".join(
        f'<span class="hu-dist-seg" style="flex:{k};background:{category_color(c)}" '
        f'title="{escape(c)}: {k} istasyon"></span>' for c, k in counts.items() if k)
    legend = "".join(
        f'<span><span class="hu-chip-swatch" style="background:{category_color(c)}"></span>'
        f'<b>{k}</b> {escape(short_label(c))}</span>' for c, k in counts.items() if k)

    def stat(label: str, value: str, sub: str, color: str) -> str:
        return (f'<div class="hu-stat"><div class="hu-stat-label">{label}</div>'
                f'<div class="hu-stat-value" style="color:{color}">{value}</div>'
                f'<div class="hu-stat-sub">{sub}</div></div>')

    stats = (stat("Uyarı", f"{n_alert}<small>/{n}</small>", "tahmin karar eşiğini aşıyor",
                  t.danger if n_alert else t.text)
             + stat("Uyarı riski", f"{n_risk}<small>/{n}</small>", "aralık 35,5'i aşıyor",
                    t.warn if n_risk else t.text)
             + stat("En yüksek", f"{tr_num(top['pm25'], 0)}<small> µg/m³</small>",
                    escape(top["name"]), t.text))
    glow = tint(category_color(top["category"]), .22 if t.name == "light" else .16)
    return (
        f'<section class="hu-hero" lang="tr" style="--hu-glow:{glow};--hu-tone:{tone}" '
        f'aria-label="Genel durum">'
        f'<div class="hu-hero-main">'
        f'<div class="hu-eyebrow">{svg("clock", 14)}Tahmin edilen saat: '
        f'{tr_datetime(target_time, year=False)}</div>'
        f'<div class="hu-hero-title" role="heading" aria-level="2">'
        f'<span class="hu-hero-icon">{svg(icon, 22)}</span>{headline}</div>'
        f'<p class="hu-hero-lead">{lead}</p>'
        f'<div class="hu-dist" role="img" aria-label="Kategorilere göre istasyon sayısı">'
        f'{segs}</div><div class="hu-dist-legend">{legend}</div></div>'
        f'<div class="hu-hero-stats">{stats}</div></section>')


def _scale_top(rows: list[dict]) -> float:
    return max(50.0, max(r["high"] for r in rows) * 1.1) if rows else 50.0


def _zones_gradient(top: float, alpha: float) -> str:
    """Kategori bölgelerini soluk renkli şeritler olarak çizen doğrusal gradyan."""
    stops, lo_pct = [], 0.0
    for c_lo, c_hi, _a, _b, name in PM25_BREAKPOINTS:
        if c_lo > top:
            break
        hi_pct = min(100.0, (c_hi + 0.1) / top * 100)
        col = tint(category_color(name), alpha)
        stops.append(f"{col} {lo_pct:.2f}%, {col} {hi_pct:.2f}%")
        lo_pct = hi_pct
    return f"linear-gradient(90deg, {', '.join(stops)})"


def ranking_html(rows: list[dict], t: Tokens = LIGHT) -> str:
    """Tüm istasyonlar tek ölçekte: nokta = tahmin, bant = %80'lik aralık, kesikli = resmî
    eşik. rows: name, pm25, low, high, category, is_alert, risk."""
    top = _scale_top(rows)

    def pct(v: float) -> float:
        return max(0.0, min(100.0, v / top * 100))

    zones = _zones_gradient(top, .14 if t.name == "light" else .12)
    items = []
    for i, r in enumerate(rows):
        color = category_color(r["category"])
        flag = ""
        if r["is_alert"]:
            flag = f'<span class="hu-rank-flag" style="color:{t.danger}">{svg("alert", 13)}</span>'
        elif r["risk"]:
            flag = f'<span class="hu-rank-flag" style="color:{t.warn}">{svg("eye", 13)}</span>'
        label = (f"{r['name']}: {tr_num(r['pm25'], 0)} µg/m³, {r['category']}; %80 olasılıkla "
                 f"{tr_num(r['low'], 0)}–{tr_num(r['high'], 0)}"
                 + ("; uyarı" if r["is_alert"] else "; uyarı riski" if r["risk"] else ""))
        items.append(
            f'<li class="hu-rank-row" style="--i:{i}" aria-label="{escape(label)}">'
            f'<span class="hu-rank-name" title="{escape(r["name"])}">{flag}'
            f'{escape(r["name"])}</span>'
            f'<span class="hu-rank-track" style="background:{zones}" aria-hidden="true">'
            f'<span class="hu-rank-band" style="left:{pct(r["low"]):.1f}%;'
            f'width:{pct(r["high"]) - pct(r["low"]):.1f}%;background:{tint(color, .55)}"></span>'
            f'<span class="hu-rank-thr" style="left:{pct(OFFICIAL_ALERT):.1f}%"></span>'
            f'<span class="hu-rank-dot" style="left:{pct(r["pm25"]):.1f}%;background:{color}">'
            f'</span></span>'
            f'<span class="hu-rank-value">{tr_num(r["pm25"], 0)}</span></li>')
    ticks = "".join(f'<span style="left:{pct(v):.1f}%">{v:g}</span>'
                    for v in range(0, int(top) + 1, 10 if top <= 60 else 20))
    return (f'<div class="hu-rank" lang="tr"><ol>{"".join(items)}</ol>'
            f'<div class="hu-rank-axis" aria-hidden="true"><span></span>'
            f'<span class="hu-rank-ticks">{ticks}<em style="left:{pct(OFFICIAL_ALERT):.1f}%">'
            f'resmî eşik</em></span><span></span></div></div>')


def sparkline_svg(forecast: dict, t: Tokens = LIGHT, hours_back: int = 48) -> str:
    """Kart içi mini grafik: son `hours_back` saatin ölçümü + önümüzdeki 24 saatin tahmini ve
    %80'lik aralığı. Ölçekten bağımsız çizgi kalınlığı (vector-effect)."""
    now = pd.Timestamp(forecast["issued_at"])
    start = now - pd.Timedelta(hours=hours_back)
    end = now + pd.Timedelta(hours=24)
    hist = [(pd.Timestamp(h["time"]), h["pm25"]) for h in forecast.get("history", [])
            if h["pm25"] is not None and pd.Timestamp(h["time"]) >= start]
    fut = [(pd.Timestamp(p["target_time"]), p["pm25"], p["low"], p["high"])
           for p in forecast.get("trajectory", []) if pd.Timestamp(p["target_time"]) > now]
    values = [v for _, v in hist] + [hi for *_, hi in fut]
    y_max = max(40.0, max(values) * 1.08) if values else 40.0
    w, h = 300.0, 64.0
    span = (end - start).total_seconds()

    def x(ts) -> float:
        return (ts - start).total_seconds() / span * w

    def y(v) -> float:
        return h - 2 - v / y_max * (h - 4)

    def line(points) -> str:
        return " ".join(f"{'M' if i == 0 else 'L'}{x(ts):.1f},{y(v):.1f}"
                        for i, (ts, v) in enumerate(points))

    parts = []
    if fut:
        band = ([(ts, hi) for ts, _p, _lo, hi in fut]
                + [(ts, lo) for ts, _p, lo, _hi in fut[::-1]])
        parts.append(f'<path d="{line(band)} Z" fill="{t.data_soft}" stroke="none"/>')
    thr = y(OFFICIAL_ALERT)
    parts.append(f'<line x1="0" x2="{w}" y1="{thr:.1f}" y2="{thr:.1f}" stroke="#F97316" '
                 f'stroke-width="1" stroke-dasharray="3 3" vector-effect="non-scaling-stroke" '
                 f'opacity=".8"/>')
    parts.append(f'<line x1="{x(now):.1f}" x2="{x(now):.1f}" y1="0" y2="{h}" stroke="{t.border}" '
                 f'stroke-width="1" vector-effect="non-scaling-stroke"/>')
    if hist:
        parts.append(f'<path d="{line(hist)}" fill="none" stroke="{t.muted}" stroke-width="1.5" '
                     f'vector-effect="non-scaling-stroke" stroke-linejoin="round"/>')
    if fut:
        parts.append(f'<path d="{line([(ts, p) for ts, p, _lo, _hi in fut])}" fill="none" '
                     f'stroke="{t.data}" stroke-width="2.25" vector-effect="non-scaling-stroke" '
                     f'stroke-linejoin="round" stroke-linecap="round"/>')
    return (f'<svg class="hu-spark" viewBox="0 0 {w:.0f} {h:.0f}" preserveAspectRatio="none" '
            f'aria-hidden="true" focusable="false">{"".join(parts)}</svg>')


def station_card_html(name: str, subtitle: str, f: dict, t: Tokens = LIGHT) -> str:
    """subtitle: istasyon türü (örn. 'Kentsel · Trafik'); ad zaten şehri içerir."""
    lm = f["latest_measurement"]
    now_txt = (f"Şu an <b>{tr_num(lm['pm25'])}</b>" if lm["pm25"] is not None
               else "Güncel ölçüm yok")
    color = category_color(f["category"])
    a = f["alert"]
    flag = flags_html(a["is_alert"], a["risk"], t) if (a["is_alert"] or a["risk"]) else ""
    return (
        f'<article class="hu-station" lang="tr" style="--hu-cat:{color}" '
        f'aria-label="{escape(name)}: 24 saat sonra {tr_num(f["pm25"], 0)} µg/m³, '
        f'{escape(f["category"])}">'
        f'<div class="hu-station-head"><div><div class="hu-station-name">{escape(name)}</div>'
        f'<div class="hu-station-city">{svg("pin", 12)}{escape(subtitle)}</div></div>{flag}</div>'
        f'<div class="hu-station-mid"><div class="hu-station-value">{tr_num(f["pm25"], 0)}'
        f'<span class="hu-unit">µg/m³</span></div>{category_chip(f["category"], t=t)}</div>'
        f'{sparkline_svg(f, t)}'
        f'<div class="hu-station-foot"><span>{now_txt}</span>'
        f'<span title="%80 olasılıkla bu aralıkta">%80: {tr_num(f["interval_80"]["low"], 0)}–'
        f'{tr_num(f["interval_80"]["high"], 0)}</span></div></article>')


def legend_html() -> str:
    """Kategoriler ve PM2.5 aralıkları (µg/m³): 'Orta (9,1–35,4)', 'Sağlıksız (55,5 ve üzeri)'."""
    items = []
    for i, (lo, hi, _a, _b, c) in enumerate(PM25_BREAKPOINTS[:4]):
        rng = (f"{tr_num(lo, 1)} ve üzeri" if i == 3 else f"{tr_num(lo, 1)}–{tr_num(hi, 1)}")
        items.append(f'<span><span class="hu-chip-swatch" '
                     f'style="background:{category_color(c)}"></span>{escape(short_label(c))} '
                     f'<em>{rng}</em></span>')
    return (f'<div class="hu-legend" lang="tr" aria-label="Hava kalitesi kategorileri ve PM2.5 '
            f'aralıkları (µg/m³)">{"".join(items)}</div>')


def range_html(pred: float, low: float, high: float, decision: float,
               t: Tokens = LIGHT) -> str:
    """%80 aralığı, tahmini ve resmî uyarı eşiğini aynı ölçekte gösteren yatay çubuk."""
    top = max(60.0, high * 1.15, OFFICIAL_ALERT * 1.25)

    def pct(v: float) -> float:
        return max(0.0, min(100.0, v / top * 100))

    ticks = "".join(f'<span class="hu-range-axis" style="left:{pct(v):.1f}%">{v:g}</span>'
                    for v in range(0, int(top) + 1, 20))
    return (
        f'<div class="hu-range" role="img" style="background:{_zones_gradient(top, .22)}" '
        f'aria-label="Tahmin: {tr_num(pred)} µg/m³. %80 olasılıkla {tr_num(low)} ile '
        f'{tr_num(high)} arasında. Resmî uyarı eşiği: 35,5 µg/m³.">'
        f'<div class="hu-range-band" style="left:{pct(low):.1f}%;'
        f'width:{pct(high) - pct(low):.1f}%"></div>'
        f'<div class="hu-range-point" style="left:{pct(pred):.1f}%"></div>'
        f'<div class="hu-range-thr" style="left:{pct(OFFICIAL_ALERT):.1f}%"></div>'
        f'<span class="hu-range-label" style="left:{pct(OFFICIAL_ALERT):.1f}%">'
        f'resmî eşik 35,5</span>'
        f'{ticks}</div>')


def hourly_strip_html(forecast: dict, t: Tokens = LIGHT) -> str:
    """Önümüzdeki 24 saat, saat saat: her hücre o saatin tahmin kategorisinin rengiyle."""
    now = pd.Timestamp(forecast["issued_at"])
    fut = [p for p in forecast.get("trajectory", []) if pd.Timestamp(p["target_time"]) > now]
    if not fut:
        return ""
    peak = max(fut, key=lambda p: p["pm25"])
    cells = []
    for i, p in enumerate(fut):
        ts = pd.Timestamp(p["target_time"])
        cat = aqi_category(p["pm25"])
        tip = f"{ts:%H.%M} · {tr_num(p['pm25'], 0)} µg/m³ · {cat}"
        label = f'<span class="hu-hour-lbl">{ts:%H}</span>' if i % 3 == 0 else ""
        cells.append(f'<span class="hu-hour" style="--c:{category_color(cat)};'
                     f'--h:{min(1.0, p["pm25"] / max(40.0, peak["pm25"] * 1.1)):.3f}" '
                     f'title="{tip}">{label}</span>')
    peak_ts = pd.Timestamp(peak["target_time"])
    return (f'<div class="hu-hours" lang="tr" role="img" aria-label="Önümüzdeki 24 saatin '
            f'saatlik tahmini; en yüksek değer {peak_ts:%H.%M} için '
            f'{tr_num(peak["pm25"], 0)} µg/m³">'
            f'<div class="hu-hours-grid">{"".join(cells)}</div>'
            f'<div class="hu-hours-note">{svg("activity", 14)}Önümüzdeki 24 saatin zirvesi: '
            f'<b>{peak_ts:%H.%M}</b> civarında <b>{tr_num(peak["pm25"], 0)} µg/m³</b> '
            f'({escape(short_label(aqi_category(peak["pm25"])))})</div></div>')


def callout_html(kind: str, text: str, t: Tokens = LIGHT) -> str:
    color, icon = {"alert": (t.danger, "alert"), "risk": (t.warn, "eye"),
                   "ok": (t.ok, "shield"), "info": (t.data, "info"),
                   "health": (t.muted, "heart")}[kind]
    return (f'<div class="hu-callout" lang="tr" style="--hu-c:{color};color:{t.text}">'
            f'<span class="hu-callout-icon" style="color:{color}">{svg(icon, 18)}</span>'
            f'<div>{text}</div></div>')


def mae_bars_html(t: Tokens = LIGHT) -> str:
    """Geri testte ortalama hata: HavaUyarı ve referans yöntemler (kısa çubuk = daha iyi)."""
    worst = max(v for _, v in BACKTEST_MAE)
    rows = []
    for i, (name, v) in enumerate(BACKTEST_MAE):
        ours = i == 0
        rows.append(
            f'<li class="hu-bar-row{" hu-bar-ours" if ours else ""}" style="--i:{i}">'
            f'<span class="hu-bar-name">{escape(name)}</span>'
            f'<span class="hu-bar-track"><span class="hu-bar-fill" '
            f'style="width:{v / worst * 100:.1f}%"></span></span>'
            f'<span class="hu-bar-value">{tr_num(v, 2)}</span></li>')
    return (f'<ol class="hu-bars" lang="tr" aria-label="Ortalama mutlak hata, µg/m³">'
            f'{"".join(rows)}</ol>')


PIPELINE = [
    ("database", "Veri", "SİM istasyon ölçümleri, CAMS kirleticileri, ERA5 ve o gün "
                         "yayımlanan hava tahmini (saatlik)"),
    ("layers", "Özellikler", "99 özellik; yalnızca tahmin anında bilinen bilgiler "
                             "(sızıntı testleriyle doğrulanır)"),
    ("cpu", "Model", "LightGBM; 12 aylık, ileriye kayan pencereli geri testle seçildi"),
    ("sliders", "Eşik ve aralık", "İstasyon bazlı uyarı eşiği ve %80'lik tahmin aralığı, "
                                  "yalnızca geçmiş veriden"),
    ("bell", "Uyarı", "Her saat yenilenen tahmin, uyarı kararı ve açıklaması"),
]


def pipeline_html() -> str:
    steps = "".join(
        f'<li class="hu-step" style="--i:{i}"><span class="hu-step-icon">{svg(icon, 18)}</span>'
        f'<span class="hu-step-num">{i + 1:02d}</span><b>{escape(title)}</b>'
        f'<span>{escape(text)}</span></li>'
        for i, (icon, title, text) in enumerate(PIPELINE))
    return f'<ol class="hu-steps" lang="tr" aria-label="Nasıl çalışır?">{steps}</ol>'


# ---------------------------------------------------------------------------------------------
# Grafikler
# ---------------------------------------------------------------------------------------------
def _aqi_bands(fig: go.Figure, y_max: float) -> None:
    for c_lo, c_hi, _i_lo, _i_hi, name in PM25_BREAKPOINTS:
        if c_lo > y_max:
            break
        fig.add_hrect(y0=c_lo, y1=min(c_hi + 0.1, y_max), fillcolor=category_color(name),
                      opacity=0.08, line_width=0, layer="below")


def forecast_figure(forecast: dict, t: Tokens = LIGHT) -> go.Figure:
    """Son 72 saatin ölçümü (düz) + aynı saatler için 24 saat önceden verilmiş tahminler
    (kesikli) + önümüzdeki 24 saatin tahmini (kalın) ve %80'lik aralık."""
    hist = pd.DataFrame(forecast["history"])
    traj = pd.DataFrame(forecast["trajectory"])
    now = pd.Timestamp(forecast["issued_at"])
    fig = go.Figure()
    hover = "%{y:.1f} µg/m³<extra>%{fullData.name}</extra>"
    if not traj.empty:
        traj["target_time"] = pd.to_datetime(traj["target_time"])
        past = traj[traj["target_time"] <= now]
        future = traj[traj["target_time"] > now]
        fig.add_trace(go.Scatter(
            x=list(future["target_time"]) + list(future["target_time"][::-1]),
            y=list(future["high"]) + list(future["low"][::-1]), fill="toself",
            fillcolor=t.data_soft, line={"width": 0}, hoverinfo="skip",
            name="%80'lik aralık"))
        fig.add_trace(go.Scatter(x=past["target_time"], y=past["pm25"], mode="lines",
                                 line={"color": t.data, "dash": "dot", "width": 1.6},
                                 name="önceki tahminler", hovertemplate=hover))
        fig.add_trace(go.Scatter(x=future["target_time"], y=future["pm25"], mode="lines",
                                 line={"color": t.data, "width": 3.2, "shape": "spline",
                                       "smoothing": 0.6},
                                 name="tahmin", hovertemplate=hover))
    if not hist.empty:
        hist["time"] = pd.to_datetime(hist["time"])
        fig.add_trace(go.Scatter(x=hist["time"], y=hist["pm25"], mode="lines",
                                 line={"color": t.measured, "width": 2}, name="ölçüm",
                                 hovertemplate=hover))
    y_values = pd.concat([hist.get("pm25", pd.Series(dtype=float)),
                          traj.get("high", pd.Series(dtype=float))]).dropna()
    y_max = max(50.0, float(y_values.max()) * 1.12 if len(y_values) else 50.0)
    _aqi_bands(fig, y_max)
    fig.add_vrect(x0=now, x1=now + pd.Timedelta(hours=24), fillcolor=t.data, opacity=0.04,
                  line_width=0, layer="below")
    fig.add_hline(y=OFFICIAL_ALERT, line={"color": "#F97316", "dash": "dot", "width": 1.5},
                  annotation_text="resmî uyarı eşiği (35,5)", annotation_position="top left",
                  annotation_font={"color": t.muted, "size": 11})
    fig.add_vline(x=now, line={"color": t.muted, "width": 1})
    fig.add_annotation(x=now, y=y_max, text="şimdi", showarrow=False, yanchor="bottom",
                       xanchor="left", xshift=4, font={"color": t.muted, "size": 11})
    fig.add_annotation(x=now + pd.Timedelta(hours=12), y=y_max, text="tahmin", showarrow=False,
                       yanchor="bottom", font={"color": t.data, "size": 11})
    fig.update_layout(**plotly_layout(
        t, height=380, hovermode="x unified",
        yaxis={"title": {"text": "PM2.5 (µg/m³)"}, "range": [0, y_max * 1.08]},
        xaxis={"tickformat": "%d.%m\n%H.%M", "hoverformat": "%d.%m, %H.%M"},
        legend={"orientation": "h", "y": -0.18, "x": 0},
        margin={"l": 8, "r": 8, "t": 16, "b": 8}))
    return fig


def explanation_figure(explanation: dict, t: Tokens = LIGHT) -> go.Figure:
    """Katkılar: artıran turuncu, azaltan mavi (renk körlüğüne uygun) + işaretli değer etiketi."""
    feats = explanation["top_features"][::-1]
    labels = [feature_label(f["feature"]) for f in feats]
    values = [f["contribution"] for f in feats]
    fig = go.Figure(go.Bar(
        x=values, y=labels, orientation="h",
        marker={"color": [t.increase if v > 0 else t.decrease for v in values],
                "cornerradius": 4},
        text=[f"{tr_num(v, sign=True)} {'↑' if v > 0 else '↓'}" for v in values],
        textposition="outside", textfont={"color": t.text},
        hovertemplate="%{y}: %{x:+.2f} µg/m³<extra></extra>"))
    fig.add_vline(x=0, line={"color": t.muted, "width": 1})
    span = max(abs(v) for v in values) if values else 1
    fig.update_layout(**plotly_layout(
        t, height=280, showlegend=False, bargap=0.35,
        xaxis={"title": {"text": "tahmine katkı (µg/m³)", "font": {"color": t.muted}},
               "range": [-span * 1.35, span * 1.35]},
        yaxis={"tickfont": {"color": t.text}}))
    return fig


def map_figure(rows: list[dict], t: Tokens = LIGHT, narrow: bool = False) -> go.Figure:
    """İstasyonlar, yarınki tahmin kategorisinin rengiyle; değer işaretin üzerinde yazılı.
    narrow=True: telefon genişliği için daha uzak görünüm (tüm istasyonlar çerçevede)."""
    df = pd.DataFrame(rows)
    text = [f"<b>{escape(r['name'])}</b><br>Yarın bu saatte: {tr_num(r['pm25'], 0)} µg/m³"
            f"<br>{escape(r['category'])}"
            + ("<br><b>Uyarı</b>" if r["is_alert"] else "")
            + ("<br>Uyarı riski: aralığın üst sınırı 35,5'i aşıyor"
               if r["risk"] and not r["is_alert"] else "")
            for r in rows]
    ring = [t.danger if r["is_alert"] else t.warn if r["risk"] else t.surface for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Scattermap(lat=df["lat"], lon=df["lon"], mode="markers", name="halka",
                                marker={"size": 36, "color": ring, "opacity": 0.9},
                                hoverinfo="skip", showlegend=False))
    df["hover"] = text
    df["ink"] = [CATEGORY_TEXT_COLORS.get(c, "#000") for c in df["category"]]
    # Scattermap yazı rengi nokta başına verilemez: yazı rengine göre ayrı izler
    for ink, part in df.groupby("ink", sort=False):
        fig.add_trace(go.Scattermap(
            lat=part["lat"], lon=part["lon"], mode="markers+text", name="istasyonlar",
            marker={"size": 30, "color": [category_color(c) for c in part["category"]]},
            text=[tr_num(v, 0) for v in part["pm25"]], textposition="middle center",
            textfont={"size": 12, "color": ink},
            hovertext=list(part["hover"]), hoverinfo="text", showlegend=False))
    style = "carto-darkmatter" if t.name == "dark" else "carto-positron"
    view = ({"center": {"lat": 39.75, "lon": 30.0}, "zoom": 4.75} if narrow
            else {"center": {"lat": 39.8, "lon": 30.1}, "zoom": 5.65})
    fig.update_layout(**plotly_layout(
        t, height=340 if narrow else 430, map={"style": style, **view},
        margin={"l": 0, "r": 0, "t": 0, "b": 0}))
    return fig


PCT_TICKS = {"tickvals": [0, 0.2, 0.4, 0.6, 0.8, 1.0],
             "ticktext": ["%0", "%20", "%40", "%60", "%80", "%100"]}   # Türkçe: %80


def pr_figure(curves: dict, operating: dict | None, t: Tokens = LIGHT) -> go.Figure:
    """Uyarı yakalama (recall) / doğru uyarı oranı (precision) dengesi. Yüzdeler Türkçe
    biçimde ('%80') önceden metne çevrilir; Plotly'nin '.0%' biçimi '80%' üretir."""
    fig = go.Figure()
    styles = {"lgbm_gercekci": {"color": t.data, "width": 3},
              "lgbm_iyimser": {"color": t.data, "width": 1.5, "dash": "dot"}}
    hover = ("Karar eşiği: %{customdata[0]} µg/m³<br>Yakalama: %{customdata[1]}"
             "<br>İsabet: %{customdata[2]}<extra></extra>")
    for m, c in curves["pr"].items():
        custom = [[tr_num(th), tr_pct(r), tr_pct(p)]
                  for th, r, p in zip(c["threshold"], c["recall"], c["precision"], strict=True)]
        fig.add_trace(go.Scatter(
            x=c["recall"], y=c["precision"], mode="lines", name=MODEL_LABELS.get(m, m),
            line=styles.get(m, {}), customdata=custom, hovertemplate=hover))
    symbols = {"persistence": "square", "cams_raw": "x", "cams_scaled": "diamond"}
    for m, p in curves["points"].items():
        fig.add_trace(go.Scatter(
            x=[p["recall"]], y=[p["precision"]], mode="markers+text", name=MODEL_LABELS[m],
            text=[MODEL_LABELS[m]], textposition="bottom center",
            textfont={"color": t.muted, "size": 11},
            marker={"size": 11, "symbol": symbols[m], "color": t.muted},
            hovertemplate=(f"Yakalama: {tr_pct(p['recall'])}<br>İsabet: "
                           f"{tr_pct(p['precision'])}<extra>{MODEL_LABELS[m]}</extra>")))
    if operating:
        fig.add_trace(go.Scatter(
            x=[operating["recall"]], y=[operating["precision"]], mode="markers+text",
            name="Canlı sistem (istasyon eşikleri)", text=["canlı sistem"],
            textposition="top right", textfont={"color": t.text, "size": 11},
            marker={"size": 14, "color": t.data, "line": {"color": t.surface, "width": 2}},
            hovertemplate=(f"Yakalama: {tr_pct(operating['recall'])}<br>İsabet: "
                           f"{tr_pct(operating['precision'])}<extra>Canlı sistem</extra>")))
    fig.update_layout(**plotly_layout(
        t, height=380, legend={"orientation": "h", "y": -0.22, "x": 0},
        margin={"l": 8, "r": 24, "t": 8, "b": 8},
        xaxis={"title": {"text": "yakalanan uyarı oranı (recall)"}, "range": [0, 1.02],
               **PCT_TICKS},
        yaxis={"title": {"text": "doğru uyarı oranı (precision)"}, "range": [0, 1.02],
               **PCT_TICKS}))
    return fig


def calibration_figure(curves: dict, t: Tokens = LIGHT) -> go.Figure:
    c = curves["calibration"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[0, 120], y=[0, 120], mode="lines", name="kusursuz tahmin",
                             line={"color": t.muted, "dash": "dot", "width": 1},
                             hoverinfo="skip"))
    styles = {"lgbm_gercekci": {"color": t.data, "width": 3},
              "persistence": {"color": t.muted, "width": 1.5, "dash": "dash"},
              "cams_raw": {"color": t.increase, "width": 1.5}}
    for m in ("lgbm_gercekci", "persistence", "cams_raw"):
        fig.add_trace(go.Scatter(x=c["true_mid"], y=c[m], mode="lines",
                                 name=MODEL_LABELS[m], line=styles[m],
                                 hovertemplate="Gerçek: %{x:.1f} µg/m³<br>Ortalama tahmin: "
                                               "%{y:.1f} µg/m³<extra>" + MODEL_LABELS[m]
                                               + "</extra>"))
    fig.update_layout(**plotly_layout(
        t, height=380, legend={"orientation": "h", "y": -0.22, "x": 0},
        xaxis={"title": {"text": "gerçek PM2.5 (µg/m³)"}, "range": [0, 120]},
        yaxis={"title": {"text": "ortalama tahmin (µg/m³)"}, "range": [0, 120]}))
    return fig


def families_figure(shares: dict[str, float], t: Tokens = LIGHT) -> go.Figure:
    items = sorted(shares.items(), key=lambda kv: kv[1])
    fig = go.Figure(go.Bar(
        x=[v for _, v in items], y=[k for k, _ in items], orientation="h",
        marker={"color": [t.data if v >= 10 else t.muted for _, v in items], "cornerradius": 4},
        text=[f"%{tr_num(v)}" for _, v in items], textposition="outside",
        textfont={"color": t.text}, hovertemplate="%{y}: %%{x:.1f}<extra></extra>"))
    fig.update_layout(**plotly_layout(
        t, height=320, showlegend=False, bargap=0.35,
        xaxis={"title": {"text": "tahmine katkı payı (%)"},
               "range": [0, max(v for _, v in items) * 1.2]},
        yaxis={"tickfont": {"color": t.text}}))
    return fig
