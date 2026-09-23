"""Tasarım sistemi: "Parçacık Defteri" (docs/tasarim/parcacik-defteri.md, levha: .png).

Bir gözlem defterinin sayfası: sıcak kâğıt zemin, is karası mürekkep, kıl inceliğinde
cetvel çizgileri. Temel birim noktadır; PM2.5 değeri, noktaların yoğunluğuyla gösterilir.

- Renk: kâğıt / mürekkep / grafit nötrleri; AQI kategorileri doğal pigmentler (adaçayı,
  hardal, pas, tuğla, mürdüm, bordo). Köz kırmızısı yalnızca sınır (resmî eşik) ve uyarı
  içindir. Gece temasında zemin mürekkebe, mürekkep kâğıda döner. Metin kontrastı ≥ 4.5:1.
- Tipografi: Instrument Serif (dev rakamlar ve başlıklar), Instrument Sans (metin),
  IBM Plex Mono (etiketler, ölçekler, harf aralıklı büyük harf). Orta büyüklükte ses yok.
- Yapı: kutu ve gölge yerine boşluk ve ince çizgiler. İkonlar: Lucide SVG (MIT), emoji yok.
- Hareket: tek bir yumuşak belirme (opacity + transform, kademeli); prefers-reduced-motion'da
  kapalı.
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
    data: str            # tahmin mürekkebi (çivit)
    data_soft: str       # aralık bandı
    measured: str        # ölçüm çizgisi
    increase: str        # katkı: artırır
    decrease: str        # katkı: azaltır
    warn: str
    danger: str          # köz: resmî eşik ve uyarı
    ok: str


LIGHT = Tokens(
    name="light", bg="#F3EFE7", surface="#FAF8F3", surface_alt="#EAE4D8", text="#1C1B19",
    muted="#5F5A52", border="#D6CFC2", grid="#E4DED2", data="#2B4C7E",
    data_soft="rgba(43,76,126,0.13)", measured="#1C1B19", increase="#B23A0E",
    decrease="#2B4C7E", warn="#8A5A00", danger="#B23A0E", ok="#35704A")

DARK = Tokens(
    name="dark", bg="#12110F", surface="#191815", surface_alt="#24221E", text="#EDE7DC",
    muted="#A8A194", border="#35322B", grid="#25231F", data="#93B4E6",
    data_soft="rgba(147,180,230,0.16)", measured="#EDE7DC", increase="#F08A5D",
    decrease="#93B4E6", warn="#E2B64E", danger="#F2825A", ok="#8CC79B")

EMBER_LINE = "#C4401A"      # resmî eşik çizgisi (her iki temada seçilir)


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


def svg(name: str, size: int = 18, color: str = "currentColor", stroke: float = 1.75) -> str:
    """Dekoratif ikon: yanında her zaman görünür metin olduğu için aria-hidden."""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
            f'viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="{stroke}" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" '
            f'focusable="false" style="flex:none">{_ICON_PATHS[name]}</svg>')


# ---------------------------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------------------------
FONT_IMPORT = ("@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500"
               "&family=Instrument+Sans:wght@400;500;600&family=Instrument+Serif:ital@0;1"
               "&display=swap');")

EASE = "cubic-bezier(.2,.8,.2,1)"
SERIF = "'Instrument Serif', 'Iowan Old Style', Georgia, serif"
SANS = "'Instrument Sans', system-ui, -apple-system, 'Segoe UI', sans-serif"
MONO = "'IBM Plex Mono', ui-monospace, 'SFMono-Regular', monospace"


def css(t: Tokens) -> str:
    grain = ("rgba(28,27,25,.035)" if t.name == "light" else "rgba(237,231,220,.025)")
    return f"""<style>
{FONT_IMPORT}
:root {{
  --hu-bg:{t.bg}; --hu-surface:{t.surface}; --hu-surface-alt:{t.surface_alt};
  --hu-text:{t.text}; --hu-muted:{t.muted}; --hu-border:{t.border}; --hu-data:{t.data};
  --hu-warn:{t.warn}; --hu-danger:{t.danger}; --hu-ok:{t.ok}; --hu-ember:{EMBER_LINE};
  --hu-serif:{SERIF}; --hu-sans:{SANS}; --hu-mono:{MONO}; --hu-ease:{EASE};
  --hu-radius:4px; --hu-space-2:8px; --hu-space-4:16px; --hu-space-6:24px; --hu-space-8:32px;
}}
/* Yazı tipi: ikon öğeleri HARİÇ. Streamlit ikonları "Material Symbols" yazı tipinin
   bitişik harfleriyle çizer ("keyboard_arrow_right" -> ok); bu yazı tipi ezilirse ikon adı
   düz metin olarak görünür ve başlıkla çakışır. */
