"""Pydantic schema validation tests.

These are the contract that forces course structure over wiki-article
structure. They are the most important tests in the suite.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from hivemind.models.domain import DomainNode, DomainTree
from hivemind.models.subject import (
    LessonFrontmatter,
    LessonRecord,
    SubjectManifest,
    SubjectState,
)


def _valid_lesson(order: int = 1) -> dict:
    return {
        "frontmatter": {
            "order": order,
            "title": "Test lesson",
            "estimated_minutes": 15,
            "learning_objectives": ["Understand X"],
        },
        "body": "Hello world.",
        "filename": f"{order:02d}-test.md",
    }


def _valid_manifest(**overrides) -> dict:
    data = {
        "slug": "test-subject",
        "title": "Test Subject",
        "domains": ["computer-science"],
        "prerequisites": [],
        "authors": [{"id": "user_a", "role": "original"}],
        "estimated_hours": 4,
        "difficulty": "beginner",
        "status": "draft",
        "version": 1,
        "forked_from": None,
    }
    data.update(overrides)
    return data


class TestSubjectManifest:
    def test_valid(self):
        SubjectManifest.model_validate(_valid_manifest())

    def test_rejects_empty_title(self):
        with pytest.raises(ValidationError):
            SubjectManifest.model_validate(_valid_manifest(title=""))

    def test_rejects_no_authors(self):
        with pytest.raises(ValidationError):
            SubjectManifest.model_validate(_valid_manifest(authors=[]))

    def test_rejects_no_domains(self):
        with pytest.raises(ValidationError):
            SubjectManifest.model_validate(_valid_manifest(domains=[]))

    def test_rejects_bad_slug(self):
        with pytest.raises(ValidationError):
            SubjectManifest.model_validate(_valid_manifest(slug="Bad Slug"))

    def test_rejects_self_prereq(self):
        with pytest.raises(ValidationError):
            SubjectManifest.model_validate(
                _valid_manifest(prerequisites=["test-subject"])
            )

    def test_rejects_duplicate_prereqs(self):
        with pytest.raises(ValidationError):
            SubjectManifest.model_validate(_valid_manifest(prerequisites=["a", "a"]))

    def test_rejects_zero_estimated_hours(self):
        with pytest.raises(ValidationError):
            SubjectManifest.model_validate(_valid_manifest(estimated_hours=0))

    def test_rejects_extra_fields(self):
        data = _valid_manifest(extra_field="oops")
        with pytest.raises(ValidationError):
            SubjectManifest.model_validate(data)


class TestLessonFrontmatter:
    def test_valid(self):
        LessonFrontmatter.model_validate(
            {
                "order": 1,
                "title": "Intro",
                "estimated_minutes": 10,
                "learning_objectives": ["Define X"],
            }
        )

    def test_rejects_empty_objectives(self):
        with pytest.raises(ValidationError):
            LessonFrontmatter.model_validate(
                {
                    "order": 1,
                    "title": "Intro",
                    "estimated_minutes": 10,
                    "learning_objectives": [],
                }
            )

    def test_rejects_blank_objective_entry(self):
        with pytest.raises(ValidationError):
            LessonFrontmatter.model_validate(
                {
                    "order": 1,
                    "title": "Intro",
                    "estimated_minutes": 10,
                    "learning_objectives": ["   "],
                }
            )

    def test_rejects_zero_minutes(self):
        with pytest.raises(ValidationError):
            LessonFrontmatter.model_validate(
                {
                    "order": 1,
                    "title": "Intro",
                    "estimated_minutes": 0,
                    "learning_objectives": ["x"],
                }
            )


class TestSubjectState:
    def test_requires_at_least_one_lesson(self):
        with pytest.raises(ValidationError):
            SubjectState.model_validate(
                {
                    "manifest": _valid_manifest(),
                    "overview": "Some text",
                    "lessons": [],
                }
            )

    def test_rejects_duplicate_lesson_orders(self):
        with pytest.raises(ValidationError):
            SubjectState.model_validate(
                {
                    "manifest": _valid_manifest(),
                    "overview": "Some text",
                    "lessons": [_valid_lesson(1), _valid_lesson(1)],
                }
            )

    def test_sorts_lessons_by_order(self):
        state = SubjectState.model_validate(
            {
                "manifest": _valid_manifest(),
                "overview": "Some text",
                "lessons": [_valid_lesson(2), _valid_lesson(1)],
            }
        )
        assert [l.frontmatter.order for l in state.lessons] == [1, 2]

    def test_valid_minimal(self):
        SubjectState.model_validate(
            {
                "manifest": _valid_manifest(),
                "overview": "Some text",
                "lessons": [_valid_lesson(1)],
            }
        )


class TestDomainTree:
    def test_valid(self):
        DomainTree.model_validate(
            {
                "domains": [
                    {
                        "slug": "math",
                        "title": "Math",
                        "children": [
                            {"slug": "algebra", "title": "Algebra", "children": []}
                        ],
                    }
                ]
            }
        )

    def test_rejects_duplicate_slugs(self):
        with pytest.raises(ValidationError):
            DomainTree.model_validate(
                {
                    "domains": [
                        {"slug": "dup", "title": "A", "children": []},
                        {"slug": "dup", "title": "B", "children": []},
                    ]
                }
            )

    def test_flatten_yields_pre_order(self):
        tree = DomainTree(
            domains=[
                DomainNode(
                    slug="a",
                    title="A",
                    children=[DomainNode(slug="b", title="B", children=[])],
                ),
                DomainNode(slug="c", title="C", children=[]),
            ]
        )
        flat = tree.flatten()
        assert [(n.slug, p) for n, p in flat] == [("a", None), ("b", "a"), ("c", None)]
