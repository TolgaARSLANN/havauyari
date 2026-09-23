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

- [x] **3.1 Walk-forward doğrulama çerçevesi** (mevcut, fold sayısı ve test penceresi sabitlenir)
  - Sonuç: `evaluation/backtest.py`. Son 12 × 30 gün (2025-09-23 → 2026-09-18) test ediliyor,
    genişleyen eğitim penceresi, **arındırma** (hedefi test dönemine düşen eğitim satırları
    çıkarılıyor; eski kodda son 24 saatin etiketleri test dönemine sızıyordu), birleştirilmiş
    metrikler ve mevsim/şehir kırılımları.
  - Ana uyarı eşiği kodda 35,5 µg/m³ olarak sabitlendi (`aqi.ALERT_INDEX`), 55,5 ikinci kademe.
  - Çıktı: `reports/backtest_h24.md` (`make train`), tahminler `data/processed/preds_h24.parquet`.
- [x] **3.2 Baseline sonuçları**: Persistence, Seasonal Naive, hareketli ortalama → ilk sonuç tablosu
  - Eklenen referans: **klimatoloji** (eğitim verisinde şehir × ay × saat medyanı).
  - En iyi referans persistence (MAE 7,43); klimatoloji MAE'de yakın (7,98) ama uyarıların
    yalnızca %14'ünü yakalıyor.
- [x] **3.3 İlk LightGBM modeli** (24 saat ufku)
  - Bitti sayılır: baseline'dan daha iyi MAE
  - Sonuç: MAE 6,75 → persistence'tan **%9,2 iyi**; her mevsimde ve her şehirde daha iyi.
    12 pencerenin 11'inde önde (Haziran 2026 penceresinde geride).
  - **Zayıf nokta:** uyarı recall 0,42 (persistence 0,52), ≥ 55,5 recall 0,28 (persistence
    0,43). Precision daha yüksek (0,62 vs 0,52): model temkinli, zirveleri bastırıyor.
    Faz 3.5 (hava tahmini) ve Faz 4.4 (eşik/quantile) bunu hedefleyecek.
- [ ] **3.4 Çoklu ufuk**: 24 / 48 / 72 saat. Direkt ve recursive yöntem karşılaştırması
  - Sıra değişikliği: Faz 3.5'teki hava tahmini deneyi 3.4'ten önce yapılacak (Faz 2 sonucu).
- [ ] **3.5 Alternatif modeller**: Ridge, Random Forest, (opsiyonel) Prophet / LSTM, gelecek hava tahmini deneyi
  - Çıktı: `notebooks/03_modeling.ipynb` + model karşılaştırma tablosu

### ⚠️ Yön değişikliği: hedef = gerçek istasyon ölçümü (Faz 3.6–3.9)

**Neden:** Hedef olarak kullanılan PM2.5 serisi CAMS atmosfer modelinin çıktısı. CAMS'ın kendisi
de tahmin yayımladığı için "CAMS verisini tahmin etmek" gerçek dünyada anlamlı bir başarı ölçüsü
değil; CAMS'ın geçmiş tahmin arşivi de Open-Meteo'da yok. Asıl değer, **yerel istasyonda gerçekte
ölçülecek** kirliliği tahmin etmek. Böylece CAMS verisi hedef değil, modelin güçlü bir girdisi olur.

**Veri erişimi:** Bakanlık SİM "İstasyon Veri İndirme" sayfasının JSON uç noktaları
(`data/fetch_sim.py`). 5 şehirde 104 istasyon, 47'si PM2.5 ölçüyor. Geçmiş hava tahmini
(1 gün önceki model çalıştırması) Open-Meteo Previous Runs API'de 2024'ten beri tam mevcut.

