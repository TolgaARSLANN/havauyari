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
- [x] **0.5 Editör bağlantısı**
  - Çıktı: VS Code + WSL eklentisi (`code .` ile açılıyor)
  - Not: Claude Code masaüstü uygulaması doğrudan `\\wsl.localhost\Ubuntu-24.04\...` klasöründe çalışıyor; VS Code isteğe bağlı.
- [x] **0.6 Ortam doğrulama**
  - Bitti sayılır: `pytest -q` → 19/19 test geçiyor, `ruff check` temiz, GitHub Actions CI yeşil

## FAZ 1: Veri Toplama ve Keşif (EDA) · ~1 hafta

- [x] **1.1 Ham veri indirme**
  - Çıktı: `data/raw/*.parquet` (5 şehir × 2023'ten bugüne saatlik)
  - Sonuç: 5 şehir × 32.544 saat (2023-01-01 → 2026-09-17), tekrar eden veya eksik saat yok,
    12 değişkenin hiçbirinde boş değer yok.
  - Not: Kirletici değerleri istasyon ölçümü değil, CAMS atmosfer modelinin çıktısı
    (~11 km çözünürlük). Bu yüzden seri kesintisiz ve pürüzsüz; README'de sınırlama olarak belirtilecek.
    Gerçek ölçümlerle karşılaştırma için SİM verisi Faz 4.3'te değerlendirilebilir.
- [x] **1.2 Veri kalite raporu**
  - Çıktı: eksik veri oranı, en uzun boşluklar, aykırı değerler, zaman damgası tutarlılığı (yaz saati yok ama kontrol et)
  - Sonuç: [`reports/veri_kalite_raporu.md`](../reports/veri_kalite_raporu.md) (`python -m havauyari.data.quality`)
  - Bulgular ve 1.3 için kararlar:
    - Eksik değer, fiziksel sınır dışı değer, tekrar eden saat yok.
    - Şehir başına 7-28 saatte PM2.5 > PM10 (fiziksel olarak imkânsız, model yuvarlaması)
      → 1.3'te PM2.5, PM10 ile sınırlanacak.
    - Ani sıçramalar (İstanbul 288 saat / 90 gün) gerçek olaylar: PM2.5/PM10 oranı sıçramalarda
      0.80, genelde 0.72 → yanma kaynaklı (kışın ısınma, yazın orman yangını dumanı).
      Uyarı sisteminin yakalaması gereken olaylar oldukları için **silinmeyecek**.
    - Ozonda 14-15 saatlik sabit koşular var (gece, tam sayı yuvarlaması); dokunulmayacak.
    - Güçlü mevsimsellik (Ankara Ocak medyanı Temmuz'un ~3 katı) ve günlük döngü (öğlen düşük,
      21:00-00:00 zirve) → takvim ve saat özellikleri kritik.
    - Bursa'da mevsimsellik neredeyse yok; CAMS'ın ~11 km çözünürlüğü yerel kış kirliliğini
      kaçırıyor olabilir → README sınırlamalarına eklenecek.
    - Şehirler arası günlük korelasyon 0.43-0.75 → bölgesel etkiler var; diğer şehirlerin geçmiş
      değerleri Faz 2'de özellik olarak denenebilir.
- [x] **1.3 Temizlik**
  - Çıktı: `data/processed/all_cities.parquet`
  - Bitti sayılır: saatlik frekans kesintisiz, negatif değer yok
  - Sonuç: 162.720 satır (5 × 32.544). Kesinti, sınır dışı değer, boş değer yok;
    PM2.5 > PM10 olan 76 saat PM10 ile sınırlandı. Sıçramalar korundu.
  - Düzeltme: `interpolate(limit=n)` uzun boşlukların ilk n saatini de dolduruyordu;
    `fill_short_gaps` yalnızca ≤ 3 saatlik boşlukları dolduruyor (testli).
  - Not (Faz 3.1 için): son 30 günlük tek test penceresinde (Ağu-Eyl) hiç uyarı saati yok,
    alarm metrikleri anlamsız kalıyor → walk-forward pencereleri kış aylarını da kapsamalı.
- [x] **1.4 EDA notebook'u** (`notebooks/01_eda.ipynb`)
  - Çıktı: saatlik/haftalık/yıllık desenler, kış ısınma etkisi, rüzgâr–PM2.5 ilişkisi,
    şehir karşılaştırması, kirleticiler arası korelasyon, otokorelasyon (ACF/PACF)
  - Sonuç: 11 bölüm + özet tablo; grafikler `reports/figures/` altında.
  - Sonraki fazlara aktarılan kararlar (gerekçeler notebook'un 12. bölümünde):
    - Faz 2: rüzgâr hızı kayan ortalaması + durgun saat sayısı, yağış 3/6/24 s toplamı,
      diğer kirleticilerin (PM10, NO₂, SO₂, CO) geçmiş değerleri, resmî tatiller.
      Diğer şehirlerin geçmişi düşük öncelik (24 s gecikmede korelasyon 0,31–0,42).
    - Faz 3: test pencereleri kışı kapsamalı, metrikler mevsime göre de raporlanmalı;
      ham hedef ile `log1p` hedef karşılaştırılmalı (çarpıklık 1,4–3,2 → 0,0–0,7).
    - Faz 3.5 önceliği yükseldi: 24 s sonraki uyarıların %37–64'ü şu an uyarı olmayan saatlerden
      geliyor; başlangıcı yakalamak için gelecek hava tahmini özelliği gerekli olabilir.
    - Ana uyarı eşiği önerisi: 35,5 µg/m³; 55,5 ikinci kademe (Faz 4.4'te kesinleşecek).
- [x] **1.5 Bulguların özeti**
  - Çıktı: README'ye 3-5 maddelik "Veriden öğrendiklerimiz" + 2-3 grafik
  - Sonuç: README'ye 5 bulgu, 3 grafik, veri kapsamı, "Sınırlamalar" bölümü, CI rozeti ve
    `make` tabanlı kurulum adımları eklendi.

## FAZ 2: Özellik Mühendisliği · ~3-4 gün

- [x] **2.1 Geçmiş değer özellikleri** (lag, kayan ortalama/std): mevcut, EDA'ya göre gözden geçir
  - Sonuç: ACF bulgusuyla lag seti (1, 2, 3, 6, 12, 24, 48, 168) korundu. Eklenenler: 24 s kayan
    maksimum, 1 s / 24 s değişim ve **hedef saatle hizalı** geçmiş değerler (hedef anından 1 gün ve
    1 hafta önceki aynı saat).
- [x] **2.2 Takvim ve tatil özellikleri** (resmî tatiller, bayramlar, okul dönemi)
  - Sonuç: `holidays` paketiyle Türkiye resmî tatilleri (dinî bayramlar dahil, 2023-2026'da 55 gün).
    Hedef anının (t+h) saati, haftanın günü, hafta sonu ve tatil bilgisi `tgt_` özellikleri olarak
    eklendi; bunlar önceden bilindiği için sızıntı değil.
  - Kapsam dışı: arefe yarım günleri, köprü tatilleri, okul dönemi (etkisi düşük beklendi).
- [x] **2.3 Meteoroloji özellikleri**
  - Çıktı: rüzgâr u/v, sıcaklık farkı (inversiyon göstergesi), yağış birikimi
  - Not: tahmin anında gelecekteki hava durumu ancak *hava tahmini* olarak bilinir.
    Önce sadece geçmiş hava durumu kullanılır, gelecek hava tahmini ayrı bir deney (Faz 3.5).
  - Sonuç: rüzgâr hızı ve u/v 24 s ortalamaları, durgun saat sayısı (< 4 km/sa), yağış 3/6/24 s
    toplamı, ısıtma derece-saati, 24 s sıcaklık aralığı ve değişimi, basınç değişimi, nem ortalaması;
    PM10, NO₂, SO₂, CO, O₃ için lag 1/24 ve 24 s ortalama; PM2.5/PM10 oranı.
  - Yüksek seviye sıcaklık verisi arşiv API'sinde olmadığı için gerçek inversiyon göstergesi
    hesaplanamadı; yerine "24 s sıcaklık aralığı + durgun saat" vekil olarak kullanıldı.
- [x] **2.4 Sızıntı testleri genişletme**
  - Bitti sayılır: her yeni özellik için "t anında sadece ≤ t bilgisi" testi var
  - Sonuç: genel sızıntı testi: t0 sonrasındaki tüm ölçümler bozulduğunda t0 ve öncesindeki
    **hiçbir** özelliğin değişmediği 5 ufukta (1/6/24/48/72 s) doğrulanıyor. İleride eklenecek
    özellikler de bu testten otomatik geçmek zorunda. Toplam 47 test.

**Faz 2 değerlendirmesi** (24 s ufku, aynı LightGBM ayarları, eski 37 vs yeni 79 özellik):

| Test dönemi | Model | MAE | RMSE | Uyarı recall (≥ 35,5) | Uyarı F1 |
|---|---|---|---|---|---|
| Kış (Ara 2025–Mar 2026) | Persistence | 11,41 | 17,44 | 0,525 | 0,523 |
| | LightGBM, eski özellikler | 10,10 | 15,09 | 0,475 | 0,523 |
| | LightGBM, yeni özellikler | **10,08** | **14,93** | 0,497 | **0,539** |
| Yaz (son 4×30 gün) | Persistence | 3,63 | 5,26 | – | – |
| | LightGBM, eski özellikler | 3,52 | 4,62 | – | – |
| | LightGBM, yeni özellikler | **3,46** | **4,57** | – | – |

- İyileşme küçük: kışın MAE %0,2, RMSE %1,1; yazın MAE %1,6. Kış MAE farkı tohum değişimiyle
  oluşan oynama düzeyinde. Yeni özellikler önem payının %35'ini alsa da çoğunlukla mevcut bilgiyi
  tekrar ediyor.
- **Asıl darboğaz gelecekteki hava durumu:** EDA'da 24 s sonraki uyarıların %37–64'ünün yeni
  başladığı görülmüştü; geçmiş meteoroloji bunu öngörmekte sınırlı. Faz 3.5 (hava tahmini özelliği)
  en büyük kazancı getirecek adım olarak öne çekilmeli.
- **Uyarı yakalama zayıf:** LightGBM kışın MAE'de persistence'tan %12 iyi olmasına rağmen uyarı
  recall'ü daha düşük (0,50 vs 0,53): ortalama hatayı küçülten model zirveleri bastırıyor.
  Faz 4.4'te eşik kaydırma, quantile tahmin ya da ayrı bir uyarı sınıflandırıcısı denenecek.
- Özellik elemesi Faz 4.6'da SHAP ile yapılacak; şimdilik tüm özellikler tutuluyor.

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
