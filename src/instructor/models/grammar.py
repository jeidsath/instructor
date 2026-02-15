import uuid
from datetime import datetime

from sqlalchemy import (
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
from instructor.models.enums import GrammarCategory, Language, MasteryLevel


class GrammarConcept(UUIDMixin, Base):
    __tablename__ = "grammar_concepts"
    __table_args__ = (UniqueConstraint("language", "name", name="uq_grammar_name"),)

    language: Mapped[Language]
    category: Mapped[GrammarCategory]
    subcategory: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    difficulty_level: Mapped[int] = mapped_column(Integer)
    prerequisite_ids: Mapped[list[str] | None] = mapped_column(JSON, default=None)


class LearnerGrammar(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "learner_grammar"
    __table_args__ = (
        UniqueConstraint("learner_id", "grammar_concept_id", name="uq_learner_grammar"),
        Index("ix_learner_grammar_mastery", "learner_id", "mastery_level"),
    )

    learner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("learners.id", ondelete="CASCADE"), index=True
    )
    grammar_concept_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("grammar_concepts.id", ondelete="CASCADE"), index=True
    )

    # Mastery progression
    mastery_level: Mapped[MasteryLevel] = mapped_column(default=MasteryLevel.UNKNOWN)

    # Tracking
    last_practiced: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    times_practiced: Mapped[int] = mapped_column(Integer, default=0)
    recent_error_rate: Mapped[float] = mapped_column(Float, default=0.0)

    grammar_concept: Mapped["GrammarConcept"] = relationship()
