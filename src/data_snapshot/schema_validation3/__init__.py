"""Run confirmatory coverage validation for Metadata Schema v1.2."""

from data_snapshot.schema_validation3.validation import (
    CandidateGap,
    RunSummary,
    SchemaValidationResult,
    run_validation,
)

__all__ = [
    "CandidateGap",
    "RunSummary",
    "SchemaValidationResult",
    "run_validation",
]
