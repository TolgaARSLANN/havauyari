"""Parçacık Defteri: tasarım dilinin levhası (docs/tasarim/parcacik-defteri.md).

    python docs/tasarim/levha.py  ->  docs/tasarim/parcacik-defteri.png

Yazı tipleri (OFL): Instrument Serif, IBM Plex Mono. FONT_DIR ortam değişkeniyle verilir.
"""

from __future__ import annotations

import math
import os
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT_DIR = Path(os.environ.get("FONT_DIR", "fonts"))
OUT = Path(__file__).with_name("parcacik-defteri.png")

S = 3                                   # süper örnekleme: kenarlar kusursuz yumuşak
W, H = 2000, 2690
M = 150

PAPER = (243, 239, 231)
INK = (28, 27, 25)
GRAPHITE = (112, 107, 99)
HAIR = (214, 207, 194)
EMBER = (196, 64, 24)
OCHRE = (196, 150, 44)
SAGE = (98, 142, 108)

STATIONS = [  # kod, tahmin, alt, üst, pigment
    ("İZM·KNK", 25, 13, 39, OCHRE), ("KOC·MRK", 17, 10, 26, OCHRE),
    ("İST·SLT", 16, 8, 24, OCHRE), ("BRS·MRK", 14, 6, 22, OCHRE),
    ("İST·ÜMR", 10, 3, 18, OCHRE), ("BRS·KLP", 10, 3, 18, OCHRE),
    ("ANK·KÇR", 4, 0, 10, SAGE), ("ANK·ETM", 2, 0, 8, SAGE),
]
SCALE_MAX = 50.0
THRESHOLD = 35.5


def font(name: str, size: float) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_DIR / name), round(size * S))


SERIF = "InstrumentSerif-Regular.ttf"
SERIF_I = "InstrumentSerif-Italic.ttf"
MONO = "IBMPlexMono-Regular.ttf"

img = Image.new("RGB", (W * S, H * S), PAPER)
d = ImageDraw.Draw(img)


def P(v: float) -> int:
    return round(v * S)


def text(x, y, s, f, fill=INK, anchor="la", spacing=0):
    d.text((P(x), P(y)), s, font=f, fill=fill, anchor=anchor)


def tracked(x, y, s, f, fill=GRAPHITE, track=2.2, anchor="l"):
    """Harf aralıklı mono etiket (anchor: l / r)."""
    widths = [d.textlength(ch, font=f) / S for ch in s]
    total = sum(widths) + track * (len(s) - 1)
    cx = x - total if anchor == "r" else x
    for ch, w in zip(s, widths, strict=True):
        text(cx, y, ch, f, fill, anchor="ls")
        cx += w + track


def hline(x0, x1, y, fill=HAIR, w=1.0):
    d.line([(P(x0), P(y)), (P(x1), P(y))], fill=fill, width=max(1, P(w)))


def vline(x, y0, y1, fill=HAIR, w=1.0):
    d.line([(P(x), P(y0)), (P(x), P(y1))], fill=fill, width=max(1, P(w)))


def dot(x, y, r, fill):
    d.ellipse([P(x - r), P(y - r), P(x + r), P(y + r)], fill=fill)


def mix(c, a):
    """Pigmenti kâğıtla karıştır (a=1: saf pigment)."""
    return tuple(round(p * a + q * (1 - a)) for p, q in zip(c, PAPER, strict=True))


def scatter(rng, n, x0, x1, y0, y1, min_d, taken):
    """Çakışmasız rastgele noktalar (basit Poisson disk örneklemesi)."""
    out, tries = [], 0
    while len(out) < n and tries < n * 60:
        tries += 1
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        if all((x - a) ** 2 + (y - b) ** 2 >= min_d ** 2 for a, b in taken[-400:]):
            taken.append((x, y))
            out.append((x, y))
    return out


# --- Başlık bloğu -------------------------------------------------------------------------
mono_s, mono_xs = font(MONO, 19), font(MONO, 15)
tracked(M, 176, "LEVHA I", mono_s, INK)
tracked(W - M, 176, "PM 2,5  ·  µg/m³", mono_s, INK, anchor="r")
hline(M, W - M, 204, INK, 1.2)

text(M - 6, 250, "Parçacık", font(SERIF, 212))
text(M + 150, 440, "Defteri", font(SERIF_I, 212))
for i, line in enumerate(["GÖZLEM", "t + 24", "08 ÖRNEK", "05 KENT"]):
    tracked(W - M, 318 + i * 34, line, mono_s, GRAPHITE if i else INK, anchor="r")
hline(M, W - M, 712, HAIR)

