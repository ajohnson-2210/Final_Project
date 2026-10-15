"""Evaluation harness for the six-model pseudocode corpus.

This module deliberately keeps corpus extraction separate from the compatibility
normaliser. It identifies the 50 supplied tasks per model, then runs each body
through GENERIC_COMPATIBILITY and the AJ parser without inventing missing logic.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import json
import re
from typing import Callable

from aj_parser import AJParserFacade
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


@dataclass
class CorpusExample:
    model: str
    task_number: int
    title: str
    source: str


@dataclass
class CorpusResult:
    model: str
    task_number: int
    title: str
    status: str
    parse_success: bool
    transformation_count: int
    error: str | None
    processed_source: str


class CorpusAdapter:
    def extract(self, text: str, model: str) -> list[CorpusExample]:
        raise NotImplementedError




class HashHeadingAdapter(CorpusAdapter):
    """Canonical research-corpus adapter. Each algorithm starts with '# <title>'."""

    HEADING = re.compile(r"(?m)^#\s+(.+?)\s*$")

    def extract(self, text: str, model: str) -> list[CorpusExample]:
        matches = list(self.HEADING.finditer(text))
        examples: list[CorpusExample] = []

        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            body = text[match.end():end].strip()
            examples.append(
                CorpusExample(
                    model=model,
                    task_number=index + 1,
                    title=match.group(1).strip(),
                    source=body,
                )
            )

        return examples


def to_hash_corpus(examples: list[CorpusExample]) -> str:
    """Serialises extracted examples using the project's canonical # heading convention."""
    sections: list[str] = []
    for example in examples:
        sections.append(f"# {example.title}\n{example.source.strip()}")
    return "\n\n".join(sections).rstrip() + "\n"


class NumberedSectionAdapter(CorpusAdapter):
    """Adapter for numbered-section text exports."""

    HEADING = re.compile(r"(?m)^(\d{1,2})\.\s+(.+?)\s*$")

    def extract(self, text: str, model: str) -> list[CorpusExample]:
        matches = list(self.HEADING.finditer(text))
        examples: list[CorpusExample] = []

        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            body = text[match.end():end].strip()
            body = re.sub(r"(?mi)^\s*text\s*$", "", body).strip()
            examples.append(
                CorpusExample(
                    model=model,
                    task_number=int(match.group(1)),
                    title=match.group(2).strip(),
                    source=body,
                )
            )

        return examples


class ExampleSectionAdapter(CorpusAdapter):
    """Adapter for exports whose tasks are followed by Example sections."""

    CODE_START = re.compile(r"(?m)^(FUNCTION|CLASS)\b")
    TASK_HEADING = re.compile(r"(?m)^\s*\d{1,2}\.\s+\S.*$")

    def extract(self, text: str, model: str) -> list[CorpusExample]:
        starts = list(self.CODE_START.finditer(text))
        examples: list[CorpusExample] = []

        for index, match in enumerate(starts):
            next_start = starts[index + 1].start() if index + 1 < len(starts) else len(text)
            segment_end = next_start
            segment = text[match.start():next_start]

            # A numbered task heading belongs to the next corpus item, even when
            # there is no blank separator before it.  Keep this extraction
            # tolerance in the corpus adapter rather than treating headings as
            # pseudocode or teaching the language normaliser to discard them.
            heading_marker = self.TASK_HEADING.search(segment, match.end() - match.start())
            if heading_marker is not None:
                segment_end = match.start() + heading_marker.start()

            example_marker = re.search(r"(?m)^Example:\s*$", segment)
            if example_marker is not None:
                segment_end = min(segment_end, match.start() + example_marker.start())

            body = text[match.start():segment_end].strip()
            prefix = text[:match.start()].rstrip().splitlines()
            title = prefix[-1].strip() if prefix else f"Task {index + 1}"
            if title.lower().startswith(("returns", "example:")):
                title = f"Task {index + 1}"

            examples.append(
                CorpusExample(
                    model=model,
                    task_number=index + 1,
                    title=title,
                    source=body,
                )
            )

        return examples


