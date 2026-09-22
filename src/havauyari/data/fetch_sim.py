"""Çevre, Şehircilik ve İklim Değişikliği Bakanlığı SİM (Sürekli İzleme Merkezi) istasyon verisi.

Kaynak: https://sim.csb.gov.tr/STN/STN_Report/StationDataDownloadNew ("İstasyon Veri İndirme").
Sayfanın kullandığı iki uç nokta kullanılır:
  - StationDataDownloadNewDefaults: istasyon listesi (şehir, koordinat, alan/kaynak türü)
  - StationDataDownloadNewData:     saatlik / günlük ölçümler (JSON)

Kamu sunucusunu yormamak için istekler arasında bekleme yapılır ve her yanıt yerelde saklanır;
aynı parça ikinci kez istenmez.

Kullanım:
    python -m havauyari.data.fetch_sim survey            # 5 şehirdeki istasyonların kapsamı
    python -m havauyari.data.fetch_sim fetch             # seçili istasyonların saatlik verisi
"""

from __future__ import annotations

import argparse
import json
import re
import time
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime, timedelta

import pandas as pd
import requests

from havauyari.config import CITIES, RAW_DIR, ROOT, START_DATE
from havauyari.reporting import to_markdown

BASE = "https://sim.csb.gov.tr"
PAGE_URL = f"{BASE}/STN/STN_Report/StationDataDownloadNew"
DEFAULTS_URL = f"{BASE}/STN/STN_Report/StationDataDownloadNewDefaults"
DATA_URL = f"{BASE}/STN/STN_Report/StationDataDownloadNewData"
USER_AGENT = "havauyari-research/0.1 (egitim amacli acik kaynak portfoy projesi)"

HOURLY, DAILY = 8, 16  # formdaki DataPeriods değerleri
PARAMETERS = ["PM25", "PM10"]
REQUEST_PAUSE_S = 2.0
CHUNK_MONTHS = 12

SIM_DIR = RAW_DIR / "sim"
STATIONS_PATH = SIM_DIR / "stations.csv"
SURVEY_PATH = SIM_DIR / "survey.csv"
SURVEY_REPORT = ROOT / "reports" / "istasyon_kapsami.md"

# SİM şehir adı -> projedeki şehir anahtarı
CITY_KEYS = {"İstanbul": "istanbul", "Ankara": "ankara", "İzmir": "izmir",
             "Bursa": "bursa", "Kocaeli": "kocaeli"}
assert set(CITY_KEYS.values()) == set(CITIES)


@dataclass(frozen=True)
class Station:
    id: str
    name: str
    city: str
    lat: float
    lon: float
    area_type: str
    source_type: str


class SimClient:
    def __init__(self, pause_s: float = REQUEST_PAUSE_S):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self.pause_s = pause_s
        self._token: str | None = None
        self._last_request = 0.0

    def _wait(self) -> None:
        delay = self.pause_s - (time.monotonic() - self._last_request)
        if delay > 0:
            time.sleep(delay)
        self._last_request = time.monotonic()

    @property
    def token(self) -> str:
        if self._token is None:
            self._wait()
            html = self.session.get(PAGE_URL, timeout=60).text
            m = re.search(r'name="__RequestVerificationToken"[^>]*value="([^"]+)"', html)
            if not m:
                raise RuntimeError("SİM sayfasında doğrulama anahtarı bulunamadı")
            self._token = m.group(1)
        return self._token

    def _post(self, url: str, data: list[tuple[str, str]], strict: bool = True) -> dict | None:
        """Result=false yanıtında strict ise hata fırlatır, değilse None döner.

        Veri sorgusunda Result=false, istasyonun istenen parametreyi o dönemde ölçmediği anlamına
        gelir (örn. PM2.5 cihazı olmayan istasyon); bu bir hata değil, "veri yok" durumudur.
        """
        self._wait()
        resp = self.session.post(
            url, data=[("__RequestVerificationToken", self.token), *data], timeout=180,
            headers={"X-Requested-With": "XMLHttpRequest", "Referer": PAGE_URL},
        )
        resp.raise_for_status()
        body = resp.json()
        if not body.get("Result"):
            if strict:
                raise RuntimeError(f"SİM hata döndürdü: {body.get('Message')!r}")
            return None
        return body["Object"]

    def stations(self) -> list[Station]:
        """Projedeki 5 şehrin istasyonları."""
        obj = self._post(DEFAULTS_URL, [("StationType", "1")])
        city_names = {c["Id"]: c["Name"] for c in obj["CityId"]}
        area = {str(a["Id"]): a["Name"] for a in obj["AreaType"]}
        source = {str(s["Id"]): s["Name"] for s in obj["SourceType"]}
        out = []
        for s in obj["StationIds"]:
            city = CITY_KEYS.get(city_names.get(s["CityId"], ""))
            m = re.match(r"POINT \(([-\d.]+) ([-\d.]+)\)", s.get("Location") or "")
            if city is None or m is None:
                continue
            out.append(Station(id=s["id"], name=s["Name"].strip(), city=city,
                               lon=round(float(m.group(1)), 5), lat=round(float(m.group(2)), 5),
                               area_type=area.get(str(s.get("AreaType")), "-"),
                               source_type=source.get(str(s.get("SourceType")), "-")))
        return sorted(out, key=lambda s: (s.city, s.name))

    def measurements(self, station_ids: list[str], start: datetime, end: datetime,
                     period: int = HOURLY, parameters: list[str] = PARAMETERS) -> pd.DataFrame:
        data = [("StationType", "1"), ("DataPeriods", str(period)),
                ("StartDateTime", start.strftime("%d.%m.%Y %H:%M")),
                ("EndDateTime", end.strftime("%d.%m.%Y %H:%M"))]
        data += [("StationIds", sid) for sid in station_ids]
        data += [("Parameters", p) for p in parameters]
        obj = self._post(DATA_URL, data, strict=False)
        rows = (obj or {}).get("Data") or []
        return rows_to_frame(rows, parameters)


