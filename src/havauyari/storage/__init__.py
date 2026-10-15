"""PostgreSQL kalıcılık katmanı: istasyonlar, tahminler ve uyarılar.

Bağlantı adresi `DATABASE_URL` ortam değişkeninden gelir. Tanımlı değilse servis bugünkü gibi
veritabanı olmadan (yalnızca bellek önbelleğiyle) çalışır.

Zamanlar veritabanında TIMESTAMPTZ (UTC) olarak saklanır; servis ve API ise Türkiye yerel
saatiyle (saat dilimi bilgisi olmayan datetime) çalışır. Dönüşüm `storage.timeutil` içindedir.

Bu modül SQLAlchemy'yi içe aktarmaz: `db` ekstrası kurulu olmayan ortamlar (ör. yalnızca pano)
da `StorageError` ve `database_url` kullanabilir.
"""

import os


def database_url() -> str | None:
    return os.environ.get("DATABASE_URL") or None


class StorageError(RuntimeError):
    """Veritabanına ulaşılamadı ya da sorgu başarısız oldu. Servis bu durumda tahmini yine
    hesaplar ve döner; yalnızca kalıcılık atlanır (bkz. /health -> database)."""
