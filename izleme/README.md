# Canlı izleme kayıtları

Bu klasörü günlük tahmin işi günceller; elle düzenlenmez. Kod: `src/havauyari/ops/daily.py`.

| Dosya | İçerik |
|---|---|
| `tahmin_kaydi.csv` | Her gün her istasyon için verilen 24 saat sonrası tahmini, %80'lik aralık, uyarı kararı; hedef saat geldikten sonra gerçekleşen ölçüm (`actual`) ve mutlak hata (`abs_error`) |
| `durum.json` | Son çalıştırmanın özeti: tahmin üretilen ve üretilemeyen istasyonlar, son 14 günün canlı ortalama hatası, sapma kararı |

## Nerede çalışır?

SİM (sim.csb.gov.tr) yurt dışı IP'lerine kapalı olduğu için GitHub Actions sunucuları ölçümlere
erişemiyor (iki denemede de bağlantı zaman aşımı). Bu yüzden iş iki parçaya ayrıldı:

1. **Üretim (yerel, Türkiye IP'si):** `scripts/gunluk_tahmin.sh`, Windows Görev Zamanlayıcı ile
   her gün 08.17'de ve oturum açılışında çalışır (`scripts/gorev_kur.ps1`). Ayrı bir klonda
   (`~/.havauyari-gunluk`) çalışır, sonucu depoya gönderir. Bilgisayar kapalıysa açılışta telafi
   eder; aynı gün ikinci kez çalışmaz. Günlük: `~/.havauyari-gunluk.log`.
2. **Bekçi (bulut, SİM gerektirmez):** `.github/workflows/izleme.yml` yeni kayıt gelince sapmayı,
   her gün 15.00'te de kaydın güncelliğini denetler (`src/havauyari/ops/check.py`).

## Uyarı kuralları

- **Sapma:** Son 14 günde en az 40 tahmin değerlendirildiyse ve canlı ortalama hata geri testin
  (6,78 µg/m³) 1,5 katını aşıyorsa `sapma` etiketli konu açılır.
- **Kesinti:** `durum.json` 30 saatten eskiyse `kesinti` etiketli konu açılır.

Açık bir konu varsa yeni konu açılmaz, mevcut konuya yorum eklenir. Bir istasyon ölçüm göndermezse
o gün tahmini üretilmez; hedef saatin ölçümü gecikirse kayıt açık kalır ve sonraki çalıştırmalarda
(72 saat boyunca) yeniden denenir.
