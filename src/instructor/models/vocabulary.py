import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from instructor.models.base import Base, TimestampMixin, UUIDMixin
from instructor.models.enums import Language, PartOfSpeech


class VocabularyItem(UUIDMixin, Base):
    __tablename__ = "vocabulary_items"
    __table_args__ = (
        UniqueConstraint("language", "lemma", "part_of_speech", name="uq_vocab_lemma"),
    )

    language: Mapped[Language]
    lemma: Mapped[str] = mapped_column(String(200))
    part_of_speech: Mapped[PartOfSpeech]
    definition: Mapped[str] = mapped_column(Text)
    forms: Mapped[dict[str, object] | None] = mapped_column(JSON, default=None)
    frequency_rank: Mapped[int | None] = mapped_column(Integer, default=None)
    difficulty_level: Mapped[int] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text, default=None)


class LearnerVocabulary(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "learner_vocabulary"
    __table_args__ = (
        UniqueConstraint("learner_id", "vocabulary_item_id", name="uq_learner_vocab"),
        Index("ix_learner_vocab_next_review", "next_review"),
        Index("ix_learner_vocab_strength", "learner_id", "strength"),
    )

    learner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("learners.id", ondelete="CASCADE"), index=True
    )
    vocabulary_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("vocabulary_items.id", ondelete="CASCADE"), index=True
    )

    # Spaced repetition state (SM-2)
    strength: Mapped[float] = mapped_column(Float, default=0.0)
    ease_factor: Mapped[float] = mapped_column(Float, default=2.5)
    interval_days: Mapped[float] = mapped_column(Float, default=0.0)
    repetition_count: Mapped[int] = mapped_column(Integer, default=0)

    # Tracking
    last_reviewed: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    next_review: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    times_correct: Mapped[int] = mapped_column(Integer, default=0)
    times_incorrect: Mapped[int] = mapped_column(Integer, default=0)

    # Knowledge depth
    knows_definition: Mapped[bool] = mapped_column(Boolean, default=False)
    knows_forms: Mapped[bool] = mapped_column(Boolean, default=False)
    knows_usage: Mapped[bool] = mapped_column(Boolean, default=False)

    vocabulary_item: Mapped["VocabularyItem"] = relationship()