# --- Şekil 1: yoğunluk bantları --------------------------------------------------------------
X0, X1 = M + 190, W - M - 200
TOP, BAND = 790, 142


def sx(v: float) -> float:
    return X0 + (X1 - X0) * v / SCALE_MAX


tracked(M, 760, "ŞEKİL 1", mono_xs, INK)
tracked(X0, 760, "HER NOKTA BİR SAYIM  ·  YOĞUNLUK = DEĞER", mono_xs, GRAPHITE)
rng = random.Random(25)
num_f, cat_f, code_f = font(SERIF, 70), font(MONO, 14), font(MONO, 17)
for i, (code, v, lo, hi, pig) in enumerate(STATIONS):
    cy = TOP + i * BAND + BAND / 2
    hline(X0, X1, cy, mix(HAIR, 0.55), 0.8)
    tracked(M, cy + 6, code, code_f, INK)
    taken: list[tuple[float, float]] = []
    # aralık kuyruğu (soluk) önce, çekirdek sonra: çekirdek üstte okunur
    for x, y in scatter(rng, int((hi - lo) * 5.2), sx(lo), sx(hi), cy - 44, cy + 44, 7.2, taken):
        dot(x, y, 2.1, mix(pig, 0.32))
    core = [(x, y) for x, y in scatter(rng, int(v * 13), sx(0), sx(v), cy - 36, cy + 36, 6.4, [])]
    for x, y in core:
        fade = 0.55 + 0.45 * (1 - abs(y - cy) / 36)          # merkezde yoğun, kenarda seyrek
        dot(x, y, 2.9, mix(pig, fade))
    vline(sx(v), cy - 50, cy + 50, INK, 1.4)                  # tahmin çizgisi
    text(W - M, cy + 22, f"{v}", num_f, INK, anchor="rs")
    tracked(W - M - 70 - 16, cy + 17, "ORTA" if pig == OCHRE else "İYİ", cat_f, GRAPHITE,
            anchor="r")

bottom = TOP + len(STATIONS) * BAND
# eşik: bütün bantları kesen tek çizgi
vline(sx(THRESHOLD), TOP - 8, bottom + 10, EMBER, 1.6)
tracked(sx(THRESHOLD) + 10, TOP + 4, "35,5", font(MONO, 17), EMBER)

# ölçek
hline(X0, X1, bottom + 26, INK, 1.0)
for v in range(0, 51, 5):
    major = v % 10 == 0
    vline(sx(v), bottom + 26, bottom + (40 if major else 33), INK, 1.0)
    if major:
        text(sx(v), bottom + 70, f"{v}", font(MONO, 17), GRAPHITE, anchor="ms")

# --- Şekil 2: saat saat sütunlar -------------------------------------------------------------
T2 = bottom + 150
hline(M, W - M, T2 - 50, HAIR)
tracked(M, T2, "ŞEKİL 2", mono_xs, INK)
tracked(X0, T2, "İZM·KNK  ·  ÖNÜMÜZDEKİ 24 SAAT", mono_xs, GRAPHITE)
hours = [17 + i for i in range(24)]
values = [20 + 6.5 * math.sin((i - 10) / 24 * 2 * math.pi) + 1.8 * math.sin(i / 3.1)
          for i in range(24)]
peak = max(range(24), key=lambda i: values[i])
base, col_w = T2 + 330, (X1 - X0) / 24
for i, (h, v) in enumerate(zip(hours, values, strict=True)):
    cx = X0 + col_w * (i + 0.5)
    n = round(v * 3)
    for k in range(n):
        row, col = divmod(k, 3)
        dot(cx + (col - 1) * 8.2, base - 6 - row * 8.2, 2.6, mix(OCHRE, 0.55 + 0.45 * (i == peak)))
    if i % 3 == 0:
        text(cx, base + 40, f"{h % 24:02d}", font(MONO, 15), GRAPHITE, anchor="ms")
top_peak = base - 6 - (round(values[peak] * 3) - 1) // 3 * 8.2
text(X0 + col_w * (peak + 0.5), top_peak - 22, f"{values[peak]:.0f}", font(SERIF_I, 44), INK,
     anchor="ms")
hline(X0, X1, base + 8, INK, 1.0)
tracked(M, base - 4, "µg/m³", font(MONO, 14), GRAPHITE)

# --- Künye -----------------------------------------------------------------------------------
hline(M, W - M, H - M - 40, INK, 1.2)
tracked(M, H - M, "HAVAUYARI", mono_s, INK)
tracked(W - M, H - M, "t₀  23.09.2026  16.00", mono_s, GRAPHITE, anchor="r")

img.resize((W, H), Image.LANCZOS).save(OUT, optimize=True)
print(OUT)