html, body, .stApp,
.stApp :is(p, li, label, a, h1, h2, h3, h4, h5, h6, button, input, select, textarea, td, th, div,
           span:not([data-testid="stIconMaterial"]):not([data-testid="stExpanderIcon"])) {{
  font-family: {SANS};
}}
[data-testid="stIconMaterial"], [data-testid="stExpanderIcon"], .material-symbols-rounded {{
  font-family: 'Material Symbols Rounded' !important; font-weight: normal; font-style: normal;
  letter-spacing: normal; text-transform: none; white-space: nowrap;
}}
/* Genel kuraldaki span:not(...) önceliği yüksek olduğu için yazı tipi sınıfları !important ister */
.stApp :is(.hu-serif, .hu-title, .hu-hero-title, .hu-big, .hu-num, .hu-kpi-value, .hu-hero-value,
           .hu-station-value, .hu-step-num, .hu-section-title),
.stApp :is(.hu-title, .hu-hero-title, .hu-section-title) :not(svg):not(svg *) {{
  font-family: {SERIF} !important; }}
.stApp :is(.hu-mono, .hu-eyebrow, .hu-kpi-label, .hu-label, .hu-meta-mono, .hu-station-code,
           .hu-rank-value-cat, .hu-status, .hu-legend, .hu-axis, .hu-bar-value, code, pre) {{
  font-family: {MONO} !important; }}
.stApp {{
  background-color: var(--hu-bg);
  background-image: radial-gradient({grain} 1px, transparent 1px);
  background-size: 22px 22px;
}}
.block-container {{ max-width: 1240px; padding-top: 2.2rem; padding-bottom: 4rem; }}
#MainMenu, footer, [data-testid="stToolbarActions"] {{ visibility: hidden; }}
[data-testid="stHeader"] {{ background: transparent; }}
.stMarkdown a {{ color: var(--hu-text); text-decoration-color: var(--hu-ember); text-underline-offset: 3px; }}
.stMarkdown p {{ color: var(--hu-text); }}

@keyframes hu-rise {{ from {{ opacity:0; transform:translateY(6px); }} to {{ opacity:1; transform:none; }} }}
@keyframes hu-fade {{ from {{ opacity:0; }} to {{ opacity:1; }} }}
@keyframes hu-pulse {{ 0% {{ box-shadow:0 0 0 0 currentColor; }} 70%, 100% {{ box-shadow:0 0 0 5px transparent; }} }}

/* --- Ortak dil: mono etiket, ince çizgi, dev serif rakam ------------------------------ */
.hu-label, .hu-eyebrow, .hu-kpi-label {{ font-size:0.72rem; font-weight:500; letter-spacing:.14em;
  text-transform:uppercase; color:var(--hu-muted); display:flex; align-items:center; gap:8px; }}
.hu-eyebrow b, .hu-label b {{ color:var(--hu-text); font-weight:500; }}
/* Birim büyük harfe çevrilmez: text-transform µ'yü Yunanca büyük Mu'ya (Μ) çevirir, "MG/M³" olur */
.hu-u {{ text-transform:none !important; letter-spacing:.04em; }}
.hu-rule {{ height:1px; background:var(--hu-text); margin:0; border:0; }}
.hu-rule-soft {{ height:1px; background:var(--hu-border); margin:0; border:0; }}
.hu-meta {{ font-size:0.84rem; color:var(--hu-muted); line-height:1.6; }}
.hu-meta b {{ color:var(--hu-text); font-weight:600; }}
.hu-lead {{ color:var(--hu-muted); font-size:0.95rem; line-height:1.65; max-width:68ch; margin:6px 0 16px; }}
.hu-lead b {{ color:var(--hu-text); font-weight:600; }}

