"""Tasarım sistemi (ui-ux-pro-max önerisinden uyarlandı): "gerçek zamanlı operasyon" panosu.

- Nötr renkler: slate skalası; açık ve koyu tema birlikte tanımlı, metin kontrastı ≥ 4.5:1.
- Durum renkleri: AQI kategori renkleri; her zaman metin ve/veya ikonla birlikte kullanılır.
- Veri rengi: mavi (#2563EB); katkı grafiğinde renk körlüğüne uygun turuncu/mavi.
- Tipografi: Fira Sans (metin), Fira Code (büyük sayılar); sayılarda sabit genişlikli rakamlar.
- İkonlar: Lucide SVG (MIT), emoji yok.
- Hareket: tek bir yumuşak "belirme" (opacity + transform, 30–60 ms kademeli), 150–280 ms
  hover geçişleri; prefers-reduced-motion'da tamamen kapalı.
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
    name="light", bg="#F6F8FB", surface="#FFFFFF", surface_alt="#EEF2F7", text="#0F172A",
    muted="#475569", border="#E2E8F0", grid="#E9EEF5", data="#2563EB",
    data_soft="rgba(37,99,235,0.14)", measured="#0F172A", increase="#C2410C",
    decrease="#1D4ED8", warn="#B45309", danger="#B91C1C", ok="#15803D")

DARK = Tokens(
    name="dark", bg="#0B1220", surface="#141C2E", surface_alt="#1F2940", text="#F8FAFC",
    muted="#A6B3C6", border="#2A3550", grid="#222C42", data="#60A5FA",
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
    "database": '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5V19A9 3 0 0 0 21 19V5"/>'
                '<path d="M3 12A9 3 0 0 0 21 12"/>',
    "layers": '<path d="M12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 '
              '0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83z"/><path d="M2 12a1 1 0 0 0 .58.91l8.6 '
              '3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 12"/><path d="M2 17a1 1 0 0 0 '
              '.58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 17"/>',
    "cpu": '<rect width="16" height="16" x="4" y="4" rx="2"/><rect width="6" height="6" x="9" '
           'y="9" rx="1"/><path d="M15 2v2"/><path d="M15 20v2"/><path d="M2 15h2"/>'
           '<path d="M2 9h2"/><path d="M20 15h2"/><path d="M20 9h2"/><path d="M9 2v2"/>'
           '<path d="M9 20v2"/>',
    "sliders": '<path d="M21 4h-7"/><path d="M10 4H3"/><path d="M21 12h-9"/><path d="M8 12H3"/>'
               '<path d="M21 20h-5"/><path d="M12 20H3"/><path d="M14 2v4"/><path d="M8 10v4"/>'
               '<path d="M16 18v4"/>',
    "bell": '<path d="M10.268 21a2 2 0 0 0 3.464 0"/><path d="M3.262 15.326A1 1 0 0 0 4 17h16a1 '
            '1 0 0 0 .74-1.673C19.41 13.956 18 12.499 18 8A6 6 0 0 0 6 8c0 4.499-1.411 '
            '5.956-2.738 7.326"/>',
    "target": '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/>'
              '<circle cx="12" cy="12" r="2"/>',
    "trending_down": '<path d="M16 17h6v-6"/><path d="m22 17-8.5-8.5-5 5L2 7"/>',
    "external": '<path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 '
                '2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>',
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

EASE = "cubic-bezier(.2,.8,.2,1)"


def css(t: Tokens) -> str:
    shadow = ("0 1px 2px rgba(15,23,42,.04), 0 4px 16px -6px rgba(15,23,42,.08)"
              if t.name == "light" else "0 1px 2px rgba(0,0,0,.3), 0 8px 24px -10px rgba(0,0,0,.5)")
    shadow_hi = ("0 2px 4px rgba(15,23,42,.05), 0 14px 32px -12px rgba(15,23,42,.18)"
                 if t.name == "light"
                 else "0 2px 4px rgba(0,0,0,.35), 0 16px 36px -12px rgba(0,0,0,.6)")
    return f"""<style>
{FONT_IMPORT}
:root {{
  --hu-bg:{t.bg}; --hu-surface:{t.surface}; --hu-surface-alt:{t.surface_alt};
  --hu-text:{t.text}; --hu-muted:{t.muted}; --hu-border:{t.border}; --hu-data:{t.data};
  --hu-warn:{t.warn}; --hu-danger:{t.danger}; --hu-ok:{t.ok};
  --hu-radius:16px; --hu-radius-sm:10px; --hu-shadow:{shadow}; --hu-shadow-hi:{shadow_hi};
  --hu-space-1:4px; --hu-space-2:8px; --hu-space-3:12px; --hu-space-4:16px;
  --hu-space-6:24px; --hu-space-8:32px; --hu-ease:{EASE};
}}
/* Yazı tipi: ikon öğeleri HARİÇ. Streamlit ikonları "Material Symbols" yazı tipinin
   bitişik harfleriyle çizer ("keyboard_arrow_right" -> ok); bu yazı tipi ezilirse ikon adı
   düz metin olarak görünür ve başlıkla çakışır. */
