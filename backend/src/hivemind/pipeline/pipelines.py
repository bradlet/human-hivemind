"""Per-operation pipeline definitions.

Most operations use the full default list. RESTORE_VERSION skips
`validate_schema` because the restored state is already valid (it was once
written through the pipeline).
"""
from __future__ import annotations

from hivemind.pipeline.context import MutationOperation
from hivemind.pipeline.runner import Step
from hivemind.pipeline.steps import (
    audit_log,
    check_authorship,
    load_existing,
    moderate,
    regenerate_ai_representation,
    update_index,
    validate_references,
    validate_schema,
    write_to_storage,
)

DEFAULT_PIPELINE: list[Step] = [
    load_existing,
    validate_schema,
    validate_references,
    check_authorship,
    moderate,
    write_to_storage,
    update_index,
    regenerate_ai_representation,
    audit_log,
]

RESTORE_PIPELINE: list[Step] = [
    load_existing,
    validate_schema,
    validate_references,
    check_authorship,
    moderate,
    write_to_storage,
    update_index,
    regenerate_ai_representation,
    audit_log,
]


def pipeline_for_operation(operation: MutationOperation) -> list[Step]:
    if operation == MutationOperation.RESTORE_VERSION:
        return RESTORE_PIPELINE
    return DEFAULT_PIPELINE
