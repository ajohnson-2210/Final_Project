"""Evidence-scored semantic input resolution.

This module deliberately separates:
1. what data structure an algorithm requires; and
2. how that structure is externally serialised.

A high semantic score must never be used as evidence for an unspecified
delimiter or textual encoding.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import re


@dataclass(frozen=True)
class InputResolution:
    variable: str
    semantic_type: str
    semantic_score: int
    semantic_confidence: str
    encoding_score: int
    encoding_confidence: str
    encoding: str | None
    deterministic_conversion: str | None
    resolution: str
    evidence: tuple[str, ...]
    encoding_evidence: tuple[str, ...]

    def to_dict(self) -> dict:
        return asdict(self)


def _confidence(score: int) -> str:
    if score >= 5:
        return "high"
    if score >= 2:
        return "medium"
    if score <= -3:
        return "insufficient"
    return "low"


def score_input_resolution(source: str, variable: str) -> InputResolution:
    """Infer semantic structure separately from external input encoding."""

    v = re.escape(variable)
    semantic_score = 0
    encoding_score = 0
    evidence: list[str] = []
    encoding_evidence: list[str] = []

    # Semantic structure evidence.
    has_for_each = bool(re.search(rf"\bFOR\s+EACH\s+\w+\s+IN\s+{v}\b", source, re.I))
    has_length = bool(re.search(rf"\bLENGTH\s+OF\s+{v}\b", source, re.I))
    indexes = [int(x) for x in re.findall(rf"\b{v}\s*\[\s*(\d+)\s*\]", source)]

    if has_for_each:
        semantic_score += 3
        evidence.append("FOR EACH traversal strongly establishes collection semantics")
    if has_length:
        semantic_score += 2
        evidence.append("LENGTH OF usage establishes collection semantics")
    if re.search(rf"\b{v}\s*\[[^\]]+\]", source):
        semantic_score += 3
        evidence.append("indexed access strongly establishes ordered/indexable structure")
    if re.search(r"(?:_List\b|\bList\b)", variable, re.I):
        semantic_score += 1
        evidence.append("identifier naming weakly supports list semantics")

    semantic_type = "UNKNOWN"
    if indexes and set(indexes).issubset({0, 1}) and {0, 1}.issubset(set(indexes)):
        semantic_type = "TUPLE"
        semantic_score += 2
        evidence.append("fixed accesses at indices 0 and 1 support tuple-like arity")
    elif has_length and re.search(rf"\b{v}\s*\[[^\]]+\]", source):
        semantic_type = "LIST"
        semantic_score += 2
        evidence.append("combined LENGTH and indexed access strongly support list/array semantics")
    elif has_for_each:
        semantic_type = "COLLECTION"
    elif re.search(rf"\b{v}\s*\[[^\]]+\]", source):
        semantic_type = "ORDERED_COLLECTION"

    deterministic_conversion = None

    # Text identity evidence:
    # Indexing and LENGTH are valid directly on strings. A text-like INPUT that
    # uses those operations therefore remains a string unless the source
    # explicitly requests a conversion. v3.66 retired the earlier inferred
    # STRING_TO_LIST_OF_CHARACTER conversion.
    input_prompt_match = re.search(
        rf"(?im)^\s*{v}\s*<-\s*INPUT\(\s*STRING\(\s*[\"'](?P<prompt>.*?)[\"']\s*\)\s*\)\s*$",
        source,
    )
    prompt_text = input_prompt_match.group("prompt") if input_prompt_match else ""
    textual_identity_evidence = bool(
        re.search(r"(?i)(?:^|_)(text|string|sentence|paragraph)(?:$|_)", variable)
        or re.search(r"(?i)\b(text|string|sentence|paragraph)\b", prompt_text)
    )
    is_text_prompt = bool(input_prompt_match and textual_identity_evidence)
    indexed_character_use = bool(
        re.search(rf"\b{v}\s*\[[^\]]+\]", source)
        and re.search(rf"\bLENGTH\s+OF\s+{v}\b", source, re.I)
    )
    if is_text_prompt and indexed_character_use:
        semantic_type = "STRING"
        semantic_score += 2
        evidence.append(
            "text input is indexed and length-traversed; both operations are valid on the source string, so no representation conversion is inferred"
        )

    # Encoding evidence is intentionally independent.
    input_match = re.search(
        rf"(?im)^\s*{v}\s*<-\s*INPUT\((?P<prompt>.+)\)\s*$",
        source,
    )
    encoding = None
    if input_match:
        prompt = input_match.group("prompt")
        # Explicit parsing/delimiter instructions are positive evidence.
        if re.search(r"\b(?:split|delimiter|comma[- ]separated|csv)\b", source, re.I):
            encoding_score += 3
            encoding_evidence.append("explicit delimiter/parsing instruction present")
        else:
            encoding_score -= 3
            encoding_evidence.append("no delimiter or parsing instruction supplied")

        if (
            semantic_type in {"LIST", "TUPLE", "COLLECTION", "ORDERED_COLLECTION"}
            and deterministic_conversion is None
            and re.search(r"\bSTRING\s*\(", prompt, re.I)
        ):
            encoding_score -= 3
            encoding_evidence.append(
                "structured semantic input is requested through a textual prompt without serialisation syntax"
            )
        elif deterministic_conversion == "STRING_TO_LIST_OF_CHARACTER":
            encoding_evidence.append(
                "no delimiter is required because each source character maps directly to one list element"
            )

    semantic_confidence = _confidence(semantic_score)
    encoding_confidence = _confidence(encoding_score)

    if deterministic_conversion is not None:
        resolution = "APPLY_DETERMINISTIC_CONVERSION"
    elif semantic_type == "STRING" and input_match:
        resolution = "PRESERVE_EXPLICIT_INPUT"
    elif semantic_confidence in {"high", "medium"} and encoding_confidence == "insufficient":
        resolution = "PROMOTE_TO_PARAMETER"
    elif semantic_confidence in {"high", "medium"} and encoding_confidence == "high":
        resolution = "INFER_ENCODING"
    elif semantic_type == "UNKNOWN":
        resolution = "PRESERVE_EXPLICIT_INPUT"
    else:
        resolution = "DO_NOT_INFER_ENCODING"

    return InputResolution(
        variable=variable,
        semantic_type=semantic_type,
        semantic_score=semantic_score,
        semantic_confidence=semantic_confidence,
        encoding_score=encoding_score,
        encoding_confidence=encoding_confidence,
        encoding=encoding,
        deterministic_conversion=deterministic_conversion,
        resolution=resolution,
        evidence=tuple(evidence),
        encoding_evidence=tuple(encoding_evidence),
    )