def slugify(name: str) -> str:
    """'İstanbul - Ümraniye-MTHM' -> 'istanbul_umraniye_mthm'"""
    ascii_name = (unicodedata.normalize("NFKD", name.replace("ı", "i").replace("İ", "I"))
                  .encode("ascii", "ignore").decode())
    return re.sub(r"[^a-z0-9]+", "_", ascii_name.lower()).strip("_")


def rows_to_frame(rows: list[dict], parameters: list[str]) -> pd.DataFrame:
    """SİM yanıtını (time, station_id, PM25, PM10, ...) tablosuna çevirir."""
    cols = ["time", "station_id", *parameters]
    if not rows:
        return pd.DataFrame(columns=cols)
    df = pd.DataFrame(rows).rename(columns={"ReadTime": "time", "Stationid": "station_id"})
    df["time"] = pd.to_datetime(df["time"])
    for p in parameters:
        df[p] = pd.to_numeric(df[p], errors="coerce") if p in df else float("nan")
    return df[cols]


# ---------------------------------------------------------------------------------------------
# Kapsam taraması
# ---------------------------------------------------------------------------------------------
def survey(client: SimClient, start: str = START_DATE, end: date | None = None) -> pd.DataFrame:
    """Her istasyon için günlük PM2.5 kapsamı (tek istek / istasyon)."""
    end = end or date.today()
    stations = client.stations()
    SIM_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([s.__dict__ for s in stations]).to_csv(STATIONS_PATH, index=False)
    t0, t1 = datetime.fromisoformat(start), datetime.combine(end, datetime.min.time())
    n_days = (t1 - t0).days
    rows = []
    for i, st in enumerate(stations, 1):
        daily = client.measurements([st.id], t0, t1, DAILY, ["PM25"])
        pm = daily.set_index("time")["PM25"].dropna() if len(daily) else pd.Series(dtype=float)
        last_year = pm[pm.index >= t1 - timedelta(days=365)]
        rows.append({
            **st.__dict__,
            "kapsam_%": len(pm) / n_days * 100,
            "son_1_yil_%": len(last_year) / 365 * 100,
            "ilk_gun": pm.index.min().date() if len(pm) else None,
            "son_gun": pm.index.max().date() if len(pm) else None,
            "ort_pm25": pm.mean() if len(pm) else None,
        })
        print(f"[{i:3d}/{len(stations)}] {st.name:45s} kapsam=%{rows[-1]['kapsam_%']:5.1f}")
    out = pd.DataFrame(rows).sort_values(["city", "kapsam_%"], ascending=[True, False])
    out.to_csv(SURVEY_PATH, index=False)
    return out


def select_stations(survey_df: pd.DataFrame, per_city: int = 2,
                    min_coverage: float = 80.0) -> pd.DataFrame:
    """Şehir başına en eksiksiz, kenti temsil eden istasyonlar.

    Kurallar: alan türü "Kentsel", kaynak türü "Sanayi" değil (OSB istasyonları kentin genel
    maruziyetini temsil etmez); tüm dönemde ve son 1 yılda PM2.5 kapsamı ≥ min_coverage.
    """
    ok = survey_df[(survey_df["kapsam_%"] >= min_coverage)
                   & (survey_df["son_1_yil_%"] >= min_coverage)
                   & (survey_df["area_type"] == "Kentsel")
                   & (survey_df["source_type"] != "Sanayi")]
    ok = ok.sort_values(["city", "kapsam_%", "son_1_yil_%"], ascending=[True, False, False])
    return ok.groupby("city", sort=False).head(per_city)