html, body, .stApp,
.stApp :is(p, li, label, a, h1, h2, h3, h4, h5, h6, button, input, select, textarea, td, th, div,
           span:not([data-testid="stIconMaterial"]):not([data-testid="stExpanderIcon"])) {{
  font-family: 'Fira Sans', system-ui, -apple-system, 'Segoe UI', sans-serif;
}}
[data-testid="stIconMaterial"], [data-testid="stExpanderIcon"], .material-symbols-rounded {{
  font-family: 'Material Symbols Rounded' !important; font-weight: normal; font-style: normal;
  letter-spacing: normal; text-transform: none; white-space: nowrap;
}}
/* Genel kuraldaki span:not(...) önceliği (0,2,1) olduğu için sayı yazı tipi !important ister */
.stApp :is(code, pre, .hu-kpi-value, .hu-station-value, .hu-hero-value, .hu-stat-value,
           .hu-rank-value, .hu-bar-value, .hu-step-num) {{
  font-family: 'Fira Code', ui-monospace, monospace !important;
}}
.stApp :is(.hu-unit, .hu-stat-value small) {{ font-family: 'Fira Sans', system-ui, sans-serif !important; }}
.stApp {{
  background:
    radial-gradient(1100px 420px at 8% -8%, color-mix(in srgb, var(--hu-data) 9%, transparent), transparent 70%),
    radial-gradient(900px 380px at 100% 0%, color-mix(in srgb, #22C55E 6%, transparent), transparent 70%),
    var(--hu-bg);
}}
.block-container {{ max-width: 1280px; padding-top: 1.25rem; padding-bottom: 3rem; }}
#MainMenu, footer, [data-testid="stToolbarActions"] {{ visibility: hidden; }}
[data-testid="stHeader"] {{ background: transparent; }}
h1, h2, h3, h4 {{ font-weight: 650; letter-spacing: -0.01em; color: var(--hu-text); }}
.stMarkdown a {{ color: var(--hu-data); text-underline-offset: 3px; }}

@keyframes hu-rise {{ from {{ opacity:0; transform:translateY(8px); }} to {{ opacity:1; transform:none; }} }}
@keyframes hu-grow {{ from {{ transform:scaleX(0); }} to {{ transform:scaleX(1); }} }}
@keyframes hu-pulse {{ 0% {{ box-shadow:0 0 0 0 currentColor; }} 70%, 100% {{ box-shadow:0 0 0 6px transparent; }} }}

/* --- Başlık -------------------------------------------------------------------------- */
.hu-header {{ display:flex; justify-content:space-between; align-items:center; gap:16px;
  flex-wrap:wrap; margin-bottom:var(--hu-space-6); }}
.hu-brand {{ display:flex; align-items:center; gap:14px; }}
.hu-logo {{ width:46px; height:46px; flex:none; border-radius:14px; display:grid; place-items:center;
  background:linear-gradient(135deg, #3B82F6 0%, #1D4ED8 60%, #1E3A8A 100%);
  box-shadow:0 6px 16px -6px rgba(37,99,235,.55), inset 0 1px 0 rgba(255,255,255,.25); }}
.stMarkdown h1.hu-title {{ font-size:1.6rem !important; font-weight:700 !important; line-height:1.1 !important;
  margin:0 !important; padding:0 !important; color:var(--hu-text); letter-spacing:-0.02em; }}
.hu-subtitle {{ font-size:0.92rem; color:var(--hu-muted); margin:3px 0 0; }}
.hu-status {{ display:flex; align-items:center; gap:8px; font-size:0.85rem; color:var(--hu-muted);
  background:var(--hu-surface); border:1px solid var(--hu-border); padding:7px 14px;
  border-radius:999px; box-shadow:var(--hu-shadow); font-variant-numeric:tabular-nums; }}
.hu-status-sep {{ width:1px; height:14px; background:var(--hu-border); }}
.hu-dot {{ width:8px; height:8px; border-radius:50%; flex:none; }}
.hu-dot-live {{ animation:hu-pulse 2s ease-out infinite; }}

/* --- Yükleme iskeleti ------------------------------------------------------------------ */
@keyframes hu-shimmer {{ from {{ background-position:-600px 0; }} to {{ background-position:600px 0; }} }}
.hu-skeleton {{ display:flex; flex-direction:column; gap:16px; }}
.hu-skel {{ border-radius:var(--hu-radius); border:1px solid var(--hu-border);
  background:linear-gradient(90deg, var(--hu-surface) 0%, var(--hu-surface-alt) 40%, var(--hu-surface) 80%);
  background-size:1200px 100%; animation:hu-shimmer 1.4s linear infinite; }}
.hu-skel-row {{ display:grid; grid-template-columns:7fr 5fr; gap:24px; }}
.hu-skel-cards {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(220px, 1fr)); gap:16px; }}
.hu-skel-note {{ font-size:0.88rem; color:var(--hu-muted); }}
.hu-sr {{ position:absolute; width:1px; height:1px; overflow:hidden; clip:rect(0 0 0 0); white-space:nowrap; }}

/* --- Özet bant (hero) --------------------------------------------------------------- */
.hu-hero {{ position:relative; overflow:hidden; display:grid;
  grid-template-columns:minmax(0,1.45fr) minmax(0,1fr); gap:28px; align-items:end;
  padding:28px 30px; border-radius:22px; border:1px solid var(--hu-border);
  background:
    radial-gradient(700px 260px at 0% 0%, var(--hu-glow), transparent 70%),
    var(--hu-surface);
  box-shadow:var(--hu-shadow); margin-bottom:var(--hu-space-6);
  animation:hu-rise 420ms var(--hu-ease) both; }}
.hu-eyebrow {{ display:inline-flex; align-items:center; gap:6px; font-size:0.78rem; font-weight:600;
  text-transform:uppercase; letter-spacing:.06em; color:var(--hu-muted); }}
.hu-hero-title {{ display:flex; align-items:center; gap:12px; font-size:1.65rem;
  line-height:1.2; font-weight:700; letter-spacing:-0.02em; margin:14px 0 8px; color:var(--hu-text); }}
.hu-hero-icon {{ width:40px; height:40px; flex:none; border-radius:12px; display:grid; place-items:center;
  color:var(--hu-tone); background:color-mix(in srgb, var(--hu-tone) 12%, transparent);
  border:1px solid color-mix(in srgb, var(--hu-tone) 30%, transparent); }}
.hu-hero-lead {{ color:var(--hu-muted); font-size:0.98rem; line-height:1.55; margin:0 0 18px; max-width:62ch; }}
.hu-hero-lead b {{ color:var(--hu-text); font-weight:600; }}
.hu-dist {{ display:flex; gap:3px; height:10px; border-radius:999px; overflow:hidden; }}
.hu-dist-seg {{ transform-origin:left; animation:hu-grow 700ms var(--hu-ease) both 150ms; }}
.hu-dist-legend {{ display:flex; flex-wrap:wrap; gap:6px 16px; margin-top:10px; font-size:0.85rem;
  color:var(--hu-muted); }}
.hu-dist-legend > span {{ display:inline-flex; align-items:center; gap:6px; }}
.hu-dist-legend b {{ color:var(--hu-text); font-variant-numeric:tabular-nums; }}
.hu-hero-stats {{ display:grid; grid-template-columns:repeat(3, minmax(0,1fr));
  background:color-mix(in srgb, var(--hu-surface) 70%, transparent); backdrop-filter:blur(8px);
  border:1px solid var(--hu-border); border-radius:16px; }}
.hu-stat {{ padding:14px 16px; min-width:0; }}
.hu-stat + .hu-stat {{ border-left:1px solid var(--hu-border); }}
.hu-stat-label {{ font-size:0.75rem; font-weight:600; text-transform:uppercase; letter-spacing:.05em;
  color:var(--hu-muted); }}
.hu-stat-value {{ font-size:1.9rem; font-weight:600; line-height:1.15; margin-top:6px;
  font-variant-numeric:tabular-nums; white-space:nowrap; }}
.hu-stat-value small {{ font-size:0.9rem; font-weight:500; color:var(--hu-muted); margin-left:2px; }}
.hu-stat-sub {{ font-size:0.78rem; color:var(--hu-muted); margin-top:4px; line-height:1.35; }}

/* --- Bölüm başlıkları ------------------------------------------------------------------ */
.stMarkdown h2.hu-section-title {{ font-size:1.12rem !important; font-weight:650 !important;
  line-height:1.3 !important; padding:0 !important; margin:var(--hu-space-6) 0 2px !important; }}
.hu-lead {{ color:var(--hu-muted); font-size:0.92rem; line-height:1.6; max-width:75ch; margin:0 0 12px; }}
.hu-meta {{ font-size:0.82rem; color:var(--hu-muted); font-variant-numeric:tabular-nums; line-height:1.55; }}

/* --- Genel kart ve KPI ---------------------------------------------------------------- */
.hu-card {{ background:var(--hu-surface); border:1px solid var(--hu-border); box-shadow:var(--hu-shadow);
  border-radius:var(--hu-radius); padding:18px 20px; }}
.hu-kpi {{ height:100%; margin-bottom:var(--hu-space-2); animation:hu-rise 420ms var(--hu-ease) both; }}
.hu-kpi-label {{ font-size:0.78rem; font-weight:600; text-transform:uppercase; letter-spacing:.05em;
  color:var(--hu-muted); display:flex; align-items:center; gap:8px; }}
.hu-kpi-icon {{ width:28px; height:28px; border-radius:8px; display:grid; place-items:center;
  color:var(--hu-data); background:color-mix(in srgb, var(--hu-data) 10%, transparent); }}
.hu-kpi-value {{ font-size:clamp(1.4rem, 2.1vw, 2rem); white-space:nowrap;
  font-weight:600; color:var(--hu-text); margin-top:10px; line-height:1.1; font-variant-numeric:tabular-nums; }}
.hu-kpi-sub {{ font-size:0.84rem; color:var(--hu-muted); margin-top:6px; }}

/* Yan yana kartlar aynı yükseklikte: sütundan karta kadar tüm kaplar tam boy */
[data-testid="stColumn"]:has(.hu-eq) :is([data-testid="stVerticalBlock"], [data-testid="stElementContainer"],
  .stMarkdown, [data-testid="stMarkdownContainer"]) {{ height:100%; }}
.hu-eq {{ height:100%; box-sizing:border-box; }}

/* --- Sıralama (tek ölçekte tüm istasyonlar) --------------------------------------------- */
.hu-rank ol {{ list-style:none; margin:0; padding:0; display:flex; flex-direction:column; gap:6px; }}
.hu-rank-row, .hu-rank-axis {{ display:grid; grid-template-columns:minmax(120px, 44%) 1fr 30px;
  gap:12px; align-items:center; }}
.hu-rank-row {{ min-height:34px; padding:2px 6px; margin:0 -6px; border-radius:8px;
  animation:hu-rise 380ms var(--hu-ease) both; animation-delay:calc(var(--i) * 45ms);
  transition:background-color 150ms ease; }}
.hu-rank-row:hover {{ background:var(--hu-surface-alt); }}
.hu-rank-name {{ font-size:0.86rem; color:var(--hu-text); white-space:nowrap; overflow:hidden;
  text-overflow:ellipsis; display:flex; align-items:center; gap:5px; }}
.hu-rank-flag {{ display:inline-flex; flex:none; }}
.hu-rank-track {{ position:relative; height:10px; border-radius:999px; }}
.hu-rank-band {{ position:absolute; top:0; bottom:0; border-radius:999px; }}
.hu-rank-thr {{ position:absolute; top:-5px; bottom:-5px; border-left:1.5px dashed #F97316; }}
.hu-rank-dot {{ position:absolute; top:50%; width:14px; height:14px; border-radius:50%;
  transform:translate(-50%,-50%); border:2px solid var(--hu-surface);
  box-shadow:0 0 0 1px rgba(15,23,42,.35), 0 2px 6px rgba(15,23,42,.2); }}
.hu-rank-value {{ font-size:0.95rem; font-weight:600; text-align:right; color:var(--hu-text);
  font-variant-numeric:tabular-nums; }}
.hu-rank-axis {{ margin-top:6px; font-size:0.72rem; color:var(--hu-muted); }}
.hu-rank-ticks {{ position:relative; height:16px; }}
.hu-rank-ticks > * {{ position:absolute; transform:translateX(-50%); font-variant-numeric:tabular-nums; }}
.hu-rank-ticks em {{ top:14px; font-style:normal; color:#C2410C; white-space:nowrap; }}
.hu-rank-axis > span:last-child {{ text-align:right; }}

/* --- İstasyon kartları: Streamlit kabı kartın kendisidir (düğme kartın içinde kalır) ----- */
[class*="st-key-card-"] {{
  background:var(--hu-surface); border:1px solid var(--hu-border); border-radius:var(--hu-radius);
  box-shadow:var(--hu-shadow); padding:16px 16px 6px; gap:4px !important; position:relative;
  overflow:hidden; transition:transform 200ms var(--hu-ease), box-shadow 200ms ease, border-color 200ms ease;
  animation:hu-rise 420ms var(--hu-ease) both;
}}
[class*="st-key-card-"]::before {{ content:""; position:absolute; inset:0 0 auto 0; height:3px;
  background:var(--hu-cat, var(--hu-border)); }}
[class*="st-key-card-"]:hover {{ transform:translateY(-2px); box-shadow:var(--hu-shadow-hi);
  border-color:color-mix(in srgb, var(--hu-data) 45%, var(--hu-border)); }}
[class*="st-key-card-"] [data-testid="stButton"] {{ border-top:1px solid var(--hu-border); margin-top:6px; }}
[class*="st-key-card-"] [data-testid="stButton"] button {{ width:100%; min-height:42px; border-radius:0;
  color:var(--hu-data); padding:0 2px; }}
[class*="st-key-card-"] [data-testid="stButton"] button > div,
[class*="st-key-card-"] [data-testid="stButton"] button > div > span {{ width:100%; display:flex;
  justify-content:space-between; align-items:center; }}
[class*="st-key-card-"] [data-testid="stButton"] button p {{ font-weight:600; font-size:0.86rem; }}
[class*="st-key-card-"] [data-testid="stButton"] [data-testid="stIconMaterial"] {{
  transition:transform 200ms var(--hu-ease); }}
[class*="st-key-card-"]:hover [data-testid="stButton"] [data-testid="stIconMaterial"] {{ transform:translateX(3px); }}
[class*="st-key-card-"] [data-testid="stButton"] button:hover {{ color:var(--hu-text); }}
.hu-station-head {{ display:flex; justify-content:space-between; gap:8px; align-items:flex-start; }}
.hu-station-head > div:first-child {{ min-width:0; }}
.hu-station-name {{ font-weight:600; font-size:0.98rem; color:var(--hu-text); line-height:1.3; }}
.hu-station-city {{ font-size:0.78rem; color:var(--hu-muted); display:flex; gap:4px;
  align-items:center; margin-top:3px; }}
.hu-station-mid {{ display:flex; justify-content:space-between; align-items:center; gap:8px;
  margin-top:12px; flex-wrap:wrap; }}
.hu-station-value {{ font-size:2.1rem; font-weight:600; line-height:1; color:var(--hu-text);
  font-variant-numeric:tabular-nums; letter-spacing:-0.02em; }}
.hu-unit {{ font-size:0.82rem; font-weight:500; color:var(--hu-muted); margin-left:5px; letter-spacing:0; }}
.hu-spark {{ display:block; width:100%; height:56px; margin:12px 0 8px; overflow:visible; }}
.hu-station-foot {{ display:flex; justify-content:space-between; gap:8px; font-size:0.8rem;
  color:var(--hu-muted); font-variant-numeric:tabular-nums; }}
.hu-station-foot b {{ color:var(--hu-text); font-weight:600; }}

/* --- Rozetler: renk + metin (+ ikon) --------------------------------------------------- */
.hu-chip {{ display:inline-flex; align-items:center; gap:6px; padding:4px 10px;
  border-radius:999px; font-size:0.8rem; font-weight:600; line-height:1.3; white-space:nowrap; }}
.hu-chip-swatch {{ width:10px; height:10px; border-radius:50%; flex:none;
  box-shadow:inset 0 0 0 1px rgba(15,23,42,.2); }}
.hu-flag {{ display:inline-flex; align-items:center; gap:5px; font-size:0.78rem; font-weight:600;
  padding:4px 9px; border-radius:999px; white-space:nowrap; flex:none;
  border:1px solid color-mix(in srgb, currentColor 35%, transparent); }}
.hu-flag-quiet {{ border-color:transparent; padding-right:0; }}
.hu-legend {{ display:flex; flex-wrap:wrap; gap:6px 14px; font-size:0.8rem; color:var(--hu-text);
  margin:10px 2px 0; }}
.hu-legend > span {{ display:inline-flex; align-items:center; gap:6px; }}
.hu-legend em {{ font-style:normal; color:var(--hu-muted); font-variant-numeric:tabular-nums; }}

/* --- Tahmin kartı ---------------------------------------------------------------------- */
.hu-forecast {{ animation:hu-rise 420ms var(--hu-ease) both; }}
.hu-forecast-top {{ display:flex; justify-content:space-between; align-items:flex-start; gap:12px; flex-wrap:wrap; }}
.hu-hero-value {{ font-size:4rem; font-weight:600; line-height:.95; color:var(--hu-text);
  font-variant-numeric:tabular-nums; letter-spacing:-0.03em; }}
.hu-range {{ position:relative; height:12px; border-radius:999px; margin:34px 0 26px; }}
.hu-range-band {{ position:absolute; top:0; bottom:0; border-radius:999px; background:var(--hu-data);
  opacity:.45; }}
.hu-range-point {{ position:absolute; top:50%; width:18px; height:18px; border-radius:50%;
  background:var(--hu-data); transform:translate(-50%,-50%); border:3px solid var(--hu-surface);
  box-shadow:0 0 0 1px var(--hu-data), 0 2px 8px rgba(37,99,235,.4); }}
.hu-range-thr {{ position:absolute; top:-8px; bottom:-8px; width:0; border-left:2px dashed #F97316; }}
.hu-range-label {{ position:absolute; top:-26px; font-size:0.72rem; color:var(--hu-muted);
  transform:translateX(-50%); white-space:nowrap; }}
.hu-range-axis {{ position:absolute; top:18px; font-size:0.72rem; color:var(--hu-muted);
  transform:translateX(-50%); font-variant-numeric:tabular-nums; }}
.hu-callout {{ display:flex; gap:10px; align-items:flex-start; padding:12px 14px; border-radius:12px;
  font-size:0.92rem; line-height:1.55; margin-top:12px;
  background:color-mix(in srgb, var(--hu-c) 7%, var(--hu-surface));
  border:1px solid color-mix(in srgb, var(--hu-c) 28%, transparent); }}
.hu-callout-icon {{ margin-top:1px; display:inline-flex; }}

/* --- Saatlik şerit ---------------------------------------------------------------------- */
.hu-hours {{ margin:4px 0 6px; }}
.hu-hours-grid {{ display:grid; grid-template-columns:repeat(24, minmax(0,1fr)); gap:3px;
  align-items:end; height:64px; padding-bottom:18px; position:relative; }}
.hu-hour {{ position:relative; height:calc(18% + var(--h) * 82%); border-radius:5px 5px 3px 3px;
  background:color-mix(in srgb, var(--c) 85%, transparent); transform-origin:bottom;
  animation:hu-rise 360ms var(--hu-ease) both; transition:filter 150ms ease; }}
.hu-hour:hover {{ filter:brightness(1.08) saturate(1.2); outline:2px solid var(--hu-text); outline-offset:1px; }}
.hu-hour-lbl {{ position:absolute; bottom:-18px; left:0; font-size:0.7rem; color:var(--hu-muted);
  font-variant-numeric:tabular-nums; }}
.hu-hours-note {{ display:flex; align-items:center; gap:6px; font-size:0.85rem; color:var(--hu-muted);
  margin-top:10px; }}
.hu-hours-note b {{ color:var(--hu-text); }}

/* --- Model: hata karşılaştırması -------------------------------------------------------- */
.hu-bars {{ list-style:none; margin:0; padding:0; display:flex; flex-direction:column; gap:10px; }}
.hu-bar-row {{ display:grid; grid-template-columns:minmax(140px, 38%) 1fr 48px; gap:12px; align-items:center;
  font-size:0.88rem; color:var(--hu-muted); }}
.hu-bar-track {{ height:12px; border-radius:999px; background:var(--hu-surface-alt); overflow:hidden; }}
.hu-bar-fill {{ display:block; height:100%; border-radius:999px; background:color-mix(in srgb, var(--hu-muted) 55%, transparent);
  transform-origin:left; animation:hu-grow 700ms var(--hu-ease) both; animation-delay:calc(var(--i) * 60ms); }}
.hu-bar-value {{ text-align:right; font-variant-numeric:tabular-nums; }}
.hu-bar-ours {{ color:var(--hu-text); font-weight:600; }}
.hu-bar-ours .hu-bar-fill {{ background:linear-gradient(90deg, #3B82F6, var(--hu-data)); }}
.hu-bar-ours .hu-bar-value {{ color:var(--hu-data); }}
.hu-big {{ font-family:'Fira Code', ui-monospace, monospace; font-size:3rem; font-weight:600;
  line-height:1; color:var(--hu-data); letter-spacing:-0.03em; }}

/* --- Hakkında: akış adımları ------------------------------------------------------------ */
.hu-steps {{ list-style:none; margin:8px 0 0; padding:0; display:grid;
  grid-template-columns:repeat(auto-fit, minmax(190px, 1fr)); gap:12px; }}
.hu-step {{ position:relative; display:flex; flex-direction:column; gap:6px; padding:16px;
  border-radius:var(--hu-radius); background:var(--hu-surface); border:1px solid var(--hu-border);
  box-shadow:var(--hu-shadow); font-size:0.86rem; color:var(--hu-muted); line-height:1.5;
  animation:hu-rise 420ms var(--hu-ease) both; animation-delay:calc(var(--i) * 60ms); }}
.hu-step b {{ color:var(--hu-text); font-size:0.98rem; }}
.hu-step-icon {{ width:36px; height:36px; border-radius:10px; display:grid; place-items:center;
  color:var(--hu-data); background:color-mix(in srgb, var(--hu-data) 10%, transparent); }}
.hu-step-num {{ position:absolute; top:16px; right:16px; font-size:0.78rem; color:var(--hu-muted); }}
.hu-prose {{ color:var(--hu-muted); font-size:0.95rem; line-height:1.65; }}
.hu-prose b {{ color:var(--hu-text); }}
.hu-footer {{ margin-top:var(--hu-space-8); padding-top:var(--hu-space-4);
  border-top:1px solid var(--hu-border); font-size:0.8rem; color:var(--hu-muted); line-height:1.6; }}

/* --- Sekmeler: segmentli kontrol + kayan seçim zemini ------------------------------------
   Streamlit 1.64 sekmeleri react-aria ile çizer. Tek bir SelectionIndicator öğesi seçili
   sekmeye 'translate' geçişiyle taşınır; onu alt çizgi yerine sekmenin arkasındaki "hap"
   zemine dönüştürüyoruz, böylece seçim sekmeler arasında kayar (mekânsal süreklilik). */
[data-testid="stTabs"] [role="tablist"] {{
  display:inline-flex; gap:4px; padding:5px; width:auto; max-width:100%;
  background:var(--hu-surface-alt); border:1px solid var(--hu-border); border-radius:14px;
  overflow-x:auto; scrollbar-width:none; margin-bottom:var(--hu-space-4);
}}
[data-testid="stTabs"] [role="tablist"]::-webkit-scrollbar {{ display:none; }}
[data-testid="stTab"] {{
  position:relative; height:40px; padding:0 16px; border-radius:10px; cursor:pointer;
  color:var(--hu-muted); white-space:nowrap; transition:color 200ms ease, background-color 200ms ease;
}}
[data-testid="stTab"] > :not(.react-aria-SelectionIndicator) {{ position:relative; z-index:1; }}
[data-testid="stTab"] p {{ font-weight:500; color:inherit; margin:0; font-size:0.92rem; }}
[data-testid="stTab"]:hover:not([data-selected="true"]) {{
  color:var(--hu-text); background:color-mix(in srgb, var(--hu-surface) 55%, transparent);
}}
[data-testid="stTab"][data-selected="true"] {{ color:var(--hu-data); }}
[data-testid="stTab"][data-selected="true"] p {{ font-weight:600; }}
[data-testid="stTab"] [data-testid="stIconMaterial"] {{ font-size:1.15rem; }}
.stApp [data-testid="stTabs"] [data-testid="stTab"] .react-aria-SelectionIndicator {{
  position:absolute !important; inset:0 !important; width:auto !important; height:auto !important;
  z-index:0 !important; border-radius:10px !important;
  background:var(--hu-surface) !important;
  box-shadow:0 1px 2px rgba(15,23,42,.10), 0 1px 3px rgba(15,23,42,.06) !important;
  transition:translate 280ms var(--hu-ease) !important;
}}
@keyframes hu-panel-in {{ from {{ opacity:0; transform:translateY(6px); }}
                         to {{ opacity:1; transform:none; }} }}
[data-testid="stTabPanel"]:not([inert]) {{ animation:hu-panel-in 240ms var(--hu-ease); }}

/* --- İstasyon seçimi (pills) ---------------------------------------------------------- */
[data-testid="stButtonGroup"] button {{ border-radius:999px !important; min-height:36px;
  transition:background-color 150ms ease, color 150ms ease, border-color 150ms ease; }}

/* --- Grafik kapları ------------------------------------------------------------------- */
[data-testid="stPlotlyChart"], [data-testid="stDataFrame"] {{
  border:1px solid var(--hu-border); border-radius:var(--hu-radius); padding:8px;
  background:var(--hu-surface); box-shadow:var(--hu-shadow); overflow:hidden; }}
[data-testid="stExpander"] details {{ border-radius:var(--hu-radius); border-color:var(--hu-border);
  background:var(--hu-surface); }}
:focus-visible {{ outline:2px solid var(--hu-data) !important; outline-offset:2px; }}
@media (prefers-reduced-motion: reduce) {{ * {{ transition:none !important; animation:none !important; }} }}
@media (max-width: 900px) {{
  .hu-hero {{ grid-template-columns:1fr; padding:22px 20px; gap:20px; }}
}}
.st-key-map-narrow {{ display:none; }}
@media (max-width: 640px) {{
  .st-key-map-wide {{ display:none; }} .st-key-map-narrow {{ display:block; }}
  .stMarkdown h1.hu-title {{ font-size:1.35rem !important; }}
  .hu-hero-title {{ font-size:1.3rem; }}
  .hu-hero-value {{ font-size:3rem; }}
  .hu-stat {{ padding:12px 10px; }} .hu-stat-value {{ font-size:1.45rem; }}
  .block-container {{ padding-left:1rem; padding-right:1rem; }}
  /* Sıralama: ad üstte tam genişlikte, çubuk ve değer altta */
  .hu-rank-row {{ grid-template-columns:1fr 30px; grid-template-areas:"name name" "track value";
    row-gap:4px; padding:6px 6px; }}
  .hu-rank-name {{ grid-area:name; }} .hu-rank-track {{ grid-area:track; }}
  .hu-rank-value {{ grid-area:value; }}
  .hu-rank-axis {{ grid-template-columns:1fr 30px; }} .hu-rank-axis > span:first-child {{ display:none; }}
  .hu-bar-row {{ grid-template-columns:minmax(110px, 42%) 1fr 44px; }}
  .hu-hour-lbl {{ font-size:0.62rem; }}
}}
</style>"""


def card_rules(styles: dict[str, str]) -> str:
    """Kart kaplarına kategori rengi ve kademeli belirme gecikmesi (kap satır içi stil almaz).
    styles: {streamlit_key: kategori rengi}."""
    rules = "".join(f".st-key-{k}{{--hu-cat:{c};animation-delay:{i * 45}ms}}"
                    for i, (k, c) in enumerate(styles.items()))
    return f"<style>{rules}</style>"


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
