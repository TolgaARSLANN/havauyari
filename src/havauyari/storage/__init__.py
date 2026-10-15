"""PostgreSQL kalıcılık katmanı: istasyonlar, tahminler ve uyarılar.

Bağlantı adresi `DATABASE_URL` ortam değişkeninden gelir. Tanımlı değilse servis bugünkü gibi
veritabanı olmadan (yalnızca bellek önbelleğiyle) çalışır.

Zamanlar veritabanında TIMESTAMPTZ (UTC) olarak saklanır; servis ve API ise Türkiye yerel
saatiyle (saat dilimi bilgisi olmayan datetime) çalışır. Dönüşüm `storage.timeutil` içindedir.
"""
