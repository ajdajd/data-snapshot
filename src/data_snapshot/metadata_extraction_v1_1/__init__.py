"""Archive the v1.1 metadata extraction package.

Warning: Imports and paths in this historical package are intentionally stale
after its move to ``metadata_extraction_v1_1`` and must be repaired before use.
"""

from data_snapshot.metadata_extraction.extraction import (
    ExtractionResult,
    extract_metadata,
    load_extraction_config,
)
from data_snapshot.metadata_extraction.schema import build_openai_schema

__all__ = [
    "ExtractionResult",
    "build_openai_schema",
    "extract_metadata",
    "load_extraction_config",
]
