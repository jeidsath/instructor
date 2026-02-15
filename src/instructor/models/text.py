from sqlalchemy import Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from instructor.models.base import Base, UUIDMixin
from instructor.models.enums import Language


class TextEntry(UUIDMixin, Base):
    __tablename__ = "text_entries"

    language: Mapped[Language]
    title: Mapped[str] = mapped_column(String(500))
    author: Mapped[str | None] = mapped_column(String(200), default=None)
    content: Mapped[str] = mapped_column(Text)
    translation: Mapped[str | None] = mapped_column(Text, default=None)
    difficulty_level: Mapped[int] = mapped_column(Integer)
    vocabulary_notes: Mapped[dict[str, object] | None] = mapped_column(
        JSON, default=None
    )
    grammar_notes: Mapped[dict[str, object] | None] = mapped_column(
        JSON, default=None
    )
    prerequisite_grammar: Mapped[list[str] | None] = mapped_column(
        JSON, default=None
    )
