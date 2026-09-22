# HavaUyarı: Faz Planı

Her alt faz tek başına tamamlanabilir, küçük bir iştir. Alt faz bitince kutucuğu işaretle ve
(Faz 0.4'ten itibaren) ayrı bir commit at. **Çıktı** o alt fazda üretilecek somut şeydir,
**Bitti sayılır** ise geçmeden önce kontrol edilecek kriterdir.

Toplam süre tahmini: ~7 hafta (haftada 10-15 saat).

---

## FAZ 0: Geliştirme Ortamı (WSL) · ~1-2 gün

- [x] **0.1 WSL2 + Ubuntu kurulumu**
  - Çıktı: Ubuntu 24.04 çalışan WSL2
  - Bitti sayılır: `wsl -l -v` Ubuntu'yu VERSION 2 olarak gösteriyor
- [x] **0.2 Linux'ta Python araçları**
  - Çıktı: `uv` (veya `python3.12-venv`), `git`, `make`, `build-essential`
  - Bitti sayılır: `python3 --version`, `make --version` çalışıyor
- [x] **0.3 Projeyi Linux dosya sistemine taşıma**
  - Çıktı: `~/projects/havauyari` (OneDrive/`/mnt/c` altında değil: hem yavaş hem senkron çakışması riski)
  - Bitti sayılır: `.venv` Linux içinde yeniden kuruldu
- [x] **0.4 Git + GitHub**
  - Çıktı: `git init`, ilk commit, GitHub'da public repo, SSH anahtarı
  - Bitti sayılır: `git push` çalışıyor, repo GitHub'da görünüyor
- [ ] **0.5 Editör bağlantısı**
  - Çıktı: VS Code + WSL eklentisi (`code .` ile açılıyor)
- [ ] **0.6 Ortam doğrulama**
  - Bitti sayılır: `pytest -q` → 19/19 test geçiyor, `ruff check` temiz, GitHub Actions CI yeşil

## FAZ 1: Veri Toplama ve Keşif (EDA) · ~1 hafta

- [ ] **1.1 Ham veri indirme**
  - Çıktı: `data/raw/*.parquet` (5 şehir × 2023'ten bugüne saatlik)
- [ ] **1.2 Veri kalite raporu**
  - Çıktı: eksik veri oranı, en uzun boşluklar, aykırı değerler, zaman damgası tutarlılığı (yaz saati yok ama kontrol et)
- [ ] **1.3 Temizlik**
  - Çıktı: `data/processed/all_cities.parquet`
  - Bitti sayılır: saatlik frekans kesintisiz, negatif değer yok
- [ ] **1.4 EDA notebook'u** (`notebooks/01_eda.ipynb`)
  - Çıktı: saatlik/haftalık/yıllık desenler, kış ısınma etkisi, rüzgâr–PM2.5 ilişkisi,
    şehir karşılaştırması, kirleticiler arası korelasyon, otokorelasyon (ACF/PACF)
- [ ] **1.5 Bulguların özeti**
  - Çıktı: README'ye 3-5 maddelik "Veriden öğrendiklerimiz" + 2-3 grafik

## FAZ 2: Özellik Mühendisliği · ~3-4 gün

- [ ] **2.1 Geçmiş değer özellikleri** (lag, kayan ortalama/std): mevcut, EDA'ya göre gözden geçir
- [ ] **2.2 Takvim ve tatil özellikleri** (resmî tatiller, bayramlar, okul dönemi)
- [ ] **2.3 Meteoroloji özellikleri**
  - Çıktı: rüzgâr u/v, sıcaklık farkı (inversiyon göstergesi), yağış birikimi
  - Not: tahmin anında gelecekteki hava durumu ancak *hava tahmini* olarak bilinir.
    Önce sadece geçmiş hava durumu kullanılır, gelecek hava tahmini ayrı bir deney (Faz 3.5).
- [ ] **2.4 Sızıntı testleri genişletme**
  - Bitti sayılır: her yeni özellik için "t anında sadece ≤ t bilgisi" testi var

## FAZ 3: Modelleme · ~1 hafta

- [ ] **3.1 Walk-forward doğrulama çerçevesi** (mevcut, fold sayısı ve test penceresi sabitlenir)
- [ ] **3.2 Baseline sonuçları**: Persistence, Seasonal Naive, hareketli ortalama → ilk sonuç tablosu
- [ ] **3.3 İlk LightGBM modeli** (24 saat ufku)
  - Bitti sayılır: baseline'dan daha iyi MAE
- [ ] **3.4 Çoklu ufuk**: 24 / 48 / 72 saat. Direkt ve recursive yöntem karşılaştırması
- [ ] **3.5 Alternatif modeller**: Ridge, Random Forest, (opsiyonel) Prophet / LSTM, gelecek hava tahmini deneyi
  - Çıktı: `notebooks/03_modeling.ipynb` + model karşılaştırma tablosu

## FAZ 4: İyileştirme, Değerlendirme, Açıklanabilirlik · ~1 hafta

- [ ] **4.1 Deney takibi**: MLflow ile tüm denemelerin kaydı
- [ ] **4.2 Hiperparametre araması**: Optuna (walk-forward skoru üzerinden)
- [ ] **4.3 Hata analizi**: şehir / mevsim / saat / ufuk bazında hata, en kötü 10 dönem incelemesi
- [ ] **4.4 Uyarı eşiği ayarı**: kaçırılan alarmı azaltmak için eşik kaydırma
  - Bitti sayılır: "Sağlıksız" seviyesinde recall ≥ 0.80
- [ ] **4.5 Tahmin aralığı**: quantile LightGBM (%10–%90 bandı)
- [ ] **4.6 SHAP**: global önem + tek tahmin açıklaması
- [ ] **4.7 Final model kaydı**: `models/` altında sürümlü model + metrik JSON

## FAZ 5: Tahmin Servisi (API) · ~3-4 gün

- [ ] **5.1 Tahmin pipeline'ı**: `predict.py`: son veriyi çek → özellik → tahmin → AQI → uyarı
- [ ] **5.2 FastAPI**: `GET /health`, `GET /forecast/{city}?hours=24`, `GET /alerts`, Pydantic şemaları
- [ ] **5.3 API testleri** (`TestClient`)
- [ ] **5.4 Önbellek**: aynı saat içindeki tekrar isteklerde Open-Meteo'ya gitmeme

## FAZ 6: Kullanıcı Arayüzü (Streamlit) · ~4-5 gün

- [ ] **6.1 Uygulama iskeleti**: şehir seçimi, API'den veri çekme
- [ ] **6.2 Tahmin grafiği**: 72 saat + belirsizlik bandı + AQI renkli arka plan
- [ ] **6.3 Türkiye haritası** (Folium): şehir başına anlık/yarınki kategori
- [ ] **6.4 Açıklama ve öneri**: SHAP "neden?" paneli, bilgilendirme amaçlı öneriler (tıbbi tavsiye değil)
- [ ] **6.5 Model performans sayfası**: geçmiş tahmin ve gerçekleşen karşılaştırması

## FAZ 7: MLOps ve Otomasyon · ~3-4 gün

- [ ] **7.1 Docker**: `Dockerfile` + `docker-compose.yml` (api + app)
- [ ] **7.2 CI genişletme**: testler + lint + Docker build
- [ ] **7.3 Günlük tahmin işi**: GitHub Actions cron → veri çek, tahmin üret, sonuçları kaydet
- [ ] **7.4 İzleme**: tahmin ve gerçekleşen değerlerin kaydı, hata artarsa uyarı (drift sinyali)
- [ ] **7.5 (Opsiyonel) Haftalık yeniden eğitim**

## FAZ 8: Yayın ve Portföy · ~2-3 gün

- [ ] **8.1 Deploy**: Streamlit → Hugging Face Spaces, API → Render
- [ ] **8.2 README son hali**: mimari diyagram, demo GIF, sonuç tablosu, canlı link, sınırlamalar
- [ ] **8.3 v1.0.0 sürümü**: GitHub Release + CHANGELOG
- [ ] **8.4 Portföy metinleri**: CV maddesi, LinkedIn gönderisi, GitHub profilinde pin
- [ ] **8.5 Canlı test**: cron en az 1 hafta kesintisiz çalışmış olmalı

---

### Özet takvim
| Hafta | Fazlar |
|---|---|
| 0 | Faz 0 |
| 1 | Faz 1 |
| 2 | Faz 2 + Faz 3.1–3.2 |
| 3 | Faz 3.3–3.5 |
| 4 | Faz 4 |
| 5 | Faz 5 + Faz 6.1–6.2 |
| 6 | Faz 6.3–6.5 + Faz 7 |
| 7 | Faz 8 |