- [x] **3.6 İstasyon verisi toplama**
  - Kapsam taraması: [`reports/istasyon_kapsami.md`](../reports/istasyon_kapsami.md).
  - Seçim kuralı: kentsel alan, sanayi kaynaklı değil, tüm dönemde ve son yılda PM2.5 kapsamı
    ≥ %80, şehir başına en fazla 2 → 8 istasyon (Ankara 2, Bursa 2, İstanbul 2, İzmir 1, Kocaeli 1).
  - Saatlik PM2.5 + PM10, 2023-01-01'den bugüne; istasyon başına ~32.600 saat, PM2.5 doluluğu
    %82–96. İstekler arasında 2 sn bekleme, her yanıt `data/raw/sim/hourly/` altında önbellekte.
  - **İlk karşılaştırma (şehir merkezi CAMS değeri ile istasyon ölçümü):**

    | İstasyon | Ort. istasyon | Ort. CAMS | Korelasyon | CAMS MAE | Persistence 24 s MAE | Uyarı % | CAMS uyarı recall |
    |---|---|---|---|---|---|---|---|
    | Ankara-Etimesgut | 9,2 | 19,6 | 0,34 | 13,1 | 5,5 | 4,1 | 0,45 |
    | Ankara-Keçiören | 10,8 | 19,7 | 0,40 | 11,8 | 6,5 | 3,4 | 0,60 |
    | Bursa | 25,2 | 15,9 | 0,30 | 14,0 | 13,7 | 21,5 | 0,11 |
    | Bursa-Kültür Park | 24,8 | 16,0 | 0,34 | 12,9 | 13,5 | 19,6 | 0,13 |
    | İstanbul-Sultangazi | 20,0 | 21,9 | 0,58 | 9,0 | 7,8 | 7,5 | 0,68 |
    | İstanbul-Ümraniye | 14,0 | 21,7 | 0,62 | 9,5 | 5,8 | 2,7 | 0,81 |
    | İzmir-Konak | 32,1 | 18,8 | 0,38 | 17,8 | 12,9 | 32,4 | 0,15 |
    | Kocaeli | 22,6 | 17,7 | 0,49 | 9,3 | 9,5 | 14,6 | 0,20 |

    CAMS yerel ölçümü zayıf temsil ediyor (korelasyon 0,30–0,62) ve şehre göre ters yönde
    sapıyor (Ankara'da ~2 kat yüksek, Bursa/İzmir'de %35–40 düşük). Yerel model için alan büyük.