/* --- Künye (başlık) ------------------------------------------------------------------- */
.hu-header {{ margin-bottom:var(--hu-space-6); animation:hu-fade 500ms var(--hu-ease) both; }}
.hu-header-top {{ display:flex; justify-content:space-between; align-items:center; gap:12px;
  flex-wrap:wrap; padding-bottom:10px; }}
.hu-header-main {{ display:flex; justify-content:space-between; align-items:flex-end; gap:24px;
  flex-wrap:wrap; padding:22px 0 18px; border-top:1px solid var(--hu-text); }}
.stMarkdown h1.hu-title {{ font-size:clamp(2.6rem, 6vw, 4.4rem) !important; font-weight:400 !important;
  line-height:.95 !important; letter-spacing:-0.015em; margin:0 !important; padding:0 !important;
  color:var(--hu-text); }}
.hu-title em {{ font-style:italic; }}
.hu-subtitle {{ font-size:0.98rem; color:var(--hu-muted); margin:10px 0 0; max-width:52ch; line-height:1.5; }}
.hu-status {{ display:flex; align-items:center; gap:10px; font-size:0.72rem; letter-spacing:.12em;
  text-transform:uppercase; color:var(--hu-muted); }}
.hu-status strong {{ font-weight:500; }}
.hu-dot {{ width:7px; height:7px; border-radius:50%; flex:none; display:inline-block; }}
.hu-dot-live {{ animation:hu-pulse 2.2s ease-out infinite; }}
.hu-colophon {{ text-align:right; }}
.hu-colophon div {{ font-family:{MONO} !important; font-size:0.72rem; letter-spacing:.12em;
  text-transform:uppercase; color:var(--hu-muted); line-height:1.9; }}
.hu-colophon div:first-child {{ color:var(--hu-text); }}

/* --- Sekmeler: mono, harf aralıklı; seçim bir mürekkep çizgisiyle kayar --------------- */
[data-testid="stTabs"] [role="tablist"] {{ gap:28px; border-bottom:1px solid var(--hu-border);
  margin-bottom:var(--hu-space-6); overflow-x:auto; scrollbar-width:none; }}
[data-testid="stTabs"] [role="tablist"]::-webkit-scrollbar {{ display:none; }}
[data-testid="stTab"] {{ height:44px; padding:0 2px; background:transparent !important;
  color:var(--hu-muted); white-space:nowrap; transition:color 200ms ease; }}
[data-testid="stTab"] p {{ font-family:{MONO} !important; font-size:0.74rem !important; font-weight:500;
  letter-spacing:.14em; text-transform:uppercase; color:inherit; margin:0; }}
[data-testid="stTab"]:hover {{ color:var(--hu-text); }}
[data-testid="stTab"][data-selected="true"] {{ color:var(--hu-text); }}
.stApp [data-testid="stTabs"] [data-testid="stTab"] .react-aria-SelectionIndicator {{
  background:var(--hu-text) !important; height:2px !important;
  transition:translate 320ms var(--hu-ease), width 320ms var(--hu-ease) !important; }}
@keyframes hu-panel-in {{ from {{ opacity:0; transform:translateY(4px); }} to {{ opacity:1; transform:none; }} }}
[data-testid="stTabPanel"]:not([inert]) {{ animation:hu-panel-in 260ms var(--hu-ease); }}

/* --- Levha (özet) ----------------------------------------------------------------------- */
.hu-hero {{ display:grid; grid-template-columns:minmax(0,1.5fr) minmax(0,1fr); gap:48px;
  align-items:end; padding:4px 0 28px; border-bottom:1px solid var(--hu-border);
  margin-bottom:var(--hu-space-6); animation:hu-rise 480ms var(--hu-ease) both; }}
.hu-hero-title {{ font-size:clamp(2.1rem, 4.2vw, 3.3rem); line-height:1.02; font-weight:400;
  letter-spacing:-0.01em; color:var(--hu-text); margin:14px 0 14px; }}
.hu-hero-title em {{ font-style:italic; color:var(--hu-tone); }}
.hu-hero-lead {{ color:var(--hu-muted); font-size:1rem; line-height:1.65; margin:0 0 22px; max-width:56ch; }}
.hu-hero-lead b {{ color:var(--hu-text); font-weight:600; }}
.hu-dist {{ display:flex; gap:8px; align-items:center; flex-wrap:wrap; }}
.hu-dist-dot {{ width:14px; height:14px; border-radius:50%; flex:none;
  animation:hu-rise 420ms var(--hu-ease) both; animation-delay:calc(var(--i) * 50ms + 150ms); }}
