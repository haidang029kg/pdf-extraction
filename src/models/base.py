from abc import ABC
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


class UtilsDatetimeModel(ABC):
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