class StructuredExportAdapter(CorpusAdapter):
    """Adapter for structured heading-based exports.

    Current research exports use column-one ``# <title>`` task headings and
    already preserve meaningful multiline indentation.  Older exports can be
    compressed and are retained through the legacy BODY_START fallback.
    """

    HASH_HEADING = re.compile(r"(?m)^#\s+(.+?)\s*$")
    BODY_START = re.compile(r"^\s*(INPUT|INIT|FUNCTION)\b", re.IGNORECASE)

    @staticmethod
    def _trim_outer_blank_lines(block: str) -> str:
        """Remove separator blank lines without altering source indentation."""
        lines = block.splitlines()
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()
        return "\n".join(lines)

    def _extract_hash_heading_format(self, text: str, model: str) -> list[CorpusExample]:
        matches = list(self.HASH_HEADING.finditer(text))
        examples: list[CorpusExample] = []

        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            body = self._trim_outer_blank_lines(text[match.end():end])
            examples.append(
                CorpusExample(
                    model=model,
                    task_number=index + 1,
                    title=match.group(1).strip(),
                    source=body,
                )
            )

        return examples

    def _extract_legacy_compressed_format(self, text: str, model: str) -> list[CorpusExample]:
        lines = text.splitlines()
        body_indices = [i for i, line in enumerate(lines) if self.BODY_START.match(line)]
        examples: list[CorpusExample] = []

        for number, start in enumerate(body_indices, start=1):
            end = body_indices[number] if number < len(body_indices) else len(lines)
            title_index = start - 1
            while title_index >= 0 and not lines[title_index].strip():
                title_index -= 1
            title = lines[title_index].strip() if title_index >= 0 else f"Task {number}"

            body_lines = []
            for line in lines[start:end]:
                if line.strip():
                    body_lines.append(line.strip())
            body = " ".join(body_lines).strip()

            # The line immediately before the next body is the next title, not code.
            if number < len(body_indices):
                next_title = body_indices[number] - 1
                while next_title >= start and not lines[next_title].strip():
                    next_title -= 1
                if next_title >= start and lines[next_title].strip() in body_lines:
                    body_lines = body_lines[:-1]
                    body = " ".join(body_lines).strip()

            examples.append(CorpusExample(model, number, title, body))

        return examples

    def extract(self, text: str, model: str) -> list[CorpusExample]:
        # Prefer the source-preserving structured format whenever explicit
        # task headings are present.  This prevents nested INPUT/INIT/FUNCTION
        # statements from being mistaken for new corpus items and avoids
        # destroying indentation that the source already supplies.
        if self.HASH_HEADING.search(text) is not None:
            return self._extract_hash_heading_format(text, model)

        return self._extract_legacy_compressed_format(text, model)


class TextExportAdapter(CorpusAdapter):
    """Adapter for plain-text structured exports."""

    HEADING = re.compile(r"(?<!\d)(\d{1,2})\.\s+")
    CODE_MARKER = re.compile(r"Plaintext(?=(FUNCTION|PROCEDURE|CLASS))", re.IGNORECASE)

    def extract(self, text: str, model: str) -> list[CorpusExample]:
        headings = list(self.HEADING.finditer(text))
        examples: list[CorpusExample] = []

        for index, heading in enumerate(headings):
            end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
            segment = text[heading.end():end]
            marker = self.CODE_MARKER.search(segment)
            if marker is None:
                title = segment.strip().splitlines()[0] if segment.strip() else f"Task {index + 1}"
                body = ""
            else:
                title = segment[:marker.start()].replace("\n", " ").strip()
                body = segment[marker.end():].strip()

            examples.append(
                CorpusExample(
                    model=model,
                    task_number=int(heading.group(1)),
                    title=title,
                    source=body,
                )
            )

        return examples


class CorpusEvaluator:
    """Runs extracted corpus examples through Generic compatibility + AJ parser."""

    def __init__(self) -> None:
        self.profile_processor = PseudocodeProfileProcessor()
        self.parser = AJParserFacade()

    def evaluate(self, examples: list[CorpusExample]) -> list[CorpusResult]:
        results: list[CorpusResult] = []
        for example in examples:
            if not example.source.strip():
                results.append(CorpusResult(
                    example.model, example.task_number, example.title,
                    "MINIMALIST_OR_INSUFFICIENT_STRUCTURE", False, 0,
                    "No executable pseudocode body was recovered.", "",
                ))
                continue

            processed = self.profile_processor.process(
                example.source,
                PseudocodeProfile.GENERIC_COMPATIBILITY,
            )
            parsed = self.parser.parse(processed.processed_source)
            if parsed.success:
                status = "PARSED"
            elif self._looks_minimalist(example.source):
                status = "MINIMALIST_OR_INSUFFICIENT_STRUCTURE"
            else:
                status = "UNSUPPORTED_CONSTRUCT"

            results.append(CorpusResult(
                example.model,
                example.task_number,
                example.title,
                status,
                parsed.success,
                processed.transformation_count,
                parsed.error,
                processed.processed_source,
            ))
        return results

    @staticmethod
    def _looks_minimalist(source: str) -> bool:
        stripped = source.strip()
        executable_markers = re.findall(
            r"\b(?:INPUT|OUTPUT|RETURN|IF|WHILE|FOR|FUNCTION|PROCEDURE|CLASS|CALL|APPEND|RAISE)\b|(?:<-|(?<![=!<>])=(?!=))",
            stripped,
            flags=re.IGNORECASE,
        )
        return len(stripped) < 45 or len(executable_markers) < 2