.hu-dist-legend {{ display:flex; flex-wrap:wrap; gap:6px 18px; margin-top:12px; font-family:{MONO} !important;
  font-size:0.72rem; letter-spacing:.12em; text-transform:uppercase; color:var(--hu-muted); }}
.hu-dist-legend > span {{ display:inline-flex; align-items:center; gap:7px; }}
.hu-dist-legend b {{ color:var(--hu-text); font-weight:500; }}
.hu-hero-side {{ border-left:1px solid var(--hu-border); padding-left:32px; }}
.hu-hero-value {{ font-size:clamp(5rem, 11vw, 8.5rem); line-height:.82; color:var(--hu-text);
  letter-spacing:-0.03em; display:flex; align-items:baseline; gap:10px; margin:10px 0 6px; }}
.hu-hero-value small {{ font-family:{MONO} !important; font-size:0.8rem; letter-spacing:.08em;
  color:var(--hu-muted); }}
.hu-hero-stats {{ display:grid; grid-template-columns:1fr 1fr; margin-top:18px; border-top:1px solid var(--hu-border); }}
.hu-stat {{ padding:12px 0 0; }}
.hu-stat + .hu-stat {{ padding-left:18px; border-left:1px solid var(--hu-border); }}
.hu-stat-value {{ font-family:{SERIF} !important; font-size:2.3rem; line-height:1; margin-top:6px; }}
.hu-stat-value small {{ font-family:{MONO} !important; font-size:0.78rem; color:var(--hu-muted); margin-left:3px; }}

/* --- Bölüm başlıkları ------------------------------------------------------------------ */
.hu-section {{ display:flex; align-items:baseline; gap:14px; margin:36px 0 4px;
  padding-top:14px; border-top:1px solid var(--hu-text); }}
.hu-section .hu-fig {{ font-family:{MONO} !important; font-size:0.72rem; letter-spacing:.14em;
  text-transform:uppercase; color:var(--hu-muted); white-space:nowrap; }}
.stMarkdown h2.hu-section-title {{ font-family:{SERIF} !important; font-size:1.9rem !important;
  font-weight:400 !important; line-height:1.1 !important; padding:0 !important; margin:0 !important;
  letter-spacing:-0.005em; }}

/* --- Şekil: parçacık bantları ----------------------------------------------------------- */
.hu-rank ol {{ list-style:none; margin:0; padding:0; }}
.hu-rank-row {{ display:grid; grid-template-columns:minmax(150px, 22%) 1fr 108px; gap:18px;
  align-items:center; padding:0; border-bottom:1px solid var(--hu-grid, var(--hu-border));
  animation:hu-fade 520ms var(--hu-ease) both; animation-delay:calc(var(--i) * 60ms); }}
.hu-rank-row:last-child {{ border-bottom:0; }}
.hu-rank-name {{ font-size:0.92rem; color:var(--hu-text); display:flex; flex-direction:column; gap:3px;
  min-width:0; }}
