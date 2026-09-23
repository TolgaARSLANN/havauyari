# 🌫️ HavaUyarı: Akıllı Hava Kalitesi Erken Uyarı Sistemi

[![CI](https://github.com/TolgaARSLANN/havauyari/actions/workflows/ci.yml/badge.svg)](https://github.com/TolgaARSLANN/havauyari/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)

Türkiye şehirlerindeki hava kalitesi izleme istasyonlarında **24 saat sonra ölçülecek PM2.5 değerini tahmin eden**, tahmini AQI kategorisine çeviren ve sağlıksız seviyeler için **erken uyarı** üreten uçtan uca bir makine öğrenmesi projesi.

> 🚧 Geliştirme aşamasında: veri, keşif ve modelleme tamamlandı; servis ve arayüz sürüyor. Ayrıntılı plan: [docs/YOL_HARITASI.md](docs/YOL_HARITASI.md)

## Problem
Hava kirliliği, özellikle kış aylarında Türkiye şehirlerinde ciddi bir halk sağlığı sorunudur. Mevcut sistemler çoğunlukla *şu anki* durumu gösterir. HavaUyarı *yarın ne olacağını* tahmin ederek hassas grupların (astım hastaları, yaşlılar, çocuklar) önlem almasına yardımcı olmayı hedefler.

Avrupa'nın CAMS atmosfer modeli zaten hava kalitesi tahmini yayımlıyor, ancak ~11 km çözünürlüğü yerel gerçeği zayıf yansıtıyor: istasyon ölçümleriyle korelasyonu 0,30–0,64 ve sapması şehirden şehre ters yönde (Ankara'da yüksek, Bursa ve İzmir'de düşük tahmin). **Bu proje, genel modeli yerel istasyon ölçümleri ve hava tahminiyle düzelterek gerçek ölçüme yakın bir erken uyarı üretiyor.**

## Veri
| Kaynak | Rol | İçerik |
|---|---|---|
| **Çevre Bakanlığı SİM** (sim.csb.gov.tr) | **Hedef** | 8 kentsel istasyonda saatlik PM2.5 ölçümü |
| [Open-Meteo Air Quality API](https://open-meteo.com/en/docs/air-quality-api) (CAMS) | Girdi | İstasyon koordinatında PM2.5, PM10, NO₂, O₃, CO, SO₂ |
| [Open-Meteo Previous Runs API](https://open-meteo.com/en/docs/previous-runs-api) | Girdi | *O gün yayımlanmış* 1 günlük hava tahminleri |
| [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api) (ERA5) | Girdi | Gerçekleşen sıcaklık, nem, rüzgâr, basınç, yağış |

- **Şehirler:** İstanbul, Ankara, İzmir, Bursa, Kocaeli · **Kapsam:** 2023-01-01 → bugün, saatlik
- **İstasyon seçimi:** 104 istasyon tarandı, 47'si PM2.5 ölçüyor; kentsel, sanayi kaynaklı olmayan ve verisi ≥ %80 eksiksiz olanlardan şehir başına en fazla 2 istasyon seçildi ([kapsam raporu](reports/istasyon_kapsami.md))
- **Kalite:** Ölçülmemiş saatler hedef olarak kullanılmaz, tahminle doldurulmaz. Temizlik kuralları ve saat hizası doğrulaması: [istasyon veri kalitesi](reports/istasyon_veri_kalitesi.md), [CAMS veri kalitesi](reports/veri_kalite_raporu.md)

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
- **Özellikler (~100):** istasyon ölçümünün geçmişi (1 saat–1 hafta lag'ler, kayan istatistikler, hedef saatle hizalı geçmiş değerler), CAMS kirleticileri, meteoroloji (rüzgâr vektörü ve durgunluk, yağış birikimi, ısıtma derece-saati, basınç ve sıcaklık değişimi), takvim ve Türkiye resmî tatilleri, **o gün yayımlanmış hava tahmininden** üretilen 17 özellik (önümüzdeki 24 saatin yağış toplamı, durgun saat sayısı, en düşük rüzgâr vb.)
- **Sızıntıya karşı:** Eksik saatler yalnızca geçmiş değerle doldurulur, hedef hiç doldurulmaz. Testler, belirli bir andan sonraki veri değiştirildiğinde hiçbir özelliğin değişmediğini doğrular. Hava tahminlerinde yalnızca yayımlanmış olan pencere kullanılır.
- **Baseline modeller:** Persistence, bir hafta önceki aynı saat, 24 saatlik hareketli ortalama, klimatoloji (istasyon × ay × saat medyanı), ham CAMS ve ölçeklenmiş CAMS
- **Model:** LightGBM
- **Doğrulama:** Son 1 yıl üzerinde 12 aylık walk-forward geri test (genişleyen eğitim penceresi + arındırma), böylece her mevsim test edilir. Rastgele split kullanılmaz; tüm modeller aynı satırlarda karşılaştırılır.
- **Metrikler:** MAE, RMSE, sMAPE + uyarı sınıfı için **recall** (kaçırılan alarm en kritik hata) ve precision
- **AQI:** US EPA 2024 PM2.5 eşikleri. Ana uyarı eşiği 35,5 µg/m³ (hassas gruplar için sağlıksız)

## Kurulum ve Çalıştırma
Linux / macOS / WSL üzerinde:
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Ana akış: istasyon hedefi
make sim-survey    # SİM istasyonlarını tara -> reports/istasyon_kapsami.md
make sim-data      # seçili istasyonların saatlik ölçümleri
make forecasts     # geçmişte yayımlanmış hava tahminleri
make stations      # birleşik veri seti + kalite raporu
make train-station # istasyon hedefli geri test -> reports/backtest_istasyon_h24.md

# Yan akış: CAMS hedefli ilk kurulum (karşılaştırma için korunuyor)
make data quality process
make train

make test          # birim testleri (80)
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
**Hedef: istasyonda 24 saat sonra ölçülecek PM2.5.** Son 1 yıl (2025-09-23 → 2026-09-18), 12 aylık walk-forward geri test, 8 istasyon, 501.000 tahmin. Tüm modeller aynı satırlarda ölçülür. Uyarı = PM2.5 ≥ 35,5 µg/m³.

| Model | MAE | RMSE | Uyarı recall | Uyarı precision |
|---|---|---|---|---|
| **HavaUyarı (uygulanabilir)** | **6,78** | **10,78** | **0,66** | **0,73** |
| HavaUyarı (üst sınır) | 6,50 | 10,45 | 0,68 | 0,73 |
| Hareketli ortalama (24 s) | 9,09 | 14,12 | 0,57 | 0,61 |
| Persistence ("yarın da bugün gibi") | 9,09 | 14,51 | 0,60 | 0,60 |
| Klimatoloji (istasyon × ay × saat) | 10,30 | 17,03 | 0,05 | 0,36 |
| CAMS (istasyon ortalamasına ölçeklenmiş) | 11,15 | 17,32 | 0,41 | 0,47 |
| Bir hafta önceki aynı saat | 11,61 | 18,32 | 0,49 | 0,49 |
| **Ham CAMS** | 12,95 | 19,73 | 0,25 | 0,36 |

- Ortalama hata ham CAMS'a göre **%47,7**, en iyi basit referansa göre **%25,4** daha düşük.
- Uyarıların yakalanma oranı 0,25'ten **0,66'ya** çıkarken isabet de 0,36'dan **0,73'e** yükseliyor: hem daha çok uyarı yakalanıyor hem daha az yanlış alarm veriliyor.
- **Uyarı eşiği ayarı:** Model zirveleri bastırdığı için karar eşiği, yakalama oranı en az %80 olacak şekilde *yalnızca geçmiş tahminlerden* seçildi (28,5 µg/m³). Son 12 ayda uyarıların **%82,4'ü** yakalandı (sabit 35,5 eşikle %65,7). Bedeli daha çok yanlış alarm: isabet %73'ten %57'ye iniyor. [Ayrıntılar](reports/uyari_esigi_h24.md)
- **Yeni başlayan kirlilik:** 24 saat sonra başlayacak uyarıların %34'ü önceden görülüyor ("yarın da bugün gibi" yöntemi %0, CAMS %26). [Hata analizi](reports/hata_analizi_istasyon_h24.md)
- **İstasyon bazlı eşik:** Her istasyon kendi eşiğini alır (18,5–32 µg/m³); en zayıf istasyonda yakalama %39 → %71.
- **Tahmin aralığı:** Her tahmine %80 aralık eşlik eder (örn. "29 µg/m³, %80 olasılıkla 17–45"); son 12 ayda gerçek değerlerin %82,9'u aralıkta kaldı. [Ayrıntılar](reports/tahmin_araligi_h24.md)
- **Açıklanabilirlik:** Tahminin %30'u o gün yayımlanan hava tahmininden, %36'sı istasyonun geçmişinden geliyor; CAMS'ın PM2.5 değerinin payı yalnızca %0,6. Her tahmin için "neden" açıklaması üretilebiliyor. [Ayrıntılar](reports/aciklanabilirlik_h24.md)
- **Uygulanabilirlik:** Ana model yalnızca bugün erişilebilen verileri kullanır (istasyon geçmişi, CAMS'ın şu ana kadarki değerleri, o gün yayımlanmış hava tahmini). "Üst sınır" modeli ek olarak CAMS'ın gelecek değerlerini görür; aradaki farkın küçük olması, sonucun CAMS'ın tahmin başarısına bağımlı olmadığını gösteriyor.
- İstasyon ve mevsim kırılımları: [reports/backtest_istasyon_h24.md](reports/backtest_istasyon_h24.md)

## Yol Haritası
Ayrıntılı alt fazlar ve alınan kararlar: [docs/YOL_HARITASI.md](docs/YOL_HARITASI.md)

- [x] Geliştirme ortamı, CI
- [x] Veri toplama, kalite raporu, temizlik
- [x] Keşifsel veri analizi (EDA)
- [x] Özellik mühendisliği (meteoroloji, tatiller, diğer kirleticiler)
- [x] Gerçek istasyon ölçümlerine geçiş (SİM) ve hava tahmini özellikleri
- [x] Modelleme ve geri test: ham CAMS'a göre MAE %47,7 daha düşük
- [x] Hata analizi, istasyon bazlı uyarı eşiği, tahmin aralıkları, açıklanabilirlik (SHAP), final model
- [x] Deney takibi: MLflow yerine hafif kayıt (`reports/deney_kaydi.csv` + `models/model_card.json`)
- [ ] Optuna ile hiperparametre araması (isteğe bağlı; zirve deneyi sınırın parametrede değil bilgide olduğunu gösterdi)
- [ ] FastAPI (`/forecast/{station}`, `/alerts`)
- [ ] Streamlit panosu + Türkiye haritası
- [ ] Docker + GitHub Actions ile günlük otomatik tahmin
- [ ] Hugging Face Spaces'e deploy

## Sınırlamalar
- **Uyarı yakalama istasyondan istasyona değişiyor.** Havuzlanmış recall (0,66), uyarının sık görüldüğü istasyonlara ağırlık verir. İstasyon bazında 0,14 (İstanbul-Ümraniye, uyarı oranı %2,7) ile 0,79 (İzmir-Konak) arasında değişiyor. İstasyon bazlı eşik ayarı planlanıyor.
- **Ankara istasyonları düşük güvenli.** İki Ankara istasyonunda kış gecesi ölçümleri şüpheli derecede düşük. Bunlar çıkarıldığında genel sonuç değişmiyor, sonuçlar ayrıca raporlanıyor.
- **CAMS karşılaştırması CAMS lehine iyimser.** Geçmiş CAMS tahmin arşivi açık olmadığı için CAMS'ın analiz değerleri kullanıldı; gerçek bir 24 saatlik CAMS tahmini bundan daha hatalı olurdu.
- **Kapsam:** 5 şehirde 8 istasyon ve tek tahmin ufku (24 saat). Daha uzun ufuklar için 2+ günlük tahmin arşivi gerekiyor.

## Sorumluluk Reddi
Bu proje eğitim ve portföy amaçlıdır. Tahminler resmi hava kalitesi uyarılarının yerine geçmez ve sağlık tavsiyesi değildir.
