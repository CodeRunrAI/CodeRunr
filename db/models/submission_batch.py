import uuid
from datetime import datetime
from typing import List, TYPE_CHECKING

from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from .submission import Submission

from db.base import Base


class SubmissionBatch(Base):
    __tablename__ = "submission_batches"

    id: Mapped[int] = mapped_column(primary_key=True)
    token: Mapped[uuid.UUID] = mapped_column(
        unique=True, default=uuid.uuid4, index=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        onupdate=func.now(), server_default=func.now()
    )

    # Submissions
    submissions: Mapped[List["Submission"]] = relationship(
        back_populates="batch", cascade="all,delete-orphan"
    )
