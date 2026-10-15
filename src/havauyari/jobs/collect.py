"""Toplama işi: tüm istasyonlar için bu saatin tahminini üretir ve veritabanına kaydeder.

Her çalışmada:
1. Migration'lar en son sürüme taşınır (idempotent).
2. Her istasyon için tahmin üretilir (ya da bu saatin tahmini zaten varsa veritabanından okunur);
   tahmin ve uyarı durumu `forecasts`/`alerts` tablolarına yazılır.
3. Yanıttaki son 72 saatin istasyon ölçümleri `measurements` tablosuna yazılır. Saatte bir
   çalıştıkça her saat birkaç kez görülür; SİM sonradan düzeltirse son değer kalır.
4. Çalışmanın özeti (başarılı/başarısız istasyon sayısı, hatalar) `runs` tablosuna yazılır.

Bir istasyonun hatası (ölçüm yok, ağ hatası) diğerlerini durdurmaz.

Çıkış kodları: 0 en az bir istasyon başarılı · 1 hiçbiri başarılı değil ya da veritabanına
ulaşılamadı · 2 DATABASE_URL tanımlı değil.

Kullanım:
    DATABASE_URL=postgresql://... python -m havauyari.jobs.collect
    make collect          # postgres'i başlatır, sonra bu modülü çalıştırır
SİM yalnızca Türkiye'den erişilebildiği için iş yerel bilgisayarda çalışır
(bkz. scripts/windows/register_collect_task.ps1).
"""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime

from havauyari.serving.service import DataUnavailable, ForecastService
from havauyari.storage import StorageError

log = logging.getLogger("havauyari.collect")


@dataclass
class RunResult:
    issued_at: datetime
    ok: list[str] = field(default_factory=list)
    errors: dict[str, str] = field(default_factory=dict)
    measurements: int = 0

    @property
    def exit_code(self) -> int:
        return 0 if self.ok else 1


def collect(service: ForecastService) -> RunResult:
    """Tüm istasyonları bir kez dolaşır. `service.repo` tanımlı olmalıdır."""
    repo = service.repo
    if repo is None:
        raise ValueError("Toplama işi veritabanı deposu olmadan çalışmaz.")
    started = datetime.now(UTC)
    result = RunResult(issued_at=service.clock())

    for slug in service.a.stations:
        try:
            f = service.forecast(slug)
            result.measurements += repo.save_measurements(slug, f["history"])
            result.ok.append(slug)
            log.info("%s: %.1f µg/m³ (uyarı=%s, risk=%s)", slug, f["pm25"],
                     f["alert"]["is_alert"], f["alert"]["risk"])
        except DataUnavailable as e:
            result.errors[slug] = str(e)
            log.warning("%s: %s", slug, e)
        except StorageError:
            raise                                   # veritabanı gitti: işin geri kalanı anlamsız
        except Exception as e:                      # noqa: BLE001 - ağ/kaynak hatası: sıradaki
            result.errors[slug] = f"{type(e).__name__}: {e}"
            log.exception("%s: beklenmeyen hata", slug)

    repo.record_run(started_at=started, finished_at=datetime.now(UTC),
                    issued_at=result.issued_at, ok=len(result.ok), failed=len(result.errors),
                    measurements=result.measurements, errors=result.errors)
    log.info("Bitti: %d istasyon kaydedildi, %d başarısız, %d ölçüm yazıldı (tahmin saati %s).",
             len(result.ok), len(result.errors), result.measurements,
             result.issued_at.strftime("%Y-%m-%d %H.%M"))
    return result


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S")
    # Alembic'in eklenti kurulum satırları her saat loga düşmesin; migration satırları kalsın
    logging.getLogger("alembic").setLevel(logging.WARNING)
    logging.getLogger("alembic.runtime.migration").setLevel(logging.INFO)
    from havauyari.storage import database_url

    url = database_url()
    if url is None:
        log.error("DATABASE_URL tanımlı değil (bkz. .env.example).")
        return 2

    from havauyari.serving.data import LiveProvider
    from havauyari.serving.service import load_artifacts
    from havauyari.storage.migrate import upgrade
    from havauyari.storage.repository import ForecastRepository

    try:
        upgrade(url)
        repo = ForecastRepository.from_url(url)
        repo.ping()
        service = ForecastService(load_artifacts(), LiveProvider(), repository=repo)
        # Servis, yazma hatalarını tahmini bozmamak için yalnızca loglar; işte ise kaydın
        # yapılması asıl amaç olduğundan istasyonlar önce açıkça eşitlenir
        repo.sync_stations(service.a.stations.values())
        return collect(service).exit_code
    except StorageError as e:
        log.error("Veritabanına ulaşılamadı: %s", e)
    except Exception as e:                          # noqa: BLE001 - migration (psycopg) hataları
        log.error("Toplama işi başlatılamadı: %s: %s", type(e).__name__, e)
    return 1


if __name__ == "__main__":
    sys.exit(main())
