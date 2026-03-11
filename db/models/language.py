from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from db.base import Base


class Language(Base):
    __tablename__ = "languages"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    version: Mapped[str] = mapped_column(String(50))
    compile_cmd: Mapped[Optional[str]] = mapped_column(Text)
    run_cmd: Mapped[str] = mapped_column(Text)
    source_file: Mapped[str] = mapped_column(String(50))
    is_archived: Mapped[bool] = mapped_column(default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        onupdate=func.now(), server_default=func.now()
    )