.hu-rank-name span {{ white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.hu-rank-name small {{ font-family:{MONO} !important; font-size:0.66rem; letter-spacing:.14em;
  text-transform:uppercase; color:var(--hu-muted); display:flex; align-items:center; gap:6px; }}
.hu-rank-flag {{ color:var(--hu-danger); }}
.hu-particles {{ display:block; width:100%; height:auto; }}
.hu-rank-value {{ display:flex; align-items:baseline; justify-content:flex-end; gap:10px; }}
.hu-rank-value .hu-num {{ font-size:2.5rem; line-height:1; color:var(--hu-text); }}
.hu-rank-value-cat {{ font-size:0.64rem; letter-spacing:.14em; text-transform:uppercase; color:var(--hu-muted);
  text-align:right; }}
.hu-axis {{ display:grid; grid-template-columns:minmax(150px, 22%) 1fr 108px; gap:18px;
  font-size:0.7rem; color:var(--hu-muted); margin-top:8px; }}
.hu-axis-ticks {{ position:relative; height:38px; border-top:1px solid var(--hu-text); }}
.hu-axis-ticks > span {{ position:absolute; top:6px; transform:translateX(-50%); }}
.hu-axis-ticks > em {{ position:absolute; top:22px; transform:translateX(-50%); font-style:normal;
  color:var(--hu-ember); white-space:nowrap; letter-spacing:.08em; }}
.hu-axis > span:first-child {{ padding-top:6px; letter-spacing:.1em; }}

/* --- Örnek kartları (istasyonlar) ------------------------------------------------------- */
[class*="st-key-card-"] {{
  background:var(--hu-surface); border:1px solid var(--hu-border); border-radius:var(--hu-radius);
  padding:18px 18px 4px; gap:2px !important; position:relative; overflow:hidden;
  transition:border-color 220ms ease, transform 220ms var(--hu-ease);
  animation:hu-rise 460ms var(--hu-ease) both;
}}
[class*="st-key-card-"]::before {{ content:""; position:absolute; left:18px; top:0; width:28px; height:3px;
  background:var(--hu-cat, var(--hu-border)); }}
[class*="st-key-card-"]:hover {{ border-color:var(--hu-text); transform:translateY(-2px); }}
[class*="st-key-card-"] [data-testid="stButton"] {{ border-top:1px solid var(--hu-border); margin-top:10px; }}
[class*="st-key-card-"] [data-testid="stButton"] button {{ width:100%; min-height:44px; border-radius:0;
  color:var(--hu-text); padding:0; background:transparent; }}
[class*="st-key-card-"] [data-testid="stButton"] button > div,
[class*="st-key-card-"] [data-testid="stButton"] button > div > span {{ width:100%; display:flex;
  justify-content:space-between; align-items:center; }}
[class*="st-key-card-"] [data-testid="stButton"] button p {{ font-family:{MONO} !important; font-size:0.72rem;
  font-weight:500; letter-spacing:.14em; text-transform:uppercase; }}
[class*="st-key-card-"] [data-testid="stButton"] [data-testid="stIconMaterial"] {{
  color:var(--hu-ember); transition:transform 220ms var(--hu-ease); }}
[class*="st-key-card-"]:hover [data-testid="stButton"] [data-testid="stIconMaterial"] {{ transform:translateX(4px); }}
.hu-station-head {{ display:flex; justify-content:space-between; gap:8px; align-items:flex-start; }}
.hu-station-code {{ font-size:0.68rem; letter-spacing:.16em; text-transform:uppercase; color:var(--hu-muted); }}
.hu-station-name {{ font-weight:600; font-size:0.98rem; color:var(--hu-text); line-height:1.3; margin-top:6px; }}
.hu-station-city {{ font-size:0.8rem; color:var(--hu-muted); margin-top:2px; }}
.hu-station-mid {{ display:flex; justify-content:space-between; align-items:flex-end; gap:8px; margin-top:10px; }}
.hu-station-value {{ font-size:3.6rem; line-height:.9; color:var(--hu-text); letter-spacing:-0.02em; }}
.hu-unit {{ font-family:{MONO} !important; font-size:0.72rem; font-weight:400; color:var(--hu-muted);
  margin-left:6px; letter-spacing:.06em; }}
.hu-spark {{ display:block; width:100%; height:52px; margin:14px 0 10px; overflow:visible; }}
.hu-station-foot {{ display:flex; justify-content:space-between; gap:8px; font-family:{MONO} !important;
  font-size:0.72rem; color:var(--hu-muted); letter-spacing:.04em; }}
.hu-station-foot b {{ color:var(--hu-text); font-weight:500; }}

/* --- Rozetler ----------------------------------------------------------------------- */
.hu-chip {{ display:inline-flex; align-items:center; gap:7px; font-family:{MONO} !important;
  font-size:0.68rem; font-weight:500; letter-spacing:.12em; text-transform:uppercase;
  line-height:1.3; white-space:nowrap; color:var(--hu-text); }}
.hu-chip-solid {{ padding:5px 10px; border-radius:2px; }}
.hu-chip-swatch {{ width:9px; height:9px; border-radius:50%; flex:none; }}
.hu-flag {{ display:inline-flex; align-items:center; gap:6px; font-family:{MONO} !important; font-size:0.66rem;
  font-weight:500; letter-spacing:.14em; text-transform:uppercase; white-space:nowrap; flex:none; }}
.hu-legend {{ display:flex; flex-wrap:wrap; gap:6px 18px; font-size:0.68rem; letter-spacing:.1em;
  text-transform:uppercase; color:var(--hu-text); margin:12px 0 0; }}
.hu-legend > span {{ display:inline-flex; align-items:center; gap:7px; }}
.hu-legend em {{ font-style:normal; color:var(--hu-muted); }}

/* --- İstasyon detayı ----------------------------------------------------------------- */
.hu-forecast {{ animation:hu-rise 460ms var(--hu-ease) both; }}
.hu-forecast .hu-hero-value {{ font-size:clamp(5.5rem, 10vw, 8rem); }}
.hu-forecast-meta {{ display:flex; gap:10px; align-items:center; flex-wrap:wrap; margin:6px 0 18px; }}
.hu-range {{ position:relative; height:10px; border-radius:1px; margin:34px 0 30px; }}
.hu-range-band {{ position:absolute; top:-3px; bottom:-3px; opacity:.75;
  background:repeating-linear-gradient(90deg, var(--hu-data) 0 1.5px, transparent 1.5px 5px);
  border-left:1.5px solid var(--hu-data); border-right:1.5px solid var(--hu-data); }}
.hu-range-point {{ position:absolute; top:-7px; bottom:-7px; width:2px; background:var(--hu-text);
  transform:translateX(-1px); }}
.hu-range-thr {{ position:absolute; top:-12px; bottom:-12px; width:0; border-left:1.5px solid var(--hu-ember); }}
.hu-range-label {{ position:absolute; top:-30px; font-family:{MONO} !important; font-size:0.66rem;
  letter-spacing:.1em; color:var(--hu-ember); transform:translateX(-50%); white-space:nowrap; }}
.hu-range-axis {{ position:absolute; top:18px; font-family:{MONO} !important; font-size:0.66rem;
  color:var(--hu-muted); transform:translateX(-50%); }}
.hu-callout {{ display:flex; gap:12px; align-items:flex-start; padding:12px 0 12px 16px;
  font-size:0.94rem; line-height:1.6; margin-top:14px; border-left:2px solid var(--hu-c); }}
.hu-callout-icon {{ margin-top:2px; display:inline-flex; }}
.hu-hours svg {{ display:block; width:100%; height:auto; }}
.hu-hours-note {{ display:flex; align-items:center; gap:8px; font-size:0.86rem; color:var(--hu-muted);
  margin-top:10px; }}
.hu-hours-note b {{ color:var(--hu-text); font-weight:600; }}
.hu-hour {{ animation:hu-fade 420ms var(--hu-ease) both; }}
.hu-panel {{ padding:0 0 4px; }}

/* --- Model -------------------------------------------------------------------------- */
.hu-big {{ font-size:clamp(5rem, 10vw, 8rem); line-height:.85; color:var(--hu-text); letter-spacing:-0.03em; }}
.hu-big-sub {{ font-family:{SERIF} !important; font-style:italic; font-size:2rem; line-height:1.1; margin-top:6px; }}
.hu-bars {{ list-style:none; margin:0; padding:0; }}
.hu-bar-row {{ display:grid; grid-template-columns:minmax(150px, 40%) 1fr 56px; gap:14px; align-items:center;
  padding:9px 0; border-bottom:1px solid var(--hu-border); font-size:0.9rem; color:var(--hu-muted); }}
.hu-bar-track {{ height:10px; position:relative; }}
.hu-bar-fill {{ display:block; height:100%; background-image:radial-gradient(var(--hu-muted) 1.4px, transparent 1.6px);
  background-size:6px 6px; background-position:0 50%; transform-origin:left;
  animation:hu-grow 800ms var(--hu-ease) both; animation-delay:calc(var(--i) * 70ms); }}
@keyframes hu-grow {{ from {{ clip-path:inset(0 100% 0 0); }} to {{ clip-path:inset(0 0 0 0); }} }}
.hu-bar-value {{ text-align:right; font-size:0.84rem; }}
.hu-bar-ours {{ color:var(--hu-text); font-weight:600; }}
.hu-bar-ours .hu-bar-fill {{ background-image:radial-gradient(var(--hu-data) 1.8px, transparent 2px); }}
.hu-kpis {{ display:grid; grid-template-columns:repeat(4, minmax(0,1fr)); border-top:1px solid var(--hu-text);
  border-bottom:1px solid var(--hu-border); margin:32px 0 8px; }}
.hu-kpi {{ padding:16px 18px 18px; animation:hu-rise 460ms var(--hu-ease) both; }}
.hu-kpi + .hu-kpi {{ border-left:1px solid var(--hu-border); }}
.hu-kpi:first-child {{ padding-left:0; }}
.hu-kpi-value {{ font-size:2.9rem; line-height:1; color:var(--hu-text); margin-top:12px; white-space:nowrap; }}
.hu-kpi-sub {{ font-size:0.84rem; color:var(--hu-muted); margin-top:8px; line-height:1.45; }}
.hu-kpi-icon {{ display:inline-flex; color:var(--hu-muted); }}

/* --- Hakkında: akış ------------------------------------------------------------------ */
.hu-steps {{ list-style:none; margin:10px 0 0; padding:0; display:grid;
  grid-template-columns:repeat(auto-fit, minmax(180px, 1fr)); border-top:1px solid var(--hu-text); }}
.hu-step {{ position:relative; display:flex; flex-direction:column; gap:8px; padding:18px 18px 22px 0;
  font-size:0.88rem; color:var(--hu-muted); line-height:1.55;
  animation:hu-rise 460ms var(--hu-ease) both; animation-delay:calc(var(--i) * 70ms); }}
.hu-step + .hu-step {{ padding-left:18px; border-left:1px solid var(--hu-border); }}
.hu-step b {{ color:var(--hu-text); font-size:1rem; font-weight:600; }}
.hu-step-num {{ font-size:2.6rem; line-height:1; color:var(--hu-text); }}
.hu-step-icon {{ position:absolute; top:22px; right:18px; color:var(--hu-muted); display:inline-flex; }}
.hu-prose {{ color:var(--hu-muted); font-size:0.97rem; line-height:1.7; max-width:62ch; }}
.hu-prose b {{ color:var(--hu-text); font-weight:600; }}
.hu-footer {{ margin-top:56px; padding-top:14px; border-top:1px solid var(--hu-text);
  font-size:0.8rem; color:var(--hu-muted); line-height:1.7; display:grid;
  grid-template-columns:minmax(0,2fr) minmax(0,1fr); gap:24px; }}
.hu-footer .hu-mono {{ font-size:0.7rem; letter-spacing:.14em; text-transform:uppercase; text-align:right; }}

/* --- Yükleme iskeleti ---------------------------------------------------------------- */
@keyframes hu-breathe {{ 0%, 100% {{ opacity:.35; }} 50% {{ opacity:1; }} }}
.hu-skeleton {{ display:flex; flex-direction:column; gap:22px; padding-top:6px; }}
.hu-skel {{ border-radius:2px; background-image:radial-gradient(var(--hu-border) 1.6px, transparent 1.8px);
  background-size:10px 10px; animation:hu-breathe 1.6s ease-in-out infinite; }}
.hu-skel-row {{ display:grid; grid-template-columns:7fr 5fr; gap:32px; }}
.hu-skel-cards {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(220px, 1fr)); gap:16px; }}
.hu-skel-note {{ font-family:{MONO} !important; font-size:0.72rem; letter-spacing:.14em; text-transform:uppercase;
  color:var(--hu-muted); }}
