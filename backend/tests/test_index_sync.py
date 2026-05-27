"""Reindex from storage tests."""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from sqlalchemy.orm import Session

from hivemind.db.models import DomainRow, LessonRow, SubjectPrerequisiteRow, SubjectRow
from hivemind.services import index_sync
from hivemind.storage.local import LocalStorage


def _write_seed(root: Path) -> None:
    (root / "domains.yaml").write_text(
        yaml.safe_dump(
            {
                "domains": [
                    {
                        "slug": "math",
                        "title": "Math",
                        "children": [
                            {"slug": "linear-algebra-domain", "title": "Linear Algebra", "children": []}
                        ],
                    },
                    {
                        "slug": "computer-science",
                        "title": "Computer Science",
                        "children": [],
                    },
                ]
            }
        )
    )
    la = root / "subjects" / "linear-algebra"
    la.mkdir(parents=True)
    (la / "subject.yaml").write_text(
        yaml.safe_dump(
            {
                "slug": "linear-algebra",
                "title": "Linear Algebra",
                "domains": ["math", "linear-algebra-domain"],
                "prerequisites": [],
                "authors": [{"id": "user_seed", "role": "original"}],
                "estimated_hours": 8,
                "difficulty": "beginner",
                "status": "published",
                "version": 1,
                "forked_from": None,
            }
        )
    )
    (la / "overview.md").write_text("Linear algebra overview.")
    (la / "lessons").mkdir()
    (la / "lessons" / "01-intro.md").write_text(
        "---\norder: 1\ntitle: Intro\nestimated_minutes: 20\nlearning_objectives:\n  - Define vectors\n---\nBody."
    )

    dnn = root / "subjects" / "deep-neural-networks"
    dnn.mkdir(parents=True)
    (dnn / "subject.yaml").write_text(
        yaml.safe_dump(
            {
                "slug": "deep-neural-networks",
                "title": "Deep Neural Networks",
                "domains": ["computer-science"],
                "prerequisites": ["linear-algebra"],
                "authors": [{"id": "user_seed", "role": "original"}],
                "estimated_hours": 12,
                "difficulty": "intermediate",
                "status": "published",
                "version": 1,
                "forked_from": None,
            }
        )
    )
    (dnn / "overview.md").write_text("DNN overview.")
    (dnn / "lessons").mkdir()
    (dnn / "lessons" / "01-perceptron.md").write_text(
        "---\norder: 1\ntitle: Perceptron\nestimated_minutes: 20\nlearning_objectives:\n  - Define a perceptron\n---\nBody."
    )


@pytest.fixture
def seeded_storage(temp_content: Path) -> LocalStorage:
    _write_seed(temp_content)
    return LocalStorage(temp_content)


def test_reindex_populates_all_tables(db: Session, seeded_storage: LocalStorage):
    report = index_sync.reindex(db, seeded_storage)
    assert report.domains == 3  # math, linear-algebra-domain, computer-science
    assert report.subjects == 2
    assert report.lessons == 2
    assert report.skipped == []

    assert db.query(DomainRow).count() == 3
    assert db.query(SubjectRow).count() == 2
    assert db.query(LessonRow).count() == 2
    # Prereq join present
    prereqs = db.query(SubjectPrerequisiteRow).all()
    assert any(p.prereq_slug == "linear-algebra" for p in prereqs)


def test_needs_reindex_true_when_empty(db: Session, seeded_storage: LocalStorage):
    assert index_sync.needs_reindex(db) is True
    index_sync.reindex(db, seeded_storage)
    assert index_sync.needs_reindex(db) is False
