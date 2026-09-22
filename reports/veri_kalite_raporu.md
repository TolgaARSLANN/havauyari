# Veri Kalite Raporu

_Oluşturulma: 2026-09-22 · Kaynak: `data/raw/*.parquet` (Open-Meteo, CAMS + ERA5) · Üreten: `python -m havauyari.data.quality`_

## 1. Kapsam

| şehir | başlangıç | bitiş | satır | beklenen | tekrar | eksik saat |
|---|---|---|---|---|---|---|
| ankara | 2023-01-01 00:00:00 | 2026-09-17 23:00:00 | 32544 | 32544 | 0 | 0 |
| bursa | 2023-01-01 00:00:00 | 2026-09-17 23:00:00 | 32544 | 32544 | 0 | 0 |
| istanbul | 2023-01-01 00:00:00 | 2026-09-17 23:00:00 | 32544 | 32544 | 0 | 0 |
| izmir | 2023-01-01 00:00:00 | 2026-09-17 23:00:00 | 32544 | 32544 | 0 | 0 |
| kocaeli | 2023-01-01 00:00:00 | 2026-09-17 23:00:00 | 32544 | 32544 | 0 | 0 |

## 2. Eksik değer oranı (%)

| değişken (% boş) | ankara | bursa | istanbul | izmir | kocaeli |
|---|---|---|---|---|---|
| pm2_5 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| pm10 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| nitrogen_dioxide | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| ozone | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| carbon_monoxide | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| sulphur_dioxide | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| temperature_2m | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| relative_humidity_2m | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| wind_speed_10m | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| wind_direction_10m | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| surface_pressure | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| precipitation | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

## 3. Fiziksel sınır dışı değer sayısı

Sınırlar `PHYSICAL_LIMITS` sözlüğünde tanımlıdır.

| değişken | ankara | bursa | istanbul | izmir | kocaeli |
|---|---|---|---|---|---|
| pm2_5 | 0 | 0 | 0 | 0 | 0 |
| pm10 | 0 | 0 | 0 | 0 | 0 |
| nitrogen_dioxide | 0 | 0 | 0 | 0 | 0 |
| ozone | 0 | 0 | 0 | 0 | 0 |
| carbon_monoxide | 0 | 0 | 0 | 0 | 0 |
| sulphur_dioxide | 0 | 0 | 0 | 0 | 0 |
| temperature_2m | 0 | 0 | 0 | 0 | 0 |
| relative_humidity_2m | 0 | 0 | 0 | 0 | 0 |
| wind_speed_10m | 0 | 0 | 0 | 0 | 0 |
| wind_direction_10m | 0 | 0 | 0 | 0 | 0 |
| surface_pressure | 0 | 0 | 0 | 0 | 0 |
| precipitation | 0 | 0 | 0 | 0 | 0 |

## 4. Tutarlılık ve anomaliler

| şehir | PM2.5 > PM10 | PM2.5 sabit koşu (≥6s) | PM2.5 en uzun sabit koşu (s) | PM2.5 sıçrama (robust z > 6) |
|---|---|---|---|---|
| ankara | 12 | 0 | 4 | 72 |
| bursa | 7 | 0 | 5 | 44 |
| istanbul | 28 | 0 | 5 | 288 |
| izmir | 11 | 0 | 5 | 91 |
| kocaeli | 15 | 0 | 4 | 2 |

Diğer değişkenlerde 12 saat ve üzeri değişmeyen koşular:

| şehir / değişken | koşu (≥12s) | en uzun (s) |
|---|---|---|
| ankara / ozone | 1 | 15 |
| istanbul / ozone | 4 | 14 |
| izmir / ozone | 1 | 14 |

## 5. PM2.5 dağılımı (µg/m³)

| şehir | mean | std | min | 50% | 90% | 99% | max |
|---|---|---|---|---|---|---|---|
| ankara | 19.5 | 16.2 | 2.1 | 14.1 | 38.7 | 84.3 | 159.7 |
| bursa | 15.6 | 9.4 | 1.7 | 13.2 | 27.6 | 49.7 | 94.7 |
| istanbul | 21.8 | 18.9 | 3.2 | 15.6 | 42.4 | 100.5 | 227.1 |
| izmir | 18.2 | 10.8 | 2.8 | 15.4 | 31.9 | 57.2 | 98.0 |
| kocaeli | 17.1 | 9.3 | 1.8 | 15.1 | 29.5 | 48.4 | 90.0 |

