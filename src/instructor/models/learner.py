import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from instructor.models.base import Base, TimestampMixin, UUIDMixin
from instructor.models.enums import Language


class Learner(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "learners"

    name: Mapped[str] = mapped_column(String(255))

    language_states: Mapped[list["LearnerLanguageState"]] = relationship(
        back_populates="learner", cascade="all, delete-orphan"
    )


class LearnerLanguageState(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "learner_language_states"
    __table_args__ = (
        UniqueConstraint("learner_id", "language", name="uq_learner_language"),
    )

    learner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("learners.id", ondelete="CASCADE"), index=True
    )
    language: Mapped[Language]

    # Capacity levels (0.0 - 10.0)
    reading_level: Mapped[float] = mapped_column(Float, default=0.0)
    writing_level: Mapped[float] = mapped_column(Float, default=0.0)
    listening_level: Mapped[float] = mapped_column(Float, default=0.0)
    speaking_level: Mapped[float] = mapped_column(Float, default=0.0)

    # Aggregate knowledge metrics
    active_vocabulary_size: Mapped[int] = mapped_column(Integer, default=0)
    grammar_concepts_mastered: Mapped[int] = mapped_column(Integer, default=0)

    # Curriculum position
    current_unit: Mapped[str | None] = mapped_column(String(100), default=None)

    # Session tracking
    last_session_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    total_study_time_minutes: Mapped[int] = mapped_column(Integer, default=0)

    learner: Mapped["Learner"] = relationship(back_populates="language_states")