- [x] **3.7 İstasyon verisi kalitesi ve temizlik**
  - Negatif/sıfır değerler, uç değerler (İzmir-Konak maks. 411 µg/m³), boşluk yapısı.
  - **Zaman hizası:** istasyon–CAMS en yüksek korelasyonu 1–3 saat gecikmede veriyor ve şehre göre
    değişiyor. SİM zaman damgası kuralı (saat başı/sonu, yerel/UTC) doğrulanmalı.
  - CAMS ve hava durumu verisini şehir merkezi yerine istasyon koordinatlarından çekmek.
  - Sonuç: `data/stations.py` → `data/processed/stations.parquet` (8 istasyon × 32.544 saat) ve
    [`reports/istasyon_veri_kalitesi.md`](../reports/istasyon_veri_kalitesi.md).
  - **Saat hizası çözüldü:** SİM yerel saat kullanıyor (yerel 20:20'de son kayıt 20:00).
    Kesin test ozon: fotokimyasal ozon öğleden sonra zirve yapar; Ankara-Keçiören istasyonunda
    13:00, CAMS'ta 13:00 → istasyon saatleri doğru, kaydırma yapılmadı. Gecikme taraması ±12 saate
    genişletilince istasyon CAMS'ın 1–6 saat gerisinde (İzmir 1, İstanbul/Kocaeli 2, Bursa 3–4,
    Ankara 5–6); istasyon ozon zirvesi de CAMS'tan 2–4 saat geç. Sonuç: CAMS olayları sistematik
    olarak erken gösteriyor. Model, CAMS'ın hedef öncesi saatlerini özellik olarak alıp bu kaymayı
    öğrenecek (canlı sistemde CAMS'ın 4 günlük tahmini mevcut olduğu için gerçekçi).
  - **Temizlik:** PM2.5 ≤ 0 (63 saat), ≥ 6 saat takılı değer (107 saat), tek saatlik sıçrama
    (6 saat) → NaN. Hedef interpole edilmiyor. PM2.5 > PM10 (farklı cihazlar; Kocaeli'de 2.281
    saat) düzeltilmeden raporlanıyor.
  - **İstasyon koordinatının etkisi:** CAMS–istasyon korelasyonu şehir merkezi yerine istasyon
    noktası kullanılınca yükseldi (Bursa 0,30 → 0,50, Ankara-Etimesgut 0,34 → 0,46).
  - **Ankara notu:** iki Ankara istasyonunda kış gecesi değerleri çok düşük (medyan 7–9 µg/m³)
    ve zirve öğleden sonra; CAMS ise gece 50 µg/m³ civarında. Saat hatası değil (ozon testi),
    ancak ölçüm düzeyi Ankara için şaşırtıcı derecede düşük. Sonuçlar istasyon bazında
    raporlanacak; Ankara sonuçları "düşük güven" olarak işaretlenecek.
- [x] **3.8 Hava tahmini özellikleri**: Previous Runs API'den 1 gün önce yayımlanmış rüzgâr,
  yağış, sıcaklık, nem, basınç tahmini (hedef saate hizalı). Eğitim 2024'ten itibaren.
  - Sonuç: `data/fetch_forecasts.py` (istasyon koordinatlarında day1 tahminleri, önbellekli),
    `features.build.add_weather_forecast` (17 özellik), istasyon veri setine eklendi.
  - Kapsam: sıcaklık 2023'ten, diğerleri 2024-01-19'dan itibaren; test döneminde %99,7 dolu.
    2023 eğitim satırlarında bu özellikler boş (LightGBM boş değeri doğal olarak işler).
  - **Tahmin kalitesi (ERA5'e göre, 2024-02 sonrası):** sıcaklık MAE 1,15 °C (r 0,99), nem 6,8 %,
    rüzgâr 2,8 km/sa (r 0,80), basınç 0,45 hPa, yağış r 0,37. Tüm değişkenlerde en iyi eşleşme
    0 saat gecikmede → zaman hizası doğru.
  - **Sızıntı kuralı:** day1 tahmini geçerlilik anından ≥ 24 saat önce yayımlanır; t anında
    yalnızca (t, t+h] penceresi kullanılıyor ve h ≤ 24 zorunlu (fazlası `ValueError`). Test:
    pencere dışı tahminler/gelecek gözlemler bozulunca özellikler değişmiyor, pencere içi
    tahminler bozulunca değişiyor (3 ufuk). Toplam 71 test.
  - Özellikler: hedef anında sıcaklık/nem/rüzgâr u-v/basınç/bulut; (t, t+h] penceresinde yağış
    toplamı, ort./min. rüzgâr, durgun saat sayısı, sıcaklık min./aralığı, ort. bulut; şu anki
    gözleme göre sıcaklık, rüzgâr ve basınç değişimi.
  - İlk sinyal: Bursa, kış 2025-26 — "önümüzdeki 24 s tahmini durgun saat" ile 24 s sonraki
    istasyon PM2.5 korelasyonu 0,58 (CAMS'ın aynı istasyondaki korelasyonu 0,50).
- [x] **3.9 İstasyon hedefiyle geri test**: aynı walk-forward çerçevesi. Referans modeller:
  istasyon persistence'ı, istasyon klimatolojisi ve **ham CAMS** (hedef anındaki CAMS değeri;
  gerçek tahmin arşivi olmadığı için CAMS lehine iyimser bir referans).
  - Çıktı: [`reports/backtest_istasyon_h24.md`](../reports/backtest_istasyon_h24.md)
    (`python -m havauyari.models.train_station`), 501.000 hizalanmış tahmin satırı.
  - İki model: **lgbm_gercekci** (CAMS yalnızca t'ye kadar + o gün yayımlanmış hava tahmini;
    bugün uygulanabilir → alt sınır) ve **lgbm_iyimser** (+ CAMS'ın hedef anı; ham CAMS
    referansıyla aynı avantaj → üst sınır). Tüm modeller aynı satırlarda ölçülür (`align_models`).

  | Model | MAE | RMSE | Uyarı recall | Uyarı precision |
  |---|---|---|---|---|
  | lgbm_iyimser | 6,50 | 10,45 | 0,68 | 0,73 |
  | **lgbm_gercekci** | **6,78** | **10,78** | **0,66** | **0,73** |
  | moving_avg_24 | 9,09 | 14,12 | 0,57 | 0,61 |
  | persistence | 9,09 | 14,51 | 0,60 | 0,60 |
  | climatology | 10,30 | 17,03 | 0,05 | 0,36 |
  | cams_scaled | 11,15 | 17,32 | 0,41 | 0,47 |
  | seasonal_naive_7d | 11,61 | 18,32 | 0,49 | 0,49 |
  | cams_raw | 12,95 | 19,73 | 0,25 | 0,36 |

  - **Ana sonuç:** gerçekçi model ham CAMS'a göre MAE'de %47,7, en iyi basit referansa göre
    %25,4 daha iyi. Uyarı recall'ü 0,25 (CAMS) → 0,66; precision aynı anda 0,36 → 0,73.
    Yani hem daha çok uyarı yakalanıyor hem daha az yanlış alarm veriliyor.
  - **İyimser ile fark küçük** (MAE 6,50 vs 6,78): model, CAMS'ın gelecek değerlerine bağımlı
    değil; kazancın çoğu istasyon geçmişi + hava tahmininden geliyor. Canlı sistemde gerçek CAMS
    tahmini kullanıldığında sonucun bu iki değer arasında kalması beklenir.
  - Ankara'nın iki düşük güvenli istasyonu çıkarıldığında tablo değişmiyor (gerçekçi model
    MAE 7,51 vs ham CAMS 13,30; recall 0,67 vs 0,24).
  - **Dürüstlük notu:** havuzlanmış recall, uyarının sık olduğu istasyonlara ağırlık verir.
    İstasyon bazında recall 0,14 (İstanbul-Ümraniye, uyarı oranı %2,7) ile 0,79 (İzmir-Konak)
    arasında değişiyor. Faz 4.4'te istasyon bazlı eşik ayarı gerekecek.

## FAZ 4: İyileştirme, Değerlendirme, Açıklanabilirlik · ~1 hafta

- [ ] **4.1 Deney takibi**: MLflow ile tüm denemelerin kaydı
- [ ] **4.2 Hiperparametre araması**: Optuna (walk-forward skoru üzerinden)
  - [x] **Zirve bastırma deneyi** (`models/experiments.py`,
    [`reports/deney_zirve_h24.md`](../reports/deney_zirve_h24.md)): log hedef, Tweedie kaybı,
    yüksek değerlere ağırlık, doğrudan uyarı sınıflandırıcısı; hepsi aynı 24 aylık protokolle
    (walk-forward eşik, recall ≥ %80) karşılaştırıldı. Deney kaydı: `reports/deney_kaydi.csv`.
  - **Sonuç: hiçbir aday mevcut L2 modelini geçmedi** (precision 0,572, F1 0,676). Log hedef ve
    Tweedie MAE'yi hafifçe düşürdü (6,73–6,77) ama zirve sapmasını KÖTÜLEŞTİRDİ (−26,6 / −28,8)
    ve aynı recall hedefinde precision 0,526'ya indi. Ağırlıklı eğitim sapmayı ancak −23,0 →
    −22,0 iyileştirdi. Sınıflandırıcı L2 ile aynı F1'e ulaştı (0,676).
  - **Çıkarım:** zirve bastırma bir kayıp fonksiyonu sorunu değil, **bilgi sınırı**: 24 saat
    önceden elimizdeki verilerle ani yükselişlerin büyüklüğü öngörülemiyor (bkz. Bursa 14 Ocak
    2026). Kaldıraç kayıp fonksiyonunda değil, daha iyi girdide: canlı sistemde gerçek CAMS
    tahmini, istasyonlar arası sinyal, daha uzun meteorolojik bağlam. L2 modeli korunuyor.
  - Yan bulgu: ayarlı eşikle (28,5) yeni başlayan uyarıların yakalanma oranı %34 → %61.
- [x] **4.3 Hata analizi**: şehir / mevsim / saat / ufuk bazında hata, en kötü 10 dönem incelemesi
  - İstasyon hedefli ana model (`lgbm_gercekci`) üzerinde yapıldı:
    [`reports/hata_analizi_istasyon_h24.md`](../reports/hata_analizi_istasyon_h24.md)
    (`python -m havauyari.evaluation.error_analysis`).
  - **Zirveler bastırılıyor:** gerçek ≥ 55,5 µg/m³ saatlerde ortalama sapma −22,9 (35,5–55,5
    aralığında −5,7). Kalibrasyon grafiğinde tahmin ~60'ta doyuyor. Düşük değerlerde (< 10)
    +3,6 fazla tahmin. → Log hedef / quantile kaybı denenecek (4.2, 4.5).
  - **Yeni başlayan uyarılar (erken uyarının asıl değeri):** model %34'ünü yakalıyor;
    persistence tanım gereği %0, CAMS %26. Süren uyarılarda model %86.
  - **Kaçırılan uyarıların çoğu eşiğe yakın:** medyan tahmin 28,7; %70'inde tahmin ≥ 25.
    Tanımlayıcı eşik tablosu: karar eşiği 30'da recall 0,80 / precision 0,60 (35,5'te
    0,66 / 0,73). → Eşik ayarı büyük kazanç vaat ediyor (4.4); seçim test dönemi görülmeden
    yapılmalı.
  - **Hata kışın ve kirli istasyonlarda yoğun:** İzmir-Konak kış MAE 19,1, Bursa 12–13.
    En kötü 10 günün 8'i İzmir-Konak'ta (Aralık 2025, gerçek ort. 100+ µg/m³). Bursa'da
    14 Ocak 2026 epizodu hiç öngörülememiş (gerçek ort. 70–86, tahmin ~20): ani başlayan
    olaylar hâlâ zayıf nokta.
  - Hedef saate göre hata dengeli (MAE 5,7–7,5), belirgin bir saat sorunu yok.
