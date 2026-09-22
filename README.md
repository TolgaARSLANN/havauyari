# 🌫️ HavaUyarı: Akıllı Hava Kalitesi Erken Uyarı Sistemi

Türkiye'nin büyük şehirleri için **PM2.5 konsantrasyonunu 24-72 saat önceden tahmin eden**, tahmini AQI kategorisine çeviren ve sağlıksız seviyeler için **erken uyarı** üreten uçtan uca bir makine öğrenmesi projesi.

> 🚧 Geliştirme aşamasında. Yol haritası aşağıda.

## Problem
Hava kirliliği, özellikle kış aylarında Türkiye şehirlerinde ciddi bir halk sağlığı sorunudur. Mevcut ölçüm sistemleri çoğunlukla *şu anki* durumu gösterir. HavaUyarı ise *yarın ne olacağını* tahmin ederek hassas grupların (astım hastaları, yaşlılar, çocuklar) önlem almasına yardımcı olmayı hedefler.

## Veri
| Kaynak | İçerik |
|---|---|
| [Open-Meteo Air Quality API](https://open-meteo.com/en/docs/air-quality-api) (CAMS) | Saatlik PM2.5, PM10, NO₂, O₃, CO, SO₂ |
| [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api) | Sıcaklık, nem, rüzgâr, basınç, yağış |

Şehirler: İstanbul, Ankara, İzmir, Bursa, Kocaeli (bkz. `src/havauyari/config.py`).

## Yaklaşım
- **Özellikler:** lag'ler (1 saat–1 hafta), kayan ortalama/std, döngüsel takvim kodlaması, rüzgâr u/v vektörü, meteoroloji
- **Baseline modeller:** Persistence, Seasonal Naive (haftalık), 24 saatlik hareketli ortalama
- **Model:** LightGBM (direkt çok-ufuklu tahmin)
- **Doğrulama:** Walk-forward (zamana göre ileri kayan) doğrulama. Rastgele split kullanılmaz.
- **Metrikler:** MAE, RMSE, sMAPE + uyarı sınıfı için **recall** (kaçırılan alarm en kritik hata)
- **AQI:** US EPA 2024 PM2.5 eşikleri

## Kurulum ve Çalıştırma
```bash
python -m venv .venv
.venv\Scripts\activate          # Linux/macOS: source .venv/bin/activate
pip install -e ".[dev,ml,serve]"

python -m havauyari.data.fetch_openmeteo   # veriyi indir  -> data/raw/
python -m havauyari.data.clean             # temizle       -> data/processed/
python -m havauyari.models.train           # baseline vs LightGBM karşılaştırması
pytest -q
```

## Proje Yapısı
```
src/havauyari/
├─ data/        # veri çekme ve temizlik
├─ features/    # zaman serisi özellikleri
├─ models/      # baseline'lar, eğitim, walk-forward değerlendirme
├─ evaluation/  # regresyon ve alarm metrikleri
├─ alerts/      # konsantrasyon -> AQI dönüşümü, uyarı kuralları
└─ config.py
notebooks/      # EDA ve deneyler
tests/          # birim testleri (AQI, sızıntı kontrolü, metrikler)
```

## Sonuçlar
_Walk-forward doğrulama tamamlandığında buraya eklenecek._

| Model | MAE (24s) | RMSE | Alarm Recall |
|---|---|---|---|
| Persistence | – | – | – |
| Seasonal Naive | – | – | – |
| **LightGBM** | – | – | – |

## Yol Haritası
- [x] Proje iskeleti, veri çekme, AQI dönüşümü, özellik üretimi, baseline'lar
- [ ] EDA notebook'u (mevsimsellik, kış etkisi, rüzgâr-PM ilişkisi)
- [ ] Optuna ile hiperparametre araması + MLflow
- [ ] SHAP ile açıklanabilirlik, quantile tahmin aralıkları
- [ ] FastAPI (`/forecast/{city}`, `/alerts`)
- [ ] Streamlit panosu + Türkiye haritası
- [ ] Docker + GitHub Actions ile günlük otomatik tahmin
- [ ] Hugging Face Spaces'e deploy

## Sorumluluk Reddi
Bu proje eğitim ve portföy amaçlıdır. Tahminler resmi hava kalitesi uyarılarının yerine geçmez ve sağlık tavsiyesi değildir.
