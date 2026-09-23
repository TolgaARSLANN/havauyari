"""Tasarım sistemi (ui-ux-pro-max önerisinden uyarlandı): Minimalizm / İsviçre stili.

- Nötr renkler: slate skalası; açık ve koyu tema birlikte tanımlı, metin kontrastı ≥ 4.5:1.
- Durum renkleri: YALNIZCA EPA AQI renkleri; her zaman metin + ikonla birlikte kullanılır.
- Veri rengi: mavi (#2563EB); katkı grafiğinde renk körlüğüne uygun turuncu/mavi.
- Tipografi: Fira Sans (metin), Fira Code (büyük sayılar); tablolarda sabit genişlikli rakamlar.
- İkonlar: Lucide SVG (MIT), emoji yok. Hareket: yalnızca 200 ms hover geçişleri,
  prefers-reduced-motion'da kapalı.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Tokens:
    name: str
    bg: str
    surface: str
    surface_alt: str
    text: str
    muted: str
    border: str
    grid: str
    data: str            # tahmin / vurgu mavisi
    data_soft: str       # bant dolgusu
    measured: str        # ölçüm çizgisi
    increase: str        # katkı: artırır
    decrease: str        # katkı: azaltır
    warn: str
    danger: str
    ok: str


LIGHT = Tokens(
    name="light", bg="#F8FAFC", surface="#FFFFFF", surface_alt="#F1F5F9", text="#0F172A",
    muted="#475569", border="#E2E8F0", grid="#E2E8F0", data="#2563EB",
    data_soft="rgba(37,99,235,0.15)", measured="#0F172A", increase="#C2410C",
    decrease="#1D4ED8", warn="#B45309", danger="#B91C1C", ok="#15803D")

DARK = Tokens(
    name="dark", bg="#0F172A", surface="#1B2336", surface_alt="#27304A", text="#F8FAFC",
    muted="#A6B3C6", border="#334155", grid="#2A3446", data="#60A5FA",
    data_soft="rgba(96,165,250,0.18)", measured="#F8FAFC", increase="#FB923C",
    decrease="#60A5FA", warn="#FBBF24", danger="#F87171", ok="#4ADE80")


def tokens_for(theme_type: str | None) -> Tokens:
    return DARK if theme_type == "dark" else LIGHT


# ---------------------------------------------------------------------------------------------
# İkonlar (Lucide, MIT lisansı): yalnızca path içerikleri; svg() ile sarılır
# ---------------------------------------------------------------------------------------------
_ICON_PATHS = {
    "wind": '<path d="M12.8 19.6A2 2 0 1 0 14 16H2"/><path d="M17.5 8a2.5 2.5 0 1 1 2 4H2"/>'
            '<path d="M9.8 4.4A2 2 0 1 1 11 8H2"/>',
    "alert": '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 '
             '1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
    "shield": '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 '
              '13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 '
              '19 5a1 1 0 0 1 1 1z"/><path d="m9 12 2 2 4-4"/>',
    "eye": '<path d="M2.06 12.35a1 1 0 0 1 0-.7 10.75 10.75 0 0 1 19.88 0 1 1 0 0 1 0 .7 '
           '10.75 10.75 0 0 1-19.88 0"/><circle cx="12" cy="12" r="3"/>',
    "heart": '<path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 '
             '2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/>',
    "clock": '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
    "pin": '<path d="M20 10c0 4.99-5.54 10.19-7.4 11.79a1 1 0 0 1-1.2 0C9.54 20.19 4 14.99 4 '
           '10a8 8 0 0 1 16 0"/><circle cx="12" cy="10" r="3"/>',
    "info": '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
    "activity": '<path d="M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 '
                '2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2"/>',
}


def svg(name: str, size: int = 18, color: str = "currentColor") -> str:
    """Dekoratif ikon: yanında her zaman görünür metin olduğu için aria-hidden."""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
            f'viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" '
            f'focusable="false" style="flex:none">{_ICON_PATHS[name]}</svg>')


# ---------------------------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------------------------
FONT_IMPORT = ("@import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@500;600"
               "&family=Fira+Sans:wght@400;500;600;700&display=swap');")


def css(t: Tokens) -> str:
    return f"""<style>
{FONT_IMPORT}
:root {{
  --hu-bg:{t.bg}; --hu-surface:{t.surface}; --hu-surface-alt:{t.surface_alt};
  --hu-text:{t.text}; --hu-muted:{t.muted}; --hu-border:{t.border}; --hu-data:{t.data};
  --hu-warn:{t.warn}; --hu-danger:{t.danger}; --hu-ok:{t.ok};
  --hu-radius:12px; --hu-space-1:4px; --hu-space-2:8px; --hu-space-3:12px; --hu-space-4:16px;
  --hu-space-6:24px; --hu-space-8:32px;
}}
html, body, [class*="st-"], .stMarkdown, .stText, button, input, select, textarea {{
  font-family: 'Fira Sans', system-ui, -apple-system, 'Segoe UI', sans-serif;
}}
.block-container {{ max-width: 1240px; padding-top: 1.5rem; padding-bottom: 3rem; }}
#MainMenu, footer, [data-testid="stToolbarActions"] {{ visibility: hidden; }}
h1, h2, h3, h4 {{ font-weight: 650; letter-spacing: -0.01em; color: var(--hu-text); }}

