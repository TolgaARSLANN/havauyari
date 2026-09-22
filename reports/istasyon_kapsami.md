# SİM İstasyon Kapsamı (PM2.5)

_Oluşturulma: 2026-09-22 · Dönem: 2023-01-01 → bugün · Üreten: `python -m havauyari.data.fetch_sim survey`_

Kapsam = PM2.5 değeri olan gün sayısı / dönemdeki gün sayısı. Seçim kuralı: kentsel alan, sanayi kaynaklı olmayan, tüm dönemde ve son 1 yılda kapsam ≥ %80 olan istasyonlardan şehir başına en eksiksiz 2 tanesi.

## Şehir özeti

| city | istasyon | pm25_olcen | kapsam_80_ustu |
|---|---|---|---|
| ankara | 19 | 13 | 11 |
| bursa | 10 | 5 | 3 |
| istanbul | 40 | 22 | 4 |
| izmir | 23 | 2 | 1 |
| kocaeli | 12 | 5 | 4 |

## İstasyonlar

| city | name | area_type | source_type | kapsam_% | son_1_yil_% | ilk_gun | son_gun | ort_pm25 | seçildi |
|---|---|---|---|---|---|---|---|---|---|
| ankara | Ankara - Törekent | Kent Çevresi | Sanayi | 98.0 | 98.1 | 2023-01-01 | 2026-09-22 | 7.2 |  |
| ankara | Ankara - Keçiören Sanatoryum | Kentsel | Isınma | 95.7 | 95.3 | 2023-01-01 | 2026-09-22 | 10.8 | ✔ |
| ankara | Ankara - Etimesgut | Kentsel | Isınma | 95.5 | 94.0 | 2023-01-01 | 2026-09-22 | 9.1 | ✔ |
| ankara | Ankara - Sıhhıye | Kentsel | Trafik | 95.2 | 92.9 | 2023-01-01 | 2026-09-22 | 14.7 |  |
| ankara | Ankara - Siteler | Kentsel | Sanayi | 95.1 | 95.6 | 2023-01-01 | 2026-09-22 | 30.4 |  |
| ankara | Ankara - Ostim | Kentsel | Sanayi | 91.8 | 82.2 | 2023-01-01 | 2026-09-22 | 10.5 |  |
| ankara | Ankara - Çankaya | Kentsel | Isınma | 90.4 | 97.5 | 2023-01-01 | 2026-09-22 | 8.3 |  |
| ankara | Ankara - Sincan | Kentsel | Isınma | 90.4 | 77.3 | 2023-01-01 | 2026-09-22 | 17.0 |  |
| ankara | Ankara Yaşamkent | Kentsel | Isınma | 89.3 | 91.0 | 2023-01-07 | 2026-09-22 | 7.4 |  |
| ankara | Ankara - Ulus | Kentsel | Trafik | 88.4 | 73.7 | 2023-01-01 | 2026-09-22 | 20.2 |  |
| ankara | Ankara - Demetevler | Kentsel | Isınma | 80.6 | 46.8 | 2023-01-02 | 2026-08-18 | 15.0 |  |
| ankara | Ankara - Bahçelievler | Kentsel | Isınma | 77.3 | 70.4 | 2023-01-01 | 2026-09-22 | 10.0 |  |
| ankara | Gölbaşı/Ankara (Seyyar - 06DV9981) | Kentsel | Trafik | 3.2 | 11.8 | 2026-02-16 | 2026-08-26 | 14.3 |  |
| ankara | Ankara - Batıkent | Kentsel | Isınma | 0.0 | 0.0 | nan | nan |  |  |
| ankara | Ankara - Etlik | Kentsel | Isınma | 0.0 | 0.0 | nan | nan |  |  |
| ankara | Ankara - Kayaş | Kent Çevresi | Isınma | 0.0 | 0.0 | nan | nan |  |  |
| ankara | Ankara - Mamak | Kentsel | Isınma | 0.0 | 0.0 | nan | nan |  |  |
| ankara | Ankara - Polatlı | Kentsel | Isınma | 0.0 | 0.0 | nan | nan |  |  |
| ankara | EMEP - Ankara Çubuk | Kırsal | Arka Plan | 0.0 | 0.0 | nan | nan |  |  |
| bursa | Bursa | Kentsel | Isınma | 91.3 | 98.4 | 2023-01-01 | 2026-09-22 | 25.2 | ✔ |
| bursa | Bursa - Kültür Park-MTHM | Kentsel | Isınma | 90.2 | 96.7 | 2023-01-01 | 2026-09-22 | 24.7 | ✔ |
| bursa | Bursa - Uludağ Üniv.-MTHM | Kent Çevresi | Arka Plan | 90.2 | 70.1 | 2023-01-01 | 2026-09-22 | 21.1 |  |
| bursa | Bursa-Nilüfer | Kentsel | Isınma | 49.3 | 54.2 | 2023-01-01 | 2026-09-22 | 31.1 |  |
| bursa | Bursa - Nilüfer | Kentsel | Sanayi | 44.0 | 17.5 | 2023-06-23 | 2026-09-22 | 21.3 |  |
| bursa | Bursa - Beyazıt Cad.-MTHM | Kentsel | Trafik | 0.0 | 0.0 | nan | nan |  |  |
| bursa | Bursa - Kestel-MTHM | Kent Çevresi | Sanayi | 0.0 | 0.0 | nan | nan |  |  |
| bursa | Bursa - İnegöl-MTHM | Kentsel | Sanayi | 0.0 | 0.0 | nan | nan |  |  |
| bursa | Bursa-Gürsu | Kentsel | Isınma | 0.0 | 0.0 | nan | nan |  |  |
| bursa | Bursa-Kestel (Hilal Parkı) | Kent Çevresi | Sanayi | 0.0 | 0.0 | nan | nan |  |  |
| istanbul | İstanbul - Sultangazi-MTHM | Kentsel | Trafik | 96.0 | 98.9 | 2023-01-01 | 2026-09-22 | 20.0 | ✔ |
| istanbul | İstanbul - Ümraniye-MTHM | Kentsel | Trafik | 95.8 | 96.2 | 2023-01-01 | 2026-09-21 | 13.9 | ✔ |
| istanbul | İstanbul - Silivri-MTHM | Kentsel | Isınma | 94.9 | 90.7 | 2023-01-01 | 2026-09-22 | 14.3 |  |
| istanbul | İstanbul - Kağıthane-MTHM | Kentsel | Trafik | 88.2 | 80.0 | 2023-01-01 | 2026-09-22 | 17.8 |  |
| istanbul | İstanbul - Beşiktaş | Kentsel | Sanayi | 77.6 | 95.6 | 2023-01-01 | 2026-09-22 | 16.2 |  |
| istanbul | İstanbul - Aksaray | Kentsel | Sanayi | 76.9 | 98.4 | 2023-01-01 | 2026-09-22 | 22.0 |  |
| istanbul | İstanbul - Alibeyköy | Kent Çevresi | Trafik | 75.4 | 89.3 | 2023-01-01 | 2026-09-22 | 17.0 |  |
| istanbul | İstanbul - Beylikdüzü | Kentsel | Trafik | 74.9 | 91.8 | 2023-10-01 | 2026-09-22 | 19.2 |  |
| istanbul | İstanbul - Maslak | Kent Çevresi | Arka Plan | 74.3 | 95.3 | 2023-01-01 | 2026-09-22 | 14.2 |  |
| istanbul | İstanbul - Arnavutköy | Kent Çevresi | Arka Plan | 74.1 | 97.8 | 2023-01-01 | 2026-09-22 | 14.6 |  |
| istanbul | İstanbul - Tuzla | Kent Çevresi | Arka Plan | 74.0 | 93.2 | 2023-01-01 | 2026-09-22 | 18.2 |  |
| istanbul | İstanbul - Avcılar | Kent Çevresi | Arka Plan | 72.2 | 91.0 | 2023-01-01 | 2026-09-22 | 19.3 |  |
| istanbul | İstanbul - Üsküdar | Kentsel | Arka Plan | 71.2 | 83.6 | 2023-01-01 | 2026-09-22 | 11.8 |  |
| istanbul | İstanbul - Selimiye | Kent Çevresi | Arka Plan | 71.1 | 94.2 | 2023-01-01 | 2026-09-21 | 20.7 |  |
| istanbul | İstanbul - Esenler | Kentsel | Trafik | 69.3 | 80.8 | 2023-01-01 | 2026-09-20 | 19.4 |  |
| istanbul | İstanbul - Ümraniye | Kentsel | Trafik | 69.0 | 94.0 | 2023-01-01 | 2026-09-22 | 19.3 |  |
| istanbul | İstanbul - Kadıköy | Kentsel | Trafik | 67.2 | 63.8 | 2023-01-01 | 2026-09-21 | 19.3 |  |
| istanbul | İstanbul - Kartal | Kent Çevresi | Sanayi | 64.2 | 69.9 | 2023-01-01 | 2026-09-22 | 20.9 |  |
| istanbul | İstanbul - Kumköy | Kent Çevresi | Arka Plan | 63.9 | 76.2 | 2023-01-01 | 2026-09-22 | 9.5 |  |
| istanbul | İstanbul - Çatladıkapı | Kent Çevresi | Arka Plan | 60.6 | 90.1 | 2023-01-01 | 2026-09-22 | 17.6 |  |
| istanbul | İstanbul - Kağıthane | Kentsel | Trafik | 59.1 | 64.7 | 2023-01-01 | 2026-09-22 | 24.4 |  |
| istanbul | İstanbul - Bağcılar | Kent Çevresi | Arka Plan | 49.5 | 90.7 | 2023-01-01 | 2026-09-22 | 18.9 |  |
| istanbul | İstanbul - Başakşehir-MTHM | Kentsel | Sanayi | 0.0 | 0.0 | nan | nan |  |  |
| istanbul | İstanbul - Büyükada | Kentsel | Sanayi | 0.0 | 0.0 | nan | nan |  |  |
| istanbul | İstanbul - Esenyurt-MTHM | Kentsel | Isınma | 0.0 | 0.0 | nan | nan |  |  |
| istanbul | İstanbul - Fikirtepe -MTHM | Kentsel | Trafik | 0.0 | 0.0 | nan | nan |  |  |
| istanbul | İstanbul - Göztepe D 100 | Kentsel | Trafik | 0.0 | 0.0 | nan | nan |  |  |
| istanbul | İstanbul - Kandilli | Kentsel | Trafik | 0.0 | 0.0 | nan | nan |  |  |
| istanbul | İstanbul - Kandilli-MTHM | Kentsel | Trafik | 0.0 | 0.0 | nan | nan |  |  |
| istanbul | İstanbul - Mecidiyeköy-MTHM | Kentsel | Trafik | 0.0 | 0.0 | nan | nan |  |  |
| istanbul | İstanbul - Sancaktepe | Kent Çevresi | Arka Plan | 0.0 | 0.0 | nan | nan |  |  |
| istanbul | İstanbul - Sarıyer | Kent Çevresi | Trafik | 0.0 | 0.0 | nan | nan |  |  |
| istanbul | İstanbul - Sultanbeyli-MTHM | Kentsel | Isınma | 0.0 | 0.0 | nan | nan |  |  |
| istanbul | İstanbul - Sultangazi 1 | Kentsel | Isınma | 0.0 | 0.0 | nan | nan |  |  |
| istanbul | İstanbul - Sultangazi 2 | Kentsel | Isınma | 0.0 | 0.0 | nan | nan |  |  |
| istanbul | İstanbul - Sultangazi 3 | Kentsel | Isınma | 0.0 | 0.0 | nan | nan |  |  |
| istanbul | İstanbul - Yenibosna | Kentsel | Sanayi | 0.0 | 0.0 | nan | nan |  |  |
| istanbul | İstanbul - Üsküdar-MTHM | Kentsel | Trafik | 0.0 | 0.0 | nan | nan |  |  |
| istanbul | İstanbul - Şile-MTHM | Kentsel | Arka Plan | 0.0 | 0.0 | nan | nan |  |  |
| istanbul | İstanbul - Şirinevler-MTHM | Kentsel | Trafik | 0.0 | 0.0 | nan | nan |  |  |
| izmir | İzmir - Konak | Kentsel | Trafik | 82.9 | 96.7 | 2023-01-01 | 2026-09-22 | 31.9 | ✔ |
| izmir | İzmir - Bornova | Kent Çevresi | Sanayi | 74.6 | 94.5 | 2023-01-01 | 2026-09-22 | 21.6 |  |
| izmir | EMEP - İzmir Seferihisar | Kentsel | Trafik | 0.0 | 0.0 | nan | nan |  |  |
| izmir | İzmir - Aliağa | Kentsel | Sanayi | 0.0 | 0.0 | nan | nan |  |  |
| izmir | İzmir - Aliağa - Bozköy | Kent Çevresi | Isınma | 0.0 | 0.0 | nan | nan |  |  |
| izmir | İzmir - Alsancak İBB | Kentsel | Sanayi | 0.0 | 0.0 | nan | nan |  |  |
| izmir | İzmir - Bayraklı İBB | Kentsel | Sanayi | 0.0 | 0.0 | nan | nan |  |  |
| izmir | İzmir - Bornova İBB | Kentsel | Isınma | 0.0 | 0.0 | nan | nan |  |  |
| izmir | İzmir - Eğitim İstasyonu | Kentsel | Isınma | 0.0 | 0.0 | nan | nan |  |  |
| izmir | İzmir - Gaziemir | Kentsel | Isınma | 0.0 | 0.0 | nan | nan |  |  |
| izmir | İzmir - Güzelyalı İBB | Kentsel | Sanayi | 0.0 | 0.0 | nan | nan |  |  |
| izmir | İzmir - Karabağlar | Kentsel | Isınma | 0.0 | 0.0 | nan | nan |  |  |
| izmir | İzmir - Karaburun | Kırsal | Arka Plan | 0.0 | 0.0 | nan | nan |  |  |
| izmir | İzmir - Karşıyaka | Kentsel | Isınma | 0.0 | 0.0 | nan | nan |  |  |
| izmir | İzmir - Karşıyaka İBB | Kentsel | Isınma | 0.0 | 0.0 | nan | nan |  |  |
| izmir | İzmir - Menemen | Kentsel | Isınma | 0.0 | 0.0 | nan | nan |  |  |
| izmir | İzmir - Torbalı | Kentsel | Sanayi | 0.0 | 0.0 | nan | nan |  |  |
| izmir | İzmir - Yenifoça | Kentsel | Isınma | 0.0 | 0.0 | nan | nan |  |  |
| izmir | İzmir - Çeşme | Kırsal | Arka Plan | 0.0 | 0.0 | nan | nan |  |  |
| izmir | İzmir - Ödemiş | Kentsel | Isınma | 0.0 | 0.0 | nan | nan |  |  |
| izmir | İzmir - Şirinyer İBB | Kentsel | Arka Plan | 0.0 | 0.0 | nan | nan |  |  |
| izmir | İzmir Güzelbahçe İBB | Kentsel | Isınma | 0.0 | 0.0 | nan | nan |  |  |
| izmir | İzmir-Kemalpaşa | Kentsel | Isınma | 0.0 | 0.0 | nan | nan |  |  |
| kocaeli | Kocaeli - Gebze OSB - MTHM | Kent Çevresi | Sanayi | 98.7 | 99.5 | 2023-01-01 | 2026-09-22 | 21.4 |  |
| kocaeli | Kocaeli - Körfez-MTHM | Kent Çevresi | Sanayi | 97.1 | 97.5 | 2023-01-01 | 2026-09-22 | 17.8 |  |
| kocaeli | Kocaeli | Kentsel | Isınma | 87.4 | 89.6 | 2023-01-01 | 2026-09-22 | 22.7 | ✔ |
| kocaeli | Kocaeli - Gölcük-MTHM | Kentsel | Isınma | 86.7 | 70.4 | 2023-01-01 | 2026-09-21 | 15.8 |  |
| kocaeli | Kocaeli - Kandıra-MTHM | Kırsal | Arka Plan | 46.0 | 29.9 | 2023-01-01 | 2026-09-21 | 11.1 |  |
| kocaeli | Kocaeli - Alikahya-MTHM | Kentsel | Isınma | 0.0 | 0.0 | nan | nan |  |  |
| kocaeli | Kocaeli - Dilovası | Kentsel | Sanayi | 0.0 | 0.0 | nan | nan |  |  |
| kocaeli | Kocaeli - Dilovası-İMES OSB 1-MTHM | Kent Çevresi | Sanayi | 0.0 | 0.0 | nan | nan |  |  |
| kocaeli | Kocaeli - Dilovası-İMES OSB 2-MTHM | Kent Çevresi | Sanayi | 0.0 | 0.0 | nan | nan |  |  |
| kocaeli | Kocaeli - Gebze - MTHM | Kentsel | Isınma | 0.0 | 0.0 | nan | nan |  |  |
| kocaeli | Kocaeli - Yeniköy-MTHM | Kentsel | Isınma | 0.0 | 0.0 | nan | nan |  |  |
| kocaeli | Kocaeli - İzmit-MTHM | Kentsel | Trafik | 0.0 | 0.0 | nan | nan |  |  |

