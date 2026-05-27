"""Round-trip a SubjectState to and from the storage backend.

This is the single place that knows the file layout of a subject:

    subjects/{slug}/subject.yaml
    subjects/{slug}/overview.md
    subjects/{slug}/lessons/NN-*.md
    subjects/{slug}/exercises/*.md           (optional)
    subjects/{slug}/references.md             (optional)
    subjects/{slug}/ai/agent.md               (derived)
    subjects/{slug}/ai/facts.yaml             (derived)
    subjects/{slug}/ai/glossary.yaml          (derived)
    subjects/{slug}/ai/meta.yaml              (derived)

All parsing flows through pydantic, so reads of malformed content raise
`ValueError` (caught by the API layer and surfaced as 422).
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import frontmatter
import yaml

from hivemind.models.ai_representation import AgentDoc, AIMeta, FactsFile, GlossaryFile
from hivemind.models.domain import DomainTree
from hivemind.models.subject import (
    LessonFrontmatter,
    LessonRecord,
    SubjectManifest,
    SubjectState,
)
from hivemind.storage.base import StorageBackend, StoredObjectNotFound

DOMAINS_FILE = "domains.yaml"
SUBJECTS_PREFIX = "subjects"

LESSON_FILENAME_RE = re.compile(r"^(?P<order>\d+)-[a-z0-9-]+\.md$")


def subject_dir(slug: str) -> str:
    return f"{SUBJECTS_PREFIX}/{slug}"


def manifest_path(slug: str) -> str:
    return f"{subject_dir(slug)}/subject.yaml"


def overview_path(slug: str) -> str:
    return f"{subject_dir(slug)}/overview.md"


def lessons_prefix(slug: str) -> str:
    return f"{subject_dir(slug)}/lessons"


def ai_prefix(slug: str) -> str:
    return f"{subject_dir(slug)}/ai"


# ---------- Domains ----------


def load_domains(storage: StorageBackend) -> DomainTree:
    try:
        obj = storage.read(DOMAINS_FILE)
    except StoredObjectNotFound as exc:
        raise ValueError(
            f"Missing required file: {DOMAINS_FILE}. The content root must declare a domain tree."
        ) from exc
    parsed = yaml.safe_load(obj.data.decode("utf-8")) or {}
    if isinstance(parsed, list):
        parsed = {"domains": parsed}
    return DomainTree.model_validate(parsed)


def dump_domains(storage: StorageBackend, tree: DomainTree) -> None:
    data = yaml.safe_dump(tree.model_dump(), sort_keys=False).encode("utf-8")
    storage.write(DOMAINS_FILE, data)


# ---------- Subject manifest ----------


def load_manifest(storage: StorageBackend, slug: str) -> SubjectManifest:
    try:
        obj = storage.read(manifest_path(slug))
    except StoredObjectNotFound as exc:
        raise ValueError(f"Subject {slug!r} has no subject.yaml in storage") from exc
    parsed = yaml.safe_load(obj.data.decode("utf-8")) or {}
    return SubjectManifest.model_validate(parsed)


def dump_manifest(storage: StorageBackend, manifest: SubjectManifest) -> None:
    payload = manifest.model_dump(mode="json", exclude_none=False)
    data = yaml.safe_dump(payload, sort_keys=False).encode("utf-8")
    storage.write(manifest_path(manifest.slug), data)


# ---------- Lessons ----------


def _parse_lesson_file(filename: str, raw: bytes) -> LessonRecord:
    text = raw.decode("utf-8")
    post = frontmatter.loads(text)
    fm = LessonFrontmatter.model_validate(post.metadata or {})
    name_match = LESSON_FILENAME_RE.match(filename)
    if name_match is None:
        raise ValueError(
            f"Lesson filename {filename!r} must look like 'NN-some-slug.md' "
            "(numeric prefix, kebab-case)."
        )
    declared_order = int(name_match.group("order"))
    if declared_order != fm.order:
        raise ValueError(
            f"Lesson {filename!r} declares `order: {fm.order}` in frontmatter but the "
            f"filename prefix is {declared_order:02d}. These must agree."
        )
    return LessonRecord(frontmatter=fm, body=post.content, filename=filename)


def _serialize_lesson(lesson: LessonRecord) -> bytes:
    meta = lesson.frontmatter.model_dump(mode="json")
    post = frontmatter.Post(content=lesson.body, **meta)
    return frontmatter.dumps(post).encode("utf-8")


def load_lessons(storage: StorageBackend, slug: str) -> list[LessonRecord]:
    prefix = lessons_prefix(slug)
    paths = storage.list_prefix(prefix)
    lessons: list[LessonRecord] = []
    for path in paths:
        filename = path.rsplit("/", 1)[-1]
        if not LESSON_FILENAME_RE.match(filename):
            continue
        obj = storage.read(path)
        lessons.append(_parse_lesson_file(filename, obj.data))
    return lessons


def dump_lesson(storage: StorageBackend, slug: str, lesson: LessonRecord) -> None:
    path = f"{lessons_prefix(slug)}/{lesson.filename}"
    storage.write(path, _serialize_lesson(lesson))


# ---------- Overview / references / exercises ----------


def load_overview(storage: StorageBackend, slug: str) -> str:
    try:
        obj = storage.read(overview_path(slug))
    except StoredObjectNotFound as exc:
        raise ValueError(f"Subject {slug!r} is missing the required overview.md") from exc
    return obj.data.decode("utf-8")


def dump_overview(storage: StorageBackend, slug: str, body: str) -> None:
    storage.write(overview_path(slug), body.encode("utf-8"))


def load_references(storage: StorageBackend, slug: str) -> str | None:
    path = f"{subject_dir(slug)}/references.md"
    try:
        return storage.read(path).data.decode("utf-8")
    except StoredObjectNotFound:
        return None


def load_exercises(storage: StorageBackend, slug: str) -> dict[str, str]:
    prefix = f"{subject_dir(slug)}/exercises"
    out: dict[str, str] = {}
    for path in storage.list_prefix(prefix):
        filename = path.rsplit("/", 1)[-1]
        out[filename] = storage.read(path).data.decode("utf-8")
    return out


# ---------- SubjectState (full assembly) ----------


def load_subject_state(storage: StorageBackend, slug: str) -> SubjectState:
    manifest = load_manifest(storage, slug)
    overview = load_overview(storage, slug)
    lessons = load_lessons(storage, slug)
    references = load_references(storage, slug)
    exercises = load_exercises(storage, slug)
    return SubjectState(
        manifest=manifest,
        overview=overview,
        lessons=lessons,
        references=references,
        exercises=exercises,
    )


def dump_subject_state(storage: StorageBackend, state: SubjectState) -> None:
    """Write a fully-validated SubjectState to storage (human side only).

    AI representation files are managed by the regenerate_ai_representation
    pipeline step and are not touched here.
    """
    dump_manifest(storage, state.manifest)
    dump_overview(storage, state.manifest.slug, state.overview)
    for lesson in state.lessons:
        dump_lesson(storage, state.manifest.slug, lesson)
    if state.references is not None:
        storage.write(
            f"{subject_dir(state.manifest.slug)}/references.md",
            state.references.encode("utf-8"),
        )
    for filename, body in state.exercises.items():
        storage.write(
            f"{subject_dir(state.manifest.slug)}/exercises/{filename}",
            body.encode("utf-8"),
        )


# ---------- AI representation ----------


@dataclass(frozen=True)
class AIRepresentation:
    agent: AgentDoc | None
    facts: FactsFile | None
    glossary: GlossaryFile | None
    meta: AIMeta | None

    @property
    def exists(self) -> bool:
        return self.agent is not None


def load_ai_representation(storage: StorageBackend, slug: str) -> AIRepresentation:
    base = ai_prefix(slug)

    def _try_read(rel: str) -> bytes | None:
        try:
            return storage.read(f"{base}/{rel}").data
        except StoredObjectNotFound:
            return None

    agent_data = _try_read("agent.md")
    facts_data = _try_read("facts.yaml")
    glossary_data = _try_read("glossary.yaml")
    meta_data = _try_read("meta.yaml")

    agent = AgentDoc(body=agent_data.decode("utf-8")) if agent_data else None
    facts = (
        FactsFile.model_validate(yaml.safe_load(facts_data.decode("utf-8")) or {})
        if facts_data
        else None
    )
    glossary = (
        GlossaryFile.model_validate(yaml.safe_load(glossary_data.decode("utf-8")) or {})
        if glossary_data
        else None
    )
    meta = (
        AIMeta.model_validate(yaml.safe_load(meta_data.decode("utf-8")) or {})
        if meta_data
        else None
    )
    return AIRepresentation(agent=agent, facts=facts, glossary=glossary, meta=meta)


def list_subject_slugs(storage: StorageBackend) -> list[str]:
    """Return every subject slug that has a subject.yaml in storage."""
    paths = storage.list_prefix(SUBJECTS_PREFIX)
    slugs: list[str] = []
    for p in paths:
        parts = p.split("/")
        if len(parts) >= 3 and parts[0] == SUBJECTS_PREFIX and parts[2] == "subject.yaml":
            slugs.append(parts[1])
    return sorted(set(slugs))
