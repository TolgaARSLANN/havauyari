# 🌫️ HavaUyarı: Akıllı Hava Kalitesi Erken Uyarı Sistemi

[![CI](https://github.com/TolgaARSLANN/havauyari/actions/workflows/ci.yml/badge.svg)](https://github.com/TolgaARSLANN/havauyari/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)

Türkiye'nin büyük şehirleri için **PM2.5 konsantrasyonunu 24-72 saat önceden tahmin eden**, tahmini AQI kategorisine çeviren ve sağlıksız seviyeler için **erken uyarı** üreten uçtan uca bir makine öğrenmesi projesi.

> 🚧 Geliştirme aşamasında: veri ve keşif aşaması tamamlandı, modelleme sürüyor. Ayrıntılı plan: [docs/YOL_HARITASI.md](docs/YOL_HARITASI.md)

## Problem
Hava kirliliği, özellikle kış aylarında Türkiye şehirlerinde ciddi bir halk sağlığı sorunudur. Mevcut ölçüm sistemleri çoğunlukla *şu anki* durumu gösterir. HavaUyarı ise *yarın ne olacağını* tahmin ederek hassas grupların (astım hastaları, yaşlılar, çocuklar) önlem almasına yardımcı olmayı hedefler.

## Veri
| Kaynak | İçerik |
|---|---|
| [Open-Meteo Air Quality API](https://open-meteo.com/en/docs/air-quality-api) (CAMS) | Saatlik PM2.5, PM10, NO₂, O₃, CO, SO₂ |
| [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api) (ERA5) | Sıcaklık, nem, rüzgâr, basınç, yağış |

- **Şehirler:** İstanbul, Ankara, İzmir, Bursa, Kocaeli
- **Kapsam:** 2023-01-01 → 2026-09-17, saatlik, şehir başına 32.544 saat (toplam 162.720 satır)
- **Kalite:** Eksik saat, boş ya da fiziksel sınır dışı değer yok. PM2.5 > PM10 olan 76 saat düzeltildi. Ayrıntılar: [reports/veri_kalite_raporu.md](reports/veri_kalite_raporu.md)

## Veriden Öğrendiklerimiz
Tam analiz: [notebooks/01_eda.ipynb](notebooks/01_eda.ipynb)

1. **Kirlilik kışın ve akşam saatlerinde yoğunlaşıyor.** Uyarı seviyesindeki (≥ 35,5 µg/m³) epizotların %70–88'i Kasım–Mart'ta başlıyor. Kış akşamları (20:00–22:00) PM2.5, öğleden sonraya göre 2,4–4,3 kat yüksek.
2. **Rüzgâr en güçlü meteorolojik etken.** Durgun havada PM2.5, 20 km/sa üstü rüzgâra göre 2,4–3,1 kat yüksek. Yön de önemli: İstanbul'da doğu-güneydoğu rüzgârında kirlilik, kuzeydoğu rüzgârına göre ~2,8 kat.
3. **Yağış havayı temizliyor.** Son 3 saatte yağış olduğunda PM2.5 medyanı %17–25 daha düşük.
4. **Asıl zorluk yeni başlayan kirlilik.** 24 saat sonraki uyarı saatlerinin %37–64'ü şu an uyarı olmayan saatlerden geliyor. "Yarın da bugün gibi olur" diyen bir model bunları kaçırır. Bu yüzden meteorolojik özellikler ve hava tahmini kritik.
5. **Kirlilik epizotları kısa.** Uyarı seviyesindeki bir epizot tipik olarak 4–5 saat, en uzunu 90 saat sürüyor.

<p align="center">
  <img src="reports/figures/02_ay_saat_isi_haritasi.png" alt="Ay ve saate göre medyan PM2.5 ısı haritası" width="100%"><br>
  <em>Ay × saat bazında medyan PM2.5: kış akşamlarındaki koyu bölge ısınma kaynaklı kirliliği gösteriyor.</em>
</p>

<p align="center">
  <img src="reports/figures/06_ruzgar_hizi.png" alt="Rüzgâr hızına göre medyan PM2.5" width="49%">
  <img src="reports/figures/11_epizot_aylar.png" alt="Aylara göre kirlilik epizotları" width="49%"><br>
  <em>Solda: rüzgâr hızı arttıkça PM2.5 düşüyor. Sağda: kirlilik epizotları kış aylarında toplanıyor.</em>
</p>

## Yaklaşım
- **Özellikler (79):** PM2.5 geçmişi (1 saat–1 hafta lag'ler, kayan istatistikler, hedef saatle hizalı geçmiş değerler), diğer kirleticilerin geçmişi, meteoroloji (rüzgâr vektörü ve durgunluk, yağış birikimi, ısıtma derece-saati, basınç ve sıcaklık değişimi), takvim ve Türkiye resmî tatilleri. Hedef anının saati ve tatil bilgisi önceden bilindiği için ayrıca kullanılır. Bir sızıntı testi, gelecek verinin hiçbir özelliğe karışmadığını doğrular.
- **Baseline modeller:** Persistence, Seasonal Naive (haftalık), 24 saatlik hareketli ortalama, klimatoloji (şehir × ay × saat medyanı)
- **Model:** LightGBM (direkt çok-ufuklu tahmin)
- **Doğrulama:** Son 1 yıl üzerinde 12 aylık walk-forward geri test (genişleyen eğitim penceresi + arındırma), böylece her mevsim test edilir. Rastgele split kullanılmaz.
- **Metrikler:** MAE, RMSE, sMAPE + uyarı sınıfı için **recall** (kaçırılan alarm en kritik hata)
- **AQI:** US EPA 2024 PM2.5 eşikleri. Ana uyarı eşiği 35,5 µg/m³ (hassas gruplar için sağlıksız)

## Kurulum ve Çalıştırma
Linux / macOS / WSL üzerinde:
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

make data      # veriyi indir          -> data/raw/
make quality   # veri kalite raporu    -> reports/veri_kalite_raporu.md
make process   # temizle               -> data/processed/
make baselines # referans modellerle hızlı geri test (~10 sn)
make train     # referans modeller + LightGBM geri testi -> reports/backtest_h24.md (~3 dk)
make test      # birim testleri
```

## Proje Yapısı
```
src/havauyari/
├─ data/        # veri çekme, kalite raporu, temizlik
├─ features/    # zaman serisi özellikleri
├─ models/      # baseline'lar, eğitim, walk-forward değerlendirme
├─ evaluation/  # regresyon ve alarm metrikleri
├─ alerts/      # konsantrasyon -> AQI dönüşümü, uyarı kuralları
└─ config.py
notebooks/      # EDA ve deneyler
reports/        # veri kalite raporu ve grafikler
docs/           # yol haritası
tests/          # birim testleri (AQI, temizlik, sızıntı kontrolü, metrikler)
```

## Sonuçlar
24 saat sonrası PM2.5 tahmini, son 1 yıl (2025-09-23 → 2026-09-18) üzerinde 12 aylık walk-forward geri test, 5 şehir, model başına 43.080 tahmin. Uyarı = PM2.5 ≥ 35,5 µg/m³.

| Model | MAE | RMSE | Kış MAE | Uyarı recall | Uyarı precision |
|---|---|---|---|---|---|
| Seasonal naive (1 hafta önce) | 9,98 | 15,78 | 14,73 | 0,40 | 0,40 |
| Hareketli ortalama (24 s) | 9,03 | 14,12 | 15,10 | 0,29 | 0,37 |
| Klimatoloji (şehir × ay × saat) | 7,98 | 12,92 | 12,36 | 0,14 | 0,67 |
| Persistence ("yarın da bugün gibi") | 7,43 | 12,32 | 12,04 | **0,52** | 0,52 |
| **LightGBM** | **6,75** | **10,80** | **10,65** | 0,42 | **0,62** |

LightGBM ortalama hatada en iyi referans modelden **%9,2** daha iyi, ancak uyarıların daha azını yakalıyor: ortalama hatayı küçülten model zirveleri bastırıyor. Sıradaki adımlar (gelecek hava tahmini özelliği, uyarı eşiği ayarı) bu açığı hedefliyor. Ayrıntılı rapor: [reports/backtest_h24.md](reports/backtest_h24.md)

## Yol Haritası
Ayrıntılı alt fazlar ve alınan kararlar: [docs/YOL_HARITASI.md](docs/YOL_HARITASI.md)

- [x] Geliştirme ortamı, CI
- [x] Veri toplama, kalite raporu, temizlik
- [x] Keşifsel veri analizi (EDA)
- [x] Özellik mühendisliği (meteoroloji, tatiller, diğer kirleticiler)
- [ ] Modelleme: baseline'lar, LightGBM, 24/48/72 saat ufukları
- [ ] Optuna, MLflow, hata analizi, SHAP, tahmin aralıkları
- [ ] FastAPI (`/forecast/{city}`, `/alerts`)
- [ ] Streamlit panosu + Türkiye haritası
- [ ] Docker + GitHub Actions ile günlük otomatik tahmin
- [ ] Hugging Face Spaces'e deploy

## Sınırlamalar
- **Veri bir model çıktısı, istasyon ölçümü değil.** Kirletici değerleri CAMS atmosfer modelinden (~11 km çözünürlük) geliyor. Proje fiilen bu modelin çıktısını tahmin ediyor. Gerçek istasyon ölçümleriyle (Çevre Bakanlığı SİM) karşılaştırma ileride yapılacak.
- **Yerel kirlilik kaçabilir.** Kış kirliliğiyle bilinen Bursa'da veride mevsimsellik çok zayıf (kış/yaz oranı 1,18). Model çözünürlüğü yerel kaynakları yakalayamıyor olabilir.
- **Nadir olaylar.** "Sağlıksız" (≥ 55,5 µg/m³) saatler Bursa ve Kocaeli'de %0,5'in altında; bu seviyede uyarı performansı sınırlı kalabilir.

## Sorumluluk Reddi
Bu proje eğitim ve portföy amaçlıdır. Tahminler resmi hava kalitesi uyarılarının yerine geçmez ve sağlık tavsiyesi değildir.
