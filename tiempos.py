from datetime import datetime, timezone
from zoneinfo import ZoneInfo

SANTIAGO = ZoneInfo("America/Santiago")


def ahora_utc():
    return datetime.now(timezone.utc)


def instante(valor, local=False):
    fecha = datetime.fromisoformat(valor)
    if fecha.tzinfo is None:
        fecha = fecha.replace(tzinfo=SANTIAGO if local else timezone.utc)
    return fecha.astimezone(timezone.utc)
