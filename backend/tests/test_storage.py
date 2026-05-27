"""LocalStorage tests."""
from __future__ import annotations

import pytest

from hivemind.storage.base import StoredObjectNotFound, normalize_path
from hivemind.storage.local import LocalStorage


def test_normalize_path_basic():
    assert normalize_path("foo/bar.md") == "foo/bar.md"
    assert normalize_path("/foo/bar.md/") == "foo/bar.md"


def test_normalize_path_rejects_dotdot():
    with pytest.raises(ValueError):
        normalize_path("foo/../bar")


def test_normalize_path_rejects_empty():
    with pytest.raises(ValueError):
        normalize_path("")


def test_write_then_read(storage: LocalStorage):
    storage.write("subjects/a/file.md", b"hello")
    obj = storage.read("subjects/a/file.md")
    assert obj.data == b"hello"


def test_read_missing_raises(storage: LocalStorage):
    with pytest.raises(StoredObjectNotFound):
        storage.read("subjects/missing/file.md")


def test_list_prefix(storage: LocalStorage):
    storage.write("subjects/a/x.md", b"x")
    storage.write("subjects/a/y.md", b"y")
    storage.write("subjects/b/x.md", b"x")
    assert sorted(storage.list_prefix("subjects/a")) == ["subjects/a/x.md", "subjects/a/y.md"]


def test_exists(storage: LocalStorage):
    storage.write("subjects/a/file.md", b"x")
    assert storage.exists("subjects/a/file.md")
    assert not storage.exists("subjects/a/missing.md")


def test_versions_track_overwrites(storage: LocalStorage):
    storage.write("subjects/a/file.md", b"v1")
    storage.write("subjects/a/file.md", b"v2")
    storage.write("subjects/a/file.md", b"v3")
    versions = storage.list_versions("subjects/a/file.md")
    assert len(versions) >= 3
    assert sum(1 for v in versions if v.is_current) == 1


def test_copy_prefix(storage: LocalStorage):
    storage.write("subjects/a/file1.md", b"1")
    storage.write("subjects/a/nested/file2.md", b"2")
    written = storage.copy_prefix("subjects/a", "subjects/b")
    assert "subjects/b/file1.md" in written
    assert "subjects/b/nested/file2.md" in written
    assert storage.read("subjects/b/file1.md").data == b"1"


def test_paths_cannot_escape_root(storage: LocalStorage):
    with pytest.raises(ValueError):
        storage.read("../etc/passwd")
