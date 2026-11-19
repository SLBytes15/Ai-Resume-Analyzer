from datetime import datetime, timezone
from sqlalchemy.orm import DeclarativeBase


def utc_now() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass
