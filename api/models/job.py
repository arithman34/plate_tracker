import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from api.core.database import Base


class JobStatus(enum.Enum):
    PENDING = "pending"  # Job is created but not yet started
    PROCESSING = "processing"  # Job is currently being processed
    COMPLETED = "completed"  # Job has been processed successfully
    FAILED = "failed"  # Job processing failed


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    video_path: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[JobStatus] = mapped_column(
        Enum(
            JobStatus, values_callable=lambda x: [e.value for e in x], name="job_status"
        ),
        nullable=False,
        default=JobStatus.PENDING,
    )
    bbox: Mapped[str] = mapped_column(String(255), nullable=False)
    mass_kg: Mapped[float | None] = mapped_column(nullable=True)  # Mass in kilograms
    result_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationship to user model
    user: Mapped["User"] = relationship("User", back_populates="jobs")