- [x] **4.4 Uyarı eşiği ayarı**: kaçırılan alarmı azaltmak için eşik kaydırma
  - Bitti sayılır: "Sağlıksız" seviyesinde recall ≥ 0.80
  - Kapsam güncellemesi: ana uyarı seviyesi 35,5 (Faz 1.4 kararı); ürün kararı olarak hedef
    **recall ≥ %80** seçildi (hassas grupları korumak öncelikli, yanlış alarm ikincil).
  - Yöntem (`alerts/threshold.py`): gerçek uyarının tanımı değişmez (ölçüm ≥ 35,5); modelin
    tahminine uygulanan karar eşiği ayarlanır. 24 aylık geri test; son 12 pencerenin her birinde
    eşik yalnızca ÖNCEKİ pencerelerin tahminlerinden, recall ≥ %80 sağlayan en yüksek değer
    olarak seçildi (test dönemi görülmedi).
  - **Sonuç (son 12 ay):** recall 0,657 → **0,824** (hedef sağlandı), precision 0,734 → 0,572,
    uyarı saati istasyon başına haftada 21 → 34. Seçilen eşikler kararlı: 28,0–29,5.
  - Canlı sistem eşiği: **28,5 µg/m³** (`models/alert_threshold.json`).
  - Zayıf yanlar: (1) yaz aylarında gerçek uyarı az olduğundan precision 0,15–0,32'ye düşüyor
    (yazın yanlış alarm oranı yüksek) → mevsime göre eşik denenebilir. (2) Tek küresel eşik
    uyarının sık olduğu İzmir/Bursa'ya göre ayarlanıyor; İstanbul-Ümraniye 0,39,
    Ankara-Keçiören 0,48, İstanbul-Sultangazi 0,55'te kalıyor → istasyon bazlı eşik ileride
    değerlendirilebilir. Rapor: [`reports/uyari_esigi_h24.md`](../reports/uyari_esigi_h24.md)
  - **Grup bazlı eşik denemesi** (aynı walk-forward kural, grup başına; 50'den az geçmiş uyarıda
    genel eşik):

    | Strateji | Recall | Precision | F1 | Yaz precision | En düşük istasyon recall |
    |---|---|---|---|---|---|
    | Tek eşik (mevcut) | 0,824 | 0,572 | 0,676 | 0,255 | 0,391 |
    | Mevsime göre | 0,825 | 0,555 | 0,663 | 0,259 | 0,385 |
    | **İstasyona göre** | 0,798 | 0,548 | 0,650 | **0,320** | **0,714** |

    Mevsime göre eşik kazanç getirmedi. İstasyona göre eşik en kötü istasyonun recall'ünü
    0,39 → 0,71'e çıkarıyor ve yaz yanlış alarmını azaltıyor; bedeli genel precision'da −0,024.
    **Karar: istasyon bazlı eşiğe geçildi.** `models/alert_threshold.json` artık istasyon başına
    eşik (18,5–32,0) ve genel yedek eşik (28,5) içeriyor; okuma:
    `alerts.threshold.decision_threshold`.
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