.hu-sr {{ position:absolute; width:1px; height:1px; overflow:hidden; clip:rect(0 0 0 0); white-space:nowrap; }}

/* --- Streamlit denetimleri ---------------------------------------------------------- */
[data-testid="stButtonGroup"] button {{ border-radius:2px !important; min-height:36px;
  font-family:{MONO} !important; letter-spacing:.06em; border-color:var(--hu-border) !important;
  transition:background-color 150ms ease, color 150ms ease, border-color 150ms ease; }}
[data-testid="stButtonGroup"] button p {{ font-family:{MONO} !important; font-size:0.78rem; }}
[data-testid="stButtonGroup"] button {{ background:transparent !important; color:var(--hu-text) !important; }}
[data-testid="stButtonGroup"] button:hover {{ border-color:var(--hu-text) !important; }}
[data-testid="stButtonGroup"] button[aria-checked="true"] {{ background:var(--hu-text) !important;
  color:var(--hu-bg) !important; border-color:var(--hu-text) !important; }}
[data-testid="stButtonGroup"] button[aria-checked="true"] p {{ color:var(--hu-bg) !important; }}
[data-testid="stPlotlyChart"] {{ border-top:1px solid var(--hu-border); padding-top:8px; }}
[data-testid="stExpander"] details {{ border-radius:2px; border-color:var(--hu-border); background:transparent; }}
[data-testid="stExpander"] summary p {{ font-family:{MONO} !important; font-size:0.8rem; letter-spacing:.04em; }}
:focus-visible {{ outline:2px solid var(--hu-ember) !important; outline-offset:3px; }}
@media (prefers-reduced-motion: reduce) {{ * {{ transition:none !important; animation:none !important; }} }}

