import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from instructor.models.base import Base, UUIDMixin
from instructor.models.enums import Language, SessionType


class Session(UUIDMixin, Base):
    __tablename__ = "sessions"
    __table_args__ = (
        Index("ix_sessions_learner_lang", "learner_id", "language", "started_at"),
    )

    learner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("learners.id", ondelete="CASCADE"), index=True
    )
    language: Mapped[Language]
    session_type: Mapped[SessionType]

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    performance_summary: Mapped[dict[str, object] | None] = mapped_column(
        JSON, default=None
    )

    activities: Mapped[list["SessionActivity"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class SessionActivity(UUIDMixin, Base):
    __tablename__ = "session_activities"

    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), index=True
    )
    activity_type: Mapped[str] = mapped_column(String(50))
    prompt: Mapped[str] = mapped_column(Text)
    response: Mapped[str | None] = mapped_column(Text, default=None)
    score: Mapped[dict[str, object] | None] = mapped_column(JSON, default=None)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )

    session: Mapped["Session"] = relationship(back_populates="activities")
