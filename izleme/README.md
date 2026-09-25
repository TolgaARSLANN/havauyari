# Canlı izleme kayıtları

Bu klasörü günlük tahmin işi (`.github/workflows/gunluk-tahmin.yml`, her gün 08.17 TSİ) günceller;
elle düzenlenmez. Kod: `src/havauyari/ops/daily.py`.

| Dosya | İçerik |
|---|---|
| `tahmin_kaydi.csv` | Her gün her istasyon için verilen 24 saat sonrası tahmini, %80'lik aralık, uyarı kararı; hedef saat geldikten sonra gerçekleşen ölçüm (`actual`) ve mutlak hata (`abs_error`) |
| `durum.json` | Son çalıştırmanın özeti: tahmin üretilen ve üretilemeyen istasyonlar, son 14 günün canlı ortalama hatası, sapma kararı |

**Sapma kuralı:** Son 14 günde en az 40 tahmin değerlendirildiyse ve canlı ortalama hata geri
testin (6,78 µg/m³) 1,5 katını aşıyorsa sapma işaretlenir ve depoda bir konu (issue) açılır.

Bir istasyon ölçüm göndermezse o gün tahmini üretilmez; hedef saatin ölçümü gecikirse kayıt
açık kalır ve sonraki çalıştırmalarda (72 saat boyunca) yeniden denenir.
