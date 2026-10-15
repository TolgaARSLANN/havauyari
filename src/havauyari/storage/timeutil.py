"""Yerel saat (Europe/Istanbul, tz bilgisi yok) <-> UTC (tz bilgili) dönüşümleri.

Servis içinde tüm zamanlar eğitimdeki gibi yerel saattir; veritabanı UTC saklar.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo

from havauyari.config import TIMEZONE

LOCAL = ZoneInfo(TIMEZONE)
# Tahmin yanıtındaki zaman alanları (iç içe listelerde de aynı adlar)
TIME_KEYS = {"issued_at", "target_time", "time"}


def to_utc(local: datetime) -> datetime:
    return local.replace(tzinfo=LOCAL).astimezone(UTC)


def to_local(value: datetime) -> datetime:
    return value.astimezone(LOCAL).replace(tzinfo=None)


def encode_payload(obj: Any) -> Any:
    """Yanıt sözlüğünü JSON'a hazırlar: zamanlar UTC ISO metnine çevrilir."""
    if isinstance(obj, dict):
        return {k: encode_payload(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [encode_payload(v) for v in obj]
    if isinstance(obj, datetime):                       # pandas.Timestamp da datetime'dır
        if hasattr(obj, "to_pydatetime"):
            obj = obj.to_pydatetime()
        return to_utc(obj).isoformat()
    return obj


def decode_payload(obj: Any) -> Any:
    """`encode_payload` tersi: zaman alanları yeniden yerel saate (tz bilgisi yok) döner."""
    if isinstance(obj, dict):
        return {k: (to_local(datetime.fromisoformat(v)) if k in TIME_KEYS and isinstance(v, str)
                    else decode_payload(v)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [decode_payload(v) for v in obj]
    return obj