def survey_report(survey_df: pd.DataFrame, selected: pd.DataFrame) -> str:
    view = survey_df.copy()
    view["seçildi"] = view["id"].isin(selected["id"]).map({True: "✔", False: ""})
    view = view[["city", "name", "area_type", "source_type", "kapsam_%", "son_1_yil_%",
                 "ilk_gun", "son_gun", "ort_pm25", "seçildi"]].set_index("city")
    counts = survey_df.assign(pm=survey_df["kapsam_%"] > 0).groupby("city").agg(
        istasyon=("id", "size"), pm25_olcen=("pm", "sum"),
        kapsam_80_ustu=("kapsam_%", lambda s: int((s >= 80).sum())))
    return "\n".join([
        "# SİM İstasyon Kapsamı (PM2.5)",
        "",
        f"_Oluşturulma: {date.today().isoformat()} · Dönem: {START_DATE} → bugün · "
        "Üreten: `python -m havauyari.data.fetch_sim survey`_",
        "",
        "Kapsam = PM2.5 değeri olan gün sayısı / dönemdeki gün sayısı. Seçim kuralı: kentsel alan, "
        "sanayi kaynaklı olmayan, tüm dönemde ve son 1 yılda kapsam ≥ %80 olan istasyonlardan "
        "şehir başına en eksiksiz 2 tanesi.",
        "",
        "## Şehir özeti", "", to_markdown(counts, ".0f"), "",
        "## İstasyonlar", "", to_markdown(view, ".1f"), "",
    ])


# ---------------------------------------------------------------------------------------------
# Saatlik veri
# ---------------------------------------------------------------------------------------------
def _chunks(start: datetime, end: datetime, months: int = CHUNK_MONTHS):
    cur = start
    while cur < end:
        nxt = min(pd.Timestamp(cur) + pd.DateOffset(months=months), pd.Timestamp(end))
        yield cur, nxt.to_pydatetime()
        cur = nxt.to_pydatetime()


def fetch_hourly(client: SimClient, station: pd.Series, start: str = START_DATE,
                 end: date | None = None) -> pd.DataFrame:
    """Bir istasyonun saatlik verisini parça parça indirir; her parça JSON olarak önbelleğe alınır.

    Tamamlanmış (bitişi bugünden önce olan) parçalar tekrar indirilmez.
    """
    end_dt = datetime.combine(end or date.today(), datetime.min.time())
    cache_dir = SIM_DIR / "hourly" / station["id"]
    cache_dir.mkdir(parents=True, exist_ok=True)
    frames = []
    for c0, c1 in _chunks(datetime.fromisoformat(start), end_dt):
        path = cache_dir / f"{c0:%Y%m%d}_{c1:%Y%m%d}.json"
        complete = c1 < end_dt
        if path.exists() and complete:
            rows = json.loads(path.read_text(encoding="utf-8"))
        else:
            df = client.measurements([station["id"]], c0, c1, HOURLY, PARAMETERS)
            rows = json.loads(df.to_json(orient="records", date_format="iso"))
            path.write_text(json.dumps(rows), encoding="utf-8")
        frames.append(rows_to_frame([{"ReadTime": r["time"], "Stationid": r["station_id"],
                                      **{p: r.get(p) for p in PARAMETERS}} for r in rows],
                                    PARAMETERS))
    df = pd.concat([f for f in frames if not f.empty], ignore_index=True)
    return (df.drop_duplicates("time").set_index("time").sort_index()
              .drop(columns="station_id"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["survey", "report", "fetch"],
                        help="survey: kapsamı ölç · report: kayıtlı taramadan raporu yeniden üret "
                             "· fetch: seçili istasyonların saatlik verisini indir")
    parser.add_argument("--per-city", type=int, default=2)
    args = parser.parse_args()
    client = SimClient()

    if args.command in ("survey", "report"):
        df = survey(client) if args.command == "survey" else pd.read_csv(SURVEY_PATH)
        selected = select_stations(df, args.per_city)
        SURVEY_REPORT.parent.mkdir(parents=True, exist_ok=True)
        SURVEY_REPORT.write_text(survey_report(df, selected) + "\n", encoding="utf-8")
        print(selected[["city", "name", "kapsam_%", "son_1_yil_%"]].to_string(index=False))
        print(f"[ok] {SURVEY_REPORT}")
        return

    if not SURVEY_PATH.exists():
        raise SystemExit("Önce `survey` çalıştırın.")
    selected = select_stations(pd.read_csv(SURVEY_PATH), args.per_city)
    for _, st in selected.iterrows():
        df = fetch_hourly(client, st)
        out = SIM_DIR / f"{st['city']}__{slugify(st['name'])}.parquet"
        df.to_parquet(out)
        filled = df["PM25"].notna().mean() * 100
        print(f"[ok] {st['name']}: {len(df):,} saat, PM2.5 dolu %{filled:.1f} -> {out.name}")


if __name__ == "__main__":
    main()
