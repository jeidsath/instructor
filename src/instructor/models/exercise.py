from sqlalchemy import Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from instructor.models.base import Base, UUIDMixin
from instructor.models.enums import Language


class Exercise(UUIDMixin, Base):
    __tablename__ = "exercises"

    language: Mapped[Language]
    exercise_type: Mapped[str] = mapped_column(String(50))
    prompt: Mapped[str] = mapped_column(Text)
    expected_response: Mapped[str | None] = mapped_column(Text, default=None)
    grammar_concepts: Mapped[list[str] | None] = mapped_column(JSON, default=None)
    vocabulary_items: Mapped[list[str] | None] = mapped_column(JSON, default=None)
    difficulty_level: Mapped[int] = mapped_column(Integer)