/* --- Başlık -------------------------------------------------------------------------- */
.hu-header {{ display:flex; justify-content:space-between; align-items:flex-end; gap:16px;
  flex-wrap:wrap; padding-bottom:var(--hu-space-4); border-bottom:1px solid var(--hu-border);
  margin-bottom:var(--hu-space-4); }}
.hu-brand {{ display:flex; align-items:center; gap:12px; }}
.hu-logo {{ width:44px; height:44px; flex:none; align-self:center; aspect-ratio:1;
  border-radius:12px; display:grid; place-items:center; background:var(--hu-data); color:#fff; }}
.stMarkdown h1.hu-title {{ font-size:1.75rem !important; font-weight:700; line-height:1.15 !important;
  margin:0 !important; padding:0 !important; color:var(--hu-text); }}
.stMarkdown h2.hu-section-title {{ font-size:1.15rem !important; font-weight:650 !important;
  line-height:1.3 !important; padding:0 !important; margin:var(--hu-space-6) 0 var(--hu-space-2) !important; }}
.hu-subtitle {{ font-size:0.95rem; color:var(--hu-muted); margin:2px 0 0; }}
.hu-status {{ display:flex; align-items:center; gap:8px; font-size:0.875rem; color:var(--hu-muted);
  background:var(--hu-surface); border:1px solid var(--hu-border); padding:6px 12px;
  border-radius:999px; }}
.hu-dot {{ width:8px; height:8px; border-radius:50%; flex:none; }}

/* --- Kartlar ------------------------------------------------------------------------- */
.hu-card {{ background:var(--hu-surface); border:1px solid var(--hu-border);
  border-radius:var(--hu-radius); padding:var(--hu-space-4) var(--hu-space-4); height:100%; }}
.hu-kpi {{ margin-bottom:var(--hu-space-2); }}
.hu-kpi-label {{ font-size:0.8rem; font-weight:500; text-transform:uppercase; letter-spacing:.04em;
  color:var(--hu-muted); display:flex; align-items:center; gap:6px; }}
.hu-kpi-value {{ font-family:'Fira Code', ui-monospace, monospace;
  font-size:clamp(1.2rem, 1.9vw, 1.75rem); white-space:nowrap;
  font-weight:600; color:var(--hu-text); margin-top:6px; line-height:1.15;
  font-variant-numeric: tabular-nums; }}
.hu-kpi-sub {{ font-size:0.85rem; color:var(--hu-muted); margin-top:4px; }}

.hu-grid {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(260px, 1fr));
  gap:var(--hu-space-3); }}
.hu-station {{ transition: border-color 200ms ease, box-shadow 200ms ease; }}
.hu-station:hover {{ border-color:var(--hu-data); box-shadow:0 1px 8px rgba(15,23,42,.08); }}
.hu-station-head {{ display:flex; justify-content:space-between; gap:8px; align-items:flex-start; }}
.hu-station-head > div:first-child {{ min-width:0; }}
.hu-station-name {{ font-weight:600; font-size:0.98rem; color:var(--hu-text); line-height:1.3; }}
.hu-station-city {{ font-size:0.8rem; color:var(--hu-muted); display:flex; gap:4px;
  align-items:center; margin-top:2px; }}
.hu-station-value {{ font-family:'Fira Code', ui-monospace, monospace; font-size:1.9rem;
  font-weight:600; color:var(--hu-text); margin:10px 0 2px; font-variant-numeric:tabular-nums; }}
.hu-unit {{ font-family:'Fira Sans', sans-serif; font-size:0.85rem; font-weight:500;
  color:var(--hu-muted); margin-left:4px; }}
.hu-row {{ display:flex; gap:8px; align-items:center; flex-wrap:wrap; margin-top:8px; }}
.hu-meta {{ font-size:0.82rem; color:var(--hu-muted); font-variant-numeric:tabular-nums; }}

/* --- Rozetler: renk + metin (+ ikon) --------------------------------------------------- */
.hu-chip {{ display:inline-flex; align-items:center; gap:6px; padding:3px 10px;
  border-radius:999px; font-size:0.8rem; font-weight:600; line-height:1.4; white-space:nowrap; }}