.st-key-map-narrow {{ display:none; }}
@media (max-width: 900px) {{
  .hu-hero {{ grid-template-columns:1fr; gap:24px; }}
  .hu-hero-side {{ border-left:0; padding-left:0; border-top:1px solid var(--hu-border); padding-top:16px; }}
  .hu-kpis {{ grid-template-columns:1fr 1fr; }}
  .hu-kpi:nth-child(3) {{ border-left:0; padding-left:0; }}
  .hu-kpi:nth-child(n+3) {{ border-top:1px solid var(--hu-border); }}
}}
@media (max-width: 640px) {{
  .st-key-map-wide {{ display:none; }} .st-key-map-narrow {{ display:block; }}
  .block-container {{ padding-left:1rem; padding-right:1rem; padding-top:1.4rem; }}
  .hu-rank-row {{ grid-template-columns:1fr 64px; grid-template-areas:"name value" "bar bar"; gap:4px 12px;
    padding:10px 0; }}
  .hu-rank-name {{ grid-area:name; }} .hu-rank-value {{ grid-area:value; }}
  .hu-rank-row > svg {{ grid-area:bar; }}
  .hu-rank-value .hu-num {{ font-size:2rem; }} .hu-rank-value-cat {{ display:none; }}
  .hu-axis {{ grid-template-columns:1fr; }} .hu-axis > span:not(.hu-axis-ticks) {{ display:none; }}
  .hu-section .hu-fig {{ display:none; }}
  .stMarkdown h2.hu-section-title {{ font-size:1.6rem !important; }}
  .hu-bar-row {{ grid-template-columns:minmax(110px, 42%) 1fr 48px; }}
  .hu-footer {{ grid-template-columns:1fr; }} .hu-footer .hu-mono {{ text-align:left; }}
  .hu-colophon {{ text-align:left; }}
  .hu-skel-row {{ grid-template-columns:1fr; }}
}}
</style>"""


def card_rules(styles: dict[str, str]) -> str:
    """Kart kaplarına kategori rengi ve kademeli belirme gecikmesi (kap satır içi stil almaz).
    styles: {streamlit_key: kategori rengi}."""
    rules = "".join(f".st-key-{k}{{--hu-cat:{c};animation-delay:{i * 55}ms}}"
                    for i, (k, c) in enumerate(styles.items()))
    return f"<style>{rules}</style>"


# ---------------------------------------------------------------------------------------------
# Plotly
# ---------------------------------------------------------------------------------------------
def plotly_layout(t: Tokens, **overrides) -> dict:
    base = {
        "font": {"family": "Instrument Sans, system-ui, sans-serif", "color": t.text, "size": 13},
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "margin": {"l": 8, "r": 8, "t": 8, "b": 8},
        "hoverlabel": {"bgcolor": t.surface, "bordercolor": t.text,
                       "font": {"family": "IBM Plex Mono, monospace", "color": t.text,
                                "size": 12}},
        "xaxis": {"gridcolor": t.grid, "linecolor": t.text, "zeroline": False,
                  "tickfont": {"color": t.muted, "family": "IBM Plex Mono, monospace",
                               "size": 11}},
        "yaxis": {"gridcolor": t.grid, "linecolor": t.border, "zeroline": False,
                  "tickfont": {"color": t.muted, "family": "IBM Plex Mono, monospace",
                               "size": 11},
                  "title": {"font": {"color": t.muted, "size": 12}}},
        "legend": {"font": {"color": t.muted, "size": 12}, "bgcolor": "rgba(0,0,0,0)"},
        "separators": ",.",   # Türkçe: ondalık virgül, binlik nokta
    }
    for k, v in overrides.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            base[k] = {**base[k], **v}
        else:
            base[k] = v
    return base
