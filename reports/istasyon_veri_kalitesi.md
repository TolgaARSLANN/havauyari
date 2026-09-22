# İstasyon Veri Kalitesi

_Oluşturulma: 2026-09-22 · Kaynak: SİM saatlik ölçüm + istasyon koordinatında Open-Meteo (CAMS, ERA5) · Üreten: `python -m havauyari.data.stations`_

## Temizlik

Kurallar `src/havauyari/data/stations.py` başındadır. Hedef (istasyon PM2.5) interpole edilmez; yalnızca ölçülmüş saatler hedef olarak kullanılır.

| istasyon | ölçüm_saati | ≤0 | takılı_sensör | tek_sıçrama | pm25>pm10 | kalan_ölçüm | saat_aralığı | hedef_dolu_% |
|---|---|---|---|---|---|---|---|---|
| Ankara - Keçiören Sanatoryum | 31305 | 6 | 7 | 0 | 63 | 31292 | 32544 | 95.9 |
| Ankara - Etimesgut | 31258 | 2 | 68 | 0 | 348 | 31188 | 32544 | 95.5 |
| Bursa | 29708 | 55 | 20 | 4 | 472 | 29629 | 32544 | 90.8 |
| Bursa - Kültür Park-MTHM | 29553 | 0 | 0 | 0 | 0 | 29553 | 32544 | 90.5 |
| İstanbul - Sultangazi-MTHM | 31402 | 0 | 12 | 0 | 339 | 31390 | 32544 | 96.2 |
| İstanbul - Ümraniye-MTHM | 31144 | 0 | 0 | 0 | 570 | 31144 | 32544 | 95.4 |
| İzmir - Konak | 26754 | 0 | 0 | 1 | 0 | 26753 | 32544 | 81.9 |
| Kocaeli | 28565 | 0 | 0 | 1 | 2281 | 28564 | 32544 | 87.5 |

## CAMS (istasyon koordinatında) ile istasyon ölçümü

Gecikme > 0: istasyon, CAMS'ın k saat önceki değeriyle en iyi eşleşiyor (CAMS erken).

| istasyon | ort. istasyon | ort. CAMS | CAMS/istasyon | korelasyon | en iyi gecikme (s) | gecikmeli korelasyon | kış zirve saati (ist.) | kış zirve saati (CAMS) | uyarı saati % (≥35,5) |
|---|---|---|---|---|---|---|---|---|---|
| ankara_etimesgut | 9.17 | 16.47 | 1.80 | 0.46 | 6 | 0.57 | 14 | 22 | 4.10 |
| ankara_kecioren_sanatoryum | 10.82 | 19.66 | 1.82 | 0.40 | 5 | 0.55 | 13 | 21 | 3.41 |
| bursa | 25.20 | 20.52 | 0.81 | 0.50 | 3 | 0.58 | 11 | 21 | 21.54 |
| bursa_kultur_park_mthm | 24.78 | 15.95 | 0.64 | 0.34 | 4 | 0.42 | 12 | 21 | 19.63 |
| istanbul_sultangazi_mthm | 19.98 | 14.78 | 0.74 | 0.61 | 2 | 0.64 | 22 | 21 | 7.49 |
| istanbul_umraniye_mthm | 13.96 | 18.58 | 1.33 | 0.64 | 2 | 0.68 | 21 | 20 | 2.68 |
| izmir_konak | 32.13 | 18.77 | 0.58 | 0.38 | 1 | 0.40 | 22 | 22 | 32.41 |
| kocaeli | 22.61 | 17.67 | 0.78 | 0.50 | 2 | 0.54 | 12 | 21 | 14.63 |

## Saat hizası kontrolü

Ozon fotokimyasal olarak öğleden sonra zirve yapar. Temmuz 2025 medyan profilinde Ankara-Keçiören istasyonunun ozon zirvesi 13:00, CAMS'ınki 13:00; ERA5 sıcaklık zirvesi 13–16 arası. SİM zaman damgaları yerel saattir ve kaydırma gerekmez. İstasyon ozon zirvesinin İstanbul/Bursa/Kocaeli'de CAMS'tan 2–4 saat geç olması, PM2.5'teki kaymayla aynı yönde: CAMS olayları sistematik olarak erken gösteriyor.

