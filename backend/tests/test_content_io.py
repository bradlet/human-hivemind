"""Round-trip tests for content_io against the local storage backend."""
from __future__ import annotations

from pathlib import Path

import pytest

from hivemind.models.subject import LessonFrontmatter, LessonRecord, SubjectManifest, SubjectState
from hivemind.services import content_io
from hivemind.storage.local import LocalStorage


def _build_state(slug: str = "test-subject") -> SubjectState:
    return SubjectState(
        manifest=SubjectManifest.model_validate(
            {
                "slug": slug,
                "title": "Test",
                "domains": ["math"],
                "prerequisites": [],
                "authors": [{"id": "user_a", "role": "original"}],
                "estimated_hours": 2.0,
                "difficulty": "beginner",
                "status": "draft",
                "version": 1,
            }
        ),
        overview="Welcome.",
        lessons=[
            LessonRecord(
                frontmatter=LessonFrontmatter(
                    order=1,
                    title="Intro",
                    estimated_minutes=10,
                    learning_objectives=["x"],
                ),
                body="Hello.",
                filename="01-intro.md",
            )
        ],
    )


def test_roundtrip(storage: LocalStorage):
    state = _build_state()
    content_io.dump_subject_state(storage, state)
    loaded = content_io.load_subject_state(storage, state.manifest.slug)
    assert loaded.manifest.slug == state.manifest.slug
    assert loaded.overview == state.overview
    assert len(loaded.lessons) == 1
    assert loaded.lessons[0].frontmatter.title == "Intro"
    assert loaded.lessons[0].body.strip() == "Hello."


def test_list_subject_slugs(storage: LocalStorage):
    state = _build_state("alpha")
    content_io.dump_subject_state(storage, state)
    state2 = _build_state("beta")
    content_io.dump_subject_state(storage, state2)
    assert sorted(content_io.list_subject_slugs(storage)) == ["alpha", "beta"]


def test_load_seed_content(seed_content_root: Path):
    """The seed content in content/ must be valid against the schemas."""
    if not seed_content_root.exists():
        pytest.skip("No seed content present in repo root")
    storage = LocalStorage(seed_content_root)
    for slug in content_io.list_subject_slugs(storage):
        state = content_io.load_subject_state(storage, slug)
        assert state.manifest.slug == slug
        ai = content_io.load_ai_representation(storage, slug)
        assert ai.agent is not None, f"seed subject {slug} is missing ai/agent.md"
        assert ai.meta is not None, f"seed subject {slug} is missing ai/meta.yaml"
