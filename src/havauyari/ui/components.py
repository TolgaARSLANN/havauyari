"""Panonun saf (Streamlit'ten bağımsız, test edilebilir) parçaları: renkler, metinler, grafikler."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from havauyari.alerts.aqi import CATEGORIES, PM25_BREAKPOINTS

# US EPA AQI renkleri
CATEGORY_COLORS = {
    "İyi": "#00e400",
    "Orta": "#ffff00",
    "Hassas gruplar için sağlıksız": "#ff7e00",
    "Sağlıksız": "#ff0000",
    "Çok sağlıksız": "#8f3f97",
    "Tehlikeli": "#7e0023",
}
CATEGORY_TEXT_COLORS = {c: ("#000000" if c in ("İyi", "Orta", "Hassas gruplar için sağlıksız")
                            else "#ffffff") for c in CATEGORIES}

# Genel bilgilendirme (US EPA AQI rehberinden özetlenmiştir; tıbbi tavsiye değildir)
ADVICE = {
    "İyi": "Hava kalitesi iyi. Dış mekân etkinlikleri için uygun.",
    "Orta": "Hava kalitesi kabul edilebilir. Kirliliğe olağandışı duyarlı kişiler uzun süreli "
            "ağır dış mekân eforunu azaltmayı düşünebilir.",
    "Hassas gruplar için sağlıksız": "Astım, kalp ya da akciğer hastalığı olanlar, yaşlılar ve "
            "çocuklar uzun süreli veya ağır dış mekân eforunu azaltmalı.",
    "Sağlıksız": "Herkes uzun süreli ağır dış mekân eforunu azaltmalı; hassas gruplar dış "
            "mekân eforundan kaçınmalı.",
    "Çok sağlıksız": "Herkes dış mekân eforundan kaçınmalı; hassas gruplar mümkünse içeride "
            "kalmalı.",
    "Tehlikeli": "Herkes dış mekân etkinliklerinden kaçınmalı ve mümkünse içeride kalmalı.",
}
DISCLAIMER = ("Bu tahminler bir makine öğrenmesi modelinden gelir; bilgilendirme amaçlıdır, "
              "resmî hava kalitesi uyarılarının ve sağlık tavsiyesinin yerine geçmez.")

CITY_LABELS = {"istanbul": "İstanbul", "ankara": "Ankara", "izmir": "İzmir", "bursa": "Bursa",
               "kocaeli": "Kocaeli"}

# Sık görülen özelliklerin okunur adları
FEATURE_LABELS = {
    "station_pm25": "istasyonun şu anki ölçümü",
    "station_pm25_lag1": "1 saat önceki ölçüm",
    "station_pm25_lag2": "2 saat önceki ölçüm",
    "station_pm25_lag3": "3 saat önceki ölçüm",
    "station_pm25_lag24": "24 saat önceki ölçüm",
    "station_pm25_lag168": "1 hafta önceki ölçüm",
    "station_pm25_tgt_day_ago": "hedef saatin dünkü ölçümü",
    "station_pm25_tgt_week_ago": "hedef saatin geçen haftaki ölçümü",
    "station_pm25_rollmean24": "son 24 saatin ortalaması",
    "station_pm25_rollmean168": "son 1 haftanın ortalaması",
    "station_pm25_rollmax24": "son 24 saatin en yüksek değeri",
    "station_pm25_rollstd168": "son 1 haftanın dalgalanması",
    "station_pm10": "istasyonun PM10 ölçümü",
    "fc_win_wind_mean": "önümüzdeki 24 saatin tahmini ortalama rüzgârı",
    "fc_win_wind_min": "önümüzdeki 24 saatin tahmini en zayıf rüzgârı",
    "fc_win_calm_hours": "önümüzdeki 24 saatte tahmini durgun saat sayısı",
    "fc_win_precip_sum": "önümüzdeki 24 saatin tahmini yağışı",
    "fc_win_temp_range": "önümüzdeki 24 saatin tahmini sıcaklık farkı",
    "fc_win_temp_min": "önümüzdeki 24 saatin tahmini en düşük sıcaklığı",
    "fc_win_cloud_mean": "önümüzdeki 24 saatin tahmini bulutluluğu",
    "fc_tgt_humidity": "hedef saatin tahmini nemi",
    "fc_tgt_wind_speed": "hedef saatin tahmini rüzgârı",
    "fc_tgt_wind_u": "hedef saatin tahmini rüzgâr yönü (doğu-batı)",
    "fc_tgt_wind_v": "hedef saatin tahmini rüzgâr yönü (kuzey-güney)",
    "fc_tgt_temperature": "hedef saatin tahmini sıcaklığı",
    "fc_tgt_temp_change": "tahmini sıcaklık değişimi",
    "fc_tgt_pressure_change": "tahmini basınç değişimi",
    "fc_tgt_cloud_cover": "hedef saatin tahmini bulutluluğu",
    "surface_pressure": "şu anki hava basıncı",
    "heating_degree_rollmean24": "son 24 saatin ısınma ihtiyacı",
    "calm_hours24": "son 24 saatteki durgun saat sayısı",
    "wind_speed_rollmean24": "son 24 saatin ortalama rüzgârı",
    "hour_sin": "günün saati", "hour_cos": "günün saati",
    "tgt_hour_sin": "hedef saat", "tgt_hour_cos": "hedef saat",
    "month_sin": "mevsim", "month_cos": "mevsim",
    "dayofweek": "haftanın günü", "tgt_dayofweek": "hedef günün haftadaki yeri",
    "station_code": "istasyonun kendine özgü seviyesi",
    "city_code": "şehrin kendine özgü seviyesi",
}


def feature_label(name: str) -> str:
    return FEATURE_LABELS.get(name, name)


def tr_num(x: float, digits: int = 1, sign: bool = False) -> str:
    """Türkçe ondalık biçimi: 6.78 -> '6,78'; sign=True: '+0,9' / '−2,8'."""
    s = f"{abs(x):.{digits}f}".replace(".", ",")
    if sign:
        return ("+" if x > 0 else "−" if x < 0 else "") + s
    return ("−" if x < 0 else "") + s


def category_color(category: str) -> str:
    return CATEGORY_COLORS.get(category, "#cccccc")


def explanation_sentence(explanation: dict) -> str:
    """Katkılardan sade Türkçe özet cümle."""
    feats = explanation["top_features"]
    up = [f for f in feats if f["contribution"] > 0]
    down = [f for f in feats if f["contribution"] < 0]
    parts = []
    if up:
        top = max(up, key=lambda f: f["contribution"])
        parts.append(f"Tahmini en çok **{feature_label(top['feature'])}** yükseltiyor "
                     f"({tr_num(top['contribution'], sign=True)} µg/m³)")
    if down:
        top = min(down, key=lambda f: f["contribution"])
        parts.append(f"en çok **{feature_label(top['feature'])}** düşürüyor "
                     f"({tr_num(top['contribution'], sign=True)} µg/m³)")
    if not parts:
        return "Belirgin bir etken yok; tahmin ortalamaya yakın."
    sentence = "; ".join(parts) + "."
    return sentence[0].upper() + sentence[1:]


# ---------------------------------------------------------------------------------------------
# Grafikler
# ---------------------------------------------------------------------------------------------
def _aqi_bands(fig: go.Figure, y_max: float) -> None:
    for c_lo, c_hi, _i_lo, _i_hi, name in PM25_BREAKPOINTS:
        if c_lo > y_max:
            break
        fig.add_hrect(y0=c_lo, y1=min(c_hi + 0.1, y_max), fillcolor=category_color(name),
                      opacity=0.12, line_width=0, layer="below")


def forecast_figure(forecast: dict) -> go.Figure:
    """Son 72 saat ölçüm + aynı dönemin 24 s önceden verilmiş tahminleri + önümüzdeki 24 saat."""
    hist = pd.DataFrame(forecast["history"])
    traj = pd.DataFrame(forecast["trajectory"])
    now = pd.Timestamp(forecast["issued_at"])
    fig = go.Figure()
    if not traj.empty:
        traj["target_time"] = pd.to_datetime(traj["target_time"])
        past = traj[traj["target_time"] <= now]
        future = traj[traj["target_time"] > now]
        fig.add_trace(go.Scatter(
            x=list(future["target_time"]) + list(future["target_time"][::-1]),
            y=list(future["high"]) + list(future["low"][::-1]), fill="toself",
            fillcolor="rgba(31,119,180,0.18)", line={"width": 0}, hoverinfo="skip",
            name="%80 aralık"))
        fig.add_trace(go.Scatter(x=past["target_time"], y=past["pm25"], mode="lines",
                                 line={"color": "#1f77b4", "dash": "dot", "width": 1.5},
                                 name="24 s önceden verilmiş tahmin"))
        fig.add_trace(go.Scatter(x=future["target_time"], y=future["pm25"], mode="lines",
                                 line={"color": "#1f77b4", "width": 3},
                                 name="önümüzdeki 24 saat tahmini"))
    if not hist.empty:
        hist["time"] = pd.to_datetime(hist["time"])
        fig.add_trace(go.Scatter(x=hist["time"], y=hist["pm25"], mode="lines",
                                 line={"color": "#222222", "width": 2}, name="ölçüm"))
    y_values = pd.concat([hist.get("pm25", pd.Series(dtype=float)),
                          traj.get("high", pd.Series(dtype=float))]).dropna()
    y_max = max(60.0, float(y_values.max()) * 1.1 if len(y_values) else 60.0)
    _aqi_bands(fig, y_max)
    fig.add_hline(y=35.5, line={"color": "#ff7e00", "dash": "dash", "width": 1},
                  annotation_text="uyarı eşiği 35,5", annotation_position="top left")
    fig.add_vline(x=now, line={"color": "grey", "width": 1})
    fig.update_layout(height=420, margin={"l": 10, "r": 10, "t": 30, "b": 10},
                      yaxis={"title": "PM2.5 (µg/m³)", "range": [0, y_max]},
                      legend={"orientation": "h", "y": -0.18}, hovermode="x unified")
    return fig


def explanation_figure(explanation: dict) -> go.Figure:
    feats = explanation["top_features"][::-1]
    labels = [feature_label(f["feature"]) for f in feats]
    values = [f["contribution"] for f in feats]
    fig = go.Figure(go.Bar(x=values, y=labels, orientation="h",
                           marker_color=["#d62728" if v > 0 else "#2ca02c" for v in values],
                           text=[tr_num(v, sign=True) for v in values], textposition="outside"))
    fig.add_vline(x=0, line={"color": "black", "width": 1})
    fig.update_layout(height=260, margin={"l": 10, "r": 30, "t": 10, "b": 10},
                      xaxis={"title": "tahmine katkı (µg/m³)"})
    return fig


def map_figure(rows: list[dict]) -> go.Figure:
    """İstasyonlar, yarınki tahmin kategorisinin rengiyle."""
    df = pd.DataFrame(rows)
    fig = go.Figure(go.Scattermap(
        lat=df["lat"], lon=df["lon"], mode="markers",
        marker={"size": 18, "color": [category_color(c) for c in df["category"]], "opacity": 0.9},
        text=[f"<b>{r['name']}</b><br>Yarın: {tr_num(r['pm25'], 0)} µg/m³ ({r['category']})"
              + ("<br>⚠️ uyarı" if r["is_alert"] else "")
              + ("<br>risk: aralık üst sınırı ≥ 35,5" if r["risk"] else "")
              for r in rows],
        hoverinfo="text"))
    fig.update_layout(map={"style": "carto-positron", "center": {"lat": 39.6, "lon": 30.5},
                           "zoom": 5.2},
                      height=480, margin={"l": 0, "r": 0, "t": 0, "b": 0})
    return fig
