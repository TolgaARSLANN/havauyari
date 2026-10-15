"""Migration'ları en son sürüme taşır (konteyner açılışı, `make migrate` ve testler).

Kullanım:
    python -m havauyari.storage.migrate            # DATABASE_URL'deki veritabanı

`alembic.ini` de depo kökünde durur; yeni migration üretmek için:
    alembic revision --autogenerate -m "açıklama"
"""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config

MIGRATIONS = Path(__file__).resolve().parent / "migrations"


def alembic_config(url: str | None = None) -> Config:
    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS))
    if url:
        cfg.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    return cfg


def upgrade(url: str | None = None, revision: str = "head") -> None:
    command.upgrade(alembic_config(url), revision)


def downgrade(url: str | None = None, revision: str = "base") -> None:
    command.downgrade(alembic_config(url), revision)


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.INFO, format="%(levelname)s [%(name)s] %(message)s")
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    upgrade()
    print("Veritabanı şeması güncel (alembic head).")