.hu-chip-swatch {{ width:10px; height:10px; border-radius:50%; border:1px solid rgba(0,0,0,.25); }}
.hu-flag {{ display:inline-flex; align-items:center; gap:5px; font-size:0.8rem; font-weight:600;
  padding:3px 9px; border-radius:6px; border:1px solid currentColor; white-space:nowrap; flex:none; }}
.hu-legend {{ display:flex; flex-wrap:wrap; gap:8px 16px; font-size:0.82rem; color:var(--hu-muted);
  margin:8px 0 4px; }}
.hu-legend span {{ display:inline-flex; align-items:center; gap:6px; }}

/* --- Tahmin kartı ---------------------------------------------------------------------- */
.hu-hero-value {{ font-family:'Fira Code', ui-monospace, monospace; font-size:3.4rem;
  font-weight:600; line-height:1; color:var(--hu-text); font-variant-numeric:tabular-nums; }}
.hu-range {{ position:relative; height:10px; border-radius:999px; background:var(--hu-surface-alt);
  margin:26px 0 22px; }}
.hu-range-band {{ position:absolute; top:0; bottom:0; border-radius:999px; background:var(--hu-data);
  opacity:.35; }}
.hu-range-point {{ position:absolute; top:-4px; width:4px; height:18px; border-radius:2px;
  background:var(--hu-data); transform:translateX(-2px); }}
.hu-range-thr {{ position:absolute; top:-8px; bottom:-8px; width:0; border-left:2px dashed
  {"#FF7E00"}; }}
.hu-range-label {{ position:absolute; top:-22px; font-size:0.72rem; color:var(--hu-muted);
  transform:translateX(-50%); white-space:nowrap; }}
.hu-range-axis {{ position:absolute; top:16px; font-size:0.72rem; color:var(--hu-muted);
  transform:translateX(-50%); font-variant-numeric:tabular-nums; }}
.hu-callout {{ display:flex; gap:10px; align-items:flex-start; padding:12px 14px; border-radius:10px;
  border:1px solid; font-size:0.92rem; line-height:1.5; margin-top:12px; }}
.hu-section-title {{ font-size:1.15rem; font-weight:650; color:var(--hu-text);
  margin:var(--hu-space-6) 0 var(--hu-space-2); }}
.hu-lead {{ color:var(--hu-muted); font-size:0.95rem; line-height:1.6; max-width:75ch; }}
.hu-footer {{ margin-top:var(--hu-space-8); padding-top:var(--hu-space-4);
  border-top:1px solid var(--hu-border); font-size:0.82rem; color:var(--hu-muted); line-height:1.6; }}

/* --- Sekmeler ------------------------------------------------------------------------ */
.stTabs [data-baseweb="tab-list"] {{ gap:4px; border-bottom:1px solid var(--hu-border); }}
.stTabs [data-baseweb="tab"] {{ height:44px; padding:0 16px; font-weight:500; }}
.stTabs [aria-selected="true"] {{ color:var(--hu-data); }}
.stTabs [data-baseweb="tab-highlight"] {{ background-color:var(--hu-data); }}
[data-testid="stPlotlyChart"], [data-testid="stDataFrame"] {{
  border:1px solid var(--hu-border); border-radius:var(--hu-radius); padding:6px;
  background:var(--hu-surface); }}
:focus-visible {{ outline:2px solid var(--hu-data) !important; outline-offset:2px; }}
@media (prefers-reduced-motion: reduce) {{ * {{ transition:none !important; animation:none !important; }} }}
@media (max-width: 640px) {{
  .stMarkdown h1.hu-title {{ font-size:1.4rem !important; }} .hu-hero-value {{ font-size:2.6rem; }}
  .block-container {{ padding-left:1rem; padding-right:1rem; }}
}}
</style>"""


# ---------------------------------------------------------------------------------------------
# Plotly
# ---------------------------------------------------------------------------------------------
def plotly_layout(t: Tokens, **overrides) -> dict:
    base = {
        "font": {"family": "Fira Sans, system-ui, sans-serif", "color": t.text, "size": 13},
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "margin": {"l": 8, "r": 8, "t": 8, "b": 8},
        "hoverlabel": {"bgcolor": t.surface, "bordercolor": t.border,
                       "font": {"family": "Fira Sans, sans-serif", "color": t.text}},
        "xaxis": {"gridcolor": t.grid, "linecolor": t.border, "zeroline": False,
                  "tickfont": {"color": t.muted}},
        "yaxis": {"gridcolor": t.grid, "linecolor": t.border, "zeroline": False,
                  "tickfont": {"color": t.muted}, "title": {"font": {"color": t.muted}}},
        "legend": {"font": {"color": t.muted, "size": 12}, "bgcolor": "rgba(0,0,0,0)"},
        "separators": ",.",   # Türkçe: ondalık virgül, binlik nokta
    }
    for k, v in overrides.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            base[k] = {**base[k], **v}
        else:
            base[k] = v
    return base