ADAPTERS: dict[str, CorpusAdapter] = {
    "source_a": NumberedSectionAdapter(),
    "source_b": NumberedSectionAdapter(),
    "source_c": NumberedSectionAdapter(),
    "source_e": ExampleSectionAdapter(),
    "source_f": StructuredExportAdapter(),
    "source_d": TextExportAdapter(),
}


def read_corpus_text(path: str | Path) -> str:
    """Read a research corpus without lossy character replacement.

    The collected corpus is mostly UTF-8, but some source exports are Windows-1252.
    Decode UTF-8 (including BOM) first and fall back to cp1252 only when the byte
    stream is not valid UTF-8.  This preserves source characters such as the
    multiplication sign instead of silently replacing them with U+FFFD.
    """
    data = Path(path).read_bytes()
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return data.decode("cp1252")


def evaluate_hash_corpus(file_map: dict[str, str | Path]) -> dict:
    """Evaluates corpus files whose only task boundary is '# <title>'."""
    evaluator = CorpusEvaluator()
    adapter = HashHeadingAdapter()
    all_results: list[CorpusResult] = []
    extraction_counts: dict[str, int] = {}

    for model, file_path in file_map.items():
        path = Path(file_path)
        text = read_corpus_text(path)
        examples = adapter.extract(text, model)
        extraction_counts[model] = len(examples)
        all_results.extend(evaluator.evaluate(examples))

    return _summarise_results(file_map, extraction_counts, all_results)


def evaluate_corpus(file_map: dict[str, str | Path]) -> dict:
    evaluator = CorpusEvaluator()
    all_results: list[CorpusResult] = []
    extraction_counts: dict[str, int] = {}

    for model, file_path in file_map.items():
        path = Path(file_path)
        text = read_corpus_text(path)
        adapter = ADAPTERS[model]
        examples = adapter.extract(text, model)
        extraction_counts[model] = len(examples)
        all_results.extend(evaluator.evaluate(examples))

    return _summarise_results(file_map, extraction_counts, all_results)


def _summarise_results(file_map: dict[str, str | Path], extraction_counts: dict[str, int], all_results: list[CorpusResult]) -> dict:
    model_summary: dict[str, dict] = {}
    for model in file_map:
        model_results = [r for r in all_results if r.model == model]
        model_summary[model] = {
            "extracted": len(model_results),
            "parsed": sum(r.parse_success for r in model_results),
            "unsupported": sum(r.status == "UNSUPPORTED_CONSTRUCT" for r in model_results),
            "minimalist_or_insufficient_structure": sum(
                r.status == "MINIMALIST_OR_INSUFFICIENT_STRUCTURE" for r in model_results
            ),
        }

    parsed_total = sum(r.parse_success for r in all_results)
    total = len(all_results)
    failure_clusters: dict[str, int] = {}
    for result in all_results:
        if result.parse_success or not result.error:
            continue
        key = cluster_error(result.error)
        failure_clusters[key] = failure_clusters.get(key, 0) + 1

    return {
        "corpus_size": total,
        "extraction_counts": extraction_counts,
        "parsed": parsed_total,
        "parse_rate_percent": round((parsed_total / total * 100) if total else 0.0, 1),
        "model_summary": model_summary,
        "failure_clusters": dict(sorted(failure_clusters.items(), key=lambda item: (-item[1], item[0]))),
        "results": [asdict(r) for r in all_results],
    }


def cluster_error(error: str) -> str:
    if "Unrecognised character" in error:
        match = re.search(r"Unrecognised character (.+?) at line", error)
        return f"LEXER_UNRECOGNISED_{match.group(1) if match else 'CHARACTER'}"
    if "Expected" in error:
        match = re.search(r"Expected ([^,.;]+)", error)
        return f"PARSER_EXPECTED_{match.group(1).strip() if match else 'TOKEN'}"
    if "Unexpected token" in error:
        return "PARSER_UNEXPECTED_TOKEN"
    if "Unsupported" in error:
        return "PARSER_UNSUPPORTED"
    return error.split(" at line", 1)[0][:100]


def write_report(report: dict, path: str | Path) -> None:
    Path(path).write_text(json.dumps(report, indent=2), encoding="utf-8")
