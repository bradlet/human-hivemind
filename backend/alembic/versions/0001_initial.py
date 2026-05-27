"""Initial schema.

Revision ID: 0001
Revises:
Create Date: 2026-05-26
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("google_sub", sa.String(255), nullable=False, unique=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("avatar_url", sa.String(1024), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_users_google_sub", "users", ["google_sub"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "domains",
        sa.Column("slug", sa.String(128), primary_key=True),
        sa.Column(
            "parent_slug",
            sa.String(128),
            sa.ForeignKey("domains.slug", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
    )
    op.create_index("ix_domains_parent_slug", "domains", ["parent_slug"])

    op.create_table(
        "subjects",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("slug", sa.String(128), nullable=False, unique=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="draft"),
        sa.Column("difficulty", sa.String(32), nullable=False),
        sa.Column("estimated_hours", sa.Float, nullable=False),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("forked_from_slug", sa.String(128), nullable=True),
        sa.Column("forked_from_version", sa.Integer, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_subjects_slug", "subjects", ["slug"], unique=True)
    op.create_index("ix_subjects_status", "subjects", ["status"])
    op.create_index("ix_subjects_difficulty", "subjects", ["difficulty"])
    op.create_index("ix_subjects_forked_from_slug", "subjects", ["forked_from_slug"])

    op.create_table(
        "subject_authors",
        sa.Column(
            "subject_id",
            sa.Integer,
            sa.ForeignKey("subjects.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            sa.String(64),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("role", sa.String(32), nullable=False, server_default="contributor"),
    )

    op.create_table(
        "subject_domains",
        sa.Column(
            "subject_id",
            sa.Integer,
            sa.ForeignKey("subjects.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "domain_slug",
            sa.String(128),
            sa.ForeignKey("domains.slug", ondelete="CASCADE"),
            primary_key=True,
        ),
    )

    op.create_table(
        "subject_prerequisites",
        sa.Column(
            "subject_id",
            sa.Integer,
            sa.ForeignKey("subjects.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("prereq_slug", sa.String(128), primary_key=True),
        sa.Column("position", sa.Integer, nullable=False, server_default="0"),
    )
    op.create_index(
        "ix_subject_prerequisites_prereq_slug", "subject_prerequisites", ["prereq_slug"]
    )

    op.create_table(
        "lessons",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "subject_id",
            sa.Integer,
            sa.ForeignKey("subjects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("order", sa.Integer, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("estimated_minutes", sa.Integer, nullable=False),
        sa.Column("learning_objectives", sa.JSON, nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("subject_id", "order", name="uq_lesson_subject_order"),
    )
    op.create_index("ix_lessons_subject_id", "lessons", ["subject_id"])

    op.create_table(
        "edit_events",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.String(64),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("operation", sa.String(64), nullable=False),
        sa.Column("slug", sa.String(128), nullable=False),
        sa.Column("payload", sa.JSON, nullable=False),
        sa.Column("accepted", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_edit_events_user_id", "edit_events", ["user_id"])
    op.create_index("ix_edit_events_operation", "edit_events", ["operation"])
    op.create_index("ix_edit_events_slug", "edit_events", ["slug"])
    op.create_index("ix_edit_events_created_at", "edit_events", ["created_at"])


def downgrade() -> None:
    op.drop_table("edit_events")
    op.drop_table("lessons")
    op.drop_table("subject_prerequisites")
    op.drop_table("subject_domains")
    op.drop_table("subject_authors")
    op.drop_table("subjects")
    op.drop_table("domains")
    op.drop_table("users")