### Aylık medyan PM2.5 (µg/m³)

| şehir | Oca | Şub | Mar | Nis | May | Haz | Tem | Ağu | Eyl | Eki | Kas | Ara |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ankara | 29.5 | 20.9 | 19.5 | 15.6 | 13.4 | 9.8 | 9.3 | 10.3 | 11.4 | 16.1 | 20.4 | 28.4 |
| bursa | 13.2 | 14.0 | 16.6 | 15.4 | 13.3 | 12.2 | 11.0 | 12.3 | 13.1 | 13.5 | 11.8 | 14.4 |
| istanbul | 21.7 | 21.2 | 24.7 | 18.4 | 15.7 | 12.4 | 11.3 | 11.3 | 11.7 | 16.1 | 18.1 | 22.8 |
| izmir | 18.9 | 17.3 | 19.1 | 17.0 | 15.0 | 13.3 | 11.6 | 13.4 | 13.9 | 15.4 | 16.1 | 19.9 |
| kocaeli | 18.1 | 16.6 | 20.6 | 16.2 | 14.8 | 12.4 | 11.3 | 12.1 | 13.2 | 15.9 | 17.3 | 20.1 |

### Saate göre medyan PM2.5 (µg/m³)

| şehir | 00:00 | 03:00 | 06:00 | 09:00 | 12:00 | 15:00 | 18:00 | 21:00 |
|---|---|---|---|---|---|---|---|---|
| ankara | 18.6 | 15.2 | 16.2 | 16.9 | 11.8 | 10.0 | 12.4 | 19.1 |
| bursa | 15.9 | 13.8 | 13.8 | 13.4 | 10.8 | 10.3 | 12.5 | 16.4 |
| istanbul | 17.8 | 15.8 | 15.9 | 16.4 | 12.9 | 12.6 | 15.7 | 20.1 |
| izmir | 19.3 | 17.4 | 17.9 | 16.4 | 12.8 | 11.6 | 13.4 | 17.9 |
| kocaeli | 17.6 | 17.0 | 17.4 | 17.1 | 12.8 | 11.0 | 12.4 | 16.6 |

### Yıllık ortalama PM2.5 (µg/m³)

Son yıl kısmi olduğu için (Eylül'e kadar) kış ayları eksik ve ortalama düşük görünür.

| şehir | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|
| ankara | 18.8 | 19.7 | 22.3 | 16.5 |
| bursa | 15.1 | 16.3 | 16.3 | 14.5 |
| istanbul | 19.0 | 22.6 | 25.3 | 19.4 |
| izmir | 19.5 | 17.9 | 19.0 | 15.7 |
| kocaeli | 17.1 | 17.1 | 18.1 | 15.6 |

## 6. AQI seviyelerinin görülme oranı (% saat)

| şehir (% saat) | ≥9.1 (Orta) | ≥35.5 (Hassas gruplar için sağlıksız) | ≥55.5 (Sağlıksız) | ≥125.5 (Çok sağlıksız) | ≥225.5 (Tehlikeli) |
|---|---|---|---|---|---|
| ankara | 77.82 | 12.01 | 4.38 | 0.07 | 0.00 |
| bursa | 76.18 | 4.38 | 0.49 | 0.00 | 0.00 |
| istanbul | 85.17 | 14.00 | 5.37 | 0.42 | 0.00 |
| izmir | 84.91 | 7.09 | 1.20 | 0.00 | 0.00 |
| kocaeli | 82.23 | 4.80 | 0.34 | 0.00 | 0.00 |

## 7. Şehirler arası korelasyon (günlük ortalama PM2.5)

| günlük PM2.5 | ankara | bursa | istanbul | izmir | kocaeli |
|---|---|---|---|---|---|
| ankara | 1.00 | 0.55 | 0.67 | 0.66 | 0.66 |
| bursa | 0.55 | 1.00 | 0.43 | 0.71 | 0.69 |
| istanbul | 0.67 | 0.43 | 1.00 | 0.59 | 0.75 |
| izmir | 0.66 | 0.71 | 0.59 | 1.00 | 0.73 |
| kocaeli | 0.66 | 0.69 | 0.75 | 0.73 | 1.00 |

