"""SQLAlchemy ORM models for the Postgres index.

Postgres mirrors content-storage metadata to make domain/prereq/author/search
queries fast. The index is always rebuildable from content storage via
`hivemind reindex`.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class UserRow(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    google_sub: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    avatar_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class DomainRow(Base):
    __tablename__ = "domains"

    slug: Mapped[str] = mapped_column(String(128), primary_key=True)
    parent_slug: Mapped[str | None] = mapped_column(
        String(128), ForeignKey("domains.slug", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class SubjectRow(Base):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True)
    difficulty: Mapped[str] = mapped_column(String(32), index=True)
    estimated_hours: Mapped[float] = mapped_column(Float)
    version: Mapped[int] = mapped_column(Integer, default=1)
    forked_from_slug: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    forked_from_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    authors: Mapped[list[SubjectAuthorRow]] = relationship(
        back_populates="subject", cascade="all, delete-orphan"
    )
    domains: Mapped[list[SubjectDomainRow]] = relationship(
        back_populates="subject", cascade="all, delete-orphan"
    )
    prerequisites: Mapped[list[SubjectPrerequisiteRow]] = relationship(
        back_populates="subject",
        cascade="all, delete-orphan",
        foreign_keys="SubjectPrerequisiteRow.subject_id",
    )
    lessons: Mapped[list[LessonRow]] = relationship(
        back_populates="subject", cascade="all, delete-orphan"
    )


class SubjectAuthorRow(Base):
    __tablename__ = "subject_authors"

    subject_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("subjects.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    role: Mapped[str] = mapped_column(String(32), default="contributor")

    subject: Mapped[SubjectRow] = relationship(back_populates="authors")


class SubjectDomainRow(Base):
    __tablename__ = "subject_domains"

    subject_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("subjects.id", ondelete="CASCADE"), primary_key=True
    )
    domain_slug: Mapped[str] = mapped_column(
        String(128), ForeignKey("domains.slug", ondelete="CASCADE"), primary_key=True
    )

    subject: Mapped[SubjectRow] = relationship(back_populates="domains")


class SubjectPrerequisiteRow(Base):
    __tablename__ = "subject_prerequisites"

    subject_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("subjects.id", ondelete="CASCADE"), primary_key=True
    )
    prereq_slug: Mapped[str] = mapped_column(String(128), primary_key=True, index=True)
    position: Mapped[int] = mapped_column(Integer, default=0)

    subject: Mapped[SubjectRow] = relationship(
        back_populates="prerequisites", foreign_keys=[subject_id]
    )


class LessonRow(Base):
    __tablename__ = "lessons"
    __table_args__ = (UniqueConstraint("subject_id", "order", name="uq_lesson_subject_order"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subject_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("subjects.id", ondelete="CASCADE"), index=True
    )
    order: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(255))
    estimated_minutes: Mapped[int] = mapped_column(Integer)
    learning_objectives: Mapped[list[str]] = mapped_column(JSON, default=list)
    filename: Mapped[str] = mapped_column(String(255))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    subject: Mapped[SubjectRow] = relationship(back_populates="lessons")


class EditEventRow(Base):
    __tablename__ = "edit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    operation: Mapped[str] = mapped_column(String(64), index=True)
    slug: Mapped[str] = mapped_column(String(128), index=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    accepted: Mapped[bool] = mapped_column(Boolean, default=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
