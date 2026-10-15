"""Controlled pseudocode processing profiles for the input pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
import ast
import json
import re
import textwrap


# Canonical-token invariant -------------------------------------------------
#
# AJ_24038155 Dialect v1.1 uses ``<-`` as its assignment operator.  A bare
# ``?`` is NOT an AJ token and must never be documented, emitted, or treated
# as a canonical alternative to ``<-``.
#
# A source-integrity stage may encounter literal ``?`` because a legacy stored
# corpus lost several Unicode glyphs during text serialisation. Assignment loss
# is recovered only where syntax makes it certain; ambiguous relations are
# restored only through an explicit evidence lookup table. ``?`` has no entry in
# the canonical character lookup. Every successful recovery must emit a known
# source glyph before strict AJ normalisation; unresolved ``?`` remains invalid.
# -------------------------------------------------------------------------


# Shared structural scanning and lexical evidence ---------------------------


# AJ reserved words that cannot be emitted as generated identifiers.  This
# mirrors the frozen lexer keyword set without importing the parser module into
# the compatibility layer.
_AJ_RESERVED_IDENTIFIER_WORDS = frozenset({
    "FUNCTION", "ACCEPTS", "ENDFUNCTION", "RETURN", "CALL", "IF", "THEN",
    "ELSE", "ENDIF", "WHILE", "DO", "ENDWHILE", "FOR", "TO", "STEP",
    "ENDFOR", "IN", "BREAK", "STOP", "QUIT", "CONTINUE", "OUTPUT", "INPUT",
    "APPEND", "TRY", "CATCH", "ENDTRY", "RAISE", "INTEGER", "FLOAT",
    "STRING", "CHAR", "BOOLEAN", "TRUE", "FALSE", "LIST", "TUPLE", "SET",
    "JOIN", "NOT", "AND", "OR", "XOR", "EXP", "MODULUS", "AS", "COMMENT",
    "CLASS", "ENDCLASS", "PROPERTY", "CONSTRUCTOR", "ENDCONSTRUCTOR",
    "METHOD", "ENDMETHOD", "NONE", "ISINSTANCE",
})


def _fresh_generated_identifier(source: str, preferred: str) -> str:
    """Return a deterministic source-fresh, non-keyword identifier.

    Generated compatibility state must never capture or overwrite a source
    identifier.  Identifiers in AJ are case-sensitive, while reserved keywords
    are case-insensitive, so collision checks use exact spelling for source
    names and uppercase spelling for the keyword set.  Scanning all identifier
    shaped tokens is intentionally conservative: names appearing in comments or
    string payloads may cause an unnecessary suffix, but can never make the
    generated name less safe.
    """
    used = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", source))
    candidate = preferred
    suffix = 1
    while candidate in used or candidate.upper() in _AJ_RESERVED_IDENTIFIER_WORDS:
        candidate = f"{preferred}_{suffix}"
        suffix += 1
    return candidate



def _discover_reserved_identifier_bindings(source: str, *, include_member_evidence: bool = True) -> dict[str, str]:
    """Return source-spelled AJ-keyword identifiers proven by binding syntax.

    The AJ lexer treats keywords case-insensitively, while source identifiers are
    case-sensitive.  A token occurring in an unambiguous binding position (for
    example the simple left-hand side of ``name <- expression``) is therefore
    direct source evidence that the author intended an identifier rather than
    the keyword meaning.  Such identifiers are represented internally using the
    long-established ``__reserved_keyword__`` escape convention.

    This is deliberately lexical and semantics-preserving: it does not infer a
    variable from a read-only occurrence, and it does not alter quoted text.
    """
    found: dict[str, str] = {}

    def add(name: str | None) -> None:
        if not name:
            return
        if name.upper() in _AJ_RESERVED_IDENTIFIER_WORDS:
            found.setdefault(name, f"__reserved_keyword__{name}")

    for raw_line in source.splitlines():
        line = raw_line.strip()
        if not line or line.upper().startswith("COMMENT"):
            continue

        # Simple assignment LHS is the strongest and most common evidence.
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*<-", line)
        if match:
            add(match.group(1))

        # Canonical AJ loop binders.
        match = re.match(r"^FOR\s+EACH\s+([A-Za-z_][A-Za-z0-9_]*)\s+IN\b", line, re.I)
        if match:
            add(match.group(1))
        match = re.match(r"^FOR\s+([A-Za-z_][A-Za-z0-9_]*)\s*<-\s*IN\s+RANGE\b", line, re.I)
        if match:
            add(match.group(1))

        # Declaration binders that the strict parser otherwise cannot consume
        # when their source spelling collides with a keyword.
        match = re.match(
            r"^(?:FUNCTION|METHOD)\s+([A-Za-z_][A-Za-z0-9_]*)\s+ACCEPTS\s*\((.*)\)\s*$",
            line,
            re.I,
        )
        if match:
            add(match.group(1))
            params = match.group(2).strip()
            if params:
                for item in params.split(','):
                    pm = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)\b", item)
                    if pm:
                        add(pm.group(1))

        match = re.match(r"^CONSTRUCTOR\s+ACCEPTS\s*\((.*)\)\s*$", line, re.I)
        if match:
            params = match.group(1).strip()
            if params:
                for item in params.split(','):
                    pm = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)\b", item)
                    if pm:
                        add(pm.group(1))

        match = re.match(r"^CLASS\s+([A-Za-z_][A-Za-z0-9_]*)\s*$", line, re.I)
        if match:
            add(match.group(1))
        match = re.match(r"^PROPERTY\s+([A-Za-z_][A-Za-z0-9_]*)\b", line, re.I)
        if match:
            add(match.group(1))
        match = re.match(r"^CATCH(?:\s+([A-Za-z_][A-Za-z0-9_]*))?\s*$", line, re.I)
        if match:
            add(match.group(1))

        # Member names are also unambiguous identifier positions.  A source
        # spelling such as object.join(...) or object.step(...) cannot denote
        # the AJ JOIN expression or range STEP keyword after a dot.  Recording
        # the name here lets the ordinary reserved-identifier escape propagate
        # it consistently without requiring the baseline source to pre-mangle
        # the identifier.
        if include_member_evidence:
            for member_match in re.finditer(r"\.\s*([A-Za-z_][A-Za-z0-9_]*)\b", line):
                add(member_match.group(1))

    return found


def _reserved_identifier_token_is_keyword_syntax(
    line: str,
    start: int,
    end: int,
    token_upper: str,
) -> bool:
    """Return True when an occurrence is clearly AJ keyword syntax.

    This guard matters only for unusual sources that spell both a bound
    identifier and an AJ keyword using exactly the same case.  Common lowercase
    identifiers such as ``string``/``char`` naturally remain distinct from
    canonical ``STRING(...)``/``CHAR(...)`` constructors.
    """
    before = line[:start]
    after = line[end:]
    before_s = before.rstrip()
    after_s = after.lstrip()
    prefix = line[:start].strip().upper()
    suffix = line[end:].strip().upper()

    # A binding occurrence is never keyword syntax.
    if after_s.startswith('<-') and not before_s.strip():
        return False

    # Constructor/literal/type surfaces.  CALL/dot context instead denotes a
    # user identifier even if its spelling matches a constructor keyword.
    if token_upper in {"INTEGER", "FLOAT", "STRING", "CHAR", "BOOLEAN", "TUPLE", "JOIN", "INPUT"}:
        if after_s.startswith('(') and not (before_s.upper().endswith('CALL') or before_s.endswith('.')):
            return True
    if token_upper in {"LIST", "SET"}:
        # LIST [..] / SET [..] literals require separation between the keyword
        # and opening bracket. A proven source identifier used as list[i] or
        # set[i] has no separating whitespace and must remain an identifier.
        if re.match(r"^\s+\[", after):
            return True
        if token_upper == "LIST" and re.match(r"(?i)^OF\b", after_s):
            return True
    if token_upper in {"LIST", "SET", "STRING"} and before_s.upper().endswith('EMPTY'):
        return True
    if token_upper in {"INTEGER", "FLOAT", "STRING", "CHAR", "BOOLEAN", "LIST", "SET", "TUPLE"}:
        if before_s.upper().endswith('AS') or re.search(r"(?i)LIST\s+OF\s*$", before_s):
            return True

    # Complete/leading statement keywords.
    leading = {
        "FUNCTION", "RETURN", "IF", "ELSE", "ENDIF", "WHILE",
        "FOR", "ENDFOR", "BREAK", "STOP", "QUIT", "CONTINUE", "OUTPUT",
        "APPEND", "TRY", "CATCH", "ENDTRY", "RAISE", "COMMENT",
        "CLASS", "ENDCLASS", "PROPERTY", "CONSTRUCTOR",
        "ENDCONSTRUCTOR", "METHOD", "ENDMETHOD", "ENDFUNCTION",
        "ENDWHILE",
    }
    if not before.strip() and token_upper in leading:
        return True

    if token_upper in {"TRUE", "FALSE", "NONE"}:
        return True
    if token_upper == "CALL" and after_s:
        return True
    if token_upper == "ACCEPTS" and after_s.startswith('('):
        return True
    if token_upper == "THEN" and suffix == "":
        return True
    if token_upper == "DO" and suffix == "":
        return True
    if token_upper in {"AND", "OR", "XOR", "EXP", "MODULUS"} and before_s and after_s:
        return True
    if token_upper == "NOT" and after_s:
        return True
    if token_upper == "IN" and before_s and after_s:
        return True
    if token_upper in {"TO", "STEP", "AS"} and before_s and after_s:
        # After a dot the token is structurally a member/property identifier,
        # never the AJ range/type keyword of the same spelling.  Likewise the
        # identifier immediately following FUNCTION/METHOD/CLASS/PROPERTY is a
        # declaration binder even if its spelling is also an AJ keyword.
        if before_s.endswith('.'):
            return False
        if re.search(r"(?i)(?:FUNCTION|METHOD|CLASS|PROPERTY)\s*$", before_s):
            return False
        return True

    return False


def _escape_proven_reserved_identifiers(
    source: str,
    *,
    include_member_evidence: bool = True,
) -> tuple[str, list["SourceTransformation"]]:
    """Escape reserved keywords that source syntax proves are identifiers.

    The transformation is representation-only.  It preserves the source name
    after a protected prefix and rewrites corresponding identifier occurrences
    outside quoted text.  It is intentionally evidence-gated by binding syntax
    and therefore does not guess from an arbitrary read occurrence.
    """
    bindings = _discover_reserved_identifier_bindings(source, include_member_evidence=include_member_evidence)
    if not bindings:
        return source, []

    transformations: list[SourceTransformation] = []
    output_lines: list[str] = []

    for line_number, line in enumerate(source.splitlines(), start=1):
        if line.strip().upper().startswith('COMMENT'):
            output_lines.append(line)
            continue

        # Work only outside quoted strings.
        parts = re.split(r'("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')', line)
        changed = False
        rebuilt: list[str] = []
        offset = 0
        for part_index, part in enumerate(parts):
            if part_index % 2 == 1:
                # Quoted text is normally opaque, but AJ STRING placeholders
                # are identifier references.  Preserve the visible text while
                # escaping only a simple {identifier} placeholder whose source
                # binding was independently proven above.
                rewritten_part = part
                for source_name, target_name in bindings.items():
                    rewritten_part = re.sub(
                        rf"(?<!\{{)\{{{re.escape(source_name)}\}}(?!\}})",
                        "{" + target_name + "}",
                        rewritten_part,
                    )
                if rewritten_part != part:
                    changed = True
                rebuilt.append(rewritten_part)
                offset += len(part)
                continue

            cursor = 0
            piece: list[str] = []
            for match in re.finditer(r'[A-Za-z_][A-Za-z0-9_]*', part):
                piece.append(part[cursor:match.start()])
                token = match.group(0)
                target = bindings.get(token)
                if target is None:
                    piece.append(token)
                else:
                    absolute_start = offset + match.start()
                    absolute_end = offset + match.end()
                    if _reserved_identifier_token_is_keyword_syntax(
                        line, absolute_start, absolute_end, token.upper()
                    ):
                        piece.append(token)
                    else:
                        piece.append(target)
                        changed = True
                cursor = match.end()
            piece.append(part[cursor:])
            rebuilt_part = ''.join(piece)
            rebuilt.append(rebuilt_part)
            offset += len(part)

        target_line = ''.join(rebuilt)
        output_lines.append(target_line)
        if changed and target_line != line:
            transformations.append(SourceTransformation(
                line=line_number,
                rule='RESERVED_IDENTIFIER_ESCAPE',
                source=line,
                target=target_line,
            ))

    return '\n'.join(output_lines), transformations


def _find_matching_delimiter(
    text: str,
    open_index: int,
    open_char: str,
    close_char: str,
) -> int | None:
    """Return the matching close delimiter, ignoring quoted delimiters.

    The caller supplies the index of the opening delimiter.  Escaped quote
    characters are respected.  This helper deliberately validates only the
    requested delimiter pair so existing compatibility rules retain their
    previous acceptance boundaries.
    """
    if (
        open_index < 0
        or open_index >= len(text)
        or text[open_index] != open_char
        or len(open_char) != 1
        or len(close_char) != 1
    ):
        return None

    depth = 0
    quote: str | None = None
    escape = False
    for index in range(open_index, len(text)):
        ch = text[index]
        if quote is not None:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == quote:
                quote = None
            continue
        if ch in "'\"":
            quote = ch
            continue
        if ch == open_char:
            depth += 1
        elif ch == close_char:
            depth -= 1
            if depth == 0:
                return index
            if depth < 0:
                return None
    return None


def _split_top_level_commas_shared(text: str) -> list[str]:
    """Split commas outside quotes and balanced (), [] and {} groups."""
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    quote: str | None = None
    escape = False
    for ch in text:
        if quote is not None:
            current.append(ch)
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == quote:
                quote = None
            continue
        if ch in "'\"":
            quote = ch
            current.append(ch)
            continue
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth = max(0, depth - 1)
        if ch == "," and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
    parts.append("".join(current))
    return parts


def _unwrap_single_outer_parentheses_shared(text: str) -> str | None:
    """Return the contents only when one (...) pair encloses all text."""
    if len(text) < 2 or text[0] != "(" or text[-1] != ")":
        return None
    close_index = _find_matching_delimiter(text, 0, "(", ")")
    if close_index != len(text) - 1:
        return None
    return text[1:-1]


def _split_statement_values_shared(text: str) -> list[str]:
    """Shared RETURN/OUTPUT tuple-surface splitter."""
    stripped = text.strip()
    values = _split_top_level_commas_shared(stripped)
    if len(values) > 1:
        return values
    inner = _unwrap_single_outer_parentheses_shared(stripped)
    if inner is None:
        return values
    inner_values = _split_top_level_commas_shared(inner)
    return inner_values if len(inner_values) > 1 else values


def _parse_balanced_member_call(
    content: str,
    methods: tuple[str, ...],
    *,
    dotted_receiver: bool,
) -> tuple[str, str, str] | None:
    """Parse one standalone member call with one non-empty argument.

    This is structural machinery only: callers remain responsible for receiver
    evidence and for assigning the historical compatibility rule ID.
    """
    receiver = (
        r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*"
        if dotted_receiver
        else r"[A-Za-z_]\w*"
    )
    method_group = "|".join(re.escape(method) for method in methods)
    match = re.match(
        rf"(?i)^(?P<receiver>{receiver})\.(?P<method>{method_group})\s*\(",
        content,
    )
    if match is None:
        return None
    open_index = content.find("(", match.start(), match.end())
    close_index = _find_matching_delimiter(content, open_index, "(", ")")
    if close_index is None or content[close_index + 1 :].strip():
        return None
    argument = content[open_index + 1 : close_index].strip()
    if not argument:
        return None
    return match.group("receiver"), match.group("method"), argument


@dataclass
class LexicalEvidenceContext:
    """Small shared store for source-proven lexical type/shape facts.

    Frames can either start empty (routine-local evidence) or inherit readable
    enclosing facts (closure-style evidence).  Shadowing removes inherited facts
    from the new frame, and direct rebinds can invalidate one evidence kind.
    Names remain case-sensitive to preserve the behaviour of the migrated rules.
    """

    frames: list[dict[str, set[str]]] = field(default_factory=lambda: [{}])

    def enter(self, *, inherit: bool = False, shadow: tuple[str, ...] = ()) -> None:
        frame = (
            {kind: set(names) for kind, names in self.frames[-1].items()}
            if inherit
            else {}
        )
        if shadow:
            for names in frame.values():
                names.difference_update(shadow)
        self.frames.append(frame)

    def exit(self) -> None:
        if len(self.frames) > 1:
            self.frames.pop()

    def establish(self, kind: str, name: str) -> None:
        self.frames[-1].setdefault(kind, set()).add(name)

    def establish_parent(self, kind: str, name: str) -> None:
        """Promote one proven fact into the immediately enclosing frame.

        This is used only for explicit instance-member assignments inside a
        constructor.  Constructor-local names remain local; the caller decides
        when the parent frame is the enclosing class scope.
        """
        if len(self.frames) > 1:
            self.frames[-2].setdefault(kind, set()).add(name)

    def invalidate(self, kind: str, name: str) -> None:
        self.frames[-1].setdefault(kind, set()).discard(name)

    def contains(self, kind: str, name: str) -> bool:
        return name in self.frames[-1].get(kind, set())

    def names(self, kind: str) -> set[str]:
        return set(self.frames[-1].get(kind, set()))




class PseudocodeProfile(str, Enum):
    """Available pseudocode processing profiles."""

    AJ_DIALECT_STRICT = "AJ_DIALECT_STRICT"
    GENERIC_COMPATIBILITY = "GENERIC_COMPATIBILITY"
    GENERAL_NO_CONVERSION = "GENERAL_NO_CONVERSION"


@dataclass
class SourceTransformation:
    """Records one deliberate source transformation."""

    line: int | None
    rule: str
    source: str
    target: str


@dataclass
class PseudocodeProcessingResult:
    """Contains processed source and an auditable transformation report."""

    profile: PseudocodeProfile
    original_source: str
    processed_source: str
    transformations: list[SourceTransformation] = field(default_factory=list)
    header_comment_removed: bool = False
    header_lines_removed: int = 0

    @property
    def source_modified(self) -> bool:
        """Returns whether the selected profile changed the supplied source."""

        return self.original_source != self.processed_source

    @property
    def transformation_count(self) -> int:
        """Returns the number of logged transformations."""

        return len(self.transformations)

    @staticmethod
    def _semantic_audit_entry(transformation: SourceTransformation) -> dict:
        """Returns a semantic audit record without exposing legacy rule IDs."""

        source = transformation.source
        target = transformation.target
        source_upper = source.upper()
        target_upper = target.upper()

        family = "SOURCE_NORMALISATION"
        branch = "GENERIC_EQUIVALENCE"
        evidence = ["source and canonical target differ by an approved compatibility equivalence"]
        confidence = "structurally_certain"

        if transformation.rule == "RESERVED_IDENTIFIER_ESCAPE":
            family = "RESERVED_IDENTIFIER_ESCAPE"
            branch = "SOURCE_PROVEN_BINDING_ESCAPE"
            evidence = [
                "the source uses an AJ reserved keyword in an unambiguous identifier-binding position",
                "the protected __reserved_keyword__ prefix preserves the source identifier spelling without assigning new algorithmic meaning",
                "corresponding identifier occurrences are rewritten while quoted text and recognised AJ keyword syntax are preserved",
            ]
            confidence = "source_proven"

        elif re.search(r"\bEND\s+(CLASS|FUNCTION|IF|WHILE|FOR)\b", source_upper) and any(
            token in target_upper
            for token in ("ENDCLASS", "ENDFUNCTION", "ENDIF", "ENDWHILE", "ENDFOR")
        ):
            family = "BLOCK_TERMINATOR"
            branch = "SPACED_END_TO_OPEN_BLOCK"
            evidence = ["a matching block is open at the point of the spaced END phrase"]

        elif "CALL CONSTRUCTOR()" in source_upper and "CALL CONSTRUCTOR()" not in target_upper:
            family = "CLASS_STRUCTURE"
            branch = "REDUNDANT_CONSTRUCTOR_MARKER"
            evidence = ["CLASS implies construction; zero-argument Constructor() adds no separate operation"]
            confidence = "user_confirmed"

        elif re.search(r"<-\s*[A-Za-z_]\w*\s*\+\s*\[[^\n]+\]", source) and "APPEND " in target_upper:
            family = "COLLECTION_SELF_ADDITION"
            branch = "APPEND_SINGLE"
            evidence = ["left side is a known collection", "RHS is a singleton list expression"]

        elif re.search(r"<-\s*[A-Za-z_]\w*\s*\+\s*CALL\s+", source, re.I) and "EXTEND_LIST" in target_upper:
            family = "COLLECTION_SELF_ADDITION"
            branch = "EXTEND_LIST"
            evidence = ["left side is a known list", "RHS is inferred to return a list"]

        elif "_NEXT" in source_upper and ".NEXT" in target_upper:
            family = "OBJECT_PROPERTY"
            branch = "LINKED_LIST_NEXT"
            evidence = ["variable is established as a linked-list node reference"]

        elif any(x in source for x in ("_position", "_velocity", "_destination", "_quantity", "_itemID")) and "." in target:
            family = "OBJECT_PROPERTY"
            branch = "FLATTENED_PROPERTY"
            evidence = ["surrounding iteration establishes the object bound to the flattened property"]

        elif " IS A NUMBER" in source_upper and "IS_NUMBER" in target_upper:
            family = "SEMANTIC_PREDICATE"
            branch = "IS_A_NUMBER"

        elif transformation.rule == "GC220":
            family = "COLLECTION_TYPE_EVIDENCE"
            branch = "EMPTY_BRACES_FROM_INDEXED_WRITE"
            evidence = [
                "source explicitly initialises a simple receiver with bare empty braces",
                "a later same-scope assignment writes through an index on that receiver before any direct rebind",
                "indexed write is incompatible with set semantics and directly evidences keyed mapping use",
            ]
            confidence = "source_proven"

        elif transformation.rule == "GC250":
            family = "COLLECTION_TYPE_EVIDENCE"
            branch = "EMPTY_BRACES_FROM_STRUCTURAL_USAGE"
            evidence = [
                "source explicitly initialises a simple receiver with bare empty braces",
                "later same-scope standard collection operations prove exactly one of set or dictionary semantics before any direct rebind",
                "identifier spelling, membership, iteration, and conflicting operation evidence are not accepted as type proof",
            ]
            confidence = "source_proven"

        elif "{}" in source and "EMPTY DICTIONARY" in target_upper:
            family = "LITERAL"
            branch = "EMPTY_DICTIONARY"

        elif "LIST [" in source_upper and "LIST_VALUE" in target_upper:
            family = "LITERAL"
            branch = "LIST_LITERAL"

        elif "NUMBER_OF_CHARACTERS" in source_upper and "LENGTH OF" in target_upper:
            family = "SEMANTIC_PRIMITIVE"
            branch = "NUMBER_OF_CHARACTERS"

        elif transformation.rule == "GC212":
            family = "SHAPE_ANNOTATION"
            branch = "SQUARE_DIMENSION_IDENTIFIER_REFERENCE"
            evidence = [
                "INPUT annotation explicitly states one square dimension symbol D x D",
                "the same otherwise-unbound symbol is referenced in executable code in that routine",
            ]
            confidence = "structurally_certain"

        elif transformation.rule in {"GC033", "GC034", "GC035", "GC036", "GC037", "GC038", "GC039"}:
            family = "COLLECTION_OPERATION"
            branch = "EVIDENCED_SIMPLE_COLLECTION_METHOD"
            evidence = [
                "receiver type is independently established by an explicit collection declaration or constructor in readable lexical scope",
                "method spelling selects an operation only after receiver evidence exists and never establishes collection type by itself",
                "direct rebinds and formal-parameter shadowing invalidate inherited receiver evidence",
            ]
            confidence = "source_proven"

        elif transformation.rule in {"GC045", "GC046", "GC047", "GC048"}:
            family = "COLLECTION_OPERATION"
            branch = "EVIDENCED_COLLECTION_QUERY_ACCESS"
            evidence = [
                "receiver type is independently established by an explicit collection declaration or constructor in readable lexical scope",
                "query/access spelling is accepted only for collection kinds that support the corresponding length/front/back/empty operation",
                "method spelling never establishes collection type and direct rebinds/formal-parameter shadowing invalidate inherited evidence",
            ]
            confidence = "source_proven"

        elif transformation.rule == "GC213":
            family = "COLLECTION_OPERATION"
            branch = "EVIDENCED_LIST_DEQUE_METHOD"
            evidence = [
                "receiver is independently established as list-backed in the same source",
                "camelCase deque method spelling maps directly to an existing AJ list operation",
            ]
            confidence = "structurally_certain"

        elif transformation.rule == "GC214":
            family = "PROVABLE_POSTCONDITION_ALIGNMENT"
            branch = "REDUNDANT_UNIQUENESS_ABSTRACTION"
            evidence = [
                "the returned collection is explicitly initialised as EMPTY LIST",
                "every APPEND to that collection is guarded by a matching value NOT IN collection condition",
                "no other collection write is present that can invalidate the uniqueness invariant",
            ]
            confidence = "source_proven"

        elif transformation.rule == "GC215":
            family = "STATEFUL_ADT_STRUCTURE"
            branch = "EVIDENCED_ORDERED_CACHE_CONSTRUCTOR"
            evidence = [
                "INIT names persistent capacity-like and ordered-cache state before multiple operations",
                "all recovered operations share the cache state and the size bound is read as LENGTH OF cache == capacity",
                "move-to-front, remove-back, and add-to-front helper calls are preserved as explicit but undefined source abstractions",
                "capacity is supplied through the recovered constructor rather than assigned a synthetic numeric default",
            ]
            confidence = "source_proven"

        elif transformation.rule == "GC216":
            family = "STATEFUL_ADT_STRUCTURE"
            branch = "EVIDENCED_COUNTED_LIST_CONSTRUCTOR"
            evidence = [
                "source explicitly initialises one persistent list as EMPTY LIST and one persistent counter as zero",
                "at least three top-level operations all share both state values",
                "append, pop, indexed-top read, and counter +/-1 updates jointly prove the counted-list interface shape",
                "the recovered zero-argument constructor reuses only source-supplied initial values",
            ]
            confidence = "source_proven"

        elif transformation.rule == "GC217":
            family = "ERROR_SIGNAL"
            branch = "STANDALONE_ERROR_RAISE"
            evidence = [
                "ERROR appears as the complete executable statement rather than as a returned value or identifier",
                "AJ v1.1 represents explicit error generation with RAISE",
            ]
            confidence = "user_confirmed"

        elif transformation.rule == "GC218":
            family = "STATEFUL_ADT_STRUCTURE"
            branch = "EVIDENCED_CONNECTED_MULTI_LIST_CONSTRUCTOR"
            evidence = [
                "source explicitly initialises multiple persistent list states as EMPTY LIST",
                "top-level operations and list states form one connected state/operation graph",
                "source includes an explicit destructive transfer from one evidenced list state into another",
                "the recovered zero-argument constructor reuses only source-supplied empty-list initial values",
            ]
            confidence = "source_proven"

        elif transformation.rule == "GC219":
            family = "STRUCTURAL_WRAPPER"
            branch = "EVIDENCED_INPUT_HELPER_FINAL_RETURN_WRAPPER"
            evidence = [
                "source supplies one or more bare top-level INPUT declarations",
                "all remaining top-level declarations are indentation-style helper routines",
                "the final top-level RETURN calls one of those explicitly supplied helpers",
                "the neutral wrapper removes only the omitted algorithm container and introduces no helper implementation",
            ]
            confidence = "source_proven"

        elif transformation.rule == "GC221":
            family = "COLLECTION_OPERATION"
            branch = "EVIDENCED_LIST_BALANCED_ADD"
            evidence = [
                "receiver is independently established as list-backed by explicit list initialisation",
                "source uses standalone .add(...) collection insertion syntax",
                "balanced-parenthesis scanning preserves the complete nested source expression without inferring a new value",
            ]
            confidence = "structurally_certain"

        elif transformation.rule == "GC223":
            family = "SHAPE_ANNOTATION"
            branch = "EVIDENCED_RECTANGULAR_MATRIX_ALLOCATION"
            evidence = [
                "source explicitly states that two matrix inputs share dimensions R x C",
                "source explicitly requests an R x C result matrix and then overwrites each result[i][j] in the matching nested row/column loops",
                "R and C have no independent runtime binding, so the first evidenced matrix supplies LENGTH OF matrix and LENGTH OF matrix[0]",
                "the source does not supply an initial cell value, so allocated result cells use NONE until the source-supplied writes assign them",
            ]
            confidence = "source_proven"

        elif transformation.rule == "GC224":
            family = "SHAPE_ANNOTATION"
            branch = "EVIDENCED_LINKED_MATRIX_MULTIPLICATION_DIMENSIONS"
            evidence = [
                "source explicitly links A as M x N and B as N x P, proving one shared inner dimension",
                "source explicitly requests an M x P result matrix and supplies the complete M/P/N loop bounds",
                "the supplied inner accumulation is exactly sum += A[i][k] * B[k][j], followed by direct C[i][j] = sum",
                "M, N and P have no independent runtime bindings, so matrix lengths represent only the source-supplied shape annotations",
                "when the source omits an initial cell value, allocated C cells use NONE; an explicit zero initialiser remains zero-filled",
            ]
            confidence = "source_proven"

        elif transformation.rule == "GC225":
            family = "TYPE_COERCION"
            branch = "EVIDENCED_NUMERIC_STRING_CONVERSION"
            evidence = [
                "the source explicitly writes STRING(variable) in a string-accumulation expression rather than a quoted STRING literal",
                "the same variable is independently established as numeric by a MOD/MODULUS assignment",
                "the destination is independently established as string-backed by EMPTY STRING initialisation",
                "only the representation of the explicit conversion is changed: CALL to_string(variable) lowers to Python str(variable)",
            ]
            confidence = "source_proven"

        elif transformation.rule == "GC228":
            family = "SORT_MODE"
            branch = "EXPLICIT_ALPHABETICAL_ORDER"
            evidence = [
                "source explicitly supplies ALPHABETICAL_ORDER as the second argument of a free two-argument SORT call",
                "ALPHABETICAL_ORDER denotes ascending alphabetical ordering rather than runtime data",
                "the existing sort_value compatibility intrinsic already represents ascending sorting and lowers to Python sorted(value)",
                "arbitrary comparators, descending markers, member methods, and other SORT arities remain untouched",
            ]
            confidence = "source_proven"

        elif transformation.rule == "GC229":
            family = "COLLECTION_OPERATION"
            branch = "SEEDED_LIST_BACKED_QUEUE"
            evidence = [
                "source explicitly initialises the receiver from a non-empty list literal, canonicalised earlier as CALL list_value(...) without changing its list representation",
                "the same receiver is explicitly passed to free DEQUEUE/ENQUEUE operations, providing source evidence for FIFO use of that list",
                "DEQUEUE lowers only to the existing REMOVE FIRST ITEM FROM list operation and ENQUEUE lowers only to the existing APPEND operation",
                "unproven receivers and seeded lists without queue operations remain untouched",
            ]
            confidence = "source_proven"

        elif transformation.rule == "GC230":
            family = "TYPE_COERCION"
            branch = "DIRECT_MODULUS_DIGIT_TO_STRING_ACCUMULATOR"
            evidence = [
                "the destination is independently established as string-backed by EMPTY STRING initialisation",
                "the source directly prepends one parenthesised MOD/MODULUS result to that same string accumulator",
                "MOD and MODULUS are accepted only as spelling variants of the same explicit modulus operation",
                "only the required result representation is made explicit as CALL to_string(...); unrelated numeric/string addition remains untouched",
            ]
            confidence = "source_proven"

        elif transformation.rule == "GC231":
            family = "COLLECTION_LITERAL"
            branch = "QUOTED_SCALAR_SET_LITERAL"
            evidence = [
                "the entire assignment RHS is a non-empty brace literal parsed as a set rather than a dictionary",
                "every set member is an explicitly quoted string scalar in the source",
                "the existing to_set compatibility intrinsic preserves the supplied set semantics without changing the frozen AJ parser",
                "dictionaries, empty braces, mixed or unquoted members, comprehensions, and unsupported control characters remain untouched",
            ]
            confidence = "source_proven"

        elif transformation.rule == "GC232":
            family = "TYPE_COERCION"
            branch = "EVIDENCED_SET_TO_LIST_CONVERSION"
            evidence = [
                "the source explicitly calls free ConvertSetToList(name) with exactly one simple identifier argument",
                "the same lexical routine previously establishes that identifier as EMPTY SET",
                "no intervening direct reassignment invalidates the set-backed evidence",
                "the existing to_list compatibility intrinsic preserves the explicit conversion and lowers deterministically to Python list(name)",
            ]
            confidence = "source_proven"

        elif transformation.rule == "GC233":
            family = "ARITHMETIC"
            branch = "EXPLICIT_SQUARE_ROOT_EXPONENTIATION"
            evidence = [
                "source explicitly calls free SQUARE_ROOT(value) with exactly one argument",
                "the approved representation is mathematical square root as value raised to the power 0.5",
                "AJ v1.1 already represents exponentiation with EXP, which lowers deterministically to Python **",
                "no integer, floor, range-bound, or other coercion is introduced by this recovery",
            ]
            confidence = "user_confirmed"

        elif transformation.rule == "GC234":
            family = "CHARACTER_PREDICATE"
            branch = "EXPLICIT_DIGIT_UPPERCASE_INTRINSICS"
            evidence = [
                "source explicitly calls free IS_DIGIT(value) or IS_UPPERCASE(value) with exactly one argument",
                "the pipeline already provides is_digit(value) and is_uppercase(value) compatibility intrinsics",
                "those intrinsics lower directly to Python value.isdigit() and value.isupper() without inventing a string conversion",
                "declarations, member methods, quoted text, and zero/multi-argument calls remain untouched",
            ]
            confidence = "source_proven"

        elif transformation.rule == "GC249":
            family = "MATRIX_DECLARATION"
            branch = "EXPLICIT_RECTANGULAR_MATRIX_ZERO_FILL"
            evidence = [
                "source explicitly declares rows x cols matrix filled with 0",
                "both row and column dimensions are preserved as simple source identifiers",
                "the pipeline already provides create_matrix(rows, cols, fill) for deterministic matrix allocation",
                "expression dimensions, non-zero or missing fills, grid spellings, and prose remain untouched",
            ]
            confidence = "source_proven"

        elif transformation.rule == "GC248":
            family = "SET_EXPRESSION"
            branch = "EVIDENCED_TWO_VALUE_TUPLE_SET_INSERTION"
            evidence = [
                "receiver is independently evidenced as set-backed by an explicit EMPTY SET declaration",
                "GC158 has already preserved the source insertion as CALL add_to_set(receiver, value)",
                "the inserted value is one outer parenthesis pair containing exactly two top-level source expressions",
                "AJ v1.1 already represents that explicit pair value with TUPLE(...) and no collection or arithmetic semantics are added",
            ]
            confidence = "source_proven"

        elif transformation.rule == "GC247":
            family = "COLLECTION_COPY"
            branch = "EVIDENCED_2D_LIST_ROW_COPY"
            evidence = [
                "source explicitly calls free Copy(name) with exactly one simple identifier argument",
                "that identifier is already evidenced as a 2D matrix by create_matrix(...) in the same lexical scope or a readable enclosing scope",
                "the approved copy operation duplicates the outer list and each row via list(map(list, name)) so later indexed board mutation cannot alter a saved snapshot",
                "unproven values, shadowed parameters, direct reassignments, member calls, wrong arities, comments, and quoted text remain untouched",
            ]
            confidence = "user_confirmed"

        elif transformation.rule == "GC246":
            family = "MATRIX_DECLARATION"
            branch = "EXPLICIT_SQUARE_GRID_ZERO_INITIALISATION"
            evidence = [
                "source explicitly declares a direct N x N grid initialized to 0",
                "the row and column dimensions are the same single source identifier",
                "the pipeline already provides create_matrix(rows, cols, fill) for deterministic matrix allocation",
                "rectangular grids, other fill values, missing initialisers, and expression dimensions remain untouched",
            ]
            confidence = "source_proven"

        elif transformation.rule == "GC245":
            family = "SET_EXPRESSION"
            branch = "EVIDENCED_NON_MUTATING_SINGLETON_SET_EXTENSION"
            evidence = [
                "a canonical routine call explicitly supplies EMPTY SET for the corresponding formal parameter",
                "inside that same routine the source forms a new value with parameter + {single_expression}",
                "the approved representation converts the existing set to a list, appends exactly one source-supplied value through list_value, then converts the result back to a set",
                "the original set is not mutated and no removal/backtracking operation is invented",
            ]
            confidence = "user_confirmed"

        elif transformation.rule == "GC242":
            family = "ASSIGNMENT_SURFACE"
            branch = "MEMBER_INDEXED_LVALUE_EQUALS"
            evidence = [
                "source uses a single assignment equals on an explicit object.member[index] lvalue",
                "the existing AJ assignment operator is <- and indexed member storage is already supported by the class/compiler path",
                "the transformation changes only the assignment token and preserves target, index expression, and right-hand value verbatim",
                "comparison spellings ==, !=, <=, and >= remain outside the rule",
            ]
            confidence = "source_proven"

        elif transformation.rule == "GC241":
            family = "CLASS_STRUCTURE"
            branch = "CONTEXTUAL_CLASS_ROUTINE_RECOVERY"
            evidence = [
                "source explicitly declares a CLASS container",
                "direct-child CONSTRUCTOR(...), PROCEDURE name(...), and FUNCTION name(...) declarations are routine declarations in that class context",
                "frozen AJ v1.1 represents class routines as CONSTRUCTOR ... ENDCONSTRUCTOR and METHOD ... ENDMETHOD",
                "routine bodies and member semantics are preserved; GC241 does not infer properties, assignments, return values, or external class behaviour",
            ]
            confidence = "user_confirmed"

        elif transformation.rule == "GC240":
            family = "COLLECTION_INITIALISATION"
            branch = "USER_CONFIRMED_NONE_FILLED_FIXED_ARRAY"
            evidence = [
                "source explicitly declares Array of size N without a fill value",
                "project rule explicitly defines that surface as N writable slots initialised to NONE",
                "the existing create_array(size, value) compatibility intrinsic can represent those slots without changing AJ v1.1",
                "deterministic Python lowering for the NONE-filled case is [None] * N; declarations with an explicit fill value remain unchanged",
            ]
            confidence = "user_confirmed"

        elif transformation.rule == "GC238":
            family = "TYPE_COERCION"
            branch = "EXPLICIT_SET_CONVERSION_INTRINSIC"
            evidence = [
                "source explicitly calls free ConvertToSet(value) with exactly one argument",
                "the operation explicitly requests set conversion rather than requiring set semantics to be inferred",
                "the existing to_set compatibility intrinsic preserves that supplied conversion and lowers deterministically to Python set(value)",
                "declarations, member methods, quoted text, and zero/multi-argument calls remain untouched",
            ]
            confidence = "source_proven"

        elif transformation.rule == "GC227":
            family = "REGEX_SUBSTITUTION"
            branch = "EVIDENCED_REGEX_REPLACE_ALL"
            evidence = [
                "source explicitly calls free REPLACE_ALL(text, pattern, replacement) with exactly three arguments",
                "the quoted pattern contains direct regex syntax evidence, so regex substitution is source-evidenced rather than inferred from the function name alone",
                "pattern and replacement backslashes are protected only across compatibility-to-AJ representation so regex escapes survive the frozen AJ string lexer",
                "the internal regex_replace intrinsic lowers the supplied pattern/replacement to Python re.sub without changing the source algorithm",
            ]
            confidence = "source_proven"

        elif transformation.rule == "GC222":
            family = "COLLECTION_DEDUPLICATION"
            branch = "EXACT_UNIQUE_TO_SET_INTRINSIC"
            evidence = [
                "source explicitly calls unique(collection) as a one-argument deduplication operation",
                "AJ v1.1 already has native set semantics, while the compatibility layer may lower that exact source operation to the existing to_set intrinsic",
                "the pair-search algorithm and collection contents are unchanged; only duplicate elimination is represented",
            ]
            confidence = "user_confirmed"

        elif re.search(r"\bFOR\s+[A-Z_]\w*\s+FROM\s+0\s+TO\s+[A-Z_]\w*\s*-\s*1", source_upper) and "LENGTH OF" in target_upper:
            family = "SHAPE_ANNOTATION"
            branch = "SQUARE_DIMENSION_LOOP_BOUND"
            evidence = [
                "INPUT annotation explicitly states one square dimension symbol D x D",
                "source loop uses that same symbol only as the inclusive upper bound D - 1",
            ]
            confidence = "structurally_certain"

        elif "CALL MODULUS" in source_upper and " MODULUS " in target_upper:
            family = "ARITHMETIC"
            branch = "FUNCTION_SHAPED_MODULUS"

        elif "CALL FLOOR" in source_upper and "INTEGER DIVISION" in target_upper:
            family = "ARITHMETIC"
            branch = "INTEGER_DIVISION"

        return {
            "line": transformation.line,
            "rule_family": family,
            "branch": branch,
            "source": source,
            "canonical": target,
            "evidence": evidence,
            "confidence": confidence,
            "semantic_change": False,
        }

    def to_dict(self) -> dict:
        """Returns a semantic, serialisable processing audit."""

        transformations = [
            self._semantic_audit_entry(transformation)
            for transformation in self.transformations
        ]

        return {
            "audit_schema": "SEMANTIC_RULE_FAMILIES_V1",
            "profile": self.profile.value,
            "source_modified": self.source_modified,
            "transformation_count": len(transformations),
            "transformations": transformations,
            "header_comment_removed": self.header_comment_removed,
            "header_lines_removed": self.header_lines_removed,
        }

    def to_json(self) -> str:
        """Returns the processing report as formatted JSON."""

        return json.dumps(
            self.to_dict(),
            indent=2,
        )


class InitialHashCommentStripper:
    """Removes an optional leading study-title metadata block before parsing.

    Supported title surfaces are a leading ``#...`` metadata block and the
    single-file study form ``<number>. <title>`` when the next non-blank line
    clearly begins executable pseudocode.
    """

    PSEUDOCODE_START_PATTERN = re.compile(
        r"^(?:"
        r"INPUT\b|OUTPUT\b|FUNCTION\b|CLASS\b|IF\b|WHILE\b|FOR\b|"
        r"RETURN\b|CALL\b|TRY\b|RAISE\b|COMMENT\b|BREAK\b|"
        r"[A-Za-z_][A-Za-z0-9_]*(?:\[[^\]]+\])?\s*(?:<-|=)"
        r")",
        re.IGNORECASE,
    )

    NUMBERED_TITLE_PATTERN = re.compile(r"^\d+\.\s+\S")

    def strip(self, source: str) -> tuple[str, bool, int]:
        """Removes a supported leading title block before pseudocode begins."""

        source_lines = source.splitlines(keepends=True)

        if not source_lines:
            return source, False, 0

        header_start_index = 0

        while header_start_index < len(source_lines):
            candidate_line = source_lines[header_start_index]
            candidate_line = candidate_line.lstrip("\ufeff \t\r\n")

            if candidate_line != "":
                break

            header_start_index += 1

        if header_start_index >= len(source_lines):
            return source, False, 0

        first_content_line = source_lines[header_start_index]
        first_content_line = first_content_line.lstrip("\ufeff \t")

        if not first_content_line.startswith("#"):
            stripped_first_content = first_content_line.strip()
            if self.NUMBERED_TITLE_PATTERN.match(stripped_first_content):
                next_content_index = header_start_index + 1
                while next_content_index < len(source_lines):
                    if source_lines[next_content_index].strip() != "":
                        break
                    next_content_index += 1

                if (
                    next_content_index < len(source_lines)
                    and self._looks_like_pseudocode(
                        source_lines[next_content_index].strip()
                    )
                ):
                    processed_source = "".join(source_lines[next_content_index:])
                    return processed_source, True, next_content_index

            return source, False, 0

        first_pseudocode_index = None

        for index in range(header_start_index + 1, len(source_lines)):
            candidate = source_lines[index]
            stripped_candidate = candidate.strip()

            if stripped_candidate == "":
                first_pseudocode_index = index + 1

                while first_pseudocode_index < len(source_lines):
                    if source_lines[first_pseudocode_index].strip() != "":
                        break

                    first_pseudocode_index += 1

                break

            if self._looks_like_pseudocode(stripped_candidate):
                first_pseudocode_index = index
                break

        if first_pseudocode_index is None:
            first_pseudocode_index = header_start_index + 1

        processed_source = "".join(
            source_lines[first_pseudocode_index:]
        )

        return processed_source, True, first_pseudocode_index

    def _looks_like_pseudocode(self, line: str) -> bool:
        """Returns whether a line clearly begins with executable pseudocode."""

        return bool(
            self.PSEUDOCODE_START_PATTERN.match(
                line
            )
        )


@dataclass(frozen=True)
class CharacterNormalisationRule:
    """Defines one auditable Generic compatibility character rule."""

    rule_id: str
    source: str
    target: str
    description: str


class GenericCharacterNormaliser:
    """Normalises deterministic source-character variants into strict AJ tokens.

    ``CANONICAL_CHARACTER_LOOKUP`` is the single authoritative lookup for
    source glyphs whose meaning is unambiguous.  Deliberately, ``?`` is absent:
    lossy question marks require source-integrity recovery first and never map
    directly to a canonical AJ operator.
    """

    CANONICAL_CHARACTER_LOOKUP = {
        "≠": ("!=", "GC001", "Unicode not-equal operator"),
        "≤": ("<=", "GC002", "Unicode less-than-or-equal operator"),
        "≥": (">=", "GC003", "Unicode greater-than-or-equal operator"),
        "←": ("<-", "GC004", "Unicode assignment arrow"),
        "×": ("*", "GC005", "Unicode multiplication operator"),
        "∞": ("INFINITY", "GC006", "Unicode infinity symbol"),
        "→": ("TO", "GC007", "Unicode right arrow"),
        "“": ('"', "GC008", "Opening smart double quote"),
        "”": ('"', "GC009", "Closing smart double quote"),
        "‘": ("'", "GC010", "Opening smart single quote"),
        "’": ("'", "GC011", "Closing smart single quote"),
        "–": ("-", "GC012", "Unicode en dash"),
        "\u2005": (" ", "GC013", "Unicode four-per-em space"),
        "\u00a0": (" ", "GC014", "Non-breaking space"),
        "\u200b": ("", "GC015", "Zero-width space"),
        "\ufeff": ("", "GC016", "UTF-8 BOM / zero-width no-break space"),
    }

    RULES = tuple(
        CharacterNormalisationRule(rule_id, source, target, description)
        for source, (target, rule_id, description)
        in CANONICAL_CHARACTER_LOOKUP.items()
    )

    def process(self, source: str) -> tuple[str, list[SourceTransformation]]:
        """Applies corpus-derived character rules and records every changed line."""

        source_lines = source.splitlines(keepends=True)
        transformations = []
        processed_lines = []

        for line_number, source_line in enumerate(source_lines, start=1):
            transformed_line = source_line

            for rule in self.RULES:
                if rule.source not in transformed_line:
                    continue

                before = transformed_line
                transformed_line = transformed_line.replace(
                    rule.source,
                    rule.target,
                )

                transformations.append(
                    SourceTransformation(
                        line=line_number,
                        rule=rule.rule_id,
                        source=before.rstrip("\r\n"),
                        target=transformed_line.rstrip("\r\n"),
                    )
                )

            degree_before = transformed_line
            transformed_line = re.sub(
                r"(?<=\d)°",
                " DEG",
                transformed_line,
            )

            if transformed_line != degree_before:
                transformations.append(
                    SourceTransformation(
                        line=line_number,
                        rule="GC017",
                        source=degree_before.rstrip("\r\n"),
                        target=transformed_line.rstrip("\r\n"),
                    )
                )

            processed_lines.append(
                transformed_line
            )

        return "".join(processed_lines), transformations


class GenericStatementBoundaryNormaliser:
    """Reconstructs logical lines in pseudocode compressed onto one physical line."""

    START_PATTERN = re.compile(
        r"(?i)(?:^|\s+)(?=(?:"
        r"INPUT\b|OUTPUT\b|PRINT\b|DISPLAY\b|RETURN\b|RAISE\b|"
        r"IF\b|ELSE\s+IF\b|ELSE\b|WHILE\b|FOR\s+EACH\b|FOR\b|"
        r"FUNCTION\b|PROCEDURE\b|CALL\b|APPEND\b|ADD\b|REMOVE\b|"
        r"SWAP\b|REVERSE\b|ENQUEUE\b|DEQUEUE\b|PUSH\b|POP\b|"
        r"CREATE\b|INIT\b|[A-Za-z_][A-Za-z0-9_]*(?:\[[^\]]+\])?\.(?:append|add|enqueue|dequeue|push|pop|popFront|popBack|pushBack)\b|"
        r"[A-Za-z_][A-Za-z0-9_]*(?:\[[^\]]+\])?\s*(?:<-|\+=|-=|\*=|/=|%=|\+\+|--|(?<![<>=!])=(?!=))"
        r"))"
    )

    def process(self, source: str) -> tuple[str, list[SourceTransformation]]:
        transformations: list[SourceTransformation] = []
        output: list[str] = []

        source, continuation_transformations = self._join_expression_continuations(source)
        transformations.extend(continuation_transformations)

        source, branch_chain_transformations = self._repair_conditional_branch_chains(source)
        transformations.extend(branch_chain_transformations)

        # Phase 11: already-structured multiline pseudocode must not be treated
        # as a compressed one-line program. Preserve its physical boundaries.
        if self._is_structured_multiline_source(source):
            return source, transformations

        for line_number, source_line in enumerate(source.splitlines(), start=1):
            stripped = source_line.strip()

            if not self._is_compressed_candidate(stripped):
                output.append(source_line)
                continue

            statements = self._split_statements(stripped)

            if len(statements) <= 1:
                output.append(source_line)
                continue

            reconstructed = self._reconstruct_indentation(statements)
            output.extend(reconstructed)
            transformations.append(
                SourceTransformation(
                    line=line_number,
                    rule="GC085",
                    source=source_line,
                    target="\n".join(reconstructed),
                )
            )

        return "\n".join(output), transformations


    def _repair_conditional_branch_chains(
        self,
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        """Remove an ENDIF that incorrectly separates ELSE/ELSE IF from its IF."""
        lines = source.splitlines()
        output: list[str] = []
        transformations: list[SourceTransformation] = []
        index = 0

        while index < len(lines):
            line = lines[index]
            stripped = line.strip()

            if re.fullmatch(r"ENDIF", stripped, re.IGNORECASE):
                lookahead = index + 1
                while lookahead < len(lines) and not lines[lookahead].strip():
                    lookahead += 1

                if lookahead < len(lines):
                    next_line = lines[lookahead]
                    next_stripped = next_line.strip()
                    current_indent = len(line) - len(line.lstrip())
                    next_indent = len(next_line) - len(next_line.lstrip())

                    if (
                        current_indent == next_indent
                        and re.match(r"ELSE(?:\s+IF\b|\b)", next_stripped, re.IGNORECASE)
                    ):
                        transformations.append(
                            SourceTransformation(
                                line=index + 1,
                                rule="GC133",
                                source=line,
                                target="",
                            )
                        )
                        index += 1
                        continue

            output.append(line)
            index += 1

        return "\n".join(output), transformations


    def _join_expression_continuations(
        self,
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        """Join arithmetic/logical expressions continued onto the next line."""
        lines = source.splitlines()
        output: list[str] = []
        transformations: list[SourceTransformation] = []
        index = 0

        continuation_end = re.compile(
            r"(?:\+|-|\*|/|%|==|!=|<=|>=|<|>|=|<-|\bAND\b|\bOR\b|\bXOR\b|,|\()\s*$",
            re.IGNORECASE,
        )

        while index < len(lines):
            current = lines[index]
            combined = current
            start_line = index + 1

            while (
                index + 1 < len(lines)
                and combined.strip()
                and continuation_end.search(combined.rstrip())
                # Postfix updates are complete statements, not expressions with
                # a dangling arithmetic operator.  Protect both forms before
                # joining physical lines so later structural rules can expand them.
                and not re.search(r"(?:\+\+|--)\s*$", combined.rstrip())
                and lines[index + 1].strip()
            ):
                next_line = lines[index + 1]
                combined = combined.rstrip() + " " + next_line.strip()
                index += 1

            output.append(combined)

            if combined != current:
                transformations.append(
                    SourceTransformation(
                        line=start_line,
                        rule="GC126",
                        source=current,
                        target=combined,
                    )
                )

            index += 1

        return "\n".join(output), transformations


    def _is_structured_multiline_source(self, source: str) -> bool:
        non_empty = [line for line in source.splitlines() if line.strip()]
        if len(non_empty) < 3:
            return False

        indented = sum(1 for line in non_empty if len(line) > len(line.lstrip()))
        control_lines = sum(
            1
            for line in non_empty
            if re.match(r"\s*(?:IF|ELSE|WHILE|FOR|FUNCTION|PROCEDURE|RETURN|INPUT|OUTPUT|INIT|CREATE)\b", line, re.I)
        )
        # Existing indentation is the strongest signal. Several separate control
        # statements is a secondary signal for flat but already-line-broken text.
        return indented >= 1 or control_lines >= 3

    def _is_compressed_candidate(self, line: str) -> bool:
        if not line or len(line) < 35:
            return False
        starts = self._candidate_positions(line)
        return len(starts) >= 3

    def _candidate_positions(self, line: str) -> list[int]:
        masked = self._mask_nested_and_quoted_text(line)
        positions = {0}
        for match in self.START_PATTERN.finditer(masked):
            pos = match.start()
            while pos < len(masked) and masked[pos].isspace():
                pos += 1
            if masked[pos:pos + 2].upper() == "IF":
                prefix = masked[:pos].rstrip().upper()
                if prefix.endswith("ELSE"):
                    continue
            positions.add(pos)
        return sorted(positions)

    def _split_statements(self, line: str) -> list[str]:
        positions = self._candidate_positions(line)
        pieces: list[str] = []
        for index, start in enumerate(positions):
            end = positions[index + 1] if index + 1 < len(positions) else len(line)
            piece = line[start:end].strip()
            if piece.endswith(","):
                piece = piece[:-1].rstrip()
            if piece:
                pieces.append(piece)
        return self._repair_control_headers(pieces)

    def _repair_control_headers(self, pieces: list[str]) -> list[str]:
        repaired: list[str] = []
        for piece in pieces:
            piece = piece.strip()
            if piece.endswith(":"):
                piece = piece[:-1].rstrip()
            repaired.append(piece)
        return repaired

    def _reconstruct_indentation(self, statements: list[str]) -> list[str]:
        output: list[str] = []
        indent = 0
        stack: list[str] = []

        for index, statement in enumerate(statements):
            upper = statement.upper()
            next_upper = statements[index + 1].upper() if index + 1 < len(statements) else ""

            if upper.startswith("ELSE IF ") or upper == "ELSE" or upper.startswith("ELSE "):
                if stack and stack[-1] == "IF":
                    indent = max(0, indent - 4)
                output.append(" " * indent + statement)
                indent += 4
                continue

            # A return immediately after IF belongs to that branch. A return after a
            # loop body normally follows the loop, so close active loop scopes first.
            if upper.startswith("RETURN ") and stack and stack[-1] != "IF":
                while stack and stack[-1] in {"FOR", "WHILE"}:
                    stack.pop()
                    indent = max(0, indent - 4)

            output.append(" " * indent + statement)

            opener = None
            if upper.startswith("FUNCTION ") or upper.startswith("PROCEDURE "):
                opener = "FUNCTION"
            elif upper.startswith("IF "):
                opener = "IF"
            elif upper.startswith("WHILE "):
                opener = "WHILE"
            elif upper.startswith("FOR "):
                opener = "FOR"

            if opener is not None:
                stack.append(opener)
                indent += 4
                continue

            # A single compact branch such as IF condition RETURN value ends after
            # the return unless an ELSE/ELSE IF immediately follows.
            if upper.startswith("RETURN ") and stack and stack[-1] == "IF":
                if not (next_upper == "ELSE" or next_upper.startswith("ELSE ") or next_upper.startswith("ELSE IF ")):
                    stack.pop()
                    indent = max(0, indent - 4)

        return output

    def _mask_nested_and_quoted_text(self, text: str) -> str:
        chars = list(text)
        quote = None
        escape = False
        depth = 0

        for index, char in enumerate(text):
            if quote is not None:
                chars[index] = " "
                if escape:
                    escape = False
                elif char == "\\":
                    escape = True
                elif char == quote:
                    quote = None
                continue

            if char in {"'", '"'}:
                quote = char
                chars[index] = " "
                continue

            if char in "([{":
                depth += 1
                chars[index] = " "
                continue

            if char in "})]":
                chars[index] = " "
                depth = max(0, depth - 1)
                continue

            if depth > 0:
                chars[index] = " "

        return "".join(chars)


@dataclass(frozen=True)
class OperatorNormalisationRule:
    """Defines one auditable Generic compatibility operator rule."""

    rule_id: str
    source: str
    target: str
    description: str


class GenericOperatorNormaliser:
    """Normalises operator forms observed across the six-model corpus."""

    COMPOUND_RULES = (
        OperatorNormalisationRule("GC018", "+=", "<-", "Compound addition assignment"),
        OperatorNormalisationRule("GC019", "-=", "<-", "Compound subtraction assignment"),
        OperatorNormalisationRule("GC020", "*=", "<-", "Compound multiplication assignment"),
        OperatorNormalisationRule("GC021", "/=", "<-", "Compound division assignment"),
        OperatorNormalisationRule("GC022", "%=", "<-", "Compound modulus assignment"),
    )

    def process(self, source: str) -> tuple[str, list[SourceTransformation]]:
        """Applies context-aware operator rules and records each changed line."""

        transformations = []
        processed_lines = []

        for line_number, source_line in enumerate(source.splitlines(keepends=True), start=1):
            transformed_line = source_line

            transformed_line, line_transformations = self._normalise_line(
                transformed_line,
                line_number,
            )
            transformations.extend(line_transformations)
            processed_lines.append(transformed_line)

        return "".join(processed_lines), transformations

    def _normalise_line(
        self,
        line: str,
        line_number: int,
    ) -> tuple[str, list[SourceTransformation]]:
        """Normalises one line without confusing comparison and assignment equals."""

        transformations = []
        transformed = line

        for rule in self.COMPOUND_RULES:
            pattern = re.compile(
                rf"(?P<target>[A-Za-z_][A-Za-z0-9_]*(?:\[[^\]]+\])?(?:\.[A-Za-z_][A-Za-z0-9_]*)*)\s*{re.escape(rule.source)}\s*(?P<value>[^,;\n]+)"
            )

            def replace_compound(match):
                target = match.group("target")
                value = match.group("value").strip()
                operator = rule.source[0]
                return f"{target} <- {target} {operator} {value}"

            before = transformed
            transformed = pattern.sub(replace_compound, transformed)
            self._record_if_changed(
                transformations, line_number, rule.rule_id, before, transformed
            )

        for rule_id, suffix, operator in (
            ("GC023", "++", "+"),
            ("GC024", "--", "-"),
        ):
            pattern = re.compile(
                rf"(?P<target>[A-Za-z_][A-Za-z0-9_]*(?:\[[^\]]+\])?(?:\.[A-Za-z_][A-Za-z0-9_]*)*)\s*{re.escape(suffix)}"
            )

            def replace_step(match, op=operator):
                target = match.group("target")
                return f"{target} <- {target} {op} 1"

            before = transformed
            transformed = pattern.sub(replace_step, transformed)
            self._record_if_changed(
                transformations, line_number, rule_id, before, transformed
            )

        before = transformed
        transformed = self._normalise_condition_equals(transformed)
        self._record_if_changed(
            transformations, line_number, "GC025", before, transformed
        )

        before = transformed
        transformed = self._normalise_member_indexed_assignment_equals(transformed)
        self._record_if_changed(
            transformations, line_number, "GC242", before, transformed
        )

        before = transformed
        transformed = self._normalise_assignment_equals(transformed)
        self._record_if_changed(
            transformations, line_number, "GC026", before, transformed
        )

        before = transformed
        transformed = self._normalise_safe_comparison_chain(transformed)
        self._record_if_changed(
            transformations, line_number, "GC195", before, transformed
        )

        return transformed, transformations

    def _normalise_safe_comparison_chain(self, line: str) -> str:
        """Expands safe unparenthesised comparison chains in control conditions.

        Canonical AJ v1.0 permits one comparison operator per comparison
        expression. Conventional pseudocode often writes a mathematical chain
        such as ``low <= target < high``. For side-effect-free operands the
        meaning is deterministic and can be represented in existing AJ syntax
        as ``low <= target AND target < high``.

        This rule is deliberately limited to explicit IF / ELSE IF / WHILE
        conditions and to operands whose repeated textual use cannot trigger an
        operation. Calls, INPUT, RANDOM expressions, Boolean operators and
        function-style expressions other than LENGTH/len are left untouched.
        The strict parser separately rejects any remaining unparenthesised chain
        so an unsafe case cannot silently acquire left-associated semantics.
        """
        line_ending = ""
        if line.endswith("\r\n"):
            line_ending = "\r\n"
            content = line[:-2]
        elif line.endswith("\n") or line.endswith("\r"):
            line_ending = line[-1]
            content = line[:-1]
        else:
            content = line

        match = re.match(
            r"^(?P<prefix>\s*(?:IF|ELSE\s+IF|WHILE)\s+)(?P<body>.*)$",
            content,
            re.IGNORECASE,
        )
        if match is None:
            return line

        prefix = match.group("prefix")
        body = match.group("body")
        boundary = re.search(r"\s+(?:THEN|DO)\b|:", body, re.IGNORECASE)
        if boundary is None:
            condition = body
            suffix = ""
        else:
            condition = body[:boundary.start()]
            suffix = body[boundary.start():]

        operands, operators = self._split_top_level_comparison_chain(condition)
        if len(operators) < 2 or len(operands) != len(operators) + 1:
            return line
        if not all(self._comparison_chain_operand_is_safe(part) for part in operands):
            return line

        expanded = " AND ".join(
            f"{operands[index].strip()} {operator} {operands[index + 1].strip()}"
            for index, operator in enumerate(operators)
        )
        return f"{prefix}{expanded}{suffix}{line_ending}"

    def _split_top_level_comparison_chain(
        self,
        expression: str,
    ) -> tuple[list[str], list[str]]:
        operands: list[str] = []
        operators: list[str] = []
        start = 0
        stack: list[str] = []
        quote = None
        escape = False
        index = 0
        closing = {"(": ")", "[": "]", "{": "}"}

        while index < len(expression):
            char = expression[index]
            if quote is not None:
                if escape:
                    escape = False
                elif char == "\\":
                    escape = True
                elif char == quote:
                    quote = None
                index += 1
                continue

            if char in {"'", '"'}:
                quote = char
                index += 1
                continue
            if char in closing:
                stack.append(char)
                index += 1
                continue
            if char in closing.values():
                if stack and closing[stack[-1]] == char:
                    stack.pop()
                index += 1
                continue
            if stack:
                index += 1
                continue

            operator = None
            for candidate in ("<=", ">=", "==", "!=", "<", ">"):
                if expression.startswith(candidate, index):
                    operator = candidate
                    break
            if operator is None:
                index += 1
                continue

            operands.append(expression[start:index].strip())
            operators.append(operator)
            index += len(operator)
            start = index

        operands.append(expression[start:].strip())
        return operands, operators

    def _comparison_chain_operand_is_safe(self, operand: str) -> bool:
        text = operand.strip()
        if not text:
            return False
        if re.search(r"(?i)\b(?:CALL|INPUT|RANDOM|AND|OR|XOR|NOT\s+IN|NOT)\b", text):
            return False
        if re.search(r"(?:<=|>=|==|!=|<|>)", text):
            return False

        # Conventional function-style calls may still exist this early in the
        # generic pipeline. LENGTH/len are read-only size expressions; other
        # calls are conservatively treated as potentially side-effecting.
        for function_name in re.findall(r"\b([A-Za-z_]\w*)\s*\(", text):
            if function_name.lower() not in {"length", "len"}:
                return False
        return True

    def _normalise_condition_equals(self, line: str) -> str:
        """Converts single equals to equality only in explicit condition clauses."""

        line_ending = ""

        if line.endswith("\r\n"):
            line_ending = "\r\n"
            content = line[:-2]
        elif line.endswith("\n") or line.endswith("\r"):
            line_ending = line[-1]
            content = line[:-1]
        else:
            content = line

        condition_match = re.match(
            r"^(?P<prefix>\s*(?:IF|ELSE\s+IF|WHILE)\s+)(?P<body>.*)$",
            content,
            re.IGNORECASE,
        )

        if condition_match is None:
            return line

        prefix = condition_match.group("prefix")
        body = condition_match.group("body")

        boundary_match = re.search(
            r"\s+THEN\b|:",
            body,
            re.IGNORECASE,
        )

        if boundary_match is None:
            condition_text = body
            suffix = ""
        else:
            condition_text = body[:boundary_match.start()]
            suffix = body[boundary_match.start():]

        condition_text = re.sub(
            r"(?<![<>=!])=(?!=)",
            "==",
            condition_text,
        )
        return f"{prefix}{condition_text}{suffix}{line_ending}"

    def _normalise_member_indexed_assignment_equals(self, line: str) -> str:
        """Recovers a direct member-index lvalue written with a single equals.

        GC242 is deliberately narrower than the ordinary GC026 assignment
        surface.  It exists for an lvalue whose indexing follows an object
        member path, for example ``self.arr[self.top_index] = item``.  The
        comparison guard is encoded in the equals token itself, so ``==``,
        ``!=``, ``<=`` and ``>=`` remain untouched.
        """

        return re.sub(
            r"^(?P<indent>\s*)(?P<target>[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)+(?:\[[^\]\n]+\])+?)\s*(?<![<>=!])=(?!=)\s*",
            lambda match: f"{match.group('indent')}{match.group('target')} <- ",
            line,
            count=1,
        )

    def _normalise_assignment_equals(self, line: str) -> str:
        """Converts a leading lvalue assignment equals to AJ assignment syntax."""

        return re.sub(
            r"^(?P<indent>\s*)(?P<target>[A-Za-z_][A-Za-z0-9_]*(?:\[[^\]]+\])?(?:\.[A-Za-z_][A-Za-z0-9_]*)*)\s*(?<![<>=!])=(?!=)\s*",
            lambda match: f"{match.group('indent')}{match.group('target')} <- ",
            line,
            count=1,
        )

    def _record_if_changed(
        self,
        transformations: list[SourceTransformation],
        line_number: int,
        rule_id: str,
        before: str,
        after: str,
    ) -> None:
        """Adds one transformation record when a rule changes a line."""

        if before == after:
            return

        transformations.append(
            SourceTransformation(
                line=line_number,
                rule=rule_id,
                source=before.rstrip("\r\n"),
                target=after.rstrip("\r\n"),
            )
        )


class GenericLiteralDeclarationNormaliser:
    """Normalises generic literal and declaration forms observed after Phase 7."""

    def process(self, source: str) -> tuple[str, list[SourceTransformation]]:
        transformations: list[SourceTransformation] = []
        output: list[str] = []

        for line_number, source_line in enumerate(source.splitlines(), start=1):
            lines, rules = self._normalise_line(source_line)
            if lines != [source_line]:
                target = "\n".join(lines)
                for rule in rules:
                    transformations.append(SourceTransformation(
                        line=line_number, rule=rule, source=source_line, target=target
                    ))
            output.extend(lines)

        return "\n".join(output), transformations

    def _normalise_line(self, line: str) -> tuple[list[str], list[str]]:
        indent = line[:len(line)-len(line.lstrip())]
        content = line.strip()
        rules: list[str] = []
        if not content:
            return [line], rules

        # Generic declarations such as CREATE map counts / CREATE empty Dictionary.
        # A type-only dictionary declaration has no supplied identifier.
        # Preserve it with a deterministic anonymous name rather than dropping
        # the declaration or inventing semantic meaning.
        if re.fullmatch(
            r"CREATE\s+(?:EMPTY\s+)?(?:MAP|HASH\s*MAP|DICTIONARY)",
            content,
            re.IGNORECASE,
        ):
            return [f"{indent}Anonymous_Dictionary <- EMPTY DICTIONARY"], ["GC115"]

        m = re.fullmatch(r"CREATE\s+(?:empty\s+)?(?:map|hash\s*map|dictionary)\s+([A-Za-z_]\w*)", content, re.I)
        if m:
            return [f"{indent}{m.group(1)} <- EMPTY DICTIONARY"], ["GC087"]
        m = re.fullmatch(r"CREATE\s+(?:empty\s+)?list\s+([A-Za-z_]\w*)", content, re.I)
        if m:
            return [f"{indent}{m.group(1)} <- EMPTY LIST"], ["GC088"]
        m = re.fullmatch(r"CREATE\s+(?:empty\s+)?array\s+([A-Za-z_]\w*)", content, re.I)
        if m:
            return [f"{indent}{m.group(1)} <- CALL create_array(0, NONE)"], ["GC088"]
        m = re.fullmatch(r"CREATE\s+(?:empty\s+)?set\s+([A-Za-z_]\w*)", content, re.I)
        if m:
            return [f"{indent}{m.group(1)} <- EMPTY SET"], ["GC089"]

        # INIT x = value is simply an initial assignment in generic pseudocode.
        m = re.fullmatch(r"INIT\s+([A-Za-z_]\w*)\s*(?:=|<-)\s*(.+)", content, re.I)
        if m:
            content = f"{m.group(1)} <- {m.group(2).strip()}"
            rules.append("GC090")

        # Empty list syntax is unambiguous.
        before = content
        content = content.replace("[]", "EMPTY LIST")
        if content != before:
            rules.append("GC091")

        # Bare ``{}`` is intentionally not classified here.  Empty braces are
        # ambiguous between set-like and dictionary-like source notation, and
        # identifier spelling is not type evidence.  The source-wide GC220/GC250
        # evidence pass runs before this line normaliser and resolves only braces
        # whose later same-scope operations prove one collection kind.

        # Whole RHS list literals map directly to AJ LIST literals.
        m = re.match(r"^([A-Za-z_]\w*)\s*(?:=|<-)\s*(\[[^\]]*\])\s*$", content)
        if m and m.group(2) != "[]":
            content = f"{m.group(1)} <- LIST {m.group(2)}"
            rules.append("GC094")

        # GC231 / QUOTED_SCALAR_SET_LITERAL:
        # A non-empty Python-style brace literal made exclusively from quoted
        # string scalars is unambiguously a set rather than a dictionary.  The
        # frozen AJ parser does not currently consume non-empty SET [...] even
        # though the v1.1 specification documents it, so compatibility routes
        # this exact source representation through the already-supported
        # to_set(CALL list_value(...)) representation.  This must run before
        # GC095; otherwise
        # escaped apostrophe/double-quote members can be corrupted by the raw
        # string wrapper.  Dictionaries, empty braces, unquoted/mixed members,
        # comprehensions and unsupported control characters are left unchanged.
        quoted_set = self._normalise_quoted_scalar_set_assignment(content)
        if quoted_set is not None:
            return [f"{indent}{quoted_set}"], rules + ["GC231"]

        # Simple dictionary literals are expanded into an empty dictionary plus indexed assignments.
        dict_match = re.match(r"^([A-Za-z_]\w*)\s*(?:=|<-)\s*\{(.+)\}\s*$", content)
        if dict_match and ":" in dict_match.group(2):
            name = dict_match.group(1)
            entries = self._split_simple_entries(dict_match.group(2))
            if entries is not None:
                lines = [f"{indent}{name} <- EMPTY DICTIONARY"]
                for key, value in entries:
                    key_expr = key.strip()
                    if re.fullmatch(r"[A-Za-z_]\w*", key_expr):
                        key_expr = f'STRING("{key_expr}")'
                    else:
                        try:
                            parsed_key = ast.parse(key_expr, mode="eval").body
                        except (SyntaxError, ValueError):
                            parsed_key = None
                        if (
                            isinstance(parsed_key, ast.Constant)
                            and isinstance(parsed_key.value, str)
                        ):
                            rendered_key = self._render_aj_string_value(parsed_key.value)
                            if rendered_key is not None:
                                key_expr = rendered_key
                    lines.append(f"{indent}{name}[{key_expr}] <- {value.strip()}")
                return lines, rules + ["GC097"]

        # Raw empty strings have a direct AJ literal form and are unambiguous.
        string_before = content
        content = re.sub(r'(?<!STRING\()(?<!CHAR\()(["\'])\1', 'EMPTY STRING', content)
        if not re.match(r"^(?:OUTPUT|COMMENT)\b", content, re.I):
            content = self._wrap_raw_strings(content)
        if content != string_before:
            rules.append("GC095")

        # A compact annotated INPUT followed by another statement is split safely.
        inline_input = re.fullmatch(r"INPUT\s+([A-Za-z_]\w*)\s*\([^)]*\)\s+(RETURN\s+.+)", content, re.I)
        if inline_input:
            name = inline_input.group(1)
            return [
                f'{indent}{name} <- INPUT(STRING("Enter {name}"))',
                f'{indent}{inline_input.group(2)}',
            ], rules + ["GC096"]

        # INPUT declarations can carry descriptive annotations such as matrix (N x N).
        m = re.fullmatch(r"INPUT\s+(.+)", content, re.I)
        if m and "INPUT(" not in content.upper():
            names = []
            for part in m.group(1).split(','):
                candidate = part.strip()
                candidate = re.sub(r"\s*\([^)]*\)\s*$", "", candidate).strip()
                candidate = re.sub(r"\s+\b(?:same|of|with)\b.*$", "", candidate, flags=re.I).strip()
                if re.fullmatch(r"[A-Za-z_]\w*", candidate):
                    names.append(candidate)
            if names:
                return [f'{indent}{name} <- INPUT(STRING("Enter {name}"))' for name in names], rules + ["GC096"]

        return [f"{indent}{content}"], rules

    @staticmethod
    def _render_aj_string_value(value: str) -> str | None:
        """Render one decoded quoted scalar as a frozen-AJ STRING literal.

        Only control characters explicitly representable by the v1.1 string
        escape surface are accepted here.  Returning None keeps the source
        untouched rather than silently changing an unsupported scalar.
        """
        rendered: list[str] = []
        for ch in value:
            if ch == "\\":
                rendered.append("\\\\")
            elif ch == '"':
                rendered.append('\\"')
            elif ch == "\n":
                rendered.append("\\n")
            elif ch == "\t":
                rendered.append("\\t")
            elif ord(ch) < 32 or ord(ch) == 127:
                return None
            else:
                rendered.append(ch)
        return f'STRING("{"".join(rendered)}")'

    @classmethod
    def _normalise_quoted_scalar_set_assignment(cls, content: str) -> str | None:
        """Lower an exact quoted-only brace set through the existing to_set helper."""
        match = re.fullmatch(
            r"(?P<target>[A-Za-z_]\w*)\s*(?:=|<-)\s*(?P<literal>\{.*\})",
            content,
        )
        if match is None:
            return None

        try:
            parsed = ast.parse(match.group("literal"), mode="eval")
        except (SyntaxError, ValueError):
            return None

        expression = parsed.body
        if not isinstance(expression, ast.Set) or not expression.elts:
            return None

        values: list[str] = []
        for element in expression.elts:
            if not isinstance(element, ast.Constant) or not isinstance(element.value, str):
                return None
            rendered = cls._render_aj_string_value(element.value)
            if rendered is None:
                return None
            values.append(rendered)

        return (
            f"{match.group('target')} <- CALL to_set("
            f"CALL list_value({', '.join(values)}))"
        )

    def _split_simple_entries(self, text: str):
        entries=[]
        for part in text.split(','):
            if ':' not in part:
                return None
            key, value = part.split(':', 1)
            if not key.strip() or not value.strip():
                return None
            entries.append((key.strip(), value.strip()))
        return entries

    def _wrap_raw_strings(self, text: str) -> str:
        pattern = re.compile(r'(?<![A-Za-z_])(["\'])(.*?)(?<!\\)\1')
        pieces=[]; last=0
        for m in pattern.finditer(text):
            prefix=text[max(0,m.start()-8):m.start()].upper().rstrip()
            if prefix.endswith("STRING(") or prefix.endswith("CHAR(") or text[:m.start()].rstrip().endswith("COMMENT"):
                continue
            pieces.append(text[last:m.start()])
            value=m.group(2).replace('\"','"')
            pieces.append(f'STRING("{value}")')
            last=m.end()
        if not pieces:
            return text
        pieces.append(text[last:])
        return ''.join(pieces)


class GenericCollectionNormaliser:
    """Normalises collection literals and source-evidenced operations."""

    _EVIDENCE_KINDS = ("list", "set", "dictionary", "queue", "deque", "stack", "matrix")

    @staticmethod
    def _routine_parameters(content: str) -> tuple[str, ...]:
        """Return simple formal parameter names from a generic routine header."""
        match = re.match(
            r"(?i)^\s*(?:FUNCTION|METHOD|CONSTRUCTOR)\b(?:\s+[A-Za-z_]\w*)?\s*"
            r"(?:ACCEPTS\s*)?\((?P<params>[^)]*)\)",
            content,
        )
        if match is None:
            return ()
        params: list[str] = []
        raw = match.group("params").strip()
        if not raw:
            return ()
        for part in _split_top_level_commas_shared(raw):
            token = part.strip()
            name = re.match(r"([A-Za-z_]\w*)", token)
            if name is not None:
                params.append(name.group(1))
        return tuple(params)

    @classmethod
    def _collection_kind_from_rhs(cls, rhs: str) -> str | None:
        """Classify only explicit collection constructors/literals.

        Method spelling is deliberately absent from this function: operations
        may consume evidence, but never create receiver-type evidence.
        """
        value = rhs.strip()
        patterns: tuple[tuple[str, str], ...] = (
            ("list", r"(?i)^(?:EMPTY\s+LIST|LIST\s*\[|CALL\s+list_value\s*\(|\[)"),
            ("set", r"(?i)^(?:EMPTY\s+SET|CALL\s+to_set\s*\(|SET\s*\[)"),
            ("dictionary", r"(?i)^(?:EMPTY\s+DICTIONARY|CALL\s+create_ordered_dictionary\s*\(\s*\))$"),
            ("queue", r"(?i)^(?:EMPTY\s+QUEUE|(?:CALL\s+)?Queue\s*\(\s*\))$"),
            ("deque", r"(?i)^(?:EMPTY\s+DEQUE|CALL\s+create_deque\s*\(\s*\)|(?:CALL\s+)?(?:Deque|DoubleEndedQueue)\s*\(\s*\))$"),
            ("stack", r"(?i)^(?:EMPTY\s+STACK|(?:CALL\s+)?Stack\s*\(\s*\))$"),
        )
        # The collection normaliser itself sees these pre-canonical generic
        # declaration spellings before GC027-GC032 rewrite the declaration line.
        generic_patterns: tuple[tuple[str, str], ...] = (
            ("list", r"(?i)^empty\s+list$"),
            ("set", r"(?i)^empty\s+set$"),
            ("dictionary", r"(?i)^empty\s+(?:hash\s*map|dictionary|map)$"),
            ("queue", r"(?i)^empty\s+queue$"),
            ("deque", r"(?i)^empty\s+(?:deque|doubleendedqueue|double\s*ended\s*queue)$"),
            ("stack", r"(?i)^empty\s+stack$"),
        )
        for kind, pattern in patterns + generic_patterns:
            if re.match(pattern, value):
                return kind
        return None

    @classmethod
    def _update_collection_evidence(
        cls,
        line: str,
        evidence: LexicalEvidenceContext,
    ) -> None:
        """Update lexical collection evidence from declarations/rebinds only."""
        assignment = re.match(
            r"^\s*(?P<name>[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)\s*"
            r"(?:<-|=)\s*(?P<rhs>.+?)\s*$",
            line,
        )
        if assignment is not None:
            name = assignment.group("name")
            rhs = assignment.group("rhs")
            # Any direct rebind first invalidates every collection-kind proof.
            for kind in cls._EVIDENCE_KINDS:
                evidence.invalidate(kind, name)
            kind = cls._collection_kind_from_rhs(rhs)
            if kind is not None:
                evidence.establish(kind, name)

        # Explicit type declarations are equally strong source evidence.
        for typed in re.finditer(
            r"(?i)\b(?P<name>[A-Za-z_]\w*)\s+AS\s+"
            r"(?P<kind>LIST|SET|DICTIONARY|MAP|QUEUE|DEQUE|STACK)\b",
            line,
        ):
            kind = typed.group("kind").lower()
            if kind == "map":
                kind = "dictionary"
            evidence.establish(kind, typed.group("name"))

    @staticmethod
    def _receiver_has_evidence(
        evidence: LexicalEvidenceContext,
        receiver: str,
        allowed_kinds: tuple[str, ...],
    ) -> bool:
        return any(evidence.contains(kind, receiver) for kind in allowed_kinds)

    @staticmethod
    def _balanced_list_append(
        content: str,
        evidence: LexicalEvidenceContext,
    ) -> tuple[str, str] | None:
        """Recognise a standalone evidenced ``list.append(nested_expression)``."""
        parsed = _parse_balanced_member_call(content, ("append",), dotted_receiver=False)
        if parsed is None:
            return None
        collection, _method, value = parsed
        if not GenericCollectionNormaliser._receiver_has_evidence(
            evidence, collection, ("list", "stack")
        ):
            return None
        return collection, value

    @staticmethod
    def _balanced_list_add(
        content: str,
        evidence: LexicalEvidenceContext,
    ) -> tuple[str, str] | None:
        """Recognise standalone evidenced list ``.add(nested_expression)``."""
        parsed = _parse_balanced_member_call(content, ("add",), dotted_receiver=False)
        if parsed is None:
            return None
        collection, _method, value = parsed
        if not evidence.contains("list", collection):
            return None
        return collection, value

    @staticmethod
    def _balanced_stack_push(
        content: str,
        evidence: LexicalEvidenceContext,
    ) -> tuple[str, str] | None:
        """Recognise evidenced ``stack.push(nested_expression)`` safely."""
        parsed = _parse_balanced_member_call(
            content, ("push_back", "push"), dotted_receiver=True
        )
        if parsed is None:
            return None
        collection, _method, value = parsed
        if not GenericCollectionNormaliser._receiver_has_evidence(
            evidence, collection, ("list", "stack", "deque")
        ):
            return None
        return collection, value

    @staticmethod
    def _evidenced_camelcase_deque_operation(
        content: str,
        evidence: LexicalEvidenceContext,
    ) -> tuple[str, str, str | None] | None:
        """Recognise camelCase deque aliases only on an evidenced list/deque."""
        pop = re.fullmatch(
            r"(?i)([A-Za-z_]\w*)\.(popFront|popBack)\s*\(\s*\)",
            content,
        )
        if pop is not None:
            collection = pop.group(1)
            if not GenericCollectionNormaliser._receiver_has_evidence(
                evidence, collection, ("list", "deque")
            ):
                return None
            operation = "pop_front" if pop.group(2).lower() == "popfront" else "pop_back"
            return operation, collection, None

        parsed = _parse_balanced_member_call(content, ("pushBack",), dotted_receiver=False)
        if parsed is None:
            return None
        collection, _method, value = parsed
        if not GenericCollectionNormaliser._receiver_has_evidence(
            evidence, collection, ("list", "deque")
        ):
            return None
        return "push_back", collection, value

    @classmethod
    def _replace_evidenced_simple_member_call(
        cls,
        text: str,
        evidence: LexicalEvidenceContext,
        *,
        pattern: str,
        allowed_kinds: tuple[str, ...],
        render,
    ) -> str:
        compiled = re.compile(pattern, re.IGNORECASE)

        def replacement(match: re.Match[str]) -> str:
            receiver = match.group("name")
            if not cls._receiver_has_evidence(evidence, receiver, allowed_kinds):
                return match.group(0)
            return render(match)

        return compiled.sub(replacement, text)

    def process(self, source: str) -> tuple[str, list[SourceTransformation]]:
        transformations: list[SourceTransformation] = []
        processed_lines: list[str] = []
        evidence = LexicalEvidenceContext()

        routine_stack: list[int] = []
        routine_kind_stack: list[str] = []
        class_stack: list[int] = []
        routine_start = re.compile(r"(?i)^\s*(?P<kind>FUNCTION|METHOD|CONSTRUCTOR)\b")
        routine_end = re.compile(r"(?i)^\s*END\s*(?:FUNCTION|METHOD|CONSTRUCTOR)\b|^\s*END(?:FUNCTION|METHOD|CONSTRUCTOR)\b")
        class_start = re.compile(r"(?i)^\s*CLASS\b")
        class_end = re.compile(r"(?i)^\s*END\s*CLASS\b|^\s*ENDCLASS\b")

        for line_number, source_line in enumerate(source.splitlines(keepends=True), start=1):
            stripped = source_line.strip()
            indent_width = len(source_line) - len(source_line.lstrip(" \t"))

            # Indentation-style generic routines may omit explicit END markers.
            # A sibling routine at the same/shallower indentation closes the
            # previous implicit routine frame before new evidence is inherited.
            routine_header = routine_start.match(stripped)
            if routine_header:
                while routine_stack and indent_width <= routine_stack[-1]:
                    evidence.exit()
                    routine_stack.pop()
                    routine_kind_stack.pop()
                params = self._routine_parameters(stripped)
                evidence.enter(inherit=True, shadow=params)
                routine_stack.append(indent_width)
                routine_kind_stack.append(routine_header.group("kind").upper())

            if class_start.match(stripped):
                while routine_stack:
                    evidence.exit()
                    routine_stack.pop()
                    routine_kind_stack.pop()
                while class_stack and indent_width <= class_stack[-1]:
                    evidence.exit()
                    class_stack.pop()
                evidence.enter(inherit=False)
                class_stack.append(indent_width)

            # Evidence comes only from declarations/rebinds, never from a method
            # name that happens to look collection-like.
            evidence_line = source_line.rstrip("\r\n")
            self._update_collection_evidence(evidence_line, evidence)

            # Explicit instance-member collection construction in a constructor
            # establishes class-readable field evidence for sibling methods.
            # Bare constructor locals are deliberately not promoted.
            if (
                routine_kind_stack
                and routine_kind_stack[-1] == "CONSTRUCTOR"
                and class_stack
            ):
                member_assignment = re.match(
                    r"^\s*(?P<name>(?:self|THIS)\.[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)\s*"
                    r"(?:<-|=)\s*(?P<rhs>.+?)\s*$",
                    evidence_line,
                    re.IGNORECASE,
                )
                if member_assignment is not None:
                    kind = self._collection_kind_from_rhs(member_assignment.group("rhs"))
                    if kind is not None:
                        evidence.establish_parent(kind, member_assignment.group("name"))

            transformed = source_line
            rules = (
                ("GC027", r"(?i)\bempty\s+list\b", "EMPTY LIST"),
                ("GC028", r"(?i)\bempty\s+set\b", "EMPTY SET"),
                ("GC029", r"(?i)\bempty\s+(?:hash\s*map|dictionary|map)\b", "EMPTY DICTIONARY"),
                ("GC030", r"(?i)\bordered\s+dictionary\b", "CALL create_ordered_dictionary()"),
                ("GC031", r"(?i)\bempty\s+queue\b", "EMPTY QUEUE"),
                ("GC032", r"(?i)\bempty\s+(?:deque|doubleendedqueue|double\s*ended\s*queue)\b", "EMPTY DEQUE"),
            )

            for rule_id, pattern, replacement in rules:
                before = transformed
                transformed = re.sub(pattern, replacement, transformed)
                self._record(transformations, line_number, rule_id, before, transformed)

            before = transformed
            transformed = self._replace_evidenced_simple_member_call(
                transformed,
                evidence,
                pattern=r"(?P<name>[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*)\.append\((?P<value>[^()]*)\)",
                allowed_kinds=("list", "stack", "queue", "deque"),
                render=lambda m: f"APPEND {m.group('value').strip()} TO {m.group('name')}",
            )
            self._record(transformations, line_number, "GC033", before, transformed)

            nested_append = self._balanced_list_append(transformed.strip(), evidence)
            if nested_append is not None:
                collection, value = nested_append
                line_ending = "\n" if transformed.endswith("\n") else ""
                indentation = transformed[: len(transformed) - len(transformed.lstrip())]
                before = transformed
                transformed = f"{indentation}APPEND {value} TO {collection}{line_ending}"
                self._record(transformations, line_number, "GC200", before, transformed)

            before = transformed
            transformed = self._replace_evidenced_simple_member_call(
                transformed,
                evidence,
                pattern=r"(?P<name>[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*)\.add\((?P<value>[^()]*)\)",
                allowed_kinds=("list", "set"),
                render=lambda m: f"ADD {m.group('value').strip()} TO {m.group('name')}",
            )
            self._record(transformations, line_number, "GC034", before, transformed)

            nested_add = self._balanced_list_add(transformed.strip(), evidence)
            if nested_add is not None:
                collection, value = nested_add
                line_ending = "\n" if transformed.endswith("\n") else ""
                indentation = transformed[: len(transformed) - len(transformed.lstrip())]
                before = transformed
                transformed = f"{indentation}APPEND {value} TO {collection}{line_ending}"
                self._record(transformations, line_number, "GC221", before, transformed)

            before = transformed
            transformed = self._replace_evidenced_simple_member_call(
                transformed,
                evidence,
                pattern=r"(?P<name>[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*)\.enqueue\((?P<value>[^()]*)\)",
                allowed_kinds=("queue", "list", "deque"),
                render=lambda m: f"ENQUEUE {m.group('value').strip()} TO {m.group('name')}",
            )
            self._record(transformations, line_number, "GC035", before, transformed)

            before = transformed
            transformed = self._replace_evidenced_simple_member_call(
                transformed,
                evidence,
                pattern=r"(?P<name>[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*)\.dequeue\(\)",
                allowed_kinds=("queue", "list", "deque"),
                render=lambda m: f"DEQUEUE FROM {m.group('name')}",
            )
            self._record(transformations, line_number, "GC036", before, transformed)

            before = transformed
            transformed = self._replace_evidenced_simple_member_call(
                transformed,
                evidence,
                pattern=r"(?P<name>[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*)\.(?:push_back|push)\((?P<value>[^()]*)\)",
                allowed_kinds=("stack", "list", "deque"),
                render=lambda m: f"PUSH {m.group('value').strip()} TO {m.group('name')}",
            )
            self._record(transformations, line_number, "GC037", before, transformed)

            nested_push = self._balanced_stack_push(transformed.strip(), evidence)
            if nested_push is not None:
                collection, value = nested_push
                line_ending = "\n" if transformed.endswith("\n") else ""
                indentation = transformed[: len(transformed) - len(transformed.lstrip())]
                before = transformed
                transformed = f"{indentation}PUSH {value} TO {collection}{line_ending}"
                self._record(transformations, line_number, "GC202", before, transformed)

            before = transformed
            transformed = self._replace_evidenced_simple_member_call(
                transformed,
                evidence,
                pattern=r"(?P<name>[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*)\.pop_front\(\)",
                allowed_kinds=("deque", "list", "queue"),
                render=lambda m: f"REMOVE FIRST ITEM FROM {m.group('name')}",
            )
            self._record(transformations, line_number, "GC038", before, transformed)

            before = transformed
            transformed = self._replace_evidenced_simple_member_call(
                transformed,
                evidence,
                pattern=r"(?P<name>[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*)\.pop_back\(\)",
                allowed_kinds=("deque", "list", "stack"),
                render=lambda m: f"REMOVE LAST ITEM FROM {m.group('name')}",
            )
            self._record(transformations, line_number, "GC039", before, transformed)

            camelcase_deque = self._evidenced_camelcase_deque_operation(
                transformed.strip(), evidence
            )
            if camelcase_deque is not None:
                operation, collection, value = camelcase_deque
                line_ending = "\n" if transformed.endswith("\n") else ""
                indentation = transformed[: len(transformed) - len(transformed.lstrip())]
                before = transformed
                if operation == "pop_front":
                    transformed = f"{indentation}REMOVE FIRST ITEM FROM {collection}{line_ending}"
                elif operation == "pop_back":
                    transformed = f"{indentation}REMOVE LAST ITEM FROM {collection}{line_ending}"
                else:
                    transformed = f"{indentation}APPEND {value} TO {collection}{line_ending}"
                self._record(transformations, line_number, "GC213", before, transformed)

            # GC045-GC048: collection query/access spellings consume the same
            # lexical receiver evidence as mutating collection operations.
            # A method-like name never establishes a collection type by itself.
            query_rules = (
                (
                    "GC045",
                    r"(?P<name>[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*)\.size\(\)",
                    ("list", "set", "dictionary", "queue", "deque", "stack"),
                    lambda m: f"{m.group('name')}~LENGTH",
                ),
                (
                    "GC046",
                    r"(?P<name>[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*)\.front\(\)",
                    ("list", "queue", "deque"),
                    lambda m: f"{m.group('name')}[0]",
                ),
                (
                    "GC047",
                    r"(?P<name>[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*)\.back\(\)",
                    ("list", "stack", "deque"),
                    lambda m: f"{m.group('name')}[LAST]",
                ),
                (
                    "GC048",
                    r"(?P<name>[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*)\.isEmpty\(\)",
                    ("list", "set", "dictionary", "queue", "deque", "stack"),
                    lambda m: f"LENGTH OF {m.group('name')} == 0",
                ),
            )
            for rule_id, pattern, allowed_kinds, render in query_rules:
                before = transformed
                transformed = self._replace_evidenced_simple_member_call(
                    transformed,
                    evidence,
                    pattern=pattern,
                    allowed_kinds=allowed_kinds,
                    render=render,
                )
                self._record(transformations, line_number, rule_id, before, transformed)

            processed_lines.append(transformed)

            if routine_end.match(stripped) and routine_stack:
                evidence.exit()
                routine_stack.pop()
                routine_kind_stack.pop()
            if class_end.match(stripped) and class_stack:
                while routine_stack:
                    evidence.exit()
                    routine_stack.pop()
                    routine_kind_stack.pop()
                evidence.exit()
                class_stack.pop()

        return "".join(processed_lines), transformations

    def _record(self, transformations, line_number, rule_id, before, after):
        if before == after:
            return
        transformations.append(SourceTransformation(
            line=line_number, rule=rule_id,
            source=before.rstrip("\r\n"), target=after.rstrip("\r\n")
        ))


class GenericStatementNormaliser:
    """Normalises common built-in and procedural statement forms from the corpus."""

    @staticmethod
    def _balanced_print_expression(content: str) -> str | None:
        """Return the single balanced argument of standalone ``PRINT(...)``.

        This is a representational statement-form recovery only.  It does not
        match member methods, empty calls, or Python-style multi-argument
        ``PRINT(a, b)`` forms.  Parentheses and quoted text inside the one
        expression are preserved.
        """
        match = re.match(r"(?i)^PRINT\s*\(", content)
        if not match:
            return None

        open_index = content.find("(", match.start())
        depth = 0
        quote: str | None = None
        escape = False
        close_index: int | None = None
        top_level_comma = False

        for index in range(open_index, len(content)):
            ch = content[index]
            if quote is not None:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == quote:
                    quote = None
                continue
            if ch in "'\"":
                quote = ch
                continue
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    close_index = index
                    break
                if depth < 0:
                    return None
            elif ch == "," and depth == 1:
                top_level_comma = True

        if close_index is None or content[close_index + 1 :].strip():
            return None
        expression = content[open_index + 1 : close_index].strip()
        if not expression or top_level_comma:
            return None
        return expression

    def process(self, source: str) -> tuple[str, list[SourceTransformation]]:
        transformations = []
        processed_lines = []

        for line_number, source_line in enumerate(source.splitlines(keepends=True), start=1):
            transformed = source_line

            # GC206: function-shaped PRINT is an output statement surface, not
            # a free routine call.  Recover only one balanced expression so
            # Python-style multi-argument print calls are not silently
            # reinterpreted as AJ tuples or formatting semantics.
            print_expression = self._balanced_print_expression(transformed.strip())
            if print_expression is not None:
                line_ending = "\n" if transformed.endswith("\n") else ""
                indentation = transformed[: len(transformed) - len(transformed.lstrip())]
                before = transformed
                transformed = f"{indentation}OUTPUT {print_expression}{line_ending}"
                self._record(transformations, line_number, "GC206", before, transformed)

            rules = (
                ("GC040", r"(?i)\b(?:length|len)\s*\(([^()]+)\)", r"LENGTH OF \1"),
                ("GC041", r"(?i)\b(?:lowercase|tolower|toLower)\s*\(([^()]+)\)", r"LOWERCASE(\1)"),
                ("GC042", r"(?i)\b(?:uppercase|toupper|toUpper)\s*\(([^()]+)\)", r"UPPERCASE(\1)"),
                ("GC043", r"(?i)^([ \t]*)PRINT\s+", r"\1OUTPUT "),
                ("GC044", r"(?i)^([ \t]*)DISPLAY\s+", r"\1OUTPUT "),
            )

            for rule_id, pattern, replacement in rules:
                before = transformed
                transformed = re.sub(pattern, replacement, transformed)
                self._record(transformations, line_number, rule_id, before, transformed)

            # Function-style split and join forms with simple arguments.
            before = transformed
            transformed = re.sub(
                r"(?i)\bSPLIT\(([^,()]+),\s*([^()]+)\)",
                lambda m: f"SPLIT {m.group(1).strip()} BY {m.group(2).strip()}",
                transformed,
            )
            self._record(transformations, line_number, "GC049", before, transformed)

            before = transformed
            transformed = re.sub(
                r"(?i)\bJOIN\(([^,()]+),\s*([^()]+)\)",
                lambda m: f"JOIN({m.group(1).strip()}, {m.group(2).strip()})",
                transformed,
            )
            self._record(transformations, line_number, "GC050", before, transformed)

            # Normalise simple standalone function-style SWAP(a, b) to the dialect statement form.
            # The anchors are intentional: a function declaration such as FUNCTION swap(a, b)
            # must preserve its case-sensitive identifier instead of being rewritten as SWAP.
            before = transformed
            transformed = re.sub(
                r"(?i)^([ \t]*)SWAP\(([^,()]+),\s*([^()]+)\)\s*$",
                lambda m: f"{m.group(1)}SWAP {m.group(2).strip()} AND {m.group(3).strip()}",
                transformed.rstrip("\r\n"),
            ) + ("\n" if source_line.endswith("\n") else "")
            self._record(transformations, line_number, "GC051", before, transformed)

            # Normalise simple REVERSE(x) calls used as standalone procedural shorthand.
            before = transformed
            transformed = re.sub(
                r"(?i)^([ \t]*)REVERSE\(([^()]+)\)\s*$",
                lambda m: f"{m.group(1)}REVERSE {m.group(2).strip()}",
                transformed.rstrip("\r\n"),
            ) + ("\n" if source_line.endswith("\n") else "")
            self._record(transformations, line_number, "GC052", before, transformed)

            processed_lines.append(transformed)

        return "".join(processed_lines), transformations

    def _record(self, transformations, line_number, rule_id, before, after):
        if before == after:
            return
        transformations.append(SourceTransformation(
            line=line_number, rule=rule_id,
            source=before.rstrip("\r\n"), target=after.rstrip("\r\n")
        ))


class GenericObviousMismatchNormaliser:
    """Normalises high-confidence corpus idioms with direct AJ equivalents."""

    def process(self, source: str) -> tuple[str, list[SourceTransformation]]:
        swap_temp = _fresh_generated_identifier(source, "temp_var")
        source, reserved_identifier_transformations = self._normalise_reserved_identifier_collisions(source)
        source, function_parameter_transformations = self._normalise_function_parameter_phrasing(source)
        source, universal_transformations = self._normalise_shared_universal_idioms(source, swap_temp)
        source, structural_transformations = self._normalise_shared_structural_idioms(source)
        source, declaration_transformations = self._normalise_shared_declarations(source)
        source, fixed_array_preallocation_transformations = (
            self._normalise_unspecified_fixed_array_preallocation(source)
        )
        source, contextual_class_routine_transformations = (
            self._normalise_contextual_class_routines(source)
        )
        source, stack_constructor_state_transformations = (
            self._normalise_evidenced_stack_constructor_state(source)
        )
        source, numeric_string_conversion_transformations = (
            self._normalise_evidenced_numeric_string_conversion(source)
        )
        source, evidenced_deque_transformations = (
            self._normalise_evidenced_deque_surface_operations(source)
        )
        source, collection_transformations = self._normalise_shared_collection_idioms(source)
        source, set_tuple_insertion_transformations = (
            self._normalise_evidenced_set_tuple_insertions(source)
        )
        source, object_transformations = self._normalise_shared_object_idioms(source)
        source, queue_transformations = self._normalise_anonymous_queue(source)
        source, explicit_grid_transformations = self._normalise_explicit_square_grid_allocation(source)
        source, rectangular_matrix_fill_transformations = (
            self._normalise_explicit_rectangular_matrix_fill(source)
        )
        source, evidenced_2d_copy_transformations = self._normalise_evidenced_2d_copy_intrinsic(source)
        source, stack_transformations = self._normalise_array_stack(source)
        source, frequency_transformations = self._normalise_character_frequency(source)
        source, linked_cycle_transformations = self._normalise_linked_cycle_detection(source)
        source, pair_sum_transformations = self._normalise_pair_sum_nested_loops(source)
        source, two_stack_queue_transformations = self._normalise_two_stack_queue(source)
        source, n_queens_transformations = self._normalise_n_queens(source)
        source, matrix_multiplication_transformations = self._normalise_matrix_multiplication(source)
        source, sliding_window_transformations = self._normalise_sliding_window_deque(source)
        source, lru_cache_transformations = self._normalise_lru_cache(source)
        source, stack_function_transformations = self._normalise_stack_function(source)
        source, queue_function_transformations = self._normalise_queue_function(source)
        source, inventory_update_transformations = self._normalise_inventory_update(source)
        source, lru_class_transformations = self._normalise_lru_class(source)
        source, case_transformations = self._normalise_case_blocks(source)
        source, process_stop_transformations = self._normalise_process_stop(source)
        transformations: list[SourceTransformation] = (
            list(reserved_identifier_transformations)
            + list(function_parameter_transformations)
            + list(universal_transformations)
            + list(structural_transformations)
            + list(declaration_transformations)
            + list(fixed_array_preallocation_transformations)
            + list(contextual_class_routine_transformations)
            + list(stack_constructor_state_transformations)
            + list(numeric_string_conversion_transformations)
            + list(evidenced_deque_transformations)
            + list(collection_transformations)
            + list(set_tuple_insertion_transformations)
            + list(object_transformations)
            + list(queue_transformations)
            + list(explicit_grid_transformations)
            + list(rectangular_matrix_fill_transformations)
            + list(evidenced_2d_copy_transformations)
            + list(stack_transformations)
            + list(frequency_transformations)
            + list(linked_cycle_transformations)
            + list(pair_sum_transformations)
            + list(two_stack_queue_transformations)
            + list(n_queens_transformations)
            + list(matrix_multiplication_transformations)
            + list(sliding_window_transformations)
            + list(lru_cache_transformations)
            + list(stack_function_transformations)
            + list(queue_function_transformations)
            + list(inventory_update_transformations)
            + list(lru_class_transformations)
            + list(case_transformations)
            + list(process_stop_transformations)
        )
        output: list[str] = []
        for line_number, source_line in enumerate(source.splitlines(), start=1):
            lines, rules = self._normalise_line(source_line, swap_temp)
            if lines != [source_line]:
                target = "\n".join(lines)
                for rule in rules:
                    transformations.append(SourceTransformation(line_number, rule, source_line, target))
            output.extend(lines)
        return "\n".join(output), transformations

    def _normalise_process_stop(self, source: str) -> tuple[str, list[SourceTransformation]]:
        """Canonicalise STOP to RETURN inside an existing generated wrapper.

        AJ v1.0 has a value-less RETURN statement but no STOP statement.  When
        compatibility normalisation has already established a complete algorithm
        wrapper (legacy ``PROCESS`` or neutral ``unnamed_function``), STOP means
        leaving that generated algorithm wrapper immediately.
        """
        lines = source.splitlines()
        output: list[str] = []
        transformations: list[SourceTransformation] = []
        in_process = False
        function_depth = 0

        for line_number, line in enumerate(lines, start=1):
            stripped = line.strip()
            if re.match(r"(?i)^FUNCTION\s+(?:PROCESS|unnamed_function)\s+ACCEPTS\s*\(", stripped):
                in_process = True
                function_depth = 1
                output.append(line)
                continue

            if in_process and re.match(r"(?i)^FUNCTION\b", stripped):
                function_depth += 1

            if in_process and function_depth == 1 and re.fullmatch(r"(?i)STOP", stripped):
                indent = line[: len(line) - len(line.lstrip())]
                replacement = f"{indent}RETURN"
                transformations.append(SourceTransformation(
                    line=line_number, rule="GC132", source=line, target=replacement
                ))
                output.append(replacement)
            else:
                output.append(line)

            if in_process and re.match(r"(?i)^ENDFUNCTION\b", stripped):
                function_depth -= 1
                if function_depth == 0:
                    in_process = False

        return "\n".join(output), transformations

    def _normalise_shared_universal_idioms(
        self,
        source: str,
        swap_temp: str | None = None,
    ) -> tuple[str, list[SourceTransformation]]:
        """Apply vocabulary/syntax equivalences that do not depend on an algorithm."""
        transformed = source




        # MATRIX_OPERATION / TRANSPOSE_IN_PLACE
        transformed = re.sub(
            r"(?im)^(?P<indent>[ \t]*)TRANSPOSE\s+(?P<name>[A-Za-z_]\w*)\s*$",
            lambda x: (
                f"{x.group('indent')}CALL transpose_in_place({x.group('name')})"
            ),
            transformed,
        )
        # COLLECTION_OPERATION / SWAP_TARGETS:
        # Expand the supplied SWAP primitive into its concrete three-assignment
        # semantics. ``temp_var`` is only the preferred generated spelling: if
        # it is already present in the algorithm, choose a deterministic fresh
        # suffix so compiler state cannot capture or overwrite source state.
        if swap_temp is None:
            swap_temp = _fresh_generated_identifier(transformed, "temp_var")
        transformed = re.sub(
            r"(?im)^(?P<indent>[ \t]*)SWAP\s+(?P<left>[A-Za-z_]\w*(?:\[[^\]\n]+\]|\.[A-Za-z_]\w*)*)\s*,\s*(?P<right>[A-Za-z_]\w*(?:\[[^\]\n]+\]|\.[A-Za-z_]\w*)*)\s*$",
            lambda x: (
                f"{x.group('indent')}{swap_temp} <- {x.group('left')}\n"
                f"{x.group('indent')}{x.group('left')} <- {x.group('right')}\n"
                f"{x.group('indent')}{x.group('right')} <- {swap_temp}"
            ),
            transformed,
        )
        # Contextual spaced block terminators. These phrases are only rewritten
        # when they correspond to a block that is actually open at that point.
        lines = transformed.splitlines()
        open_blocks: list[tuple[str, int]] = []
        repaired_lines: list[str] = []

        opener_patterns = (
            ("CLASS", re.compile(r"(?i)^\s*CLASS\b")),
            ("FUNCTION", re.compile(r"(?i)^\s*FUNCTION\b")),
            ("IF", re.compile(r"(?i)^\s*IF\b.*\bTHEN\s*$")),
            ("WHILE", re.compile(r"(?i)^\s*WHILE\b.*\bDO\s*$")),
            ("FOR", re.compile(r"(?i)^\s*FOR\b.*\bDO\s*$")),
        )
        compact_end = {
            "CLASS": "ENDCLASS",
            "FUNCTION": "ENDFUNCTION",
            "IF": "ENDIF",
            "WHILE": "ENDWHILE",
            "FOR": "ENDFOR",
        }

        for line in lines:
            stripped = line.strip()
            indent = len(line) - len(line.lstrip())

            spaced_end = re.fullmatch(
                r"(?i)END\s+(CLASS|FUNCTION|IF|WHILE|FOR)",
                stripped,
            )
            if spaced_end:
                block = spaced_end.group(1).upper()
                if open_blocks and open_blocks[-1][0] == block:
                    line = (" " * indent) + compact_end[block]
                    open_blocks.pop()
                    repaired_lines.append(line)
                    continue

            compact_match = re.fullmatch(
                r"(?i)(ENDCLASS|ENDFUNCTION|ENDIF|ENDWHILE|ENDFOR)",
                stripped,
            )
            if compact_match:
                reverse = {
                    "ENDCLASS": "CLASS",
                    "ENDFUNCTION": "FUNCTION",
                    "ENDIF": "IF",
                    "ENDWHILE": "WHILE",
                    "ENDFOR": "FOR",
                }
                block = reverse[compact_match.group(1).upper()]
                if open_blocks and open_blocks[-1][0] == block:
                    open_blocks.pop()
                repaired_lines.append(line)
                continue

            for block, pattern in opener_patterns:
                if pattern.match(line):
                    open_blocks.append((block, indent))
                    break

            repaired_lines.append(line)

        transformed = "\n".join(repaired_lines)

        # In class context, an explicit zero-argument Constructor() marker is
        # redundant: CLASS already implies construction. Preserve the following
        # state assignments as class initialisation.
        transformed = re.sub(
            r"(?im)^(?P<indent>[ \t]*)CLASS\s+(?P<name>[A-Za-z_]\w*)\s*$",
            lambda x: f"{x.group('indent')}CLASS {x.group('name')} ACCEPTS()",
            transformed,
        )
        transformed = re.sub(
            r"(?im)^(?P<indent>[ \t]*)CALL\s+Constructor\(\)\s*$",
            "",
            transformed,
        )
        transformed = re.sub(
            r"(?is)(\bENDFUNCTION\b)\s*Example\s*:.*$",
            r"\1",
            transformed,
        )
        transformed = re.sub(
            r"(?is)(\bENDCLASS\b)\s*Example\s*:.*$",
            r"\1",
            transformed,
        )

        midpoint_candidates = re.findall(
            r"(?im)^\s*(?P<name>[A-Za-z_]\w*)\s*<-\s*\((?P<a>[A-Za-z_]\w*)\s*\+\s*(?P<b>[A-Za-z_]\w*)\)\s*/\s*2\s*$",
            transformed,
        )
        for name, a, b in midpoint_candidates:
            if re.search(rf"\[[ \t]*{re.escape(name)}[ \t]*\]", transformed):
                transformed = re.sub(
                    rf"(?im)^(?P<indent>[ \t]*){re.escape(name)}\s*<-\s*\({re.escape(a)}\s*\+\s*{re.escape(b)}\)\s*/\s*2\s*$",
                    lambda x, n=name, aa=a, bb=b: (
                        f"{x.group('indent')}{n} <- ({aa} + {bb}) INTEGER DIVISION 2"
                    ),
                    transformed,
                )

        # Bare empty braces are deliberately *not* defaulted to a dictionary.
        # v3.52 resolves them earlier only when same-scope usage proves set or
        # dictionary semantics (GC220/GC250).  Leaving an unresolved ``{}``
        # visible is preferable to inventing a collection type.

        transformed = re.sub(
            r"(?is)(\bENDFUNCTION\b)\s*`{2,}.*$",
            r"\1",
            transformed,
        )
        transformed = re.sub(
            r"(?is)(\bENDCLASS\b)\s*`{2,}.*$",
            r"\1",
            transformed,
        )

        transformed = re.sub(
            r"(?i)\b([A-Za-z_]\w*)\s+IS\s+A\s+NUMBER\b",
            lambda x: f"CALL is_number({x.group(1)})",
            transformed,
        )

        transformed = re.sub(
            r"(?im)^(?P<indent>[ \t]*)(?P<target>[A-Za-z_]\w*)\s*<-\s*LIST\s*\[(?P<values>[^\n]*)\]\s*$",
            lambda x: (
                f"{x.group('indent')}{x.group('target')} <- "
                f"CALL list_value({x.group('values').strip()})"
            ),
            transformed,
        )

        transformed = re.sub(
            r"(?i)(?<!CALL\s)\bSPLIT\(([^()\n]+(?:\([^()\n]*\)[^()\n]*)*)\)",
            lambda x: f"CALL SPLIT({x.group(1).strip()})",
            transformed,
        )

        transformed = re.sub(
            r"(?i)(?:CALL\s+)?NUMBER_OF_CHARACTERS\(([^()]+)\)",
            lambda x: f"LENGTH OF {x.group(1).strip()}",
            transformed,
        )

        transformed = re.sub(r"(?i)\bCALL\s+AND\b", "AND", transformed)
        transformed = re.sub(r"(?i)\bCALL\s+OR\b", "OR", transformed)

        # Function-shaped arithmetic emitted by some generators maps back to
        # canonical AJ operators.
        transformed = re.sub(
            r"(?i)(?<![A-Za-z0-9_.])(?:CALL\s+)?(?:MODULUS|MOD)\(\s*([^,()]+)\s*,\s*([^,()]+)\s*\)",
            lambda x: f"({x.group(1).strip()} MODULUS {x.group(2).strip()})",
            transformed,
        )
        transformed = re.sub(
            r"(?i)(?<![A-Za-z0-9_.])(?:CALL\s+)?FLOOR\(\s*([^()]+?)\s*/\s*([^()]+?)\s*\)",
            lambda x: f"({x.group(1).strip()} INTEGER DIVISION {x.group(2).strip()})",
            transformed,
        )

        # Preserve an explicitly authored NULL sentinel textually.  Natural
        # ``IS [NOT] NULL`` relations are structural surface syntax only, so
        # normalise the relation while keeping NULL itself unchanged.  This
        # keeps source intent visible in canonical AJ.  Native AJ ``NONE``
        # remains distinct and is handled by the v1.1/v1.2 literal pass.
        transformed = re.sub(
            r"(?i)\b([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)\s+IS\s+NULL\b",
            r"\1 == NULL",
            transformed,
        )
        transformed = re.sub(
            r"(?i)\b([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)\s+IS\s+NOT\s+NULL\b",
            r"\1 != NULL",
            transformed,
        )

        # ASCII(x) is a representational overstatement of the existing CHAR(x)
        # conversion used by the AJ/Python compatibility layer.  Accept both
        # raw Python-like syntax and an already-prefixed generic CALL form so
        # this recovery is independent of pipeline ordering and source shape.
        transformed = re.sub(
            r"(?i)(?:CALL\s+)?ASCII\(([^()]+)\)",
            lambda m: f"CHAR({m.group(1).strip()})",
            transformed,
        )

        transformed = re.sub(
            r"(?i)\b([A-Za-z_]\w*)\s+IS\s+NOT\s+empty\b",
            r"LENGTH OF \1 > 0",
            transformed,
        )
        transformed = re.sub(
            r"(?i)\b([A-Za-z_]\w*)\s+IS\s+empty\b",
            r"LENGTH OF \1 == 0",
            transformed,
        )

        if transformed == source:
            return source, []
        return transformed, [
            SourceTransformation(line=1, rule="GC157", source=source, target=transformed)
        ]


    @classmethod
    def _split_statement_values(cls, text: str) -> list[str]:
        """Delegate RETURN/OUTPUT tuple-surface splitting to shared machinery."""
        return _split_statement_values_shared(text)

    @staticmethod
    def _unwrap_single_outer_parentheses(text: str) -> str | None:
        return _unwrap_single_outer_parentheses_shared(text)

    @staticmethod
    def _split_top_level_commas(text: str) -> list[str]:
        return _split_top_level_commas_shared(text)


    def _normalise_reserved_identifier_collisions(
        self,
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        transformed = source
        transformations: list[SourceTransformation] = []

        reserved = {
            "LENGTH", "RETURN", "CLASS", "FUNCTION", "IF", "ELSE", "WHILE",
            "FOR", "AND", "OR", "NOT", "IN", "CALL", "OUTPUT", "BREAK",
            "STOP", "QUIT", "CONTINUE", "BOOLEAN", "STRING", "CHAR", "INTEGER", "FLOAT",
            "MODULUS",
        }

        pattern = re.compile(
            r"(?im)^(?P<indent>[ \t]*)FUNCTION\s+(?P<name>[A-Za-z_]\w*)\s*\((?P<params>[^)]*)\)\s*$"
        )

        def repl(match: re.Match) -> str:
            name = match.group("name")
            params = match.group("params").strip()
            canonical = name
            if name.upper() in reserved:
                canonical = f"__reserved_keyword__{name}"
            target = (
                f"{match.group('indent')}FUNCTION {canonical} ACCEPTS({params})"
            )
            transformations.append(
                SourceTransformation(
                    line=1,
                    rule="GC166",
                    source=match.group(0),
                    target=target,
                )
            )
            return target

        transformed = pattern.sub(repl, transformed)

        mangled_length = re.compile(
            r"(?im)^(?P<indent>[ \t]*)FUNCTION\s+LENGTH\s+OF\s+(?P<param>[A-Za-z_]\w*)\s*$"
        )

        def repl_mangled_length(match: re.Match) -> str:
            target = (
                f"{match.group('indent')}FUNCTION "
                f"__reserved_keyword__LENGTH ACCEPTS({match.group('param')})"
            )
            transformations.append(
                SourceTransformation(
                    line=1,
                    rule="GC166",
                    source=match.group(0),
                    target=target,
                )
            )
            return target

        transformed = mangled_length.sub(repl_mangled_length, transformed)
        return transformed, transformations


    def _normalise_function_parameter_phrasing(
        self,
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        transformed = source
        transformations: list[SourceTransformation] = []

        pattern = re.compile(
            r"(?im)^(?P<indent>[ \t]*)FUNCTION\s+(?P<name>[A-Za-z_]\w*)\s+"
            r"(?P<p1>[A-Za-z_]\w*)\s+AND\s+(?P<p2>[A-Za-z_]\w*)\s*$"
        )

        def repl(match: re.Match) -> str:
            target = (
                f"{match.group('indent')}FUNCTION {match.group('name')} "
                f"ACCEPTS({match.group('p1')}, {match.group('p2')})"
            )
            transformations.append(
                SourceTransformation(
                    line=1,
                    rule="GC168",
                    source=match.group(0),
                    target=target,
                )
            )
            return target

        transformed = pattern.sub(repl, transformed)
        return transformed, transformations


    def _normalise_shared_structural_idioms(
        self,
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        """Repair high-confidence malformed block structure without changing logic."""
        lines = source.splitlines()

        # CONDITIONAL / CASE_TO_IF_CHAIN:
        # CASE selector OF followed by "value: statement" branches maps to
        # an equivalent mutually-exclusive IF / ELSE IF chain.
        case_source = "\n".join(lines)
        case_pattern = re.compile(
            r"(?ims)^(?P<indent>[ \t]*)CASE\s+(?P<selector>.+?)\s+OF\s*$"
            r"(?P<body>.*?)"
            r"^(?P=indent)ENDCASE\s*$"
        )

        def case_repl(match: re.Match) -> str:
            indent = match.group("indent")
            selector = match.group("selector").strip()
            branch_lines = []
            for raw in match.group("body").splitlines():
                stripped = raw.strip()
                if not stripped:
                    continue
                branch = re.fullmatch(r"(.+?):\s*(.+)", stripped)
                if not branch:
                    return match.group(0)
                branch_lines.append((branch.group(1).strip(), branch.group(2).strip()))

            if not branch_lines:
                return match.group(0)

            out = []
            for index, (value, statement) in enumerate(branch_lines):
                keyword = "IF" if index == 0 else "ELSE IF"
                out.append(f"{indent}{keyword} {selector} == {value} THEN")
                out.append(f"{indent}    {statement}")
            out.append(f"{indent}ENDIF")
            return "\n".join(out)

        case_source = case_pattern.sub(case_repl, case_source)
        lines = case_source.splitlines()
        changed = False
        i = 0

        while i < len(lines):
            if lines[i].strip().upper() != "ELSE":
                i += 1
                continue

            else_indent = len(lines[i]) - len(lines[i].lstrip())

            # Look backwards over comments/blanks.  A same-indent ENDIF directly
            # before ELSE is a high-confidence premature close of this IF branch.
            j = i - 1
            while j >= 0 and (
                not lines[j].strip()
                or lines[j].lstrip().upper().startswith("COMMENT")
            ):
                j -= 1

            if (
                j < 0
                or lines[j].strip().upper() != "ENDIF"
                or (len(lines[j]) - len(lines[j].lstrip())) != else_indent
            ):
                i += 1
                continue

            # Confirm that this ENDIF corresponds to a same-indent IF and that
            # there is at least one nested block between them.  This avoids
            # touching ordinary IF/ENDIF followed by unrelated ELSE text.
            opener = j - 1
            found_same_indent_if = False
            found_nested_block = False
            while opener >= 0:
                text = lines[opener].strip().upper()
                indent = len(lines[opener]) - len(lines[opener].lstrip())
                if indent < else_indent:
                    break
                if indent > else_indent and text.startswith(("IF ", "WHILE ", "FOR ")):
                    found_nested_block = True
                if indent == else_indent and text.startswith("IF ") and text.endswith(" THEN"):
                    found_same_indent_if = True
                    break
                opener -= 1

            if not (found_same_indent_if and found_nested_block):
                i += 1
                continue

            # Remove the premature ENDIF, preserving intervening comments.
            lines.pop(j)
            if j < i:
                i -= 1

            # The ELSE branch remains open. Close it immediately before the
            # enclosing construct's next lower-indentation line.
            insert_at = i + 1
            while insert_at < len(lines):
                text = lines[insert_at].strip()
                if not text:
                    insert_at += 1
                    continue
                indent = len(lines[insert_at]) - len(lines[insert_at].lstrip())
                if indent < else_indent:
                    break
                insert_at += 1

            lines.insert(insert_at, " " * else_indent + "ENDIF")
            changed = True
            i = insert_at + 1

        transformed = "\n".join(lines)
        if not changed:
            return source, []

        return transformed, [
            SourceTransformation(
                line=1,
                rule="GC162",
                source=source,
                target=transformed,
            )
        ]


    def _normalise_evidenced_numeric_string_conversion(
        self,
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        """Represent an explicit numeric STRING(variable) conversion safely.

        Frozen AJ uses STRING("...") for literals, so compatibility normalisation
        must not reinterpret STRING(expression) globally as a cast.  This rule is
        deliberately contextual: the destination must already be string-backed,
        the converted identifier must already be numeric by a MOD/MODULUS
        assignment, and the exact expression must prepend that explicit
        STRING(identifier) to the same string accumulator.
        """
        string_names = set(re.findall(
            r"(?im)^\s*([A-Za-z_]\w*)\s*<-\s*EMPTY STRING\s*$",
            source,
        ))
        modulus_vars = set(re.findall(
            r"(?im)^\s*([A-Za-z_]\w*)\s*<-\s*[^\n]+?\s+(?:MODULUS|MOD)\s+[^\n]+$",
            source,
        ))

        if not string_names:
            return source, []

        transformed = source
        transformations: list[SourceTransformation] = []

        # GC230 / DIRECT_MODULUS_DIGIT_TO_STRING_ACCUMULATOR — RETIRED.
        #
        # A source-authored expression such as ``(n MOD 2) + text`` is an
        # explicit mixed numeric/string addition.  Even when ``text`` is
        # independently known to be string-backed, inserting ``to_string``
        # would repair a source semantic/type error rather than normalise its
        # representation.  Preserve the arithmetic exactly and allow the
        # executable-correctness audit to classify the resulting Python
        # TypeError as an expected source failure.  Explicit STRING(variable)
        # conversions remain handled below by GC225.

        if not modulus_vars:
            return transformed, transformations

        for string_name in sorted(string_names, key=len, reverse=True):
            string_escaped = re.escape(string_name)
            for numeric_name in sorted(modulus_vars, key=len, reverse=True):
                numeric_escaped = re.escape(numeric_name)
                pattern = re.compile(
                    rf"(?im)^(?P<indent>[ \t]*){string_escaped}\s*<-\s*"
                    rf"STRING\(\s*{numeric_escaped}\s*\)\s*\+\s*{string_escaped}\s*$"
                )

                def replacement(match, sname=string_name, nname=numeric_name):
                    return (
                        f"{match.group('indent')}{sname} <- "
                        f"CALL to_string({nname}) + {sname}"
                    )

                before = transformed
                transformed = pattern.sub(replacement, transformed)
                if transformed != before:
                    transformations.append(SourceTransformation(
                        line=1,
                        rule="GC225",
                        source=before,
                        target=transformed,
                    ))

        if transformed == source:
            return source, []
        return transformed, transformations


    @staticmethod
    def _normalise_evidenced_deque_surface_operations(
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        """Preserve explicit deque surface operations using local deque evidence.

        GC237 requires a receiver to be explicitly initialised as ``EMPTY DEQUE``
        in the same lexical routine before any front/back operation is rewritten.
        A later direct reassignment invalidates that evidence.  The recovered
        operations remain explicit deque intrinsics; Python representation
        lowering is a compiler concern. No deque semantics are inferred for
        arbitrary list-backed or queue-like receivers.
        """
        scope_start = re.compile(r"(?i)^\s*(?:FUNCTION|METHOD|CONSTRUCTOR)\b")
        scope_end = re.compile(r"(?i)^\s*(?:ENDFUNCTION|ENDMETHOD|ENDCONSTRUCTOR)\b")
        direct_assignment = re.compile(
            r"^\s*(?P<name>[A-Za-z_]\w*)\s*<-\s*(?P<rhs>.+?)\s*$"
        )
        deque_backing = re.compile(r"(?i)^EMPTY\s+DEQUE$")

        evidence = LexicalEvidenceContext()
        transformations: list[SourceTransformation] = []
        output_lines: list[str] = []

        for line_number, original in enumerate(source.splitlines(), start=1):
            stripped = original.strip()
            if scope_start.match(stripped):
                evidence.enter(inherit=False)

            assignment = direct_assignment.match(original)
            if assignment is not None:
                name = assignment.group("name")
                rhs = assignment.group("rhs").strip()
                if deque_backing.fullmatch(rhs):
                    evidence.establish("deque", name)
                else:
                    evidence.invalidate("deque", name)

            updated = original
            for name in sorted(evidence.names("deque"), key=len, reverse=True):
                escaped = re.escape(name)

                match = re.fullmatch(
                    rf"(?i)(?P<indent>[ \t]*)REMOVE\s+FRONT\s+FROM\s+{escaped}\s*",
                    updated,
                )
                if match is not None:
                    updated = f"{match.group('indent')}CALL deque_pop_front({name})"
                    break

                match = re.fullmatch(
                    rf"(?i)(?P<indent>[ \t]*)REMOVE\s+BACK\s+FROM\s+{escaped}\s*",
                    updated,
                )
                if match is not None:
                    updated = f"{match.group('indent')}CALL deque_pop_back({name})"
                    break

                match = re.fullmatch(
                    rf"(?i)(?P<indent>[ \t]*)(?:ADD|APPEND)\s+BACK\s+(?P<value>.+?)\s+TO\s+{escaped}\s*",
                    updated,
                )
                if match is not None:
                    updated = (
                        f"{match.group('indent')}CALL deque_push_back("
                        f"{name}, {match.group('value').strip()})"
                    )
                    break

            if updated != original:
                transformations.append(SourceTransformation(
                    line=line_number,
                    rule="GC237",
                    source=original,
                    target=updated,
                ))
            output_lines.append(updated)

            if scope_end.match(stripped):
                evidence.exit()

        if not transformations:
            return source, []

        transformed = "\n".join(output_lines)
        if source.endswith("\n"):
            transformed += "\n"
        return transformed, transformations


    def _normalise_evidenced_stack_constructor_state(
        self,
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        """Preserve evidenced ``Stack()`` class state as an abstract stack.

        GC244 is deliberately contextual. It applies only inside an explicit
        canonical CLASS whose CONSTRUCTOR directly assigns a member from the
        exact zero-argument free constructor ``Stack()`` (with or without an
        already-added ``CALL`` prefix). The member must also be used as a stack
        in the same class through at least one already exposed stack operation.

        An evidenced constructor value becomes ``CALL create_stack()`` rather
        than ``EMPTY LIST``. PUSH/pop/empty-query surfaces for that same member
        are canonicalised through ``PUSH``, ``POP`` and ``stack_is_empty``
        intrinsics. The Python compiler may lower those intrinsics to a list
        backing, but canonical AJ therefore preserves the source STACK
        abstraction instead of leaking the implementation representation.

        A later direct rebind of the member refuses recovery. Local Stack()
        calls, member-named Stack methods, non-zero-argument calls and unrelated
        objects remain untouched.
        """
        lines = source.splitlines()
        if not any(re.fullmatch(r"(?i)\s*CLASS\s+[A-Za-z_]\w*\s*", line) for line in lines):
            return source, []

        constructor_start: int | None = None
        constructor_end: int | None = None
        for index, line in enumerate(lines):
            stripped = line.strip()
            if re.fullmatch(r"(?i)CONSTRUCTOR\s+ACCEPTS\s*\([^)]*\)\s*", stripped):
                if constructor_start is not None:
                    return source, []
                constructor_start = index
                continue
            if constructor_start is not None and constructor_end is None:
                if re.fullmatch(r"(?i)ENDCONSTRUCTOR\s*", stripped):
                    constructor_end = index
                    break

        if constructor_start is None or constructor_end is None:
            return source, []

        init_pattern = re.compile(
            r"(?i)^(?P<indent>[ \t]*)(?P<receiver>self|THIS)\."
            r"(?P<name>[A-Za-z_]\w*)\s*<-\s*(?:CALL\s+)?Stack\s*\(\s*\)\s*$"
        )
        candidates: dict[str, tuple[int, str, str]] = {}
        for index in range(constructor_start + 1, constructor_end):
            match = init_pattern.fullmatch(lines[index])
            if match is None:
                continue
            key = match.group("name").lower()
            if key in candidates:
                return source, []
            candidates[key] = (index, match.group("receiver"), match.group("name"))

        if not candidates:
            return source, []

        eligible: dict[str, tuple[int, str, str]] = {}
        for key, candidate in candidates.items():
            init_index, _receiver, name = candidate
            path_pattern = rf"(?:self|THIS)\.{re.escape(name)}"
            rebind = re.compile(rf"(?i)^\s*{path_pattern}\s*<-\s*.+$")
            if any(
                rebind.fullmatch(lines[index])
                for index in range(init_index + 1, len(lines))
            ):
                continue

            usage_patterns = (
                re.compile(rf"(?i)^\s*PUSH\s+.+?\s+(?:TO|ONTO)\s+{path_pattern}\s*$"),
                re.compile(rf"(?i)^\s*{path_pattern}\.push\s*\("),
                re.compile(rf"(?i).*{path_pattern}\.pop\s*\(\s*\)"),
                re.compile(rf"(?i).*\bLENGTH\s+OF\s+{path_pattern}\b"),
                re.compile(rf"(?i).*\b(?:NOT\s+)?CALL\s+stack_is_empty\s*\(\s*{path_pattern}\s*\)"),
            )
            if any(
                pattern.search(line)
                for pattern in usage_patterns
                for line in lines[constructor_end + 1 :]
            ):
                eligible[key] = candidate

        if not eligible:
            return source, []

        output = list(lines)
        transformations: list[SourceTransformation] = []
        for _key, (index, receiver, name) in eligible.items():
            original = output[index]
            match = init_pattern.fullmatch(original)
            assert match is not None
            updated = f"{match.group('indent')}{receiver}.{name} <- CALL create_stack()"
            output[index] = updated
            transformations.append(SourceTransformation(
                line=index + 1, rule="GC244", source=original, target=updated
            ))

        for index, original in enumerate(output):
            updated = original
            if not updated.strip() or re.match(r"(?i)^\s*(?:COMMENT\b|#|//)", updated):
                continue

            for _key, (_init_index, _receiver, name) in eligible.items():
                path = rf"(?:self|THIS)\.{re.escape(name)}"

                # Exact statement-form pushes become the abstract PUSH call.
                push_statement = re.fullmatch(
                    rf"(?i)(?P<indent>[ \t]*)PUSH\s+(?P<value>.+?)\s+(?:TO|ONTO)\s+"
                    rf"(?P<path>{path})\s*",
                    updated,
                )
                if push_statement is not None:
                    updated = (
                        f"{push_statement.group('indent')}CALL PUSH("
                        f"{push_statement.group('value').strip()}, "
                        f"{push_statement.group('path')})"
                    )
                else:
                    # A balanced member push statement can still be present on
                    # paths not converted by the earlier generic collection pass.
                    member_prefix = re.match(
                        rf"(?i)^(?P<indent>[ \t]*)(?P<path>{path})\.push\s*\(",
                        updated,
                    )
                    if member_prefix is not None:
                        open_index = updated.find("(", member_prefix.start())
                        close_index = _find_matching_delimiter(updated, open_index, "(", ")")
                        if close_index is not None and not updated[close_index + 1 :].strip():
                            value = updated[open_index + 1 : close_index].strip()
                            if value:
                                updated = (
                                    f"{member_prefix.group('indent')}CALL PUSH("
                                    f"{value}, {member_prefix.group('path')})"
                                )

                # Preserve empty-stack semantics after earlier query
                # normalisation has exposed a LENGTH predicate.
                updated = re.sub(
                    rf"(?i)\bNOT\s+LENGTH\s+OF\s+(?P<path>{path})\s*==\s*0\b",
                    lambda m: f"NOT CALL stack_is_empty({m.group('path')})",
                    updated,
                )
                updated = re.sub(
                    rf"(?i)\bLENGTH\s+OF\s+(?P<path>{path})\s*==\s*0\b",
                    lambda m: f"CALL stack_is_empty({m.group('path')})",
                    updated,
                )
                updated = re.sub(
                    rf"(?i)\bLENGTH\s+OF\s+(?P<path>{path})\s*>\s*0\b",
                    lambda m: f"NOT CALL stack_is_empty({m.group('path')})",
                    updated,
                )

                # Preserve POP in expression context, including a nested pop
                # used as the value supplied to another PUSH operation.
                updated = re.sub(
                    rf"(?i)\b(?P<path>{path})\.pop\s*\(\s*\)",
                    lambda m: f"CALL POP({m.group('path')})",
                    updated,
                )

            if updated != original:
                output[index] = updated
                transformations.append(SourceTransformation(
                    line=index + 1, rule="GC244", source=original, target=updated
                ))

        transformed = "\n".join(output)
        if source.endswith("\n"):
            transformed += "\n"
        return transformed, transformations


    def _normalise_evidenced_set_tuple_insertions(
        self,
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        """Canonicalise an explicit two-value tuple inserted into an evidenced set.

        GC248 completes the ordering path where GC158 has already converted
        ``ADD (a, b) TO set_name`` into ``CALL add_to_set(set_name, (a, b))``.
        AJ v1.1 requires tuple values to use ``TUPLE(...)`` explicitly.  The
        receiver must be independently evidenced by an ``EMPTY SET``
        declaration in the same processed source, and the payload must be one
        outer parenthesis pair containing exactly two top-level values.
        Grouped single expressions and unproven receivers remain untouched.
        """
        evidence = LexicalEvidenceContext()
        for name in re.findall(
            r"(?im)^\s*([A-Za-z_]\w*)\s*<-\s*EMPTY\s+SET\s*$",
            source,
        ):
            evidence.establish("set", name)
        set_names = evidence.names("set")
        if not set_names:
            return source, []

        transformed_lines: list[str] = []
        changed = False
        for line in source.splitlines(keepends=True):
            ending = "\n" if line.endswith("\n") else ""
            content = line[:-1] if ending else line
            replaced = content
            for name in sorted(set_names, key=len, reverse=True):
                match = re.fullmatch(
                    rf"(?P<indent>[ \t]*)CALL\s+add_to_set\(\s*{re.escape(name)}\s*,\s*(?P<value>.+)\)\s*",
                    content,
                    re.I,
                )
                if not match:
                    continue
                value = match.group("value").strip()
                inner = self._unwrap_single_outer_parentheses(value)
                if inner is None:
                    continue
                values = self._split_top_level_commas(inner)
                if len(values) != 2:
                    continue
                rendered = ", ".join(part.strip() for part in values)
                replaced = (
                    f"{match.group('indent')}CALL add_to_set({name}, TUPLE({rendered}))"
                )
                changed = True
                break
            transformed_lines.append(replaced + ending)

        if not changed:
            return source, []
        transformed = "".join(transformed_lines)
        return transformed, [
            SourceTransformation(
                line=1,
                rule="GC248",
                source=source,
                target=transformed,
            )
        ]


    def _normalise_shared_collection_idioms(
        self,
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        """Apply queue/deque/set/stack operations from declarations and local usage."""
        transformed = source

        # ABSTRACT_STACK_PRESERVATION:
        # An explicit ``empty stack`` declaration proves the source abstraction
        # is a stack, but it does not prove that the canonical pseudocode should
        # be re-described as a LIST. Preserve recognised stack operations as
        # stack intrinsics; the Python compiler may choose a list-backed
        # implementation later.  This runs before the historical generic
        # PUSH->APPEND fallback so list-backed PUSH surfaces retain their old
        # behaviour while explicitly stack-backed receivers do not leak the
        # Python representation into canonical AJ.
        explicit_stack_names = set(re.findall(
            r"(?im)^\s*([A-Za-z_]\w*)\s*<-\s*empty\s+(?:CALL\s+)?stack(?:\s*\([^\n]*\))?\s*$",
            transformed,
        ))
        explicit_stack_names.update(re.findall(
            r"(?im)^\s*([A-Za-z_]\w*)\s*<-\s*EMPTY\s+STACK\s*$",
            transformed,
        ))
        explicit_stack_names.update(re.findall(
            r"(?im)^\s*([A-Za-z_]\w*)\s*<-\s*CALL\s+create_stack\(\s*\)\s*$",
            transformed,
        ))

        for name in sorted(explicit_stack_names, key=len, reverse=True):
            escaped = re.escape(name)

            # Preserve explicit POP semantics in any expression context.
            transformed = re.sub(
                rf"(?i)\b{escaped}\.pop\(\s*\)",
                f"CALL POP({name})",
                transformed,
            )
            transformed = re.sub(
                rf"(?i)CALL\s+{escaped}_pop\(\s*\)",
                f"CALL POP({name})",
                transformed,
            )

            # Preserve the pre-existing explicit top/back access spelling.
            # This is intentionally not generalised into a new stack-peek
            # intrinsic in this release; it only prevents the declaration
            # representation change from stranding the earlier [LAST] alias.
            transformed = re.sub(
                rf"(?i)\b{escaped}\[LAST\]",
                f"{name}[-1]",
                transformed,
            )

            # Preserve explicit source stack emptiness rather than exposing a
            # list-length predicate in canonical AJ. Accept the direct prose
            # form and the query surface that may already have become ~LENGTH.
            transformed = re.sub(
                rf"(?i)\b{escaped}\s+IS\s+NOT\s+empty\b",
                f"NOT CALL stack_is_empty({name})",
                transformed,
            )
            transformed = re.sub(
                rf"(?i)\b{escaped}\s+IS\s+empty\b",
                f"CALL stack_is_empty({name})",
                transformed,
            )
            transformed = re.sub(
                rf"(?i)\b{escaped}~LENGTH\s*==\s*0\b",
                f"CALL stack_is_empty({name})",
                transformed,
            )
            transformed = re.sub(
                rf"(?i)\b{escaped}~LENGTH\s*>\s*0\b",
                f"NOT CALL stack_is_empty({name})",
                transformed,
            )
            transformed = re.sub(
                rf"(?i)\bLENGTH\s+OF\s+{escaped}\s*==\s*0\b",
                f"CALL stack_is_empty({name})",
                transformed,
            )
            transformed = re.sub(
                rf"(?i)\bLENGTH\s+OF\s+{escaped}\s*>\s*0\b",
                f"NOT CALL stack_is_empty({name})",
                transformed,
            )

            # GenericCollectionNormaliser has already source-evidenced
            # ``stack.push(value)`` as ``PUSH value TO stack``. Route only this
            # evidenced receiver to the abstract PUSH intrinsic.
            transformed = re.sub(
                rf"(?im)^(?P<indent>[ \t]*)PUSH\s+(?P<value>.+?)\s+(?:TO|ONTO)\s+{escaped}\s*$",
                lambda x, n=name: (
                    f"{x.group('indent')}CALL PUSH({x.group('value').strip()}, {n})"
                ),
                transformed,
            )
            transformed = re.sub(
                rf"(?im)^(?P<indent>[ \t]*)CALL\s+{escaped}_push\((?P<value>.+)\)\s*$",
                lambda x, n=name: (
                    f"{x.group('indent')}CALL PUSH({x.group('value').strip()}, {n})"
                ),
                transformed,
            )

        # GENERIC_PUSH_REPRESENTATION_INFERENCE — RETIRED.
        #
        # A source-authored ``PUSH value TO receiver`` establishes a PUSH
        # operation, but not the receiver's backing representation.  Do not
        # collapse unknown receivers to LIST/APPEND here.  Evidence-specific
        # passes below may still lower PUSH to APPEND when the receiver is
        # explicitly list-backed; explicit stacks have already been routed to
        # CALL PUSH above.  Any remaining PUSH is preserved as an abstraction
        # at the end of this routine.

        # IMPLICIT_NUMERIC_TO_STRING_COERCION — RETIRED.
        #
        # Earlier compatibility code used EMPTY STRING backing plus MODULUS
        # provenance to insert ``CALL to_string(...)`` into mixed numeric/string
        # additions. That is a semantic repair, not representation recovery.
        # Preserve the source-authored addition and let executable validation
        # expose the resulting type error. Explicit STRING(variable) conversion
        # remains supported separately by GC225.

        transformed = re.sub(
            r"(?i)CALL\s+values\(([^()]+)\)",
            lambda m: f"CALL to_list({m.group(1).strip()})",
            transformed,
        )

        # ABSTRACT_QUEUE_PRESERVATION:
        # Explicit queue declarations prove a queue abstraction, not a LIST.
        # Preserve queue operations in canonical AJ and leave the Python
        # backing representation to the compiler.  This mirrors the approved
        # stack boundary: representation lowering is a compiler concern.
        explicit_queue_names = set(re.findall(
            r"(?im)^\s*([A-Za-z_]\w*)\s*<-\s*EMPTY\s+QUEUE\s*$",
            transformed,
        ))
        explicit_queue_names.update(re.findall(
            r"(?im)^\s*([A-Za-z_]\w*)\s*<-\s*CALL\s+create_queue\(\s*\)\s*$",
            transformed,
        ))

        for name in sorted(explicit_queue_names, key=len, reverse=True):
            escaped = re.escape(name)

            transformed = re.sub(
                rf"(?im)^(?P<indent>[ \t]*){escaped}\s*<-\s*EMPTY\s+QUEUE\s*$",
                lambda m, n=name: f"{m.group('indent')}{n} <- CALL create_queue()",
                transformed,
            )

            # Member-call normalisation has already exposed these as the
            # source-shaped ENQUEUE/DEQUEUE forms. Route only the explicitly
            # queue-backed receiver to queue intrinsics.
            transformed = re.sub(
                rf"(?im)^(?P<indent>[ \t]*)ENQUEUE\s+(?P<value>.+?)\s+TO\s+{escaped}\s*$",
                lambda m, n=name: (
                    f"{m.group('indent')}CALL ENQUEUE({n}, {m.group('value').strip()})"
                ),
                transformed,
            )
            transformed = re.sub(
                rf"(?im)^(?P<indent>[ \t]*)(?P<target>[A-Za-z_]\w*)\s*<-\s*DEQUEUE\s+FROM\s+{escaped}\s*$",
                lambda m, n=name: f"{m.group('indent')}{m.group('target')} <- CALL DEQUEUE({n})",
                transformed,
            )
            transformed = re.sub(
                rf"(?i)\bDEQUEUE\s+FROM\s+{escaped}\b",
                f"CALL DEQUEUE({name})",
                transformed,
            )

            # Preserve explicit queue size/emptiness as queue queries rather
            # than list LENGTH predicates.
            transformed = re.sub(
                rf"(?i)\b{escaped}\s+IS\s+NOT\s+empty\b",
                f"NOT CALL queue_is_empty({name})",
                transformed,
            )
            transformed = re.sub(
                rf"(?i)\b{escaped}\s+IS\s+empty\b",
                f"CALL queue_is_empty({name})",
                transformed,
            )
            transformed = re.sub(
                rf"(?i)\b{escaped}~LENGTH\s*==\s*0\b",
                f"CALL queue_is_empty({name})",
                transformed,
            )
            transformed = re.sub(
                rf"(?i)\b{escaped}~LENGTH\s*>\s*0\b",
                f"NOT CALL queue_is_empty({name})",
                transformed,
            )
            transformed = re.sub(
                rf"(?i)\bLENGTH\s+OF\s+{escaped}\s*==\s*0\b",
                f"CALL queue_is_empty({name})",
                transformed,
            )
            transformed = re.sub(
                rf"(?i)\bLENGTH\s+OF\s+{escaped}\s*>\s*0\b",
                f"NOT CALL queue_is_empty({name})",
                transformed,
            )
            transformed = re.sub(
                rf"(?i)\b{escaped}~LENGTH\b",
                f"CALL queue_size({name})",
                transformed,
            )
            transformed = re.sub(
                rf"(?i)\bLENGTH\s+OF\s+{escaped}\b",
                f"CALL queue_size({name})",
                transformed,
            )

        # ABSTRACT_DEQUE_PRESERVATION:
        # Explicit deque declarations prove a double-ended queue abstraction,
        # not a LIST. Preserve front/back operations in canonical AJ and leave
        # the Python backing representation to the compiler, matching the
        # approved stack and queue boundaries. Explicitly list-backed deque
        # idioms remain on GC136's historical LIST path.
        explicit_deque_names = set(re.findall(
            r"(?im)^\s*([A-Za-z_]\w*)\s*<-\s*EMPTY\s+DEQUE\s*$",
            transformed,
        ))
        explicit_deque_names.update(re.findall(
            r"(?im)^\s*([A-Za-z_]\w*)\s*<-\s*CALL\s+create_deque\(\s*\)\s*$",
            transformed,
        ))
        explicit_deque_names.update(re.findall(
            r"(?im)^\s*([A-Za-z_]\w*)\s*<-\s*(?:CALL\s+)?(?:Deque|DoubleEndedQueue)\s*\(\s*\)\s*$",
            transformed,
        ))

        for name in sorted(explicit_deque_names, key=len, reverse=True):
            escaped = re.escape(name)

            transformed = re.sub(
                rf"(?im)^(?P<indent>[ \t]*){escaped}\s*<-\s*(?:EMPTY\s+DEQUE|(?:CALL\s+)?(?:Deque|DoubleEndedQueue)\s*\(\s*\))\s*$",
                lambda m, n=name: f"{m.group('indent')}{n} <- CALL create_deque()",
                transformed,
            )

            # Mutating deque operations may already have been exposed as AJ
            # list primitives by the earlier generic collection pass. Once the
            # receiver is explicitly deque-backed, restore the source
            # abstraction rather than leaking that intermediate representation.
            transformed = re.sub(
                rf"(?im)^(?P<indent>[ \t]*)APPEND\s+(?P<value>.+?)\s+TO\s+{escaped}\s*$",
                lambda m, n=name: (
                    f"{m.group('indent')}CALL deque_push_back("
                    f"{n}, {m.group('value').strip()})"
                ),
                transformed,
            )
            transformed = re.sub(
                rf"(?im)^(?P<indent>[ \t]*)PUSH\s+(?P<value>.+?)\s+(?:TO|ONTO)\s+{escaped}\s*$",
                lambda m, n=name: (
                    f"{m.group('indent')}CALL deque_push_back("
                    f"{n}, {m.group('value').strip()})"
                ),
                transformed,
            )
            transformed = re.sub(
                rf"(?i)REMOVE\s+FIRST\s+ITEM\s+FROM\s+{escaped}\b",
                f"CALL deque_pop_front({name})",
                transformed,
            )
            transformed = re.sub(
                rf"(?i)REMOVE\s+LAST\s+ITEM\s+FROM\s+{escaped}\b",
                f"CALL deque_pop_back({name})",
                transformed,
            )

            # Query/access operations retain deque meaning. Fixed front/back
            # indexing is rewritten only for reads, never indexed assignment
            # targets.
            transformed = re.sub(
                rf"(?i)\b{escaped}\s+IS\s+NOT\s+empty\b",
                f"NOT CALL deque_is_empty({name})",
                transformed,
            )
            transformed = re.sub(
                rf"(?i)\b{escaped}\s+IS\s+empty\b",
                f"CALL deque_is_empty({name})",
                transformed,
            )
            transformed = re.sub(
                rf"(?i)\b{escaped}~LENGTH\s*==\s*0\b",
                f"CALL deque_is_empty({name})",
                transformed,
            )
            transformed = re.sub(
                rf"(?i)\b{escaped}~LENGTH\s*>\s*0\b",
                f"NOT CALL deque_is_empty({name})",
                transformed,
            )
            transformed = re.sub(
                rf"(?i)\bLENGTH\s+OF\s+{escaped}\s*==\s*0\b",
                f"CALL deque_is_empty({name})",
                transformed,
            )
            transformed = re.sub(
                rf"(?i)\bLENGTH\s+OF\s+{escaped}\s*>\s*0\b",
                f"NOT CALL deque_is_empty({name})",
                transformed,
            )
            transformed = re.sub(
                rf"(?i)\b{escaped}\[0\](?!\s*<-)",
                f"CALL deque_front({name})",
                transformed,
            )
            transformed = re.sub(
                rf"(?i)\b{escaped}\[(?:-1|LAST)\](?!\s*<-)",
                f"CALL deque_back({name})",
                transformed,
            )
            transformed = re.sub(
                rf"(?i)\b{escaped}~LENGTH\b",
                f"CALL deque_size({name})",
                transformed,
            )
            transformed = re.sub(
                rf"(?i)\bLENGTH\s+OF\s+{escaped}\b",
                f"CALL deque_size({name})",
                transformed,
            )


        # GC229 / SEEDED_LIST_BACKED_QUEUE_OPERATION_NORMALISATION:
        # GC157 canonicalises a non-empty source list literal such as
        # ``queue <- LIST [root]`` to ``queue <- CALL list_value(root)`` before
        # collection idioms run.  That remains explicit list-backing evidence.
        # When the same receiver is used by the source-provided free
        # DEQUEUE/ENQUEUE operations, accept both their bare and already-CALL
        # forms and lower them to the existing AJ list-backed FIFO operations.
        # This does not infer queue behaviour for arbitrary list variables.
        seeded_list_names = set(re.findall(
            r"(?im)^\s*([A-Za-z_]\w*)\s*<-\s*CALL\s+list_value\([^)]*\)\s*$",
            transformed,
        ))
        seeded_queue_names = {
            name for name in seeded_list_names
            if (
                re.search(
                    rf"(?i)(?:CALL\s+)?DEQUEUE\(\s*{re.escape(name)}\s*\)",
                    transformed,
                )
                or re.search(
                    rf"(?i)(?:CALL\s+)?ENQUEUE\(\s*{re.escape(name)}\s*,",
                    transformed,
                )
            )
        }
        before_seeded_queue = transformed
        for name in sorted(seeded_queue_names, key=len, reverse=True):
            escaped = re.escape(name)
            transformed = re.sub(
                rf"(?i)(?:CALL\s+)?DEQUEUE\(\s*{escaped}\s*\)",
                f"REMOVE FIRST ITEM FROM {name}",
                transformed,
            )
            transformed = re.sub(
                rf"(?im)^(?P<indent>[ \t]*)(?:CALL\s+)?ENQUEUE\(\s*{escaped}\s*,\s*(?P<value>.+)\)\s*$",
                lambda x, n=name: f"{x.group('indent')}APPEND {x.group('value').strip()} TO {n}",
                transformed,
            )
        seeded_queue_changed = transformed != before_seeded_queue
        after_seeded_queue = transformed

        queue_names = set(re.findall(
            r"(?im)^\s*([A-Za-z_]\w*)\s*<-\s*(?:EMPTY LIST|CALL\s+list_value\([^)]*\))\s*$",
            transformed,
        ))
        for name in sorted(queue_names, key=len, reverse=True):
            escaped = re.escape(name)
            transformed = re.sub(
                rf"(?i)CALL\s+DEQUEUE\(\s*{escaped}\s*\)",
                f"REMOVE FIRST ITEM FROM {name}",
                transformed,
            )
            transformed = re.sub(
                rf"(?im)^(?P<indent>[ \t]*)CALL\s+ENQUEUE\(\s*{escaped}\s*,\s*(?P<value>.+)\)\s*$",
                lambda x, n=name: f"{x.group('indent')}APPEND {x.group('value').strip()} TO {n}",
                transformed,
            )

        # Capture variables known to be collection-backed after declaration normalisation.
        dictionary_names = set(re.findall(
            r"(?im)^\s*([A-Za-z_]\w*)\s*<-\s*EMPTY\s+DICTIONARY\s*$",
            transformed,
        ))

        for name in sorted(dictionary_names, key=len, reverse=True):
            escaped = re.escape(name)
            transformed = re.sub(
                rf"(?i)CALL\s+{escaped}_get\(([^,()]+),\s*([^()]+)\)",
                lambda m, n=name: (
                    f"CALL dictionary_get({n}, "
                    f"{m.group(1).strip()}, {m.group(2).strip()})"
                ),
                transformed,
            )

        collection_names = set(re.findall(
            r"(?im)^\s*([A-Za-z_]\w*)\s*<-\s*EMPTY\s+(?:LIST|SET)\s*$",
            transformed,
        ))
        collection_names.update(re.findall(
            r"(?im)^\s*([A-Za-z_]\w*)\s*<-\s*(?:values\s*)?\[",
            transformed,
        ))

        for name in sorted(collection_names, key=len, reverse=True):
            escaped = re.escape(name)

            # COLLECTION_SELF_ADDITION dispatch:
            #   known_list <- known_list + [single]   => APPEND single
            #   known_list <- known_list + list_expr  => extend_list(...)
            transformed = re.sub(
                rf"(?im)^(?P<indent>[ \t]*){escaped}\s*<-\s*{escaped}\s*\+\s*\[(?P<value>[^\n]+)\]\s*$",
                lambda x, n=name: f"{x.group('indent')}APPEND {x.group('value').strip()} TO {n}",
                transformed,
            )

            # A recursive call to the current function is list-valued when the
            # function returns this known list variable.
            function_match = re.search(
                r"(?im)^\s*FUNCTION\s+(?P<fn>[A-Za-z_]\w*)\s+ACCEPTS\([^)]*\)",
                transformed,
            )
            if function_match and re.search(
                rf"(?im)^\s*RETURN\s+{escaped}\s*$",
                transformed,
            ):
                fn = function_match.group("fn")
                transformed = re.sub(
                    rf"(?im)^(?P<indent>[ \t]*){escaped}\s*<-\s*{escaped}\s*\+\s*(?P<rhs>CALL\s+{re.escape(fn)}\([^\n]+\))\s*$",
                    lambda x, n=name: (
                        f"{x.group('indent')}CALL extend_list("
                        f"{n}, {x.group('rhs').strip()})"
                    ),
                    transformed,
                )

            transformed = re.sub(
                rf"(?i)CALL\s+{escaped}_pop\(\)",
                f"CALL stack_pop({name})",
                transformed,
            )

            transformed = re.sub(
                rf"(?im)^(?P<indent>[ \t]*)CALL\s+{escaped}_push\((.+)\)\s*$",
                lambda m, n=name: f"{m.group('indent')}APPEND {m.group(2).strip()} TO {n}",
                transformed,
            )

            transformed = re.sub(
                rf"(?i)\b{escaped}\[LAST\]",
                f"{name}[-1]",
                transformed,
            )

            transformed = re.sub(
                rf"(?im)^(?P<indent>[ \t]*)CALL\s+{escaped}_append\((.+)\)\s*$",
                lambda m, n=name: f"{m.group('indent')}APPEND {m.group(2).strip()} TO {n}",
                transformed,
            )

            transformed = re.sub(
                rf"(?im)^(?P<indent>[ \t]*)CALL\s+{escaped}_enqueue\((.+)\)\s*$",
                lambda m, n=name: f"{m.group('indent')}APPEND {m.group(2).strip()} TO {n}",
                transformed,
            )

            transformed = re.sub(
                rf"(?im)^(?P<indent>[ \t]*)CALL\s+{escaped}_reverse\(\)\s*$",
                lambda m, n=name: f"{m.group('indent')}CALL reverse_list({n})",
                transformed,
            )

            transformed = re.sub(
                rf"(?i)\b{escaped}\s+IS\s+NOT\s+empty\b",
                f"LENGTH OF {name} > 0",
                transformed,
            )
            transformed = re.sub(
                rf"(?i)\b{escaped}\s+IS\s+empty\b",
                f"LENGTH OF {name} == 0",
                transformed,
            )
            transformed = re.sub(
                rf"(?i)\b{escaped}~LENGTH\b",
                f"LENGTH OF {name}",
                transformed,
            )

            transformed = re.sub(
                rf"(?im)^(?P<indent>[ \t]*)ENQUEUE\s+(.+?)\s+TO\s+{escaped}\s*$",
                lambda m, n=name: f"{m.group('indent')}APPEND {m.group(2).strip()} TO {n}",
                transformed,
            )
            transformed = re.sub(
                rf"(?im)^(?P<indent>[ \t]*)(?P<target>[A-Za-z_]\w*)\s*<-\s*DEQUEUE\s+FROM\s+{escaped}\s*$",
                lambda m, n=name: f"{m.group('indent')}{m.group('target')} <- REMOVE FIRST ITEM FROM {n}",
                transformed,
            )
            transformed = re.sub(
                rf"(?im)^(?P<indent>[ \t]*)PUSH\s+(?!CALL\s+POP\()(.+?)\s+(?:TO|ONTO)\s+{escaped}\s*$",
                lambda m, n=name: f"{m.group('indent')}APPEND {m.group(2).strip()} TO {n}",
                transformed,
            )

        # Set operations are contextual: an explicit EMPTY SET declaration is
        # sufficient evidence to distinguish set insertion/removal from list
        # operations without inventing a collection type.  Keep the emitted AJ
        # source within the frozen v1.0 grammar by using ordinary CALL syntax.
        set_names = set(re.findall(
            r"(?im)^\s*([A-Za-z_]\w*)\s*<-\s*EMPTY\s+SET\s*$",
            transformed,
        ))
        for name in sorted(set_names, key=len, reverse=True):
            escaped = re.escape(name)
            transformed = re.sub(
                rf"(?im)^(?P<indent>[ \t]*)ADD\s+(?P<value>.+?)\s+TO\s+{escaped}\s*$",
                lambda m, n=name: (
                    f"{m.group('indent')}CALL add_to_set({n}, {m.group('value').strip()})"
                ),
                transformed,
            )
            transformed = re.sub(
                rf"(?im)^(?P<indent>[ \t]*)APPEND\s+(?P<value>.+?)\s+TO\s+{escaped}\s*$",
                lambda m, n=name: (
                    f"{m.group('indent')}CALL add_to_set({n}, {m.group('value').strip()})"
                ),
                transformed,
            )
            transformed = re.sub(
                rf"(?im)^(?P<indent>[ \t]*)CALL\s+{escaped}_remove\((.+)\)\s*$",
                lambda m, n=name: f"{m.group('indent')}CALL remove_from_set({n}, {m.group(2).strip()})",
                transformed,
            )

        # Preserve any remaining source-authored PUSH whose receiver has no
        # explicit representation evidence.  The compiler may lower this
        # abstraction to a list-backed stack operation, but canonical AJ must
        # not claim the source declared a LIST.
        transformed = re.sub(
            r"(?im)^(?P<indent>[ \t]*)PUSH\s+(?P<value>(?!CALL\s+POP\().+?)\s+TO\s+(?P<receiver>[A-Za-z_]\w*)\s*$",
            lambda m: (
                f"{m.group('indent')}CALL PUSH("
                f"{m.group('value').strip()}, {m.group('receiver')})"
            ),
            transformed,
        )

        if transformed == source:
            return source, []

        transformations: list[SourceTransformation] = []
        if seeded_queue_changed:
            transformations.append(SourceTransformation(
                line=1,
                rule="GC229",
                source=before_seeded_queue,
                target=after_seeded_queue,
            ))
        if transformed != after_seeded_queue:
            transformations.append(SourceTransformation(
                line=1, rule="GC158", source=after_seeded_queue, target=transformed
            ))
        elif not seeded_queue_changed:
            transformations.append(SourceTransformation(
                line=1, rule="GC158", source=source, target=transformed
            ))
        return transformed, transformations

    def _normalise_shared_object_idioms(
        self,
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        """Expose flattened properties only when the surrounding object context is clear."""
        transformed = source

        # Do not infer generic linked-list member access from a variable being
        # initialised from ``head`` plus an underscored identifier such as
        # ``current_next``.  Underscores are valid AJ identifier characters, so
        # neither ``current <- head`` nor the ``*_next`` spelling independently
        # proves that the source denotes a ``.next`` property.  The separately
        # gated Floyd ``slow``/``fast`` recovery below remains available and is
        # audited independently.

        # Do not infer binary-tree member access from flattened identifiers
        # such as ``node_value``, ``node_left``, or ``node_right``, even inside
        # a level-order traversal where ``node`` is explicitly dequeued.  Those
        # spellings are valid AJ identifiers in their own right; the traversal
        # context establishes the role of ``node`` but does not establish that a
        # distinct underscored identifier denotes one of its properties.
        # Explicit source member access such as ``node.value`` remains intact.

        # Do not infer Floyd linked-list member access from iterator/state
        # variable names such as ``slow``/``fast`` or ``tortoise``/``hare``
        # combined with flattened identifiers such as ``slow_next`` or
        # ``hare_next``.  These underscored spellings are valid AJ identifiers
        # and do not prove ``.next`` member structure.  Explicit source member
        # access such as ``slow.next`` and ``fast.next.next`` is preserved by
        # the parser without compatibility-layer invention.

        # Do not infer transaction object properties merely from the iterator
        # spelling ``FOR EACH transaction IN transactions``.  Identifiers such
        # as ``transaction_itemID`` and ``transaction_quantity`` are valid AJ
        # identifiers in their own right; the iterator/collection names do not
        # prove member-access structure.  The separate GC146 inventory-update
        # recogniser remains independently gated and is audited separately.

        if (
            re.search(r"(?i)FUNCTION\s+\w+\s+ACCEPTS\(maze,\s*start,\s*end\)", transformed)
            and re.search(r"(?i)\bdirections\s*<-", transformed)
        ):
            # Do not infer coordinate indexing from flattened identifier names
            # such as ``start_row``, ``current_col``, or ``direction_row``.
            # Each spelling is already a valid AJ identifier, and the presence
            # of ``maze``, ``start``, ``end``, and ``directions`` does not prove
            # that those identifiers denote tuple/list coordinates.  Keep the
            # independent explicit directions-literal and indexed-assignment
            # surface recoveries below; they do not rely on these names.

            transformed = re.sub(
                r"(?im)^(?P<indent>[ \t]*)directions\s*<-\s*\[\s*\(0\s*,\s*1\)\s*,\s*\(1\s*,\s*0\)\s*,\s*\(0\s*,\s*-1\)\s*,\s*\(-1\s*,\s*0\)\s*\]\s*$",
                lambda x: (
                    f"{x.group('indent')}directions <- CALL list_value("
                    "TUPLE(0, 1), TUPLE(1, 0), TUPLE(0, -1), TUPLE(-1, 0))"
                ),
                transformed,
            )

            transformed = re.sub(
                r"(?im)^(?P<indent>[ \t]*)(?P<target>[A-Za-z_]\w*(?:\[[^\]]+\])+?)\s*=\s*(?P<value>.+)$",
                lambda x: f"{x.group('indent')}{x.group('target')} <- {x.group('value').strip()}",
                transformed,
            )

            transformed = re.sub(
                r"(?im)^(?P<indent>[ \t]*)directions\s*<-\s*(?:values\s*)?\[\s*\(0\s*,\s*1\)\s*,\s*\(1\s*,\s*0\)\s*,\s*\(0\s*,\s*-1\)\s*,\s*\(-1\s*,\s*0\)\s*\]\s*$",
                lambda x: (
                    f"{x.group('indent')}directions <- CALL list_value("
                    "TUPLE(0, 1), TUPLE(1, 0), TUPLE(0, -1), TUPLE(-1, 0))"
                ),
                transformed,
            )

            # Do not operationalise descriptive bounds/wall semantics here.
            # ``within bounds`` and ``is not blocked`` require a concrete
            # coordinate/maze representation or an explicit dependency from
            # the source; choosing one in compatibility recovery would be
            # algorithmic inference.


        # Do not infer generic object properties from flattened identifiers such
        # as ``item_value`` or ``otherItem_value``.  Underscores are valid AJ
        # identifier characters, and nested iterator naming does not establish
        # that either identifier denotes ``item.value``.  Object-property
        # recovery in the separate specialised contexts above is unchanged by
        # this narrow retirement and can be audited independently.


        if transformed == source:
            return source, []
        return transformed, [
            SourceTransformation(line=1, rule="GC159", source=source, target=transformed)
        ]

    def _normalise_shared_declarations(
        self,
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        """Canonicalise common explicit collection/matrix initialisers."""
        transformed = source





        # INPUT_RESOLUTION / NUMERIC_TYPE_FROM_USAGE:
        # Generic INPUT(STRING(prompt)) is only a default acquisition form.
        # Downstream arithmetic may establish a stronger numeric type.
        numeric_input_matches = list(re.finditer(
            r'(?im)^(?P<indent>[ \t]*)(?P<name>[A-Za-z_]\w*)\s*<-\s*INPUT\(\s*STRING\((?P<prompt>.+)\)\s*\)\s*$',
            transformed,
        ))

        for input_match in numeric_input_matches:
            input_name = input_match.group("name")
            escaped = re.escape(input_name)

            integer_evidence = bool(
                # This pass runs before the final generic token/operator
                # conversion. Accept both canonical AJ operators and their
                # unambiguous generic source equivalents so downstream integer
                # evidence is not lost because of transformation ordering.
                re.search(r"\b(?:INTEGER\s+DIVISION|DIV)\b", transformed, re.I)
                or re.search(rf"\b{escaped}\b\s+(?:MODULUS|MOD)\s+", transformed, re.I)
                or re.search(rf"\b(?:MODULUS|MOD)\s+{escaped}\b", transformed, re.I)
            )

            arithmetic_evidence = bool(
                re.search(
                    rf"(?:\b{escaped}\b\s*[+\-*/<>]=?\s*|\s*[+\-*/<>]=?\s*\b{escaped}\b)",
                    transformed,
                )
                or re.search(rf"\b{escaped}\b\s*==\s*[^ \n]+", transformed)
                or re.search(rf"[^ \n]+\s*==\s*\b{escaped}\b", transformed)
            )

            if integer_evidence and arithmetic_evidence:
                transformed = re.sub(
                    rf'(?im)^(?P<indent>[ \t]*){escaped}\s*<-\s*INPUT\(\s*STRING\((?P<prompt>.+)\)\s*\)\s*$',
                    lambda x, n=input_name: (
                        f'{x.group("indent")}{n} <- INPUT(INTEGER({x.group("prompt")}))'
                    ),
                    transformed,
                    count=1,
                )
        # INPUT_RESOLUTION / STRING_TO_LIST_OF_CHARACTER (retired v3.66):
        # Indexing and LENGTH are valid string operations and therefore do not
        # establish that an externally supplied text value must be converted
        # into a character list. Preserve INPUT(...) unless conversion is
        # explicit in the source.
        # GENERIC_IDENTIFIER / RESOLVE_ANONYMOUS_DECLARATION_FROM_USAGE:
        # Resolve "CREATE EMPTY DICTIONARY" to a subsequently used dictionary
        # identifier only when usage uniquely identifies one candidate.
        if re.search(r"(?im)^[ \t]*CREATE\s+EMPTY\s+DICTIONARY[ \t]*$", transformed):
            dictionary_candidates = set()

            # Membership use: value IN Dictionary
            dictionary_candidates.update(re.findall(
                r"(?i)\bIN\s+([A-Za-z_]\w*)\b",
                transformed,
            ))

            # Indexed use: Dictionary[key]
            dictionary_candidates.update(re.findall(
                r"(?i)\b([A-Za-z_]\w*)\s*\[[^\]\n]+\]",
                transformed,
            ))

            # Output/return use provides supporting evidence.
            output_candidates = set(re.findall(
                r"(?im)^[ \t]*(?:OUTPUT|RETURN)\s+([A-Za-z_]\w*)\s*$",
                transformed,
            ))

            # Exclude obvious loop/source variables and reserved words.
            excluded = {
                "IN", "RANGE", "LIST", "SET", "DICTIONARY", "STRING",
                "BOOLEAN", "INTEGER", "FLOAT", "CHAR",
            }
            dictionary_candidates = {
                name for name in dictionary_candidates
                if name.upper() not in excluded
            }

            # Prefer a candidate supported both by dictionary operations and
            # final output/return; otherwise require exactly one operation-based
            # candidate.
            supported = dictionary_candidates & output_candidates
            if len(supported) == 1:
                dictionary_name = next(iter(supported))
            elif len(dictionary_candidates) == 1:
                dictionary_name = next(iter(dictionary_candidates))
            else:
                dictionary_name = None

            if dictionary_name is not None:
                transformed = re.sub(
                    r"(?im)^(?P<indent>[ \t]*)CREATE\s+EMPTY\s+DICTIONARY[ \t]*$",
                    lambda x: (
                        f"{x.group('indent')}{dictionary_name} <- EMPTY DICTIONARY"
                    ),
                    transformed,
                    count=1,
                )
        # INPUT_BINDING / NEUTRAL_UNNAMED_WRAPPER:
        # INPUT(prompt) marks external dependencies. When an input-driven
        # top-level algorithm has observable OUTPUT or RETURN and does not
        # declare a source-named function, represent that algorithm with the
        # neutral structural wrapper ``unnamed_function``. This avoids inventing
        # a semantic function name such as PROCESS while keeping source-provided
        # function names untouched.
        input_matches = list(re.finditer(
            r"(?im)^(?P<indent>[ \t]*)(?P<name>[A-Za-z_]\w*)\s*<-\s*INPUT\((?P<prompt>.+)\)\s*$",
            transformed,
        ))
        has_observable_result = bool(
            re.search(r"(?im)^[ \t]*(?:OUTPUT|RETURN)\b", transformed)
        )
        has_function_decl = bool(
            re.search(r"(?im)^[ \t]*FUNCTION\b", transformed)
        )

        if input_matches and has_observable_result and not has_function_decl:
            declared_parameter_names = [match.group("name") for match in input_matches]
            parameter_names = list(declared_parameter_names)

            # ABSTRACT_PARAMETER / REDUNDANT_MATRIX_DIMENSION:
            # In the specific square-matrix rotation idiom, Matrix is operated
            # on directly by transpose + row traversal while N is never used.
            # Preserve N in the audit as the conceptual N x N dimension, but
            # omit it from the executable wrapper. Do not generalise this to
            # arbitrary unused inputs.
            if (
                len(declared_parameter_names) == 2
                and declared_parameter_names[0].lower() == "matrix"
                and declared_parameter_names[1].lower() == "n"
                and re.search(r"(?im)^\s*CALL\s+transpose_in_place\(Matrix\)\s*$", transformed)
                and re.search(r"(?im)^\s*FOR\s+EACH\s+Row\s+IN\s+Matrix\s+DO\s*$", transformed)
            ):
                body_without_inputs = transformed
                for input_match in input_matches:
                    name = input_match.group("name")
                    body_without_inputs = re.sub(
                        rf"(?im)^[ \t]*{re.escape(name)}\s*<-\s*INPUT\(.+\)[ \t]*\n?",
                        "",
                        body_without_inputs,
                        count=1,
                    )
                if not re.search(r"\bN\b", body_without_inputs):
                    parameter_names = ["Matrix"]

            input_names = set(declared_parameter_names)
            body_lines = []
            for line in transformed.splitlines():
                assignment = re.fullmatch(
                    r"[ \t]*(?P<name>[A-Za-z_]\w*)\s*<-\s*INPUT\(.+\)[ \t]*",
                    line,
                    re.I,
                )
                if assignment and assignment.group("name") in input_names:
                    continue
                body_lines.append("    " + line if line.strip() else line)

            transformed = (
                f"FUNCTION unnamed_function ACCEPTS({', '.join(parameter_names)})\n"
                + "\n".join(body_lines).rstrip()
                + "\nENDFUNCTION"
            )
        transformed = re.sub(
            r"(?im)^(?P<indent>[ \t]*)(?P<target>[A-Za-z_]\w*)\s*<-\s*empty\s+(?:CALL\s+)?stack(?:\s*\([^\n]*\))?\s*$",
            lambda m: f"{m.group('indent')}{m.group('target')} <- CALL create_stack()",
            transformed,
        )

        transformed = re.sub(
            r"(?im)^(?P<indent>[ \t]*)(?P<target>[A-Za-z_]\w*)\s*<-\s*empty\s+array\s*$",
            lambda m: (
                f"{m.group('indent')}{m.group('target')} <- "
                "CALL create_array(0, NONE)"
            ),
            transformed,
        )

        transformed = re.sub(
            r"(?im)^(?P<indent>[ \t]*)(?P<target>[A-Za-z_]\w*)\s*<-\s*2D\s+array\s+of\s+size\s+(?P<n>[A-Za-z_]\w*)x(?P=n)\s+initialized\s+to\s+(?P<value>.+?)\s*$",
            lambda m: (
                f"{m.group('indent')}{m.group('target')} <- "
                f"CALL create_matrix({m.group('n')}, {m.group('n')}, {m.group('value').strip()})"
            ),
            transformed,
        )

        transformed = re.sub(
            r"(?im)^(?P<indent>[ \t]*)(?P<target>[A-Za-z_]\w*)\s*<-\s*2D\s+boolean\s+array\s+same\s+size\s+as\s+(?P<source>[A-Za-z_]\w*)\s+initialized\s+to\s+(?P<value>.+?)\s*$",
            lambda m: (
                f"{m.group('indent')}{m.group('target')} <- "
                f"CALL create_matrix(LENGTH OF {m.group('source')}, LENGTH OF {m.group('source')}[0], {m.group('value').strip()})"
            ),
            transformed,
        )

        transformed = re.sub(
            r"(?im)^(?P<indent>[ \t]*)(?P<target>[A-Za-z_]\w*)\s*<-\s*matrix\s+of\s+size\s+(?P<rows>[A-Za-z_]\w*)\s*x\s*(?P<cols>[A-Za-z_]\w*)\s+initialized\s+with\s+(?P<value>.+?)\s*$",
            lambda m: (
                f"{m.group('indent')}{m.group('target')} <- "
                f"CALL create_matrix({m.group('rows')}, {m.group('cols')}, {m.group('value').strip()})"
            ),
            transformed,
        )

        transformed = re.sub(
            r"(?im)^(?P<indent>[ \t]*)(?P<target>[A-Za-z_]\w*)\s*<-\s*matrix\s+of\s+size\s+(?P<rows>[A-Za-z_]\w*)\s*x\s*(?P<cols>[A-Za-z_]\w*)\s*$",
            lambda m: (
                f"{m.group('indent')}{m.group('target')} <- "
                f"CALL create_matrix({m.group('rows')}, {m.group('cols')}, NONE)"
            ),
            transformed,
        )

        # Generic zero-filled 2D matrix declaration.
        transformed = re.sub(
            r"(?im)^(?P<indent>[ \t]*)(?P<target>[A-Za-z_]\w*)\s*<-\s*(?P<rows>[A-Za-z_]\w*)\s*\*\s*(?P<cols>[A-Za-z_]\w*)\s+matrix\s+of\s+0s\s*$",
            lambda m: (
                f"{m.group('indent')}{m.group('target')} <- "
                f"CALL create_matrix({m.group('rows')}, {m.group('cols')}, 0)"
            ),
            transformed,
        )

        # Generic fixed-size array declaration.
        transformed = re.sub(
            r"(?im)^(?P<indent>[ \t]*)(?P<target>[A-Za-z_]\w*)\s*<-\s*array\s+of\s+size\s+(?P<size>.+?)\s+initialized\s+to\s+(?P<value>.+?)\s*$",
            lambda m: (
                f"{m.group('indent')}{m.group('target')} <- "
                f"CALL create_array({m.group('size').strip()}, {m.group('value').strip()})"
            ),
            transformed,
        )

        if transformed == source:
            return source, []
        return transformed, [
            SourceTransformation(line=1, rule="GC160", source=source, target=transformed)
        ]


    def _normalise_contextual_class_routines(
        self,
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        """Recover legacy routine spellings when their CLASS context is explicit.

        GC241 is structural/contextual only.  When the entire source is one
        explicit CLASS, direct child ``CONSTRUCTOR(...)`` is represented as the
        frozen AJ constructor form, while direct child ``PROCEDURE name(...)``
        and ``FUNCTION name(...)`` declarations are represented as METHODs.
        Missing routine terminators are closed only at the next direct-child
        routine, an explicit class terminator, or end-of-source.  A missing
        terminal ENDCLASS is added only when no unindented executable material
        follows the class.

        Method bodies, member names, ``self``/``THIS`` spelling, assignments,
        return behaviour, and all other semantics are left unchanged.
        """
        lines = source.splitlines()
        nonblank = [i for i, line in enumerate(lines) if line.strip()]
        if len(nonblank) < 2:
            return source, []

        first_i = nonblank[0]
        class_match = re.fullmatch(
            r"(?i)(?P<indent>[ \t]*)CLASS\s+(?P<name>[A-Za-z_]\w*)"
            r"(?P<accepts>\s+ACCEPTS\s*\((?P<class_params>.*?)\))?\s*:?\s*",
            lines[first_i],
        )
        if class_match is None:
            return source, []
        class_indent = len(class_match.group("indent"))

        # Refuse a source that visibly contains executable/top-level material
        # after the class body.  Numbered-corpus extraction should isolate one
        # algorithm; GC241 must not guess where a larger source's class ends.
        explicit_end_indices = [
            i for i in nonblank[first_i + 1:]
            if re.fullmatch(r"(?i)[ \t]*END\s*CLASS\s*", lines[i])
            or re.fullmatch(r"(?i)[ \t]*ENDCLASS\s*", lines[i])
        ]
        if explicit_end_indices:
            end_i = explicit_end_indices[0]
            if any(lines[i].strip() for i in range(end_i + 1, len(lines))):
                return source, []
        else:
            end_i = len(lines)
            for i in range(first_i + 1, len(lines)):
                if not lines[i].strip():
                    continue
                indent = len(lines[i]) - len(lines[i].lstrip())
                if indent <= class_indent:
                    return source, []

        constructor_re = re.compile(
            r"(?i)^(?P<indent>[ \t]*)CONSTRUCTOR(?:\s+ACCEPTS)?\s*\((?P<params>.*?)\)\s*:?\s*$"
        )
        routine_re = re.compile(
            r"(?i)^(?P<indent>[ \t]*)(?P<kind>FUNCTION|PROCEDURE)\s+"
            r"(?P<name>[A-Za-z_]\w*)(?:\s+ACCEPTS)?\s*\((?P<params>.*?)\)\s*:?\s*$"
        )
        explicit_constructor_end_re = re.compile(r"(?i)^[ \t]*END\s*CONSTRUCTOR\s*$|^[ \t]*ENDCONSTRUCTOR\s*$")
        explicit_routine_end_re = re.compile(
            r"(?i)^[ \t]*END\s*(?:FUNCTION|PROCEDURE|METHOD)\s*$|^[ \t]*(?:ENDFUNCTION|ENDPROCEDURE|ENDMETHOD)\s*$"
        )
        explicit_class_end_re = re.compile(r"(?i)^[ \t]*END\s*CLASS\s*$|^[ \t]*ENDCLASS\s*$")

        direct_headers: list[tuple[int, str, re.Match[str]]] = []
        routine_indent: int | None = None
        for i in range(first_i + 1, end_i):
            line = lines[i]
            if not line.strip():
                continue
            m_constructor = constructor_re.fullmatch(line)
            m_routine = routine_re.fullmatch(line)
            m = m_constructor or m_routine
            if m is None:
                continue
            indent = len(m.group("indent"))
            if indent <= class_indent:
                return source, []
            if routine_indent is None:
                routine_indent = indent
            if indent != routine_indent:
                continue
            direct_headers.append((i, "CONSTRUCTOR" if m_constructor else "METHOD", m))

        if (
            not direct_headers
            or not any(kind == "CONSTRUCTOR" for _, kind, _ in direct_headers)
            or not any(kind == "METHOD" for _, kind, _ in direct_headers)
        ):
            return source, []

        direct_header_indices = {i for i, _, _ in direct_headers}
        transformed_lines: list[str] = []
        transformed_lines.extend(lines[:first_i])
        class_header = f"{class_match.group('indent')}CLASS {class_match.group('name')}"
        if class_match.group("accepts") is not None:
            class_header += f" ACCEPTS({class_match.group('class_params').strip()})"
        transformed_lines.append(class_header)

        open_kind: str | None = None
        open_indent = ""
        changed = lines[first_i] != transformed_lines[-1]

        for i in range(first_i + 1, end_i):
            line = lines[i]

            if i in direct_header_indices:
                if open_kind is not None:
                    transformed_lines.append(
                        f"{open_indent}{'ENDCONSTRUCTOR' if open_kind == 'CONSTRUCTOR' else 'ENDMETHOD'}"
                    )
                    changed = True
                _, kind, match = next(item for item in direct_headers if item[0] == i)
                indent_text = match.group("indent")
                params = match.group("params").strip()
                if kind == "CONSTRUCTOR":
                    canonical = f"{indent_text}CONSTRUCTOR ACCEPTS({params})"
                else:
                    canonical = f"{indent_text}METHOD {match.group('name')} ACCEPTS({params})"
                transformed_lines.append(canonical)
                changed = changed or canonical != line
                open_kind = kind
                open_indent = indent_text
                continue

            if explicit_constructor_end_re.fullmatch(line):
                if open_kind != "CONSTRUCTOR":
                    return source, []
                canonical = f"{open_indent}ENDCONSTRUCTOR"
                transformed_lines.append(canonical)
                changed = changed or canonical != line
                open_kind = None
                continue

            if explicit_routine_end_re.fullmatch(line):
                if open_kind != "METHOD":
                    return source, []
                canonical = f"{open_indent}ENDMETHOD"
                transformed_lines.append(canonical)
                changed = changed or canonical != line
                open_kind = None
                continue

            transformed_lines.append(line)

        if open_kind is not None:
            transformed_lines.append(
                f"{open_indent}{'ENDCONSTRUCTOR' if open_kind == 'CONSTRUCTOR' else 'ENDMETHOD'}"
            )
            changed = True

        if end_i < len(lines) and explicit_class_end_re.fullmatch(lines[end_i]):
            canonical_end = f"{class_match.group('indent')}ENDCLASS"
            transformed_lines.append(canonical_end)
            changed = changed or canonical_end != lines[end_i]
            transformed_lines.extend(lines[end_i + 1:])
        else:
            transformed_lines.append(f"{class_match.group('indent')}ENDCLASS")
            changed = True

        transformed = "\n".join(transformed_lines)
        if source.endswith("\n"):
            transformed += "\n"
        if not changed or transformed == source:
            return source, []
        return transformed, [
            SourceTransformation(
                line=first_i + 1,
                rule="GC241",
                source=source,
                target=transformed,
            )
        ]


    @staticmethod
    def _normalise_explicit_matrix_allocation_surface(
        source: str,
        *,
        pattern: re.Pattern[str],
        rule: str,
        row_group: str,
        column_group: str | None,
    ) -> tuple[str, list[SourceTransformation]]:
        """Shared renderer for explicit zero-filled matrix allocation spellings.

        The surface recogniser remains rule-specific; this helper only owns the
        identical line traversal, ``create_matrix`` rendering and audit record.
        """
        transformations: list[SourceTransformation] = []
        output_lines: list[str] = []
        for line_number, line in enumerate(source.splitlines(), start=1):
            match = pattern.fullmatch(line)
            if match is None:
                output_lines.append(line)
                continue
            rows = match.group(row_group)
            cols = match.group(column_group) if column_group is not None else rows
            target = (
                f"{match.group('indent')}{match.group('target')} <- "
                f"CALL create_matrix({rows}, {cols}, 0)"
            )
            output_lines.append(target)
            transformations.append(SourceTransformation(
                line=line_number,
                rule=rule,
                source=line,
                target=target,
            ))

        if not transformations:
            return source, []
        transformed = "\n".join(output_lines)
        if source.endswith("\n"):
            transformed += "\n"
        return transformed, transformations

    @staticmethod
    def _normalise_explicit_square_grid_allocation(
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        """Recover the explicit ``N x N grid initialized to 0`` surface (GC246)."""
        pattern = re.compile(
            r"(?im)^(?P<indent>[ \t]*)(?P<target>[A-Za-z_]\w*)"
            r"\s*<-\s*(?P<n>[A-Za-z_]\w*)\s*x\s*(?P=n)"
            r"\s+grid\s+initialized\s+to\s+0\s*$"
        )
        return GenericObviousMismatchNormaliser._normalise_explicit_matrix_allocation_surface(
            source,
            pattern=pattern,
            rule="GC246",
            row_group="n",
            column_group=None,
        )

    @staticmethod
    def _normalise_explicit_rectangular_matrix_fill(
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        """Recover explicit ``rows x cols matrix filled with 0`` allocation (GC249)."""
        pattern = re.compile(
            r"(?im)^(?P<indent>[ \t]*)(?P<target>[A-Za-z_]\w*)"
            r"\s*<-\s*(?P<rows>[A-Za-z_]\w*)\s*x\s*(?P<cols>[A-Za-z_]\w*)"
            r"\s+matrix\s+filled\s+with\s+0\s*$"
        )
        return GenericObviousMismatchNormaliser._normalise_explicit_matrix_allocation_surface(
            source,
            pattern=pattern,
            rule="GC249",
            row_group="rows",
            column_group="cols",
        )


    @staticmethod
    def _normalise_evidenced_2d_copy_intrinsic(
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        """Recover exact ``Copy(name)`` only for an evidenced 2D matrix value.

        GC247 is deliberately narrower than a general copy/deep-copy rule. A
        simple identifier becomes matrix-backed only after a direct canonical
        assignment from ``CALL create_matrix(...)``. Nested routines inherit
        readable evidence from enclosing lexical scopes, matching the source's
        closure use in an Algorithm 41 form, but a parameter of the same name or
        any later direct rebind invalidates that evidence in the affected scope.

        Only the exact free, one-argument ``CALL Copy(name)`` spelling is
        represented as ``CALL copy_2d_list(name)``. Member calls, other arities,
        comments, quoted text, unproven values, and shadowed/reassigned names are
        intentionally left unchanged. Deterministic Python lowering is
        ``list(map(list, name))``.
        """
        lines = source.splitlines()
        if not lines:
            return source, []

        scope_start = re.compile(
            r"(?i)^\s*(?:FUNCTION|METHOD|CONSTRUCTOR)\b(?:[^\n]*?ACCEPTS\s*\((?P<params>[^)]*)\))?"
        )
        scope_end = re.compile(r"(?i)^\s*(?:ENDFUNCTION|ENDMETHOD|ENDCONSTRUCTOR)\b")
        direct_assignment = re.compile(
            r"^\s*(?P<name>[A-Za-z_]\w*)\s*<-\s*(?P<rhs>.+?)\s*$"
        )
        matrix_initialisation = re.compile(r"(?i)^CALL\s+create_matrix\s*\(")
        copy_call = re.compile(
            r"(?i)(?<![.\w])(?:CALL\s+)?Copy\s*\(\s*(?P<name>[A-Za-z_]\w*)\s*\)"
        )

        # Frames contain the matrix evidence readable at that lexical depth.
        # Nested routines inherit outer evidence unless a formal parameter
        # shadows the name or a direct assignment rebinds it.
        evidence = LexicalEvidenceContext()
        transformations: list[SourceTransformation] = []
        output_lines: list[str] = []

        def match_is_quoted(text: str, start: int) -> bool:
            quote: str | None = None
            escape = False
            for ch in text[:start]:
                if quote is not None:
                    if escape:
                        escape = False
                    elif ch == "\\":
                        escape = True
                    elif ch == quote:
                        quote = None
                elif ch in "'\"":
                    quote = ch
            return quote is not None

        for line_number, original in enumerate(lines, start=1):
            stripped = original.strip()

            start_match = scope_start.match(original)
            if start_match is not None:
                shadowed: list[str] = []
                raw_params = start_match.groupdict().get("params")
                if raw_params:
                    for part in raw_params.split(","):
                        param = part.strip().split()[0] if part.strip() else ""
                        if re.fullmatch(r"[A-Za-z_]\w*", param):
                            shadowed.append(param)
                evidence.enter(inherit=True, shadow=tuple(shadowed))

            assignment = direct_assignment.match(original)
            if assignment is not None:
                name = assignment.group("name")
                rhs = assignment.group("rhs").strip()
                if matrix_initialisation.match(rhs):
                    evidence.establish("matrix", name)
                else:
                    evidence.invalidate("matrix", name)

            updated = original
            if not stripped.upper().startswith("COMMENT"):
                search_from = 0
                while True:
                    match = copy_call.search(updated, search_from)
                    if match is None:
                        break
                    if match_is_quoted(updated, match.start()):
                        search_from = match.end()
                        continue
                    prefix = updated[:match.start()].rstrip()
                    if re.search(r"(?i)(?:FUNCTION|PROCEDURE|METHOD)\s*$", prefix):
                        search_from = match.end()
                        continue
                    name = match.group("name")
                    if not evidence.contains("matrix", name):
                        search_from = match.end()
                        continue
                    replacement = f"CALL copy_2d_list({name})"
                    updated = updated[:match.start()] + replacement + updated[match.end():]
                    search_from = match.start() + len(replacement)

            if updated != original:
                transformations.append(SourceTransformation(
                    line=line_number,
                    rule="GC247",
                    source=original,
                    target=updated,
                ))
            output_lines.append(updated)

            if scope_end.match(stripped):
                evidence.exit()

        if not transformations:
            return source, []
        transformed = "\n".join(output_lines)
        if source.endswith("\n"):
            transformed += "\n"
        return transformed, transformations


    def _normalise_unspecified_fixed_array_preallocation(
        self,
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        """Recover the approved no-fill fixed-size-array representation.

        Project rule (user-confirmed): ``Array of size N`` means N writable
        slots initialised to ``NONE``.  The AJ surface reuses the existing
        ``create_array(size, value)`` compatibility intrinsic; deterministic
        Python lowering emits ``[None] * N`` for the NONE-filled case.

        The recogniser is intentionally narrow: the size must be a single
        identifier or non-negative integer literal, and declarations that
        already supply an explicit initial value remain under GC160.
        """
        pattern = re.compile(
            r"(?im)^(?P<indent>[ \t]*)(?P<target>[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)"
            r"\s*<-\s*array\s+of\s+size\s+"
            r"(?P<size>[A-Za-z_]\w*|[0-9]+)\s*$"
        )
        transformed = pattern.sub(
            lambda m: (
                f"{m.group('indent')}{m.group('target')} <- "
                f"CALL create_array({m.group('size')}, NONE)"
            ),
            source,
        )
        if transformed == source:
            return source, []
        return transformed, [
            SourceTransformation(
                line=1,
                rule="GC240",
                source=source,
                target=transformed,
            )
        ]


    def _normalise_lru_class(
        self,
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        """Recover an explicit LRU class without replacing method logic.

        GC161 historically recognised the ``LRUCache`` surface and emitted a
        complete stock LRU implementation, regardless of what the source wrote
        inside ``get`` and ``put``.  That crossed the compatibility boundary:
        class/constructor syntax may be recovered from explicit state/header
        evidence, but algorithmic method bodies must remain source-derived.

        This recogniser therefore performs only structural recovery plus exact
        surface canonicalisation of operations that are already explicitly
        present in those preserved bodies.
        """
        upper = source.upper()
        required = (
            "CLASS LRUCACHE",
            "CACHE <- EMPTY DICTIONARY",
            "CAPACITY <- GIVEN CAPACITY",
            "ORDER <- EMPTY LIST",
        )
        if not all(fragment in upper for fragment in required):
            return source, []

        lines = source.splitlines()
        get_index = None
        put_index = None
        get_pattern = re.compile(
            r"^\s*FUNCTION\s+get(?:\s+ACCEPTS\s*\(\s*key\s*\)|\s*\(\s*key\s*\)\s*:?)\s*$",
            re.IGNORECASE,
        )
        put_pattern = re.compile(
            r"^\s*FUNCTION\s+put(?:\s+ACCEPTS\s*\(\s*key\s*,\s*value\s*\)|\s*\(\s*key\s*,\s*value\s*\)\s*:?)\s*$",
            re.IGNORECASE,
        )
        for index, line in enumerate(lines):
            if get_index is None and get_pattern.match(line):
                get_index = index
            if put_index is None and put_pattern.match(line):
                put_index = index

        if get_index is None or put_index is None or put_index <= get_index:
            return source, []

        def _method_body(start: int, end: int) -> list[str]:
            body = [
                line for line in lines[start:end]
                if not re.match(r"^\s*(?:ENDFUNCTION|ENDCLASS)\s*$", line, re.IGNORECASE)
            ]
            while body and not body[0].strip():
                body.pop(0)
            while body and not body[-1].strip():
                body.pop()
            if not body:
                return []

            indents = [len(line) - len(line.lstrip()) for line in body if line.strip()]
            base_indent = min(indents) if indents else 0
            rebased: list[str] = []
            for line in body:
                if not line.strip():
                    rebased.append("")
                    continue
                relative = max(0, (len(line) - len(line.lstrip())) - base_indent)
                rebased.append("        " + (" " * relative) + line.strip())
            return rebased

        get_body = _method_body(get_index + 1, put_index)
        put_body = _method_body(put_index + 1, len(lines))

        # ``capacity <- GIVEN CAPACITY`` is recovered as the explicit state
        # field ``given_capacity <- capacity``.  Once that state name exists,
        # later executable references to the source field ``capacity`` must
        # point at ``given_capacity`` too; otherwise canonical pseudocode and
        # generated Python would disagree about which instance field exists.
        # Quoted text and explanatory ``//`` comments are not variable reads
        # and therefore remain untouched.
        def _rewrite_capacity_state(body: list[str]) -> list[str]:
            rewritten: list[str] = []
            identifier = re.compile(r"\bcapacity\b", re.IGNORECASE)

            for line in body:
                if not line.strip():
                    rewritten.append(line)
                    continue

                # Split an explanatory ``//`` comment without treating a
                # slash pair inside a quoted literal as a comment delimiter.
                comment_index: int | None = None
                scan_quote: str | None = None
                scan_escape = False
                scan_index = 0
                while scan_index < len(line) - 1:
                    char = line[scan_index]
                    if scan_quote is not None:
                        if scan_escape:
                            scan_escape = False
                        elif char == "\\":
                            scan_escape = True
                        elif char == scan_quote:
                            scan_quote = None
                        scan_index += 1
                        continue
                    if char in {"'", '"'}:
                        scan_quote = char
                        scan_index += 1
                        continue
                    if line[scan_index:scan_index + 2] == "//":
                        comment_index = scan_index
                        break
                    scan_index += 1

                if comment_index is None:
                    executable, comment = line, None
                else:
                    executable, comment = line[:comment_index], line[comment_index + 2:]

                out: list[str] = []
                cursor = 0
                quote: str | None = None
                escape = False
                segment_start = 0
                while cursor < len(executable):
                    char = executable[cursor]
                    if quote is None:
                        if char in {"'", '"'}:
                            out.append(identifier.sub("given_capacity", executable[segment_start:cursor]))
                            quote = char
                            segment_start = cursor
                    else:
                        if escape:
                            escape = False
                        elif char == "\\":
                            escape = True
                        elif char == quote:
                            out.append(executable[segment_start:cursor + 1])
                            quote = None
                            segment_start = cursor + 1
                    cursor += 1

                if segment_start < len(executable):
                    tail = executable[segment_start:]
                    out.append(tail if quote is not None else identifier.sub("given_capacity", tail))
                elif segment_start == len(executable) and not out:
                    out.append("")

                rebuilt = "".join(out)
                if comment is not None:
                    rebuilt += "//" + comment
                rewritten.append(rebuilt)

            return rewritten

        get_body = _rewrite_capacity_state(get_body)
        put_body = _rewrite_capacity_state(put_body)

        replacement_lines = [
            "CLASS LRUCache ACCEPTS(capacity)",
            # Preserve the source phrase ``capacity <- GIVEN CAPACITY`` as an
            # explicit recovered state field rather than silently lowering the
            # constructor argument to ``self.capacity`` in Python.
            "    given_capacity <- capacity",
            "    cache <- EMPTY DICTIONARY",
            "    order <- EMPTY LIST",
            "",
            "    FUNCTION get ACCEPTS(key)",
            *get_body,
            "    ENDFUNCTION",
            "",
            "    FUNCTION put ACCEPTS(key, value)",
            *put_body,
            "    ENDFUNCTION",
            "ENDCLASS",
        ]
        replacement = "\n".join(replacement_lines)

        # Canonicalise only operations explicitly written in the preserved
        # bodies.  These spellings do not add LRU steps; they map the source's
        # own list/dictionary method calls to existing AJ compatibility
        # intrinsics.
        replacement = re.sub(
            r"(?im)^(?P<indent>[ \t]*)order\.remove\(\s*(?P<arg>[^()\n]+?)\s*\)[ \t]*$",
            lambda m: f"{m.group('indent')}CALL remove_from_list(order, {m.group('arg').strip()})",
            replacement,
        )
        replacement = re.sub(
            r"(?im)^(?P<indent>[ \t]*)order\.insert_front\(\s*(?P<arg>[^()\n]+?)\s*\)[ \t]*$",
            lambda m: f"{m.group('indent')}CALL insert_front(order, {m.group('arg').strip()})",
            replacement,
        )
        replacement = re.sub(
            r"(?im)^(?P<indent>[ \t]*)order\.remove_back\(\s*\)[ \t]*$",
            lambda m: f"{m.group('indent')}CALL remove_last_from_list(order)",
            replacement,
        )
        replacement = re.sub(
            r"(?im)^(?P<indent>[ \t]*)cache\.remove\(\s*(?P<arg>[^()\n]+?)\s*\)[ \t]*$",
            lambda m: f"{m.group('indent')}CALL remove_key(cache, {m.group('arg').strip()})",
            replacement,
        )
        replacement = re.sub(
            r"(?im)^(?P<indent>[ \t]*)CALL\s+order_remove\(\s*(?P<arg>[^()\n]+?)\s*\)[ \t]*$",
            lambda m: f"{m.group('indent')}CALL remove_from_list(order, {m.group('arg').strip()})",
            replacement,
        )
        replacement = re.sub(
            r"(?im)^(?P<indent>[ \t]*)CALL\s+order_insert_front\(\s*(?P<arg>[^()\n]+?)\s*\)[ \t]*$",
            lambda m: f"{m.group('indent')}CALL insert_front(order, {m.group('arg').strip()})",
            replacement,
        )
        replacement = re.sub(
            r"(?im)^(?P<indent>[ \t]*)CALL\s+order_remove_back\(\s*\)[ \t]*$",
            lambda m: f"{m.group('indent')}CALL remove_last_from_list(order)",
            replacement,
        )
        replacement = re.sub(
            r"(?im)^(?P<indent>[ \t]*)CALL\s+cache_remove\(\s*(?P<arg>[^()\n]+?)\s*\)[ \t]*$",
            lambda m: f"{m.group('indent')}CALL remove_key(cache, {m.group('arg').strip()})",
            replacement,
        )

        return replacement, [
            SourceTransformation(
                line=1,
                rule="GC161",
                source=source,
                target=replacement,
            )
        ]


    def _normalise_inventory_update(
        self,
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        """Normalise the inventory-update surface without inventing member access.

        Historical GC146 handling also converted valid AJ identifiers such as
        ``transaction_item`` and ``transaction_quantity`` into Transaction
        properties.  The ``updateInventory`` function name and those identifier
        spellings do not establish member-access structure, so v3.63 preserves
        them as identifiers.  The independent ``ALERT expression`` surface
        recovery remains available here.
        """
        upper = source.upper()
        required = (
            "FUNCTION UPDATEINVENTORY ACCEPTS(INVENTORY, TRANSACTIONS)",
            "TRANSACTION_ITEM",
            "TRANSACTION_TYPE",
            "TRANSACTION_QUANTITY",
        )
        if not all(fragment in upper for fragment in required):
            return source, []

        transformed = re.sub(
            r"(?im)^(?P<indent>[ \t]*)ALERT[ \t]+(?P<expr>.+?)[ \t]*$",
            lambda m: f"{m.group('indent')}OUTPUT {m.group('expr')}",
            source,
        )
        if transformed == source:
            return source, []
        return transformed, [
            SourceTransformation(line=1, rule="GC146", source=source, target=transformed)
        ]


    def _normalise_queue_function(
        self,
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        """Normalise a queue implemented explicitly with two stack lists."""
        upper = source.upper()
        required = (
            "FUNCTION QUEUE ACCEPTS()",
            "STACK1 <- EMPTY LIST",
            "STACK2 <- EMPTY LIST",
            "FUNCTION ENQUEUE ACCEPTS(ITEM)",
            "FUNCTION DEQUEUE ACCEPTS()",
            "UNDERFLOW",
        )
        if not all(fragment in upper for fragment in required):
            return source, []

        transformed = source
        transformed = re.sub(
            r"(?i)\bstack2\s+is\s+empty\b",
            "LENGTH OF stack2 == 0",
            transformed,
        )
        transformed = re.sub(
            r"(?i)\bstack1\s+is\s+not\s+empty\b",
            "LENGTH OF stack1 > 0",
            transformed,
        )

        transformed = re.sub(
            r"(?im)^(?P<indent>[ \t]*)PUSH[ \t]+item[ \t]+ONTO[ \t]+stack1[ \t]*$",
            lambda m: f"{m.group('indent')}APPEND item TO stack1",
            transformed,
        )

        transformed = re.sub(
            r"(?im)^(?P<indent>[ \t]*)PUSH[ \t]+CALL[ \t]+POP\(stack1\)[ \t]+ONTO[ \t]+stack2[ \t]*$",
            lambda m: (
                f"{m.group('indent')}Item <- REMOVE LAST ITEM FROM stack1\n"
                f"{m.group('indent')}APPEND Item TO stack2"
            ),
            transformed,
        )

        transformed = re.sub(
            r"(?im)^(?P<indent>[ \t]*)RETURN[ \t]+CALL[ \t]+POP\(stack2\)[ \t]*$",
            lambda m: f"{m.group('indent')}RETURN REMOVE LAST ITEM FROM stack2",
            transformed,
        )

        if transformed == source:
            return source, []

        return transformed, [
            SourceTransformation(
                line=1,
                rule="GC141",
                source=source,
                target=transformed,
            )
        ]


    def _normalise_floyd_cycle(
        self,
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        """Legacy hook retained for compatibility; shared object rules do the normalisation."""
        return source, []


    def _normalise_stack_function(
        self,
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        """Normalise explicit last-item shorthand for list-backed collections.

        GC139 began as a Stack-specific compatibility hook.  The source idioms it
        handles are not Stack-specific, however: ``REMOVE and RETURN last item of
        <name>`` explicitly denotes a destructive last-item return, while ``RETURN
        last item of <name>`` explicitly denotes a non-destructive last-item read.

        Apply those rewrites only when ``<name>`` is already evidenced as a
        list-backed collection in the source.  This removes the old dependency on
        particular function names or nesting shapes and does not invent a data
        structure or external interface.
        """
        list_names = set(re.findall(
            r"(?im)^\s*([A-Za-z_]\w*)\s*<-\s*EMPTY\s+LIST\s*$",
            source,
        ))
        list_names.update(re.findall(
            r"(?im)^\s*([A-Za-z_]\w*)\s*<-\s*LIST\s*\[",
            source,
        ))
        list_names.update(re.findall(
            r"(?im)^\s*([A-Za-z_]\w*)\s*<-\s*CALL\s+list_value\(",
            source,
        ))
        list_names.update(re.findall(
            r"(?i)\b([A-Za-z_]\w*)\s+AS\s+LIST\b",
            source,
        ))
        if not list_names:
            return source, []

        transformed = source
        for name in sorted(list_names, key=len, reverse=True):
            escaped = re.escape(name)
            transformed = re.sub(
                rf"(?im)^(?P<indent>[ \t]*)REMOVE[ \t]+and[ \t]+RETURN[ \t]+last[ \t]+item[ \t]+of[ \t]+{escaped}[ \t]*$",
                lambda m, n=name: (
                    f"{m.group('indent')}RETURN REMOVE LAST ITEM FROM {n}"
                ),
                transformed,
            )
            transformed = re.sub(
                rf"(?im)^(?P<indent>[ \t]*)RETURN[ \t]+last[ \t]+item[ \t]+of[ \t]+{escaped}[ \t]*$",
                lambda m, n=name: f"{m.group('indent')}RETURN {n}[-1]",
                transformed,
            )

        if transformed == source:
            return source, []

        return transformed, [
            SourceTransformation(
                line=1,
                rule="GC139",
                source=source,
                target=transformed,
            )
        ]


    def _normalise_lru_cache(
        self,
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        """Normalise LRU ordering operations on the explicitly declared cache dictionary."""
        upper = source.upper()
        required = (
            "FUNCTION LRUCACHE ACCEPTS(CAPACITY)",
            "MOST RECENTLY USED",
            "LEAST RECENTLY",
        )
        cache_declaration = (
            "CACHE <- EMPTY DICTIONARY" in upper
            or "CACHE <- CALL CREATE_ORDERED_DICTIONARY()" in upper
        )
        if not cache_declaration or not all(fragment in upper for fragment in required):
            return source, []

        transformed = source

        transformed = re.sub(
            r"(?i)(THEN[ \t]+)REMOVE[ \t]+key(?=[ \t]+THEN|[ \t]*$)",
            r"\1CALL remove_key(cache, key)",
            transformed,
        )

        # Existing key: remove then append the same key/value at the MRU end.
        transformed = re.sub(
            r"(?im)^(?P<indent>[ \t]*)MOVE[ \t]+key[ \t]+to[ \t]+most[ \t]+recently[ \t]+used[ \t]+position[ \t]*$",
            lambda m: (
                f"{m.group('indent')}CALL move_key_to_back(cache, key)"
            ),
            transformed,
        )

        # Plain REMOVE key inside put() means remove that key from the cache.
        transformed = re.sub(
            r"(?im)^(?P<indent>[ \t]*)REMOVE[ \t]+key[ \t]*$",
            lambda m: f"{m.group('indent')}CALL remove_key(cache, key)",
            transformed,
        )

        transformed = re.sub(
            r"(?im)^(?P<indent>[ \t]*)REMOVE[ \t]+least[ \t]+recently[ \t]+used[ \t]*\(front\)[ \t]+item[ \t]*$",
            lambda m: f"{m.group('indent')}CALL remove_first_mapping(cache)",
            transformed,
        )

        transformed = re.sub(
            r"(?im)^(?P<indent>[ \t]*)INSERT[ \t]+key:value[ \t]+at[ \t]+most[ \t]+recently[ \t]+used[ \t]+position[ \t]*$",
            lambda m: f"{m.group('indent')}cache[key] <- value",
            transformed,
        )

        if transformed == source:
            return source, []

        return transformed, [
            SourceTransformation(
                line=1,
                rule="GC138",
                source=source,
                target=transformed,
            )
        ]


    def _normalise_sliding_window_deque(
        self,
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        """Normalise explicit shorthand for a list-backed variable named ``deque``.

        GC136 is intentionally driven by source-level deque evidence rather than
        by recognition of a particular algorithm.  The variable must already be
        explicitly initialised as a list, and at least one front/back deque idiom
        must be present before any conversion is attempted.
        """
        list_backed_deque = re.search(
            r"(?im)^[ \t]*deque[ \t]*<-[ \t]*(?:EMPTY[ \t]+LIST|LIST[ \t]*\[|CALL[ \t]+list_value\()",
            source,
        )
        if list_backed_deque is None:
            return source, []

        deque_evidence = (
            r"(?i)\bdeque\s+not\s+empty\b",
            r"(?i)\bdeque_front\b",
            r"(?i)\bdeque_back\b",
            r"(?i)\bdeque\.front\b",
            r"(?i)\bdeque\.back\b",
            r"(?im)^[ \t]*REMOVE[ \t]+front[ \t]+of[ \t]+deque[ \t]*$",
            r"(?im)^[ \t]*REMOVE[ \t]+back[ \t]+of[ \t]+deque[ \t]*$",
            r"(?im)^[ \t]*APPEND[ \t]+.+?[ \t]+TO[ \t]+back[ \t]+of[ \t]+deque[ \t]*$",
        )
        if not any(re.search(pattern, source) for pattern in deque_evidence):
            return source, []

        transformed = source
        transformed = re.sub(
            r"(?i)\bdeque\s+not\s+empty\b",
            "LENGTH OF deque > 0",
            transformed,
        )
        transformed = re.sub(
            r"(?i)\b(?:deque_front|deque\.front)\b",
            "deque[0]",
            transformed,
        )
        transformed = re.sub(
            r"(?i)\b(?:deque_back|deque\.back)\b",
            "deque[-1]",
            transformed,
        )

        def replace_line(pattern: str, replacement_body):
            nonlocal transformed

            def repl(match):
                indent = match.group("indent")
                if callable(replacement_body):
                    body = replacement_body(match)
                else:
                    body = replacement_body
                return indent + body

            transformed = re.sub(
                pattern,
                repl,
                transformed,
                flags=re.IGNORECASE | re.MULTILINE,
            )

        replace_line(
            r"^(?P<indent>[ \t]*)REMOVE[ \t]+front[ \t]+of[ \t]+deque[ \t]*$",
            "REMOVE FIRST ITEM FROM deque",
        )
        replace_line(
            r"^(?P<indent>[ \t]*)REMOVE[ \t]+back[ \t]+of[ \t]+deque[ \t]*$",
            "REMOVE LAST ITEM FROM deque",
        )
        replace_line(
            r"^(?P<indent>[ \t]*)APPEND[ \t]+(?P<value>.+?)[ \t]+TO[ \t]+back[ \t]+of[ \t]+deque[ \t]*$",
            lambda match: f"APPEND {match.group('value')} TO deque",
        )

        if transformed == source:
            return source, []

        return transformed, [
            SourceTransformation(
                line=1,
                rule="GC136",
                source=source,
                target=transformed,
            )
        ]


    def _normalise_matrix_multiplication(
        self,
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        """Do not reconstruct missing matrix-multiplication setup.

        Legacy GC127 generated random input matrices, derived dimensions and a
        Result allocation that were not present in the model response.  Those
        operations cross the semantic-alignment boundary, so matrix
        multiplication is now left to the source-provided procedure only.
        """
        return source, []


    @staticmethod
    def _has_undefined_n_queens_safety(source: str) -> bool:
        """Identify an N-Queens form whose safety rule is undefined."""
        checks = (
            r"(?i)CREATE\s+N\s*\*\s*N\s+board",
            r"(?i)FUNCTION\s+Solve(?:\s+ACCEPTS)?\s*\(\s*Row\s*\)",
            r"(?i)Position\s*\(\s*Row\s*,\s*Col\s*\)\s+is\s+safe",
            r"(?i)PLACE\s+Queen\s+at",
            r"(?i)REMOVE\s+Queen\s+from",
        )
        return all(re.search(pattern, source) for pattern in checks)

    @staticmethod
    def _has_undefined_n_queens_routines(source: str) -> bool:
        """Identify N-Queens source with descriptive, undefined routines.

        The response supplies the placement/backtracking skeleton but leaves
        ``RECORD solution`` and the ``isSafe`` body as natural-language
        descriptions.  Neither operation is an AJ/Python intrinsic, explicitly
        imported dependency, nor a routine defined elsewhere in the response.
        Reconstructing them would therefore invent algorithmic behaviour.
        """
        required = (
            r"(?i)FUNCTION\s+solveNQueens",
            r"(?i)FUNCTION\s+placeQueens",
            r"(?i)FUNCTION\s+isSafe",
            r"(?i)RECORD\s+solution",
            r"(?i)CHECK\s+column\s*,\s*upper-left\s+diagonal\s*,\s*upper-right\s+diagonal\s+for\s+queens",
            r"(?i)RETURN\s+(?:BOOLEAN\(TRUE\)|TRUE)\s+if\s+no\s+conflicts",
        )
        return all(re.search(pattern, source) for pattern in required)


    @staticmethod
    def _has_undefined_punctuation_predicate(source: str) -> bool:
        """Identify an algorithm with an undefined punctuation test.

        The source provides the filtering loop and string accumulation but never
        defines what counts as punctuation.  Converting ``Character is NOT
        punctuation`` into an invented ``is_punctuation`` helper would only
        rename the missing predicate semantics, so this form remains an
        expected failure.
        """
        required = (
            r"(?im)^\s*INPUT\s+Sentence\s*$",
            r"(?im)^\s*Result\s*<-\s*\"\"\s*$",
            r"(?im)^\s*FOR\s+EACH\s+Character\s+IN\s+Sentence(?:\s+DO)?\s*$",
            r"(?im)^\s*IF\s+Character\s+is\s+NOT\s+punctuation\s+THEN\s*$",
            r"(?im)^\s*Result\s*<-\s*Result\s*\+\s*Character\s*$",
            r"(?im)^\s*OUTPUT\s+Result\s*$",
        )
        return all(re.search(pattern, source) for pattern in required)


    @staticmethod
    def _has_undefined_environmental_file_type_predicates(source: str) -> bool:
        """Detect descriptive file/folder predicates lacking executable evidence.

        This is deliberately source-shape and model independent.  Phrases such
        as ``item is a file`` or ``item is a folder`` describe an environmental
        type test but do not identify the Python/AJ routine that performs it.
        GC104 historically renamed those phrases to free calls such as
        ``is_file(item)`` and ``is_directory(item)``; unless those exact helper
        dependencies are explicitly defined or imported by the supplied source,
        that conversion creates a false executable pass.

        Explicit member calls such as ``item.is_file()`` are already executable
        v1.1 syntax and do not match this detector.
        """
        predicate_matches = list(re.finditer(
            r"(?i)\b([A-Za-z_]\w*)\s+is\s+(?:a\s+)?(file|folder|directory)\b",
            source,
        ))
        if not predicate_matches:
            return False

        required_helpers: set[str] = set()
        for match in predicate_matches:
            kind = match.group(2).lower()
            required_helpers.add("is_file" if kind == "file" else "is_directory")

        def helper_has_source_evidence(helper: str) -> bool:
            helper_re = re.escape(helper)
            defined = re.search(
                rf"(?im)^\s*(?:FUNCTION|PROCEDURE)\s+{helper_re}(?:\s+ACCEPTS)?\s*\(",
                source,
            )
            imported = (
                re.search(rf"(?im)^\s*IMPORT\s+{helper_re}(?:\s|$|,)", source)
                or re.search(rf"(?im)^\s*FROM\s+[^\n]+\s+IMPORT\s+[^\n]*\b{helper_re}\b", source)
                or re.search(rf"(?im)^\s*IMPORT\s+[^\n]+\s+AS\s+{helper_re}\s*$", source)
            )
            return bool(defined or imported)

        return any(not helper_has_source_evidence(helper) for helper in required_helpers)


    @staticmethod
    def _has_abstract_maze_navigation_semantics(source: str) -> bool:
        """Detect unresolved neighbour/traversability descriptions corpus-wide.

        This boundary is deliberately independent of model, filename, function
        name and algorithm number.  A descriptive neighbour relation or
        branch-driving maze predicate is not executable merely because a
        conventional implementation is familiar.  The source must state the
        relation/test in executable AJ (for example ``IN CALL neighbours(...)``
        or ``CALL is_traversable(...)``) rather than leaving it as prose.
        """
        navigation_context = bool(re.search(
            r"(?i)\b(?:maze|grid|cell|neighbou?r|wall|blocked|traversable)\b",
            source,
        ))
        if not navigation_context:
            return False

        unresolved_patterns = (
            # Undefined relation: source does not say how neighbours are
            # generated or represented.
            r"(?im)^\s*FOR\s+EACH\s+[^\n]*neighbou?r[^\n]*\s+OF\s+[^\n]+$",
            # Descriptive branch-driving predicates whose concrete semantics
            # depend on representation/environmental definitions.
            r"(?i)\bneighbou?r\s+is\s+valid\b",
            r"(?i)\bnot\s+(?:a\s+)?wall\b",
            r"(?i)\bis\s+not\s+blocked\b",
            r"(?i)\bare\s+within\s+bounds\b",
            r"(?i)\bis\s+within\s+(?:the\s+)?(?:maze|grid)\s+bounds\b",
        )
        if any(re.search(pattern, source) for pattern in unresolved_patterns):
            return True

        # A free navigation helper is also an unresolved dependency unless the
        # supplied pseudocode defines or imports that exact helper.  Explicit
        # object member calls (``maze.neighbours(...)``) are already an
        # executable interface and are intentionally excluded here.
        helper_call = re.compile(
            r"(?i)(?<!\.)\b(?:CALL\s+)?(?P<helper>"
            r"get_?valid_?neighbou?rs?|getvalidneighbou?rs?|"
            r"neighbou?rs?|is_?traversable|is_?wall|is_?blocked"
            r")\s*\("
        )

        def helper_has_source_evidence(helper: str) -> bool:
            escaped = re.escape(helper)
            defined = bool(re.search(
                rf"(?im)^\s*(?:FUNCTION|METHOD)\s+{escaped}\s+(?:ACCEPTS\s*)?\(",
                source,
            ))
            imported = bool(
                re.search(rf"(?im)^\s*FROM\s+[^\n]+\s+IMPORT\s+[^\n]*\b{escaped}\b", source)
                or re.search(rf"(?im)^\s*IMPORT\s+{escaped}\s*$", source)
                or re.search(rf"(?im)^\s*IMPORT\s+[^\n]+\s+AS\s+{escaped}\s*$", source)
            )
            return defined or imported

        for match in helper_call.finditer(source):
            line_start = source.rfind("\n", 0, match.start()) + 1
            prefix = source[line_start:match.start()]
            if re.search(r"(?i)(?:FUNCTION|METHOD)\s+$", prefix):
                continue
            helper = match.group("helper")
            if not helper_has_source_evidence(helper):
                return True

        return False


    @staticmethod
    def _has_abstract_coordination_semantics(source: str) -> bool:
        """Detect unresolved coordination/control semantics without source-specific cues.

        The compatibility pipeline must not turn descriptive coordination prose
        into an executable algorithm merely because a conventional solution is
        familiar.  This detector is deliberately independent of model,
        filename, algorithm number, wrapper function and variable names.

        Explicit object member calls (for example ``drone.move(...)``) are an
        executable interface in frozen AJ v1.1 and are intentionally allowed.
        Free helper calls are different: in a coordination context they require
        an explicit local definition/import unless they are a known AJ/Python
        intrinsic.  Otherwise preserving the call would create a runtime
        dependency that the supplied pseudocode never binds.
        """
        coordination_context = bool(re.search(
            r"(?i)\b(?:drone|swarm|collision|airspace|trajectory|obstacle|"
            r"safety[_ ]?radius|mission|coordinate|coordination|synchroni[sz]e)\b",
            source,
        ))
        if not coordination_context:
            return False

        # Natural-language conditions/operations whose executable meaning is
        # not established by the source.  Do not choose a completion predicate,
        # geometry/bounds representation, proximity metric, barrier mechanism,
        # path planner, collision detector or motion-control routine on behalf
        # of the author.
        unresolved_patterns = (
            r"(?im)^\s*WHILE\s+[^\n]*(?:mission\s+not\s+complete|have\s+not\s+reached)"
            r"(?:\s+DO)?\s*:?[ \t]*$",
            r"(?i)\bis\s+within\s+[^\n]+\s+bounds\b",
            r"(?i)\bis\s+near\s+(?:an?\s+)?(?:obstacle|drone|other[_ ]?drone)\b",
            r"(?i)\bcollision\s+risk\s+detected\b",
            r"(?im)^\s*(?:DETECT|CALCULATE|UPDATE|CHECK|RECALCULATE)\s+[^<\n]+$",
            r"(?im)^\s*SYNCHRONI[ZS]E\s+[^\n]+$",
        )
        if any(re.search(pattern, source) for pattern in unresolved_patterns):
            return True

        # A free helper call in this semantic family is executable only when
        # its binding is supplied.  Member calls are excluded by the negative
        # look-behind because the object itself supplies the explicit interface.
        free_call = re.compile(r"(?i)(?<!\.)\b(?P<helper>[A-Za-z_]\w*)\s*\(")
        intrinsic_calls = {
            # Python/AJ primitives and constructors that may legitimately be
            # preserved without a user-supplied helper definition.
            "abs", "all", "any", "bool", "dict", "enumerate", "float",
            "input", "int", "len", "list", "max", "min", "print",
            "range", "round", "set", "sorted", "str", "sum", "tuple", "zip",
            "accepts", "boolean", "call", "dictionary", "integer", "length", "null",
            "random", "string", "create_matrix", "copy_2d_list", "list_value",
        }

        def helper_has_source_evidence(helper: str) -> bool:
            escaped = re.escape(helper)
            defined = bool(re.search(
                rf"(?im)^\s*(?:FUNCTION|PROCEDURE|METHOD)\s+{escaped}"
                rf"(?:\s+ACCEPTS)?\s*\(",
                source,
            ))
            imported = bool(
                re.search(rf"(?im)^\s*FROM\s+[^\n]+\s+IMPORT\s+[^\n]*\b{escaped}\b", source)
                or re.search(rf"(?im)^\s*IMPORT\s+{escaped}(?:\s|$|,)", source)
                or re.search(rf"(?im)^\s*IMPORT\s+[^\n]+\s+AS\s+{escaped}\s*$", source)
            )
            return defined or imported

        for match in free_call.finditer(source):
            helper = match.group("helper")
            helper_lower = helper.lower()
            if helper_lower in intrinsic_calls:
                continue

            line_start = source.rfind("\n", 0, match.start()) + 1
            prefix = source[line_start:match.start()]
            # Function/procedure/method declarations are not calls.
            if re.search(r"(?i)(?:FUNCTION|PROCEDURE|METHOD)\s+$", prefix):
                continue
            # ``CALL`` is syntax, not a helper identifier, and is already in
            # the intrinsic set; this also documents why it is harmless here.
            if helper_has_source_evidence(helper):
                continue
            return True

        return False


    @staticmethod
    def _has_uninitialised_matrix_addition_result(source: str) -> bool:
        """Identify element-wise matrix addition that never creates Result.

        The corpus form explicitly defines the element-wise addition but writes
        to ``Result[i][j]`` without any prior declaration/allocation of Result.
        Making it executable would require inventing that missing state, so the
        generic compatibility path must leave this form unresolved.
        """
        required = (
            r"(?im)^\s*INPUT\s+MatrixA\s*,\s*MatrixB\s*$",
            r"(?im)^\s*INPUT\s+Rows\s*,\s*Columns\s*$",
            r"(?im)^\s*FOR\s+i\s*<-\s*0\s+TO\s+Rows\s*-\s*1\s*$",
            r"(?im)^\s*FOR\s+j\s*<-\s*0\s+TO\s+Columns\s*-\s*1\s*$",
            r"(?im)^\s*Result\[i\]\[j\]\s*<-\s*MatrixA\[i\]\[j\]\s*\+\s*MatrixB\[i\]\[j\]\s*$",
            r"(?im)^\s*OUTPUT\s+Result\s*$",
        )
        if not all(re.search(pattern, source) for pattern in required):
            return False

        # An explicit whole-Result assignment/allocation removes the missing
        # state condition. Indexed writes are intentionally not counted as
        # initialisation because they are the operation whose prerequisite is
        # absent in the corpus response.
        has_result_initialisation = bool(
            re.search(r"(?im)^\s*CREATE\s+.*\bResult\b.*$", source)
            or re.search(r"(?im)^\s*Result\s*<-\s*(?!.*\[i\]\[j\]).+$", source)
        )
        return not has_result_initialisation

    @staticmethod
    def _has_uninitialised_matrix_multiplication_result(source: str) -> bool:
        """Identify matrix multiplication that writes into an uncreated Result.

        The corpus form explicitly supplies the triple-loop accumulation and
        even sets each ``Result[i][j]`` cell to zero, but it never creates the
        containing Result matrix.  Creating that storage (or generating input
        matrices/dimensions) would add model-absent algorithmic state.
        """
        required = (
            r"(?im)^\s*INPUT\b[^\n]*\bMatrixA\b",
            r"(?im)^\s*INPUT\b[^\n]*\bMatrixB\b",
            r"(?im)^\s*INPUT\b[^\n]*\bRowsA\b",
            r"(?im)^\s*INPUT\b[^\n]*\bColumnsA\b",
            r"(?im)^\s*INPUT\b[^\n]*\bColumnsB\b",
            r"(?im)^\s*FOR\s+i\s*<-\s*0\s+TO\s+RowsA\s*-\s*1\s*$",
            r"(?im)^\s*FOR\s+j\s*<-\s*0\s+TO\s+ColumnsB\s*-\s*1\s*$",
            r"(?im)^\s*Result\[i\]\[j\]\s*<-\s*0\s*$",
            r"(?im)^\s*FOR\s+k\s*<-\s*0\s+TO\s+ColumnsA\s*-\s*1\s*$",
            r"(?is)Result\[i\]\[j\]\s*<-\s*Result\[i\]\[j\]\s*\+\s*MatrixA\[i\]\[k\]\s*\*\s*MatrixB\[k\]\[j\]",
            r"(?im)^\s*OUTPUT\s+Result\s*$",
        )
        if not all(re.search(pattern, source) for pattern in required):
            return False

        has_result_initialisation = bool(
            re.search(r"(?im)^\s*CREATE\s+.*\bResult\b.*$", source)
            or re.search(
                r"(?im)^\s*Result\s*<-\s*(?!\s*Result\[|.*\[i\]\[j\]).+$",
                source,
            )
        )
        return not has_result_initialisation

    def _normalise_n_queens(self, source: str) -> tuple[str, list[SourceTransformation]]:
        """Do not reconstruct an undefined N-Queens safety predicate.

        The source form states ``Position(Row, Col) is safe`` but does
        not define the column/diagonal safety semantics. Earlier GC125 builds
        invented that algorithm. Under the semantic-alignment policy this
        response is an expected failure, so the compatibility layer deliberately
        leaves it unreconstructed.
        """
        return source, []


    def _normalise_linear_search_case(self, source: str) -> tuple[str, list[SourceTransformation]]:
        """Canonicalise the explicit linear-search form without changing its search logic.

        The source explicitly performs a first-match linear search and uses an
        inclusive ``TO LENGTH(List)-1`` bound. AJ v1.0 ``RANGE`` endpoints are
        end-exclusive, so the canonical source records the required ``+ 1``
        adjustment. ``EXIT FOR`` is preserved structurally as ``BREAK``.

        The stored text export is lossy and may contain ``?`` where the
        authoritative source uses ``←``. In this *narrow source-recovery rule*
        only, ``?`` is accepted as evidence of that known export corruption. It
        is never emitted, never treated as AJ syntax, and never presented as an
        alternative to canonical assignment ``<-``.
        """
        patterns = (
            r"(?im)^\s*INPUT\s+List\s*,\s*Target\s*$",
            r"(?im)^\s*Found\s*<-\s*FALSE\s*$",
            r"(?im)^\s*FOR\s+i\s*<-\s*0\s+TO\s+LENGTH(?:\s+OF|\s*\()\s*List\)?\s*-\s*1\s*$",
            r"(?im)^\s*IF\s+List\[i\]\s*(?:=|==)\s*Target\s+THEN\s*$",
            r'''(?im)^\s*OUTPUT\s+["']Found at position["']\s*,\s*i\s*$''',
            r"(?im)^\s*Found\s*<-\s*TRUE\s*$",
            r"(?im)^\s*EXIT\s+FOR\s*$",
            r"(?im)^\s*IF\s+Found\s*(?:=|==)\s*FALSE\s+THEN\s*$",
            r'''(?im)^\s*OUTPUT\s+["']Target not found["']\s*$''',
        )
        if not all(re.search(pattern, source) for pattern in patterns):
            return source, []

        replacement = '''FUNCTION unnamed_function ACCEPTS(List, Target)
    Found <- BOOLEAN(False)

    FOR i <- IN RANGE 0 TO (LENGTH OF List - 1) + 1 DO
        IF List[i] == Target THEN
            OUTPUT STRING("Found at position {i}")
            Found <- BOOLEAN(True)
            BREAK
        ENDIF
    ENDFOR

    IF Found == BOOLEAN(False) THEN
        OUTPUT STRING("Target not found")
    ENDIF
ENDFUNCTION'''

        return replacement, [
            SourceTransformation(
                line=1,
                rule="GC175",
                source=source,
                target=replacement,
            )
        ]


    def _normalise_bubble_sort_case(self, source: str) -> tuple[str, list[SourceTransformation]]:
        """Canonicalise the explicit bubble-sort procedure.

        The source ``TO`` bounds are inclusive while AJ v1.0 ``RANGE`` ends are
        exclusive, so the canonical form records the required ``+ 1`` endpoint
        adjustments.  ``SWAP`` is an explicit source primitive; keep that
        operation visible in canonical AJ as ``CALL swap(collection, left_index,
        right_index)`` and leave the implementation temporary to the Python
        compiler rather than attributing it to the model.
        """
        patterns = (
            r"(?im)^\s*INPUT\s+WordList\s*$",
            r"(?im)^\s*FOR\s+i\s*<-\s*0\s+TO\s+LENGTH(?:\s+OF|\s*\()\s*WordList\)?\s*-\s*2\s*$",
            r"(?im)^\s*FOR\s+j\s*<-\s*0\s+TO\s+LENGTH(?:\s+OF|\s*\()\s*WordList\)?\s*-\s*2\s*-\s*i\s*$",
            r"(?im)^\s*IF\s+WordList\[j\]\s*>\s*WordList\[j\s*\+\s*1\]\s+THEN\s*$",
            r"(?im)^\s*SWAP\s+WordList\[j\]\s*,\s*WordList\[j\s*\+\s*1\]\s*$",
            r"(?im)^\s*OUTPUT\s+WordList\s*$",
        )
        if not all(re.search(pattern, source) for pattern in patterns):
            return source, []

        replacement = """FUNCTION unnamed_function ACCEPTS(WordList)
    FOR i <- IN RANGE 0 TO (LENGTH OF WordList - 2) + 1 DO
        FOR j <- IN RANGE 0 TO (LENGTH OF WordList - 2 - i) + 1 DO
            IF WordList[j] > WordList[j + 1] THEN
                CALL swap(WordList, j, j + 1)
            ENDIF
        ENDFOR
    ENDFOR

    OUTPUT WordList
ENDFUNCTION"""

        return replacement, [
            SourceTransformation(
                line=1,
                rule="GC174",
                source=source,
                target=replacement,
            )
        ]


    def _normalise_tower_of_hanoi(self, source: str) -> tuple[str, list[SourceTransformation]]:
        """Canonicalise the explicit Tower-of-Hanoi recursion without reconstruction.

        AJ_24038155 Dialect v1.2 permits local/nested FUNCTION declarations, so
        the source's Hanoi helper remains inside the neutral outer computation
        that accepts the external ``N`` value.  No interactive INPUT prompt,
        numeric conversion, function hoisting, or Hanoi logic is invented.
        The explicit comma-separated move message is represented by the existing
        canonical STRING placeholder form.
        """
        patterns = (
            r"(?im)^\s*INPUT\s+N\s*$",
            r"(?im)^\s*FUNCTION\s+Hanoi\s*\(\s*Discs\s*,\s*Source\s*,\s*Auxiliary\s*,\s*Destination\s*\)\s*$",
            r"(?im)^\s*IF\s+Discs\s*(?:=|==)\s*1\s+THEN\s*$",
            r"(?im)^\s*Hanoi\s*\(\s*Discs\s*-\s*1\s*,\s*Source\s*,\s*Destination\s*,\s*Auxiliary\s*\)\s*$",
            r"(?im)^\s*Hanoi\s*\(\s*Discs\s*-\s*1\s*,\s*Auxiliary\s*,\s*Source\s*,\s*Destination\s*\)\s*$",
            r"(?im)^\s*OUTPUT\s+[\"']Move disk from[\"']\s*,\s*Source\s*,\s*[\"']to[\"']\s*,\s*Destination\s*$",
            r"(?im)^\s*Hanoi\s*\(\s*N\s*,\s*[\"']A[\"']\s*,\s*[\"']B[\"']\s*,\s*[\"']C[\"']\s*\)\s*$",
        )
        if not all(re.search(pattern, source) for pattern in patterns):
            return source, []

        replacement = '''FUNCTION unnamed_function ACCEPTS(N)
    FUNCTION Hanoi ACCEPTS(Discs, Source, Auxiliary, Destination)
        IF Discs == 1 THEN
            OUTPUT STRING("Move disk from {Source} to {Destination}")
        ELSE
            CALL Hanoi(Discs - 1, Source, Destination, Auxiliary)

            OUTPUT STRING("Move disk from {Source} to {Destination}")

            CALL Hanoi(Discs - 1, Auxiliary, Source, Destination)
        ENDIF
    ENDFUNCTION

    CALL Hanoi(N, STRING("A"), STRING("B"), STRING("C"))
ENDFUNCTION'''

        return replacement, [
            SourceTransformation(
                line=1,
                rule="GC170",
                source=source,
                target=replacement,
            )
        ]


    def _normalise_pair_sum_nested_loops(self, source: str) -> tuple[str, list[SourceTransformation]]:
        """Canonicalise the explicit nested-loop pair-sum algorithm.

        The source gives two inclusive ``TO`` bounds expressed from
        ``LENGTH(Array)``. AJ v1.0 ranges are end-exclusive, so this rule
        records the required ``+ 1`` endpoint adjustment explicitly in the
        canonical source. The compiler may later simplify only this narrow
        length-derived adjustment when emitting Python.

        ``Array`` and ``Target`` are external dependencies of a complete
        functionless computation, so the neutral generated wrapper name
        ``unnamed_function`` is used rather than inventing a semantic name.
        """
        patterns = (
            r"(?im)^\s*INPUT\s+Array\s*,\s*Target\s*$",
            r"(?im)^\s*FOR\s+i\s*<-\s*0\s+TO\s+LENGTH(?:\s+OF|\s*\()\s*Array\)?\s*-\s*2\s*$",
            r"(?im)^\s*FOR\s+j\s*<-\s*i\s*\+\s*1\s+TO\s+LENGTH(?:\s+OF|\s*\()\s*Array\)?\s*-\s*1\s*$",
            r"(?im)^\s*IF\s+Array\[i\]\s*\+\s*Array\[j\]\s*(?:=|==)\s*Target\s+THEN\s*$",
            r"(?im)^\s*OUTPUT\s+Array\[i\]\s*,\s*Array\[j\]\s*$",
        )
        if not all(re.search(pattern, source) for pattern in patterns):
            return source, []

        replacement = """FUNCTION unnamed_function ACCEPTS(Array, Target)
    FOR i <- IN RANGE 0 TO (LENGTH OF Array - 2) + 1 DO
        FOR j <- IN RANGE i + 1 TO (LENGTH OF Array - 1) + 1 DO
            IF Array[i] + Array[j] == Target THEN
                OUTPUT CALL output_values(Array[i], Array[j])
            ENDIF
        ENDFOR
    ENDFOR
ENDFUNCTION"""

        return replacement, [
            SourceTransformation(
                line=1,
                rule="GC169",
                source=source,
                target=replacement,
            )
        ]


    def _normalise_kadane_max_sum(self, source: str) -> tuple[str, list[SourceTransformation]]:
        """Canonicalise the explicit Kadane recurrence without reconstruction.

        ``Array`` is a structured external dependency because the source indexes
        it and queries its length, so a neutral ``unnamed_function`` wrapper is
        used. The source ``TO LENGTH(Array)-1`` bound is inclusive, while AJ
        v1.0 ranges are end-exclusive; therefore the canonical AJ records the
        required ``+ 1`` adjustment explicitly. The recurrence itself is copied
        without alteration.
        """
        patterns = (
            r"(?im)^\s*INPUT\s+Array\s*$",
            r"(?im)^\s*CurrentSum\s*<-\s*Array\[0\]\s*$",
            r"(?im)^\s*MaxSum\s*<-\s*Array\[0\]\s*$",
            r"(?im)^\s*FOR\s+i\s*<-\s*1\s+TO\s+LENGTH(?:\s+OF|\s*\()\s*Array\)?\s*-\s*1\s*$",
            r"(?im)^\s*CurrentSum\s*<-\s*(?:CALL\s+)?MAX\s*\(\s*Array\[i\]\s*,\s*CurrentSum\s*\+\s*Array\[i\]\s*\)\s*$",
            r"(?im)^\s*IF\s+CurrentSum\s*>\s*MaxSum\s+THEN\s*$",
            r"(?im)^\s*MaxSum\s*<-\s*CurrentSum\s*$",
            r"(?im)^\s*OUTPUT\s+MaxSum\s*$",
        )
        if not all(re.search(pattern, source) for pattern in patterns):
            return source, []

        replacement = """FUNCTION unnamed_function ACCEPTS(Array)
    CurrentSum <- Array[0]
    MaxSum <- Array[0]

    FOR i <- IN RANGE 1 TO (LENGTH OF Array - 1) + 1 DO
        CurrentSum <- CALL max(Array[i], CurrentSum + Array[i])

        IF CurrentSum > MaxSum THEN
            MaxSum <- CurrentSum
        ENDIF
    ENDFOR

    OUTPUT MaxSum
ENDFUNCTION"""

        return replacement, [
            SourceTransformation(
                line=1,
                rule="GC171",
                source=source,
                target=replacement,
            )
        ]


    def _normalise_inventory_update_case(self, source: str) -> tuple[str, list[SourceTransformation]]:
        """Canonicalise the explicit inventory-update algorithm.

        The source exposes all four values as external dependencies and directly
        indexes ``Inventory`` with ``Item``. No inventory representation or
        validation behaviour is invented. The pipeline-supplied wrapper is
        therefore the neutral ``unnamed_function``.
        """
        patterns = (
            r"(?im)^\s*INPUT\s+Inventory\s*$",
            r"(?im)^\s*INPUT\s+TransactionType\s*$",
            r"(?im)^\s*INPUT\s+Item\s*$",
            r"(?im)^\s*INPUT\s+Quantity\s*$",
            r"(?im)^\s*IF\s+TransactionType\s*==?\s*\"Purchase\"\s+THEN\s*$",
            r"(?im)^\s*Inventory\[Item\]\s*<-\s*Inventory\[Item\]\s*-\s*Quantity\s*$",
            r"(?im)^\s*ELSE\s+IF\s+TransactionType\s*==?\s*\"Delivery\"\s+THEN\s*$",
            r"(?im)^\s*Inventory\[Item\]\s*<-\s*Inventory\[Item\]\s*\+\s*Quantity\s*$",
            r"(?im)^\s*OUTPUT\s+Inventory\s*$",
        )
        if not all(re.search(pattern, source) for pattern in patterns):
            return source, []

        replacement = """FUNCTION unnamed_function ACCEPTS(Inventory, TransactionType, Item, Quantity)
    IF TransactionType == STRING(\"Purchase\") THEN
        Inventory[Item] <- Inventory[Item] - Quantity
    ELSE IF TransactionType == STRING(\"Delivery\") THEN
        Inventory[Item] <- Inventory[Item] + Quantity
    ENDIF

    OUTPUT Inventory
ENDFUNCTION"""

        return replacement, [
            SourceTransformation(
                line=1,
                rule="GC172",
                source=source,
                target=replacement,
            )
        ]


    def _normalise_two_stack_queue(self, source: str) -> tuple[str, list[SourceTransformation]]:
        """Canonicalise the source's explicit two-stack queue algorithm.

        ``ENQUEUE`` and ``DEQUEUE`` are source-provided operation names, so
        only their missing function delimiters are recovered.  The source's
        abstract stack primitives remain visible as ``PUSH``/``POP`` calls in
        canonical AJ.  Stack creation remains an explicit abstract operation
        through ``CALL create_stack()`` rather than being re-described as an
        ``EMPTY LIST``.  Empty/non-empty predicates likewise use the abstract
        ``stack_is_empty`` compatibility intrinsic.  The Python compiler may
        lower those explicit stack operations to a list-backed representation
        as an implementation detail.

        In particular, the nested source instruction
        ``PUSH POP(Stack1) onto Stack2`` remains a nested POP-then-PUSH in AJ;
        the Python compiler may introduce a temporary solely as a lowering
        detail.
        """
        upper = source.upper()
        required = (
            "CREATE STACK1",
            "CREATE STACK2",
            "ENQUEUE(ITEM)",
            "DEQUEUE()",
            "PUSH ITEM ONTO STACK1",
            "POP(STACK1)",
            "POP(STACK2)",
        )
        if not all(fragment in upper for fragment in required):
            return source, []

        replacement = """Stack1 <- CALL create_stack()
Stack2 <- CALL create_stack()

FUNCTION ENQUEUE ACCEPTS(Item)
    CALL PUSH(Item, Stack1)
ENDFUNCTION

FUNCTION DEQUEUE ACCEPTS()
    IF CALL stack_is_empty(Stack2) THEN
        WHILE NOT CALL stack_is_empty(Stack1) DO
            CALL PUSH(CALL POP(Stack1), Stack2)
        ENDWHILE
    ENDIF

    OUTPUT CALL POP(Stack2)
ENDFUNCTION"""

        return replacement, [
            SourceTransformation(
                line=1,
                rule="GC124",
                source=source,
                target=replacement,
            )
        ]


    def _normalise_linked_cycle_detection(self, source: str) -> tuple[str, list[SourceTransformation]]:
        """Preserve Floyd cycle detection with a structured Head parameter.

        The source ``INPUT Head`` is an abstract structured dependency: the
        subsequent ``.Next`` traversal proves that Head is not ordinary text.
        The whole algorithm is therefore wrapped as ``unnamed_function(Head)`` rather
        than fabricating an interactive string input or linked-list data.

        Only the independently constrained NULL-relation corruption is
        recovered here. Assignment-position ``?`` loss is handled earlier by
        generic source-integrity rule GC193 and reaches this helper as canonical
        ``<-`` after ordinary character normalisation. The remaining two NULL
        relations recover to not-equal guards. NULL remains visible in canonical
        AJ. STOP is deliberately left for
        the generic generated-wrapper termination rule, which lowers it to RETURN.
        """
        upper = source.upper()
        required = ("SLOW", "FAST", "NEXT", "CYCLE")
        if not all(fragment in upper for fragment in required):
            return source, []
        if not re.search(r"(?i)\b(?:HEAD|SLOW|FAST)\.NEXT\b", source):
            return source, []

        original = source

        # Explicit source NULL remains visible in canonical AJ.  Generic
        # normalisation no longer rewrites it through CALL NULL(), so there is
        # no compatibility-call round-trip here.

        # The subsequent member traversal constrains these lost relations to
        # NULL guards rather than equality checks.
        source = re.sub(
            r"(?i)\bFast\s*\?\s*NULL",
            "Fast != NULL",
            source,
        )
        source = re.sub(
            r"(?i)\bFast\.Next\s*\?\s*NULL",
            "Fast.Next != NULL",
            source,
        )

        # INPUT Head denotes a supplied linked-node/reference dependency.  Do
        # not convert it to INPUT(STRING(...)); make the complete algorithm a
        # function accepting that structured value instead.
        lines = source.splitlines()
        if lines and lines[0].strip().upper() == "BEGIN":
            lines = lines[1:]
        if lines and lines[-1].strip().upper() == "END":
            lines = lines[:-1]

        input_patterns = (
            re.compile(r"(?i)^\s*INPUT\s+Head\s*$"),
            re.compile(r"(?i)^\s*Head\s*<-\s*INPUT\(STRING\(\"Enter Head\"\)\)\s*$"),
        )
        removed_input = False
        body_lines: list[str] = []
        for line in lines:
            if not removed_input and any(pattern.match(line) for pattern in input_patterns):
                removed_input = True
                continue
            body_lines.append(line)

        if not removed_input:
            return original, []

        # Remove only the wrapper indentation inherited from BEGIN/END.  The
        # relative indentation of the model-authored procedure is preserved.
        nonblank = [line for line in body_lines if line.strip()]
        common_indent = min(
            (len(line) - len(line.lstrip()) for line in nonblank),
            default=0,
        )
        if common_indent:
            body_lines = [
                line[common_indent:] if line.strip() else ""
                for line in body_lines
            ]

        while body_lines and not body_lines[0].strip():
            body_lines.pop(0)
        while body_lines and not body_lines[-1].strip():
            body_lines.pop()

        wrapped = ["FUNCTION unnamed_function ACCEPTS(Head)"]
        wrapped.extend(("    " + line) if line.strip() else "" for line in body_lines)
        wrapped.append("ENDFUNCTION")
        source = "\n".join(wrapped)

        if source == original:
            return source, []
        return source, [
            SourceTransformation(
                line=1,
                rule="GC123",
                source="Floyd structured-input and syntax recovery",
                target=source,
            )
        ]


    def _normalise_character_frequency(self, source: str) -> tuple[str, list[SourceTransformation]]:
        """Retired GC122 abstract character-frequency operationalisation.

        ``COUNT frequency of each character`` is an abstract, non-AJ v1.1
        operation.  Earlier compatibility versions expanded it into a complete
        dictionary-counting algorithm and also rewrote the downstream
        ``Frequency(Character)``/``STOP`` surface.  That supplied missing
        algorithmic operations, contrary to the semantic-preservation boundary.

        Preserve the unresolved source verbatim here.  Ordinary structural
        canonicalisation may still wrap/format the surrounding program, but no
        frequency implementation is invented and no Python should be generated
        unless the source is otherwise made valid by explicit evidence.
        """
        return source, []


    def _normalise_array_stack(self, source: str) -> tuple[str, list[SourceTransformation]]:
        """Recover implicit stack operation blocks without changing their algorithm.

        This rule is deliberately structural only.  It recognises the common
        ``CREATE Stack`` + PUSH/POP/PEEK definition idiom and makes the
        operation boundaries explicit.  ``CREATE Stack`` itself remains
        unresolved because the source supplies neither array capacity nor a
        backing representation.  The rule must preserve the source's Top
        variable, indexed reads/writes, conditions, and updates; replacing
        them with EMPTY LIST/APPEND/POP/LENGTH operations would invent a
        different implementation and violate semantic integrity.
        """
        upper = source.upper()
        required = (
            "CREATE STACK",
            "PUSH(ITEM)",
            "POP()",
            "PEEK()",
            "STACK[TOP]",
        )
        if not all(fragment in upper for fragment in required):
            return source, []

        lines = source.splitlines()
        output: list[str] = []
        in_operation = False
        changed = False

        header_re = re.compile(
            r"^(?P<indent>[ \t]*)(?:CALL\s+)?(?P<name>PUSH|POP|PEEK)\s*\((?P<args>[^)]*)\)\s*$",
            re.IGNORECASE,
        )
        create_re = re.compile(r"^(?P<indent>[ \t]*)CREATE\s+Stack\s*$", re.IGNORECASE)

        for line in lines:
            create_match = create_re.match(line)
            if create_match:
                # Preserve the abstract array creation verbatim.  The source
                # supplies neither a capacity nor a backing representation, so
                # rewriting it as ``Stack <- EMPTY LIST`` would invent a
                # dynamic-list implementation and make subsequent indexed
                # writes semantically different.
                output.append(line)
                continue

            header_match = header_re.match(line)
            if header_match:
                if in_operation:
                    output.append("ENDFUNCTION")
                name = header_match.group("name").upper()
                args = header_match.group("args").strip()
                output.append(f"FUNCTION {name} ACCEPTS({args})")
                in_operation = True
                changed = True
                continue

            output.append(line)

        if in_operation:
            output.append("ENDFUNCTION")

        if not changed:
            return source, []

        transformed = "\n".join(output)
        if source.endswith("\n"):
            transformed += "\n"

        return transformed, [
            SourceTransformation(
                line=1,
                rule="GC121",
                source=source,
                target=transformed,
            )
        ]


    def _normalise_rotated_array_search(
        self,
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        """Legacy hook; shared structural rules now handle rotated-array block repair."""
        return source, []


    # GC118/GC119 synthetic input inference was retired in v3.56.
    # Compatibility normalisation must preserve external inputs rather than
    # fabricate random matrices/lists merely to make an algorithm executable.


    def _normalise_anonymous_queue(self, source: str) -> tuple[str, list[SourceTransformation]]:
        """Resolve an unnamed queue from its explicit Queue usage.

        For the binary-tree traversal idiom, a bare INPUT Root expresses the
        algorithm's external dependency. Do not invent a textual tree encoding,
        lookup key, Node class, or child parameters. Preserve Root as the
        supplied node and wrap the algorithm body with a neutral function
        accepting Root.
        """
        if not re.search(r"(?im)^\s*CREATE\s+(?:EMPTY\s+)?QUEUE\s*$", source):
            return source, []

        dequeue_match = re.search(
            r"(?im)^\s*([A-Za-z_]\w*)\s*(?:<-|←)\s*DEQUEUE(?:\s+FROM)?\s+Queue\s*$",
            source,
        )
        dequeued_name = dequeue_match.group(1) if dequeue_match else None

        enqueue_match = re.search(
            r"(?im)^\s*ENQUEUE\s+([A-Za-z_]\w*)(?:\s+TO\s+Queue)?\s*$",
            source,
        )
        root_name = enqueue_match.group(1) if enqueue_match else None

        properties: set[str] = set()
        if dequeued_name:
            properties = {
                match.group(1).lower()
                for match in re.finditer(
                    rf"\b{re.escape(dequeued_name)}\.([A-Za-z_]\w*)\b",
                    source,
                    re.I,
                )
            }

        binary_tree_context = bool(
            root_name
            and dequeued_name
            and {"left", "right"}.issubset(properties)
        )

        output: list[str] = []
        transformations: list[SourceTransformation] = []

        for line_number, line in enumerate(source.splitlines(), start=1):
            indent = line[:len(line) - len(line.lstrip())]
            content = line.strip()
            target = line

            # INPUT Root may already have been expanded by generic recovery into
            # Root <- INPUT(STRING("Enter Root")). In this binary-tree context,
            # that string is only an unjustified prompt encoding; the dependency
            # is represented by the wrapper parameter instead.
            if binary_tree_context and root_name and (
                re.fullmatch(
                    rf"INPUT\s+{re.escape(root_name)}",
                    content,
                    re.I,
                )
                or re.fullmatch(
                    rf"{re.escape(root_name)}\s*<-\s*INPUT\(STRING\([\"']Enter\s+{re.escape(root_name)}[\"']\)\)",
                    content,
                    re.I,
                )
            ):
                target = ""
            elif re.fullmatch(r"CREATE\s+(?:EMPTY\s+)?QUEUE", content, re.I):
                target = f"{indent}Queue <- CALL create_queue()"
            elif re.fullmatch(r"ENQUEUE\s+(.+?)(?:\s+TO\s+Queue)?", content, re.I):
                match = re.fullmatch(
                    r"ENQUEUE\s+(.+?)(?:\s+TO\s+Queue)?",
                    content,
                    re.I,
                )
                target = f"{indent}CALL ENQUEUE(Queue, {match.group(1).strip()})"
            elif re.fullmatch(
                r"([A-Za-z_]\w*)\s*(?:<-|←)\s*DEQUEUE(?:\s+FROM)?\s+Queue",
                content,
                re.I,
            ):
                match = re.fullmatch(
                    r"([A-Za-z_]\w*)\s*(?:<-|←)\s*DEQUEUE(?:\s+FROM)?\s+Queue",
                    content,
                    re.I,
                )
                target = (
                    f"{indent}{match.group(1)} <- "
                    "CALL DEQUEUE(Queue)"
                )

            target = re.sub(
                r"(?i)\bQueue\s+is\s+not\s+empty\b",
                "NOT CALL queue_is_empty(Queue)",
                target,
            )
            target = re.sub(
                r"(?i)\bLENGTH\s+OF\s+Queue\s*>\s*0\b",
                "NOT CALL queue_is_empty(Queue)",
                target,
            )
            target = re.sub(
                r"(?i)\bLENGTH\s+OF\s+Queue\s*==\s*0\b",
                "CALL queue_is_empty(Queue)",
                target,
            )
            target = re.sub(
                r"(?i)\bQueue~LENGTH\b",
                "CALL queue_size(Queue)",
                target,
            )
            if dequeued_name:
                target = re.sub(
                    rf"(?i)\b{re.escape(dequeued_name)}\.([A-Za-z_]\w*)\s+exists\b",
                    rf"{dequeued_name}.\1 != NULL",
                    target,
                )

            if target != line:
                transformations.append(
                    SourceTransformation(
                        line=line_number,
                        rule="GC117",
                        source=line,
                        target=target,
                    )
                )
            if target:
                output.extend(target.splitlines())

        transformed = "\n".join(output)

        if binary_tree_context and root_name and not re.search(
            r"(?im)^\s*FUNCTION\b", transformed
        ):
            body = "\n".join(
                ("    " + line) if line.strip() else line
                for line in transformed.splitlines()
            ).rstrip()
            transformed = (
                f"FUNCTION PROCESS ACCEPTS({root_name})\n"
                f"{body}\n"
                "ENDFUNCTION"
            )
            transformations.append(
                SourceTransformation(
                    line=1,
                    rule="GC117",
                    source=f"INPUT {root_name} with binary-tree queue traversal",
                    target=f"FUNCTION PROCESS ACCEPTS({root_name})",
                )
            )

        return transformed, transformations

    def _normalise_case_blocks(self, source: str) -> tuple[str, list[SourceTransformation]]:
        """Expand simple CASE ... OF blocks into AJ IF/ELSE structures."""
        lines = source.splitlines()
        output: list[str] = []
        transformations: list[SourceTransformation] = []
        index = 0

        while index < len(lines):
            line = lines[index]
            match = re.match(r"^(\s*)CASE\s+(.+?)\s+OF\s*$", line, re.IGNORECASE)
            if not match:
                output.append(line)
                index += 1
                continue

            indent = match.group(1)
            selector = match.group(2).strip()
            branches: list[tuple[str, str]] = []
            end_index = index + 1

            while end_index < len(lines):
                candidate = lines[end_index]
                if re.match(r"^\s*ENDCASE\s*$", candidate, re.IGNORECASE):
                    break
                branch = re.match(r"^\s*(.+?)\s*:\s*(.+?)\s*$", candidate)
                if branch:
                    branches.append((branch.group(1).strip(), branch.group(2).strip()))
                elif candidate.strip():
                    branches = []
                    break
                end_index += 1

            if branches and end_index < len(lines):
                replacement: list[str] = []
                for branch_index, (value, statement) in enumerate(branches):
                    keyword = "IF" if branch_index == 0 else "ELSE IF"
                    replacement.append(f"{indent}{keyword} {selector} == {value} THEN")
                    replacement.append(f"{indent}    {statement}")
                replacement.append(f"{indent}ENDIF")
                output.extend(replacement)
                transformations.append(SourceTransformation(
                    line=index + 1,
                    rule="GC112",
                    source="\n".join(lines[index:end_index + 1]),
                    target="\n".join(replacement),
                ))
                index = end_index + 1
                continue

            output.append(line)
            index += 1

        return "\n".join(output), transformations

    @staticmethod
    def _replace_is_space_predicate_outside_quotes_and_comments(text: str) -> str:
        """Replace exact ``<identifier> is space`` predicates outside prose.

        ``space`` here denotes the single space character only.  Broader words
        such as whitespace, blank, empty, or ``a space`` are intentionally not
        accepted.  Quoted string contents and text following an unquoted ``#``
        comment marker are preserved byte-for-byte.
        """
        if text.lstrip().upper().startswith("COMMENT"):
            return text

        out: list[str] = []
        index = 0
        quote: str | None = None
        escaped = False
        pattern = re.compile(r"(?i)([A-Za-z_]\w*)\s+is\s+space\b")

        while index < len(text):
            ch = text[index]
            if quote is not None:
                out.append(ch)
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == quote:
                    quote = None
                index += 1
                continue

            if ch in {"'", '"'}:
                quote = ch
                out.append(ch)
                index += 1
                continue

            if ch == "#":
                out.append(text[index:])
                break

            if ch.isalpha() or ch == "_":
                match = pattern.match(text, index)
                if match is not None:
                    previous = text[index - 1] if index else ""
                    if not (previous.isalnum() or previous in {"_", "."}):
                        out.append(f'{match.group(1)} == CHAR(" ")')
                        index = match.end()
                        continue

            out.append(ch)
            index += 1

        return "".join(out)

    @staticmethod
    def _replace_omitted_is_not_empty_predicate_outside_quotes_and_comments(text: str) -> str:
        """Replace exact ``<identifier> NOT EMPTY`` predicates outside prose.

        This is a surface synonym for the already-supported
        ``<identifier> IS NOT EMPTY`` predicate.  It is intentionally limited
        to a simple identifier and does not reinterpret broader notions such
        as blank/null/missing, quoted text, or comments.
        """
        if text.lstrip().upper().startswith("COMMENT"):
            return text

        out: list[str] = []
        index = 0
        quote: str | None = None
        escaped = False
        pattern = re.compile(r"(?i)(?!IS\b)([A-Za-z_]\w*)\s+NOT\s+EMPTY\b")

        while index < len(text):
            ch = text[index]
            if quote is not None:
                out.append(ch)
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == quote:
                    quote = None
                index += 1
                continue

            if ch in {"'", '"'}:
                quote = ch
                out.append(ch)
                index += 1
                continue

            if ch == "#":
                out.append(text[index:])
                break

            if ch.isalpha() or ch == "_":
                match = pattern.match(text, index)
                if match is not None:
                    previous = text[index - 1] if index else ""
                    if not (previous.isalnum() or previous in {"_", "."}):
                        out.append(f"LENGTH OF {match.group(1)} > 0")
                        index = match.end()
                        continue

            out.append(ch)
            index += 1

        return "".join(out)

    def _normalise_line(
        self,
        line: str,
        swap_temp: str = "temp_var",
    ) -> tuple[list[str], list[str]]:
        indent = line[:len(line)-len(line.lstrip())]
        content = line.strip()
        rules: list[str] = []

        m = re.fullmatch(
            r"CALL\s+APPEND\s+(.+?)\s+TO\s+([A-Za-z_]\w*)",
            content,
            re.I,
        )
        if m:
            value = m.group(1).strip()
            collection = m.group(2)
            return [f"{indent}APPEND {value} TO {collection}"], ["GC143"]

        m = re.fullmatch(r"ALERT\s+(.+)", content, re.I)
        if m:
            return [f"{indent}OUTPUT {m.group(1).strip()}"], ["GC146"]

        m = re.fullmatch(
            r"([A-Za-z_]\w*)\s*<-\s*(.+?),\s*([A-Za-z_]\w*)\s*=\s*(.+)",
            content,
            re.I,
        )
        if m:
            left_name, left_value, right_name, right_value = (
                m.group(1),
                m.group(2).strip(),
                m.group(3),
                m.group(4).strip(),
            )
            return [
                f"{indent}{left_name} <- {left_value}",
                f"{indent}{right_name} <- {right_value}",
            ], ["GC149"]

        # Python-like set construction is a representational surface form of
        # the existing AJ compatibility helper.  Accept both raw ``set(x)``
        # and an already-prefixed ``CALL set(x)`` form, and accept either raw
        # ``=`` or canonical ``<-`` assignment so the recovery does not depend
        # on which generic pass happened first.
        m = re.fullmatch(
            r"([A-Za-z_]\w*)\s*(?:<-|=)\s*(?:CALL\s+)?set\((.+)\)",
            content,
            re.I,
        )
        if m:
            target = m.group(1)
            value = m.group(2).strip()
            return [f"{indent}{target} <- CALL to_set({value})"], ["GC150"]

        # Explicit negative-infinity sentinels are representational aliases of
        # the existing AJ compatibility helper.  Accept the symbolic
        # ``-infinity`` spelling and the common identifier-shaped
        # ``NEGATIVE_INFINITY`` spelling, with either raw ``=`` or canonical
        # ``<-`` assignment.  This is deliberately assignment-scoped so an
        # arbitrary identifier containing these words is never rebound.
        m = re.fullmatch(
            r"([A-Za-z_]\w*)\s*(?:<-|=)\s*(?:-\s*infinity|NEGATIVE_INFINITY)",
            content,
            re.I,
        )
        if m:
            return [
                f"{indent}{m.group(1)} <- CALL negative_infinity()"
            ], ["GC151"]

        # A bare ERROR token in an explicit RETURN position is a common
        # pseudocode sentinel surface.  The approved compatibility meaning is
        # the literal string value "ERROR", not an exception, output statement,
        # or user-defined identifier.  Keep this return-position-only so an
        # assignment such as ``status <- ERROR`` remains subject to the normal
        # unbound-identifier checks.
        if re.fullmatch(r"RETURN\s+ERROR", content, re.I):
            return [f'{indent}RETURN STRING("ERROR")'], ["GC204"]

        # A bare ERROR token in statement position is an explicit error signal.
        # Unlike GC204's ``RETURN ERROR`` sentinel recovery, this spelling
        # denotes control-flow termination, so canonicalise only the exact
        # standalone statement to AJ RAISE.  Do not create a global ERROR
        # constant or reinterpret assignments/member names containing ERROR.
        if re.fullmatch(r"ERROR", content, re.I):
            return [f'{indent}RAISE STRING("ERROR")'], ["GC217"]

        m = re.fullmatch(
            r"RETURN\s*\[(.*)\]",
            content,
            re.I,
        )
        if m:
            values = self._split_top_level_commas(m.group(1))
            return [
                f"{indent}RETURN CALL list_value({', '.join(v.strip() for v in values)})"
            ], ["GC167"]

        m = re.fullmatch(
            r"APPEND\s*\((.+)\)\s+TO\s+([A-Za-z_]\w*)",
            content,
            re.I,
        )
        if m:
            values = self._split_top_level_commas(m.group(1))
            if len(values) > 1:
                # GC221 can expose a nested tuple append during this same
                # normaliser pass.  Canonicalise the already-supported simple
                # MIN/MAX call spellings here because returning GC165 early
                # would otherwise prevent the later GC105 block from seeing
                # them.  This is pass-order completion only; no new built-in or
                # expression meaning is introduced.
                normalised_values: list[str] = []
                builtin_changed = False
                for value in values:
                    rendered = value.strip()
                    before_builtin = rendered
                    rendered = re.sub(
                        r"\bMAX\(([^,()]+),\s*([^()]*)\)",
                        r"CALL max(\1, \2)",
                        rendered,
                        flags=re.I,
                    )
                    rendered = re.sub(
                        r"\bMIN\(([^,()]+),\s*([^()]*)\)",
                        r"CALL min(\1, \2)",
                        rendered,
                        flags=re.I,
                    )
                    builtin_changed = builtin_changed or rendered != before_builtin
                    normalised_values.append(rendered)
                tuple_rules = ["GC165"]
                if builtin_changed:
                    tuple_rules.append("GC105")
                return [
                    f"{indent}APPEND TUPLE({', '.join(normalised_values)}) TO {m.group(2)}"
                ], tuple_rules

        m = re.fullmatch(
            r"APPEND\s+copy\s+of\s+(.+?)\s+TO\s+([A-Za-z_]\w*)",
            content,
            re.I,
        )
        if m:
            return [
                f"{indent}APPEND CALL copy_value({m.group(1).strip()}) TO {m.group(2)}"
            ], ["GC164"]

        m = re.fullmatch(
            r"CALL\s+RETURN\s*\((.+)\)",
            content,
            re.I,
        )
        if m:
            values = m.group(1).strip()
            return [f"{indent}RETURN TUPLE({values})"], ["GC152"]

        m = re.fullmatch(
            r"FUNCTION\s+([A-Za-z_]\w*)\s+([A-Za-z_]\w*)\s+AND\s+([A-Za-z_]\w*)",
            content,
            re.I,
        )
        if m:
            function_name = m.group(1)
            first = m.group(2)
            second = m.group(3)
            return [
                f"{indent}FUNCTION {function_name} ACCEPTS({first}, {second})"
            ], ["GC153"]

        m = re.fullmatch(
            r"CALL\s+seen_remove\((.+)\)",
            content,
            re.I,
        )
        if m:
            value = m.group(1).strip()
            return [
                f"{indent}CALL remove_from_set(seen, {value})"
            ], ["GC154"]

        if re.match(r"(?i)^CALL\s+CALL\s+", content):
            return [
                f"{indent}{re.sub(r'(?i)^CALL\\s+CALL\\s+', 'CALL ', content)}"
            ], ["GC155"]

        m = re.fullmatch(
            r"(?P<target>[A-Za-z_]\w*(?:\[[^\]]+\])*)\s*=\s*(?P<value>.+)",
            content,
        )
        if m and all(op not in content for op in ("==", "!=", "<=", ">=")):
            return [
                f"{indent}{m.group('target')} <- {m.group('value').strip()}"
            ], ["GC163"]

        if not content:
            return [line], rules

        # Legacy corpus section labels are not pseudocode. The research files
        # used for normal processing do not contain them, but historical corpus
        # exports may include lines such as "Part 3 - Pseudocode for Tasks 21-30".
        if re.fullmatch(r"(?i)Part\s+\d+\s*-\s*.+", content):
            return [], ["GC116"]

        # Raw quoted values in OUTPUT/RETURN are AJ STRING literals.
        if re.match(r"^(?:OUTPUT|RETURN)\b", content, re.I):
            before = content
            content = self._wrap_raw_strings(content)
            if content != before:
                rules.append("GC098")

        # Common semantic shorthands with direct, non-ambiguous equivalents.
        m = re.fullmatch(
            r"SORT\s+characters\s+of\s+([A-Za-z_]\w*)\s+TO\s+([A-Za-z_]\w*)",
            content,
            re.I,
        )
        if m:
            source_name, destination_name = m.group(1), m.group(2)
            return [
                f"{indent}{destination_name} <- CALL sort_characters({source_name})"
            ], rules + ["GC129"]

        m = re.fullmatch(r"SORT\s+characters\s+of\s+([A-Za-z_]\w*)", content, re.I)
        if m:
            name = m.group(1)
            return [f"{indent}{name} <- CALL sort_characters({name})"], rules + ["GC099"]
        m = re.fullmatch(r"SORT\s+([A-Za-z_]\w*)", content, re.I)
        if m:
            name = m.group(1)
            return [f"{indent}{name} <- CALL sort_value({name})"], rules + ["GC100"]
        m = re.fullmatch(r"CALL\s+APPEND\s+(.+?)\s+TO\s+([A-Za-z_]\w*)", content, re.I)
        if m:
            value = m.group(1).strip()
            collection = m.group(2)
            return [f"{indent}APPEND {value} TO {collection}"], rules + ["GC143"]

        m = re.fullmatch(
            r"([A-Za-z_]\w*)\s*<-\s*convert\s+(.+?)\s+to\s+set",
            content,
            re.I,
        )
        if m:
            target = m.group(1)
            value = m.group(2).strip()
            return [
                f"{indent}{target} <- CALL to_set({value})"
            ], rules + ["GC137"]

        m = re.fullmatch(
            r"REVERSE\s+([A-Za-z_]\w*(?:\[[^\]]+\])*)",
            content,
            re.I,
        )
        if m:
            target = m.group(1)
            # Standalone REVERSE is an imperative mutation request. Preserve
            # that operation directly instead of rebinding the target to a
            # reversed copy (which would require FOR EACH write-back to make
            # aliases into containing collections appear mutated).
            return [f"{indent}CALL reverse_list({target})"], rules + ["GC101"]
        m = re.fullmatch(r"TRANSPOSE\s+([A-Za-z_]\w*)", content, re.I)
        if m:
            name = m.group(1)
            return [f"{indent}{name} <- CALL transpose({name})"], rules + ["GC118"]

        # SWAP is expanded rather than adding new AJ grammar.
        # Accept either "SWAP a AND b" or "SWAP a, b", including indexed
        # operands such as WordList[j] and WordList[j+1].
        if re.match(r"(?i)^SWAP\s+", content):
            swap_body = re.sub(r"(?i)^SWAP\s+", "", content, count=1)
            swap_parts = re.split(r"(?i)\s+AND\s+|\s*,\s*", swap_body, maxsplit=1)
            if len(swap_parts) == 2:
                a = swap_parts[0].strip()
                b = swap_parts[1].strip()
                if a and b:
                    return [
                        f"{indent}{swap_temp} <- {a}",
                        f"{indent}{a} <- {b}",
                        f"{indent}{b} <- {swap_temp}",
                    ], rules + ["GC102"]

        before = content
        content = re.sub(r"\bEXISTS\s+IN\b", "IN", content, flags=re.I)
        if content != before:
            rules.append("GC103")

        # GC207: ``value is space`` is an exact character-value predicate
        # surface.  The approved compatibility meaning is equality with the
        # single space character, not a broad whitespace/blank/empty test.
        # Apply only outside quoted strings and inline comments so prose and
        # literal payloads remain untouched.
        before = content
        content = self._replace_is_space_predicate_outside_quotes_and_comments(content)
        if content != before:
            rules.append("GC207")

        # GC211: some pseudocode surfaces omit ``IS`` from the already-supported
        # ``identifier IS NOT EMPTY`` predicate.  Preserve exactly the same
        # empty-state meaning without broadening to blank/null/missing or
        # interpreting text inside strings/comments.
        before = content
        content = self._replace_omitted_is_not_empty_predicate_outside_quotes_and_comments(content)
        if content != before:
            rules.append("GC211")

        # Compatibility predicate spellings.  Descriptive file/folder forms only
        # reach this conversion after the early dependency-evidence guard has
        # confirmed that the exact free helper(s) are defined/imported.
        predicates = (
            (r"([A-Za-z_]\w*)\s+is\s+NOT\s+punctuation", r"NOT CALL is_punctuation(\1)"),
            (r"([A-Za-z_]\w*)\s+is\s+punctuation", r"CALL is_punctuation(\1)"),
            (r"([A-Za-z_]\w*)\s+is\s+(?:a\s+)?digit", r"CALL is_digit(\1)"),
            (r"([A-Za-z_]\w*)\s+is\s+(?:an\s+)?uppercase(?:\s+letter)?", r"CALL is_uppercase(\1)"),
            (r"([A-Za-z_]\w*)\s+is\s+(?:a\s+)?file", r"CALL is_file(\1)"),
            (r"([A-Za-z_]\w*)\s+is\s+(?:a\s+)?(?:folder|directory)", r"CALL is_directory(\1)"),
        )
        for pattern, replacement in predicates:
            changed = re.sub(pattern, replacement, content, flags=re.I)
            if changed != content:
                content = changed
                rules.append("GC104")

        # Built-in expression spellings that the AJ AST can represent as calls.
        builtins = (
            (r"\bLOWERCASE\(([^()]*)\)", r"CALL lowercase(\1)"),
            (r"\bUPPERCASE\(([^()]*)\)", r"CALL uppercase(\1)"),
            (r"\bMAX\(([^,()]+),\s*([^()]*)\)", r"CALL max(\1, \2)"),
            (r"\bMIN\(([^,()]+),\s*([^()]*)\)", r"CALL min(\1, \2)"),
        )
        for pattern, replacement in builtins:
            changed = re.sub(pattern, replacement, content, flags=re.I)
            if changed != content:
                content = changed
                rules.append("GC105")

        # Assignment form of the common SPLIT ... BY spaces idiom.
        m = re.fullmatch(r"([A-Za-z_]\w*)\s*<-\s*SPLIT\s+(.+?)\s+BY\s+spaces", content, re.I)
        if m:
            return [f"{indent}{m.group(1)} <- CALL split_on_space({m.group(2).strip()})"], rules + ["GC106"]

        # Generic descending range form missed by earlier grammar normalisation.
        m = re.fullmatch(r"FOR\s+([A-Za-z_]\w*)\s*<-\s*(.+?)\s+DOWN\s*TO\s+(.+?)(?:\s+DO)?", content, re.I)
        if m:
            end = re.sub(r"\s+DO$", "", m.group(3).strip(), flags=re.I).strip()
            return [
                f"{indent}FOR {m.group(1)} <- IN RANGE {m.group(2).strip()} TO ({end}) - 1 STEP -1 DO"
            ], rules + ["GC178"]

        return [f"{indent}{content}"], rules

    @staticmethod
    def _wrap_raw_strings(text: str) -> str:
        pattern = re.compile(r'(?<![A-Za-z_])(["\'])(.*?)(?<!\\)\1')
        out=[]; last=0
        for m in pattern.finditer(text):
            prefix=text[max(0,m.start()-8):m.start()].upper().rstrip()
            if prefix.endswith("STRING(") or prefix.endswith("CHAR("):
                continue
            out.append(text[last:m.start()])
            value=m.group(2).replace('\"','"')
            out.append(f'STRING("{value}")')
            last=m.end()
        if not out:
            return text
        out.append(text[last:])
        return ''.join(out)


class GenericGrammarNormaliser:
    """Normalises structural grammar variants observed in the six-model corpus."""

    def process(self, source: str) -> tuple[str, list[SourceTransformation]]:
        transformations = []
        processed_lines = []

        # A top-level BEGIN/END pair is only a wrapper. Remove its shared
        # indentation before normalising individual statements.
        source_lines = source.splitlines()
        non_empty = [i for i, line in enumerate(source_lines) if line.strip()]
        if (
            len(non_empty) >= 2
            and source_lines[non_empty[0]].strip().upper() == "BEGIN"
            and source_lines[non_empty[-1]].strip().upper() == "END"
        ):
            start = non_empty[0]
            end = non_empty[-1]
            inner = "\n".join(source_lines[start + 1:end])
            dedented = textwrap.dedent(inner)
            prefix = source_lines[:start]
            suffix = source_lines[end + 1:]
            rebuilt = prefix + ["BEGIN"] + dedented.splitlines() + ["END"] + suffix
            source = "\n".join(rebuilt)

        for line_number, source_line in enumerate(source.splitlines(), start=1):
            transformed_lines, rule_ids = self._normalise_line(source_line)

            if transformed_lines != [source_line]:
                target = "\n".join(transformed_lines)
                for rule_id in rule_ids:
                    transformations.append(
                        SourceTransformation(
                            line=line_number,
                            rule=rule_id,
                            source=source_line,
                            target=target,
                        )
                    )

            processed_lines.extend(transformed_lines)

        return "\n".join(processed_lines), transformations

    def _normalise_line(self, line: str) -> tuple[list[str], list[str]]:
        indent = line[: len(line) - len(line.lstrip())]
        content = line.strip()
        rules = []

        if content == "":
            return [line], rules

        if re.fullmatch(r"BEGIN", content, re.IGNORECASE):
            return [], ["GC053"]

        if re.fullmatch(r"END", content, re.IGNORECASE):
            return [], ["GC054"]

        match = re.fullmatch(r"FUNCTION\s+([A-Za-z_][A-Za-z0-9_]*)\s*\((.*?)\)\s*:?", content, re.IGNORECASE)
        if match is not None:
            return [f"{indent}FUNCTION {match.group(1)} ACCEPTS({match.group(2).strip()})"], ["GC055"]

        match = re.fullmatch(r"PROCEDURE\s+([A-Za-z_][A-Za-z0-9_]*)\s*\((.*?)\)\s*:?", content, re.IGNORECASE)
        if match is not None:
            return [f"{indent}FUNCTION {match.group(1)} ACCEPTS({match.group(2).strip()})"], ["GC056"]

        terminators = (
            (r"END\s+FUNCTION", "ENDFUNCTION", "GC057"),
            (r"END\s+PROCEDURE", "ENDFUNCTION", "GC058"),
            (r"END\s+IF", "ENDIF", "GC059"),
            (r"END\s+WHILE", "ENDWHILE", "GC060"),
            (r"END\s+FOR", "ENDFOR", "GC061"),
            # Legacy surface spelling observed in explicit class pseudocode.
            # This is terminator spelling only: no class body, state, method,
            # or constructor semantics are inferred here.
            (r"END\s+CLASS", "ENDCLASS", "GC205"),
        )
        for pattern, replacement, rule_id in terminators:
            if re.fullmatch(pattern, content, re.IGNORECASE):
                return [f"{indent}{replacement}"], [rule_id]

        if re.fullmatch(r"ELSE\s*:", content, re.IGNORECASE):
            return [f"{indent}ELSE"], ["GC062"]

        match = re.fullmatch(
            r"ELSE\s+IF\s+(.+?)\s+THEN\s+(.+?)(?:\s+THEN)?\s*:?",
            content,
            re.IGNORECASE,
        )
        if match is not None:
            condition = match.group(1).strip()
            body = match.group(2).strip()
            return [
                f"{indent}ELSE IF {condition} THEN",
                f"{indent}    {body}",
            ], ["GC130"]

        match = re.fullmatch(r"ELSE\s+(?:DO\s+)?(.+)", content, re.IGNORECASE)
        if match is not None and not re.match(r"IF\b", match.group(1), re.IGNORECASE):
            body = match.group(1).strip()
            return [
                f"{indent}ELSE",
                f"{indent}    {body}",
            ], ["GC131"]

        match = re.fullmatch(r"ELSE\s+IF\s+(.+?)(?:\s+THEN)?\s*:?", content, re.IGNORECASE)
        if match is not None:
            condition = match.group(1).strip()
            condition = re.sub(r"\s+THEN$", "", condition, flags=re.IGNORECASE).strip()
            return [f"{indent}ELSE IF {condition} THEN"], ["GC063"]

        match = re.fullmatch(
            r"IF\s+(.+?)\s+THEN\s+(.+?)(?:\s+THEN)?\s*:?",
            content,
            re.IGNORECASE,
        )
        if match is not None:
            condition = match.group(1).strip()
            body = match.group(2).strip()
            return [
                f"{indent}IF {condition} THEN",
                f"{indent}    {body}",
            ], ["GC132"]

        match = re.fullmatch(r"IF\s+(.+?)\s+THEN\s+RETURN\s+(.+)", content, re.IGNORECASE)
        if match is not None:
            condition = match.group(1).strip()
            value = match.group(2).strip().rstrip(":")
            return [
                f"{indent}IF {condition} THEN",
                f"{indent}    RETURN {value}",
                f"{indent}ENDIF",
            ], ["GC064"]

        match = re.fullmatch(r"IF\s+(.+?)\s+RETURN\s+(.+)", content, re.IGNORECASE)
        if match is not None:
            condition = match.group(1).strip().rstrip(":")
            value = match.group(2).strip()
            return [
                f"{indent}IF {condition} THEN",
                f"{indent}    RETURN {value}",
                f"{indent}ENDIF",
            ], ["GC065"]

        match = re.fullmatch(r"IF\s+(.+?)\s*:?", content, re.IGNORECASE)
        if match is not None:
            condition = match.group(1).strip()
            condition = re.sub(r"\s+THEN$", "", condition, flags=re.IGNORECASE).strip()
            return [f"{indent}IF {condition} THEN"], ["GC066"]

        match = re.fullmatch(r"WHILE\s+(.+?)\s*:?", content, re.IGNORECASE)
        if match is not None:
            condition = match.group(1).strip()
            condition = re.sub(r"\s+DO$", "", condition, flags=re.IGNORECASE).strip()
            return [f"{indent}WHILE {condition} DO"], ["GC067"]

        match = re.fullmatch(r"FOR\s+EACH\s+([A-Za-z_][A-Za-z0-9_]*)\s+IN\s+(.+?)\s*:?", content, re.IGNORECASE)
        if match is not None:
            collection = re.sub(r"\s+DO$", "", match.group(2).strip(), flags=re.IGNORECASE).strip()
            return [f"{indent}FOR EACH {match.group(1)} IN {collection} DO"], ["GC068"]

        match = re.fullmatch(r"FOR\s+([A-Za-z_][A-Za-z0-9_]*)\s+IN\s+(.+?)\s*:?", content, re.IGNORECASE)
        if match is not None:
            collection = re.sub(r"\s+DO$", "", match.group(2).strip(), flags=re.IGNORECASE).strip()
            return [f"{indent}FOR EACH {match.group(1)} IN {collection} DO"], ["GC069"]

        # Canonical AJ range loops are already normalised. Leave them
        # untouched so later generic FOR rules remain idempotent.
        if re.fullmatch(
            r"FOR\s+[A-Za-z_][A-Za-z0-9_]*\s*<-\s*IN\s+RANGE\s+.+?\s+TO\s+.+?(?:\s+STEP\s+.+?)?\s+DO",
            content,
            re.IGNORECASE,
        ):
            return [line], rules

        # Generic source ranges use inclusive TO semantics. AJ v1.0 RANGE
        # endpoints are end-exclusive, so preserve the source endpoint
        # explicitly at the source->AJ boundary by adding + 1 exactly once.
        # Already-canonical ``IN RANGE`` lines are returned above unchanged.
        # Descending forms use the direction-aware counterpart: an inclusive
        # source endpoint becomes ``(end) - 1`` with ``STEP -1``.
        match = re.fullmatch(r"FOR\s+([A-Za-z_][A-Za-z0-9_]*)\s+FROM\s+(.+?)\s+(DOWN\s*TO|DOWNTO|TO)\s+(.+?)\s*(?:DO)?\s*:?", content, re.IGNORECASE)
        if match is not None:
            iterator = match.group(1)
            start = match.group(2).strip()
            direction = match.group(3).upper().replace(" ", "")
            end = re.sub(r"\s+DO$", "", match.group(4).strip(), flags=re.IGNORECASE).strip()
            if direction == "DOWNTO":
                return [
                    f"{indent}FOR {iterator} <- IN RANGE {start} TO ({end}) - 1 STEP -1 DO"
                ], ["GC178"]

            # One corpus form writes an implicit descending traversal as
            # ``FROM LENGTH(x) - 1 TO 0`` without spelling DOWNTO.  The start
            # is explicitly the final valid index and the destination is zero,
            # so direction is structurally determined by the endpoints.  Keep
            # this recovery narrow; arbitrary ``FROM a TO b`` expressions are
            # not guessed to be descending.
            if (
                re.fullmatch(r"LENGTH(?:\s+OF)?\s+.+?\s*-\s*1", start, re.IGNORECASE)
                and re.fullmatch(r"0", end)
            ):
                return [
                    f"{indent}FOR {iterator} <- IN RANGE {start} TO ({end}) - 1 STEP -1 DO"
                ], ["GC177"]

            return [f"{indent}FOR {iterator} <- IN RANGE {start} TO ({end}) + 1 DO"], ["GC176"]

        match = re.fullmatch(r"FOR\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:<-|=)\s*(.+?)\s+TO\s+(.+?)\s*:?", content, re.IGNORECASE)
        if match is not None:
            start = match.group(2).strip()
            end = re.sub(r"\s+DO$", "", match.group(3).strip(), flags=re.IGNORECASE).strip()
            return [f"{indent}FOR {match.group(1)} <- IN RANGE {start} TO ({end}) + 1 DO"], ["GC176"]

        if content.endswith(":"):
            return [f"{indent}{content[:-1].rstrip()}"], ["GC072"]

        return [line], rules



class GenericRecoveryNormaliser:
    """Applies corpus-derived parser recovery rules after grammar normalisation."""

    RESERVED_IDENTIFIER_RENAMES = {
        "char": "__reserved_keyword__char",
        "list": "__reserved_keyword__List",
    }

    KNOWN_CALL_WORDS = {
        "FUNCTION", "INPUT", "OUTPUT", "RETURN", "BOOLEAN", "STRING", "CHAR",
        "INTEGER", "FLOAT", "LIST", "TUPLE", "JOIN", "IF", "WHILE",
        "FOR", "CALL", "LENGTH", "COMMENT", "LOWERCASE", "UPPERCASE",
        "SPLIT", "REVERSE", "SWAP", "MAX", "MIN", "TO",
    }

    @staticmethod
    def _split_unquoted_slash_comment(content: str) -> tuple[str, str] | None:
        """Return executable/comment parts for the first unquoted ``//``."""
        quote: str | None = None
        escape = False
        index = 0
        while index < len(content) - 1:
            char = content[index]
            if quote is not None:
                if escape:
                    escape = False
                elif char == "\\":
                    escape = True
                elif char == quote:
                    quote = None
                index += 1
                continue

            if char in {"'", '"'}:
                quote = char
                index += 1
                continue

            if content[index:index + 2] == "//":
                return content[:index], content[index + 2:]
            index += 1
        return None

    def process(self, source: str) -> tuple[str, list[SourceTransformation]]:
        transformations: list[SourceTransformation] = []
        lines = source.splitlines()
        expanded: list[tuple[int, str]] = []

        for line_number, line in enumerate(lines, start=1):
            before = line
            produced, rules = self._normalise_line(line)
            for rule_id in rules:
                transformations.append(
                    SourceTransformation(
                        line=line_number,
                        rule=rule_id,
                        source=before,
                        target="\\n".join(produced),
                    )
                )
            for produced_line in produced:
                expanded.append((line_number, produced_line))

        closed_lines, closure_transforms = self._insert_indentation_closures(expanded)
        transformations.extend(closure_transforms)

        closed_lines, wrapper_transform = self._wrap_functionless_return_program(closed_lines)
        if wrapper_transform is not None:
            transformations.append(wrapper_transform)

        return "\n".join(closed_lines), transformations

    def _wrap_functionless_return_program(
        self,
        lines: list[str],
    ) -> tuple[list[str], SourceTransformation | None]:
        has_function = any(
            line.strip().upper().startswith(("FUNCTION ", "CLASS "))
            for line in lines
        )
        has_return = any(
            line.strip().upper().startswith("RETURN ")
            for line in lines
        )

        if has_function or not has_return:
            return lines, None

        body = []
        for line in lines:
            if line.strip():
                body.append("    " + line)
            else:
                body.append(line)

        wrapped = ["FUNCTION generic_algorithm ACCEPTS()"]
        wrapped.extend(body)
        wrapped.append("ENDFUNCTION")
        wrapped.append("CALL generic_algorithm()")

        return wrapped, SourceTransformation(
            line=None,
            rule="GC086",
            source="Functionless program containing top-level RETURN",
            target="Wrapped in FUNCTION generic_algorithm ACCEPTS()",
        )

    def _normalise_line(self, line: str) -> tuple[list[str], list[str]]:
        indent = line[: len(line) - len(line.lstrip())]
        content = line.strip()
        rules: list[str] = []

        m = re.fullmatch(
            r"CALL\s+APPEND\s+(.+?)\s+TO\s+([A-Za-z_]\w*)",
            content,
            re.I,
        )
        if m:
            value = m.group(1).strip()
            collection = m.group(2)
            return [f"{indent}APPEND {value} TO {collection}"], rules + ["GC143"]

        slash_comment = self._split_unquoted_slash_comment(content)
        if slash_comment is not None and not content.startswith("//"):
            code, _comment = slash_comment
            content = code.rstrip()
            rules.append("GC135")

        if content == "":
            return [line], rules

        m = re.fullmatch(
            r"CALL\s+APPEND\s+(.+?)\s+TO\s+([A-Za-z_]\w*)",
            content,
            re.I,
        )
        if m:
            value = m.group(1).strip()
            collection = m.group(2)
            return [f"{indent}APPEND {value} TO {collection}"], rules + ["GC143"]

        if re.match(r"(?i)^Part\s+\d+\s*-", content):
            return [], ["GC113"]

        if content.startswith("#"):
            return [f"{indent}COMMENT {content[1:].strip()}"], ["GC073"]
        if content.startswith("//"):
            return [f"{indent}COMMENT {content[2:].strip()}"], ["GC074"]

        # Standalone generic input declarations become explicit AJ INPUT assignments.
        m = re.fullmatch(r"INPUT\s+(.+)", content, re.IGNORECASE)
        if m and "(" not in m.group(1):
            names = [x.strip() for x in m.group(1).split(",") if x.strip()]
            if names and all(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", x) for x in names):
                out = []
                for name in names:
                    safe_name = self.RESERVED_IDENTIFIER_RENAMES.get(name.lower(), name)
                    out.append(f'{indent}{safe_name} <- INPUT(STRING("Enter {name}"))')
                return out, ["GC075"]

        # Rename identifiers that collide with AJ literal/type keywords.
        # Apply only outside quoted strings, and do not rewrite canonical
        # constructs such as LIST OF.
        renamed_parts = re.split(r'("(?:[^"\\]|\\.)*")', content)
        for part_index in range(0, len(renamed_parts), 2):
            part = renamed_parts[part_index]
            for source_name, target_name in self.RESERVED_IDENTIFIER_RENAMES.items():
                if source_name.lower() == "list":
                    pattern = rf"(?<!EMPTY )\b{re.escape(source_name)}\b(?!\s+OF\b|\s*\()"
                elif source_name.lower() == "char":
                    # Preserve the built-in CHAR(...) conversion while escaping
                    # only identifiers named char.
                    pattern = rf"\b{re.escape(source_name)}\b(?!\s*\()"
                else:
                    pattern = rf"(?<!EMPTY )\b{re.escape(source_name)}\b"
                part = re.sub(pattern, target_name, part, flags=re.IGNORECASE)
            renamed_parts[part_index] = part
        renamed = "".join(renamed_parts)
        if renamed != content:
            content = renamed
            rules.append("GC076")

        # Generic ADD <value> TO <collection> is the same collection
        # insertion operation represented canonically by APPEND.
        add_before = content
        content = re.sub(
            r"(?i)^ADD\s+(.+?)\s+TO\s+(.+)$",
            r"APPEND \1 TO \2",
            content,
        )
        if content != add_before:
            rules.append("GC114")

        # Generic loop-exit phrases map directly to AJ BREAK.
        exit_before = content
        content = re.sub(r"(?i)^EXIT\s+(?:FOR|WHILE|LOOP)$", "BREAK", content)
        if content != exit_before:
            rules.append("GC111")

        # Bare booleans are valid generic pseudocode but AJ expects BOOLEAN(...).
        boolean_before = content
        content = re.sub(r"(?<!BOOLEAN\()\bTRUE\b", "BOOLEAN(True)", content, flags=re.IGNORECASE)
        content = re.sub(r"(?<!BOOLEAN\()\bFALSE\b", "BOOLEAN(False)", content, flags=re.IGNORECASE)
        if content != boolean_before:
            rules.append("GC077")

        # Multiple simple assignments on one line.
        pieces = self._split_top_level_commas(content)
        if len(pieces) > 1 and all("<-" in piece for piece in pieces):
            assignment_lines = []
            valid = True
            for piece in pieces:
                if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*(?:\[[^\]]+\])?\s*<-\s*.+$", piece.strip()):
                    valid = False
                    break
                assignment_lines.append(f"{indent}{piece.strip()}")
            if valid:
                return assignment_lines, rules + ["GC078"]

        # Chained assignment: a <- b <- expression.
        #
        # GC079 expands the chain into two ordinary AJ assignments.  If the
        # shared RHS is an explicit negative-infinity sentinel, complete the
        # already-approved GC151 representation recovery here as well.  GC151
        # normally runs earlier in this same line pass, so without this narrow
        # composition the new assignment exposed by GC079 would retain the
        # non-AJ ``-INFINITY`` token and later compile as an unbound Python
        # identifier.  Do not recursively re-normalise arbitrary generated
        # lines: only this exact GC151 assignment surface is replayed.
        m = re.fullmatch(r"([A-Za-z_]\w*)\s*<-\s*([A-Za-z_]\w*)\s*<-\s*(.+)", content)
        if m:
            shared_rhs = m.group(3).strip()
            chained_rules = rules + ["GC079"]
            if re.fullmatch(
                r"(?:-\s*infinity|NEGATIVE_INFINITY)",
                shared_rhs,
                re.I,
            ):
                shared_rhs = "CALL negative_infinity()"
                chained_rules.append("GC151")
            return [
                f"{indent}{m.group(2)} <- {shared_rhs}",
                f"{indent}{m.group(1)} <- {m.group(2)}",
            ], chained_rules

        # AJ RETURN is a single-expression statement, so multi-value RETURN
        # remains tuple data. OUTPUT needs a stricter distinction: an explicit
        # parenthesised tuple is tuple data, while a bare comma-separated source
        # OUTPUT supplies multiple output arguments.  Preserve that distinction
        # with the output-only compatibility intrinsic ``output_values``; the
        # Python compiler lowers it to ``print(arg1, arg2, ...)`` without
        # changing genuine ``OUTPUT TUPLE(...)`` semantics.
        m = re.fullmatch(r"RETURN\s+(.+)", content, re.IGNORECASE)
        if m:
            vals = self._split_statement_values(m.group(1))
            if len(vals) > 1:
                content = f"RETURN TUPLE({', '.join(v.strip() for v in vals)})"
                rules.append("GC080")
        m = re.fullmatch(r"OUTPUT\s+(.+)", content, re.IGNORECASE)
        if m:
            payload = m.group(1).strip()
            top_level_values = self._split_top_level_commas(payload)
            if len(top_level_values) > 1:
                content = (
                    "OUTPUT CALL output_values("
                    + ", ".join(value.strip() for value in top_level_values)
                    + ")"
                )
                rules.append("GC081")
            else:
                tuple_values = self._split_statement_values(payload)
                if len(tuple_values) > 1:
                    content = f"OUTPUT TUPLE({', '.join(v.strip() for v in tuple_values)})"
                    rules.append("GC081")

        # Python-like ``list(expression)`` is an explicit collection-constructor
        # surface.  AJ reserves LIST as a keyword, so preserve the supplied
        # operation through the existing compatibility helper before generic
        # call-prefixing/tokenisation sees it.  GC201 is deliberately free-call
        # only (never object.list(...)) and requires exactly one top-level
        # argument; nested calls/indexing inside that argument are permitted.
        list_before = content
        content = self._normalise_free_list_constructor_calls(content)
        if content != list_before:
            rules.append("GC201")

        # GC209: free ``array(value)`` is an explicit ARRAY conversion
        # surface. Preserve that source abstraction through the ``to_array``
        # compatibility intrinsic; Python may still use list storage as the
        # compiler-level implementation detail. The rule remains limited to a
        # free single-argument call. Member methods, zero/multi-argument calls,
        # quoted text, and comments remain untouched.
        array_before = content
        content = self._normalise_free_array_constructor_calls(content)
        if content != array_before:
            rules.append("GC209")

        # GC210: a free one-argument ``join(collection)`` conventionally joins
        # the supplied collection with an empty separator.  Canonical AJ makes
        # that separator explicit.  Two-argument JOIN is already native AJ and
        # is left unchanged; member methods and non-single-argument calls are
        # outside this recovery boundary.
        join_before = content
        content = self._normalise_free_one_argument_join_calls(content)
        if content != join_before:
            rules.append("GC210")

        # GC233: explicit free ``SQUARE_ROOT(value)`` is a mathematical
        # exponentiation surface supplied by the source.  AJ v1.1 already
        # represents exponentiation with EXP, so preserve exactly that
        # operation as ``(value EXP 0.5)``.  This rule is expression-only: it
        # must not rewrite a routine declaration named SQUARE_ROOT, a member
        # method, or a zero/multi-argument call.  In particular, it does not
        # add integer/floor coercion when the resulting value is later used as
        # a range bound; any such type requirement remains separately visible.
        square_root_before = content
        if not re.match(r"(?i)^(?:FUNCTION|METHOD|CONSTRUCTOR|CLASS)\b", content):
            content = self._normalise_free_single_argument_call(
                content,
                call_name="SQUARE_ROOT",
                replacement=lambda argument: f"({argument} EXP 0.5)",
            )
        if content != square_root_before:
            rules.append("GC233")

        # GC234: explicit free single-argument character-class predicates map
        # only to the already-supported compatibility intrinsics.  This is a
        # spelling/representation recovery for source calls such as
        # IS_DIGIT(value) and IS_UPPERCASE(value); declarations, member
        # methods, quoted text, and zero/multi-argument calls remain untouched.
        predicate_before = content
        if not re.match(r"(?i)^(?:FUNCTION|METHOD|CONSTRUCTOR|CLASS)\b", content):
            content = self._normalise_free_single_argument_call(
                content,
                call_name="IS_DIGIT",
                replacement=lambda argument: f"CALL is_digit({argument})",
            )
            content = self._normalise_free_single_argument_call(
                content,
                call_name="IS_UPPERCASE",
                replacement=lambda argument: f"CALL is_uppercase({argument})",
            )
        if content != predicate_before:
            rules.append("GC234")

        # GC238: explicit free single-argument ConvertToSet(value) is a direct
        # collection-conversion surface supplied by the source.  Preserve it
        # through the existing to_set compatibility intrinsic so deterministic
        # Python lowering uses set(value).  This is deliberately limited to a
        # free call with exactly one balanced argument; declarations, member
        # methods, quoted text, and zero/multi-argument calls remain untouched.
        convert_to_set_before = content
        if not re.match(r"(?i)^(?:FUNCTION|METHOD|CONSTRUCTOR|CLASS)\b", content):
            content = self._normalise_free_single_argument_call(
                content,
                call_name="ConvertToSet",
                replacement=lambda argument: f"CALL to_set({argument})",
            )
        if content != convert_to_set_before:
            rules.append("GC238")

        # Explicit object.member notation is semantic evidence of property
        # access and must be preserved for the AST/compiler.
        # Prefix generic function calls with CALL so the AJ expression parser can represent them.
        call_before = content
        content = self._prefix_generic_calls(content)
        if content != call_before:
            rules.append("GC083")

        return [f"{indent}{content}"], rules

    @classmethod
    def _normalise_free_list_constructor_calls(cls, content: str) -> str:
        """Canonicalise free Python-like list(value) calls to CALL to_list(value).

        This is syntax-surface recovery only.  It does not touch member methods
        (``object.list(...)``), zero-argument calls, or calls with more than one
        top-level argument.  A balanced scan is used so an explicit single
        argument may itself contain nested calls, indexing, tuples, or strings.
        """
        if re.match(r"(?i)^COMMENT\b", content):
            return content

        pattern = re.compile(r"(?i)(?:\bCALL\s+)?\blist\s*\(")
        offset = 0
        while True:
            match = pattern.search(content, offset)
            if match is None:
                break

            # Ignore constructor-looking text inside quoted strings.
            quote: str | None = None
            escape = False
            for ch in content[:match.start()]:
                if quote is not None:
                    if escape:
                        escape = False
                    elif ch == "\\":
                        escape = True
                    elif ch == quote:
                        quote = None
                elif ch in "'\"":
                    quote = ch
            if quote is not None:
                offset = match.end()
                continue

            # Do not reinterpret a member method, allowing whitespace around '.'.
            prefix_text = content[:match.start()]
            prior_nonspace = prefix_text.rstrip()[-1:] if prefix_text.rstrip() else ""
            if prior_nonspace == ".":
                offset = match.end()
                continue

            open_index = content.find("(", match.start(), match.end())
            if open_index < 0:
                offset = match.end()
                continue

            depth = 0
            quote: str | None = None
            escape = False
            close_index: int | None = None
            for index in range(open_index, len(content)):
                ch = content[index]
                if quote is not None:
                    if escape:
                        escape = False
                    elif ch == "\\":
                        escape = True
                    elif ch == quote:
                        quote = None
                    continue
                if ch in "'\"":
                    quote = ch
                    continue
                if ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                    if depth == 0:
                        close_index = index
                        break
                    if depth < 0:
                        break

            if close_index is None:
                offset = match.end()
                continue

            argument = content[open_index + 1:close_index].strip()
            values = cls._split_top_level_commas(argument) if argument else []
            if len(values) != 1:
                offset = close_index + 1
                continue

            replacement = f"CALL to_list({argument})"
            content = content[:match.start()] + replacement + content[close_index + 1:]
            offset = match.start() + len(replacement)

        return content

    @classmethod
    def _normalise_free_array_constructor_calls(cls, content: str) -> str:
        """Canonicalise free ``array(value)`` calls to ``CALL to_array(value)``.

        The compatibility intrinsic preserves the source-declared ARRAY
        abstraction. Python may lower it to ``list(value)`` as a mutable
        sequence backing, but canonical AJ no longer renames the operation as a
        LIST conversion. It applies only to a free call with exactly one
        balanced top-level argument and never to member methods or quoted/comment
        text.
        """
        return cls._normalise_free_single_argument_call(
            content,
            call_name="array",
            replacement=lambda argument: f"CALL to_array({argument})",
        )

    @classmethod
    def _normalise_free_one_argument_join_calls(cls, content: str) -> str:
        """Canonicalise free ``join(values)`` to ``JOIN(values, EMPTY STRING)``.

        Native/two-argument AJ JOIN remains unchanged.  This recovery applies
        only to a free single-argument call so it cannot guess separators for
        other arities or reinterpret object-specific ``.join(...)`` methods.
        """
        return cls._normalise_free_single_argument_call(
            content,
            call_name="join",
            replacement=lambda argument: f"JOIN({argument}, EMPTY STRING)",
        )

    @classmethod
    def _normalise_free_single_argument_call(
        cls,
        content: str,
        *,
        call_name: str,
        replacement,
    ) -> str:
        """Rewrite one balanced free call while respecting strings and members."""
        if re.match(r"(?i)^COMMENT\b", content):
            return content

        pattern = re.compile(rf"(?i)(?:\bCALL\s+)?\b{re.escape(call_name)}\s*\(")
        offset = 0
        while True:
            match = pattern.search(content, offset)
            if match is None:
                break

            quote: str | None = None
            escape = False
            for ch in content[:match.start()]:
                if quote is not None:
                    if escape:
                        escape = False
                    elif ch == "\\":
                        escape = True
                    elif ch == quote:
                        quote = None
                elif ch in "'\"":
                    quote = ch
            if quote is not None:
                offset = match.end()
                continue

            prefix_text = content[:match.start()]
            prior_nonspace = prefix_text.rstrip()[-1:] if prefix_text.rstrip() else ""
            if prior_nonspace == ".":
                offset = match.end()
                continue

            open_index = content.find("(", match.start(), match.end())
            if open_index < 0:
                offset = match.end()
                continue

            depth = 0
            quote = None
            escape = False
            close_index: int | None = None
            for index in range(open_index, len(content)):
                ch = content[index]
                if quote is not None:
                    if escape:
                        escape = False
                    elif ch == "\\":
                        escape = True
                    elif ch == quote:
                        quote = None
                    continue
                if ch in "'\"":
                    quote = ch
                    continue
                if ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                    if depth == 0:
                        close_index = index
                        break
                    if depth < 0:
                        break

            if close_index is None:
                offset = match.end()
                continue

            argument = content[open_index + 1:close_index].strip()
            values = cls._split_top_level_commas(argument) if argument else []
            if len(values) != 1:
                offset = close_index + 1
                continue

            rendered = replacement(argument)
            content = content[:match.start()] + rendered + content[close_index + 1:]
            offset = match.start() + len(rendered)

        return content

    def _prefix_generic_calls(self, content: str) -> str:
        # Avoid declarations and already canonical CALL expressions.
        if re.match(
            r"^(FUNCTION|METHOD|CONSTRUCTOR|CLASS|ENDCLASS|ENDMETHOD|ENDCONSTRUCTOR|COMMENT)\b",
            content,
            re.IGNORECASE,
        ):
            return content
        pattern = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(")
        offset = 0
        while True:
            m = pattern.search(content, offset)
            if not m:
                break
            name = m.group(1)
            prefix = content[max(0, m.start()-6):m.start()].upper()
            before = content[:m.start()].rstrip()
            if (
                name.upper() in self.KNOWN_CALL_WORDS
                or prefix.endswith("CALL ")
                or before.endswith(".")
            ):
                offset = m.end()
                continue
            content = content[:m.start()] + "CALL " + content[m.start():]
            offset = m.end() + 5
        return content


    @classmethod
    def _split_statement_values(cls, text: str) -> list[str]:
        """Delegate RETURN/OUTPUT tuple-surface splitting to shared machinery."""
        return _split_statement_values_shared(text)

    @staticmethod
    def _unwrap_single_outer_parentheses(text: str) -> str | None:
        return _unwrap_single_outer_parentheses_shared(text)

    @staticmethod
    def _split_top_level_commas(text: str) -> list[str]:
        return _split_top_level_commas_shared(text)

    def _insert_indentation_closures(self, expanded: list[tuple[int, str]]) -> tuple[list[str], list[SourceTransformation]]:
        output: list[str] = []
        transforms: list[SourceTransformation] = []
        stack: list[tuple[int, str, int]] = []
        opener_patterns = (
            (re.compile(r"^FUNCTION\b", re.I), "ENDFUNCTION"),
            (re.compile(r"^IF\b.*\bTHEN$", re.I), "ENDIF"),
            (re.compile(r"^WHILE\b.*\bDO$", re.I), "ENDWHILE"),
            (re.compile(r"^FOR\b.*\bDO$", re.I), "ENDFOR"),
        )
        explicit = {"ENDFUNCTION", "ENDIF", "ENDWHILE", "ENDFOR"}

        for line_number, line in expanded:
            content=line.strip()
            if not content:
                output.append(line); continue
            indent=len(line)-len(line.lstrip())
            upper=content.upper()

            # COMMENT is opaque, non-executable text. It must never open,
            # close, or otherwise influence indentation-based block recovery.
            if upper.startswith("COMMENT"):
                output.append(line)
                continue

            continuation = upper == "ELSE" or upper.startswith("ELSE IF ")

            if upper in explicit:
                while stack and stack[-1][1] != upper:
                    i, closer, opened_line = stack.pop()
                    output.append(" " * i + closer)
                    transforms.append(SourceTransformation(line=line_number, rule="GC084", source="", target=closer))
                if stack and stack[-1][1] == upper:
                    stack.pop()
                output.append(line)
                continue

            while stack and indent <= stack[-1][0] and not (continuation and stack[-1][1] == "ENDIF" and indent == stack[-1][0]):
                i, closer, opened_line = stack.pop()
                output.append(" " * i + closer)
                transforms.append(SourceTransformation(line=line_number, rule="GC084", source="", target=closer))

            output.append(line)
            for pattern, closer in opener_patterns:
                if pattern.match(content):
                    stack.append((indent, closer, line_number))
                    break

        while stack:
            i, closer, opened_line = stack.pop()
            output.append(" " * i + closer)
            transforms.append(SourceTransformation(line=opened_line, rule="GC084", source="", target=closer))
        return output, transforms


@dataclass
class GenericLineToken:
    """Represents one classified line of generic pseudocode."""

    line_number: int
    indentation: str
    content: str
    category: str


class GenericPseudocodeLexer:
    """Classifies common generic pseudocode statements without parsing them."""

    def tokenise(self, source: str) -> list[GenericLineToken]:
        """Converts generic pseudocode into classified line tokens."""

        tokens = []
        source_lines = source.splitlines()

        for line_number, source_line in enumerate(source_lines, start=1):
            indentation = source_line[: len(source_line) - len(source_line.lstrip())]
            content = source_line.strip()
            category = self._classify_line(
                content=content,
            )

            line_token = GenericLineToken(
                line_number=line_number,
                indentation=indentation,
                content=content,
                category=category,
            )

            tokens.append(
                line_token
            )

        return tokens

    def _classify_line(self, content: str) -> str:
        """Returns the recognised category for one source line."""

        upper_content = content.upper()

        if not content:
            return "BLANK"

        if re.match(r"^SET\s+.+?\s+TO\s+.+$", content, re.IGNORECASE):
            return "SET_ASSIGNMENT"

        if re.match(r"^(PRINT|DISPLAY)\s+.+$", content, re.IGNORECASE):
            return "OUTPUT"

        if upper_content == "END IF":
            return "END_IF"

        if upper_content == "END WHILE":
            return "END_WHILE"

        if re.match(r"^NEXT(?:\s+\w+)?$", content, re.IGNORECASE):
            return "NEXT"

        if re.match(r"^IF\s+.+$", content, re.IGNORECASE):
            return "IF"

        if re.match(r"^WHILE\s+.+$", content, re.IGNORECASE):
            return "WHILE"

        if re.match(r"^FOR\s+EACH\s+\w+\s+IN\s+.+$", content, re.IGNORECASE):
            return "FOR_EACH"

        if self._is_simple_assignment(content):
            return "EQUALS_ASSIGNMENT"

        return "UNCHANGED"

    def _is_simple_assignment(self, content: str) -> bool:
        """Identifies assignment equals without confusing comparison operators."""

        assignment_pattern = r"^[A-Za-z_][A-Za-z0-9_]*(?:\[[^\]]+\])?\s*=\s*.+$"

        if not re.match(assignment_pattern, content):
            return False

        comparison_operators = [
            "==",
            "!=",
            "<=",
            ">=",
        ]

        for comparison_operator in comparison_operators:
            if comparison_operator in content:
                return False

        return True


class StrictPseudocodeProcessor:
    """Performs only non-semantic AJ Dialect source cleanup."""

    def process(
        self,
        source: str,
        *,
        include_member_identifier_evidence: bool = True,
    ) -> PseudocodeProcessingResult:
        """Processes source using strict, auditable cleanup rules."""

        processed_source = source
        transformations = []

        normalised_line_endings = processed_source.replace("\r\n", "\n").replace("\r", "\n")

        if normalised_line_endings != processed_source:
            transformations.append(
                SourceTransformation(
                    line=None,
                    rule="NORMALISE_LINE_ENDINGS",
                    source="Mixed platform line endings",
                    target="Unix line endings",
                )
            )

            processed_source = normalised_line_endings

        processed_source, fence_transformations = self._remove_markdown_fences(
            source=processed_source,
        )
        transformations.extend(
            fence_transformations
        )

        source_lines = processed_source.splitlines()
        normalised_lines = []

        for line_number, source_line in enumerate(source_lines, start=1):
            transformed_line = source_line.rstrip()

            if transformed_line != source_line:
                transformations.append(
                    SourceTransformation(
                        line=line_number,
                        rule="REMOVE_TRAILING_WHITESPACE",
                        source=source_line,
                        target=transformed_line,
                    )
                )

            arrow_normalised_line = transformed_line.replace("←", "<-")

            if arrow_normalised_line != transformed_line:
                transformations.append(
                    SourceTransformation(
                        line=line_number,
                        rule="NORMALISE_ASSIGNMENT_ARROW",
                        source=transformed_line,
                        target=arrow_normalised_line,
                    )
                )

            normalised_lines.append(
                arrow_normalised_line
            )

        processed_source = "\n".join(normalised_lines)

        processed_source, reserved_identifier_transformations = (
            _escape_proven_reserved_identifiers(
                processed_source,
                include_member_evidence=include_member_identifier_evidence,
            )
        )
        transformations.extend(reserved_identifier_transformations)

        return PseudocodeProcessingResult(
            profile=PseudocodeProfile.AJ_DIALECT_STRICT,
            original_source=source,
            processed_source=processed_source,
            transformations=transformations,
        )

    def _remove_markdown_fences(
        self,
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        """Removes a surrounding Markdown code fence when present."""

        source_lines = source.splitlines()
        transformations = []

        if len(source_lines) < 2:
            return source, transformations

        first_line = source_lines[0].strip()
        final_line = source_lines[-1].strip()

        if first_line.startswith("```") and final_line == "```":
            transformed_source = "\n".join(source_lines[1:-1])

            transformations.append(
                SourceTransformation(
                    line=None,
                    rule="REMOVE_MARKDOWN_CODE_FENCE",
                    source=f"{first_line} ... {final_line}",
                    target="Code-fence contents",
                )
            )

            return transformed_source, transformations

        return source, transformations


@dataclass(frozen=True)
class EvidenceBackedGlyphReplacement:
    """One exact lossy-source relation and its independently evidenced glyph."""

    evidence_id: str
    line_pattern: str
    recovered_glyph: str


@dataclass(frozen=True)
class EvidenceBackedGlyphRecovery:
    """Recognised source signature plus all relational glyph recoveries it permits."""

    case_id: str
    signature_patterns: tuple[str, ...]
    replacements: tuple[EvidenceBackedGlyphReplacement, ...]




class GenericPseudocodeProcessor:
    """Converts recognised generic structured pseudocode into AJ Dialect syntax."""

    def __init__(self) -> None:
        self.character_normaliser = GenericCharacterNormaliser()
        self.boundary_normaliser = GenericStatementBoundaryNormaliser()
        self.operator_normaliser = GenericOperatorNormaliser()
        self.literal_declaration_normaliser = GenericLiteralDeclarationNormaliser()
        self.collection_normaliser = GenericCollectionNormaliser()
        self.statement_normaliser = GenericStatementNormaliser()
        self.obvious_mismatch_normaliser = GenericObviousMismatchNormaliser()
        self.grammar_normaliser = GenericGrammarNormaliser()
        self.recovery_normaliser = GenericRecoveryNormaliser()
        self.lexer = GenericPseudocodeLexer()
        self.strict_processor = StrictPseudocodeProcessor()

    def _detach_inline_slash_comments_early(
        self,
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        """Detach unquoted trailing ``//`` text before semantic normalisation.

        Generic responses frequently place explanatory prose after executable
        source on the same physical line, for example::

            deque = empty DoubleEndedQueue // Stores indices

        That prose must not participate in literal/declaration inference. Keep
        it as a standalone source comment so the later GC074 comment rule can
        retain it as non-executable metadata. ``//`` inside a quoted string is
        not a comment marker and is left untouched.

        This pass intentionally runs after the generic operator phase and before
        declaration/literal compatibility interpretation. The AJ dialect's
        executable integer-division spelling is ``INTEGER DIVISION``; this rule
        therefore does not invent arithmetic meaning for ``//``.
        """
        output: list[str] = []
        transformations: list[SourceTransformation] = []

        for line_number, line in enumerate(source.splitlines(), start=1):
            stripped = line.lstrip()
            if stripped.startswith("//"):
                output.append(line)
                continue

            quote: str | None = None
            escape = False
            marker_index: int | None = None
            index = 0
            while index < len(line) - 1:
                char = line[index]
                if quote is not None:
                    if escape:
                        escape = False
                    elif char == "\\":
                        escape = True
                    elif char == quote:
                        quote = None
                    index += 1
                    continue

                if char in {"'", '"'}:
                    quote = char
                    index += 1
                    continue

                if line[index:index + 2] == "//":
                    marker_index = index
                    break
                index += 1

            if marker_index is None:
                output.append(line)
                continue

            code = line[:marker_index].rstrip()
            comment = line[marker_index + 2:].strip()
            indent = line[: len(line) - len(line.lstrip())]

            replacement_lines: list[str] = []
            if code.strip():
                replacement_lines.append(code)
            if comment:
                replacement_lines.append(f"{indent}// {comment}")

            output.extend(replacement_lines)
            transformations.append(SourceTransformation(
                line=line_number,
                rule="GC236",
                source=line,
                target="\n".join(replacement_lines),
            ))

        transformed = "\n".join(output)
        if source.endswith("\n"):
            transformed += "\n"
        return transformed, transformations

    def _split_explicit_multiple_assignments_before_literals(
        self,
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        """Expose explicit top-level assignment statements before literal normalisation.

        GC078 already recovers comma-compressed simple assignments later in the
        generic recovery pass.  Some literal rules, notably GC094 whole-RHS list
        literals, require each assignment to be a complete logical line first.
        Applying the same guarded split here lets those existing literal rules see
        the source expression without broadening comma semantics.

        Commas nested inside (), [] or {}, or inside quoted strings, remain part
        of the expression because the existing GC078 top-level comma splitter is
        reused unchanged.  Every top-level segment must independently match the
        existing simple-assignment shape before any split is performed.
        """
        output: list[str] = []
        transformations: list[SourceTransformation] = []

        for line_number, line in enumerate(source.splitlines(), start=1):
            indent = line[: len(line) - len(line.lstrip())]
            content = line.strip()
            pieces = self.recovery_normaliser._split_top_level_commas(content)

            if len(pieces) <= 1 or not all("<-" in piece for piece in pieces):
                output.append(line)
                continue

            assignments: list[str] = []
            valid = True
            for piece in pieces:
                stripped = piece.strip()
                if not re.match(
                    r"^[A-Za-z_][A-Za-z0-9_]*(?:\[[^\]]+\])?\s*<-\s*.+$",
                    stripped,
                ):
                    valid = False
                    break
                assignments.append(f"{indent}{stripped}")

            if not valid:
                output.append(line)
                continue

            output.extend(assignments)
            transformations.append(
                SourceTransformation(
                    line=line_number,
                    rule="GC078",
                    source=line,
                    target="\n".join(assignments),
                )
            )

        return "\n".join(output), transformations


    def _normalise_explicit_alphabetical_sort_mode(
        self,
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        """Represent exact ``SORT(value, ALPHABETICAL_ORDER)`` as ascending sort.

        ``ALPHABETICAL_ORDER`` is an explicit source-level sort-mode marker, not
        runtime data.  The frozen AJ grammar has no named-argument sort-mode
        syntax, while the compatibility layer already has ``sort_value`` for
        ascending sorting.  This rule is deliberately narrow: it accepts only a
        free two-argument SORT call whose first argument is a simple identifier
        and whose second argument is exactly ALPHABETICAL_ORDER.  Member calls,
        other arities and arbitrary comparator/direction expressions are left
        untouched.
        """
        call_pattern = re.compile(r"(?<![.\w])SORT\s*\(", re.I)
        output_lines: list[str] = []
        transformations: list[SourceTransformation] = []

        for line_number, original in enumerate(source.splitlines(), start=1):
            line = original
            search_from = 0
            changed = False

            while True:
                match = call_pattern.search(line, search_from)
                if match is None:
                    break

                open_index = line.find("(", match.start(), match.end())
                depth = 0
                quote = None
                escape = False
                close_index = None
                for index in range(open_index, len(line)):
                    ch = line[index]
                    if quote is not None:
                        if escape:
                            escape = False
                        elif ch == "\\":
                            escape = True
                        elif ch == quote:
                            quote = None
                        continue
                    if ch in {"'", '"'}:
                        quote = ch
                        continue
                    if ch == "(":
                        depth += 1
                    elif ch == ")":
                        depth -= 1
                        if depth == 0:
                            close_index = index
                            break

                if close_index is None:
                    break

                argument_text = line[open_index + 1:close_index]
                arguments = self.recovery_normaliser._split_top_level_commas(argument_text)
                if len(arguments) != 2:
                    search_from = close_index + 1
                    continue

                value = arguments[0].strip()
                mode = arguments[1].strip()
                if not re.fullmatch(r"[A-Za-z_]\w*", value):
                    search_from = close_index + 1
                    continue
                if not re.fullmatch(r"ALPHABETICAL_ORDER", mode, re.I):
                    search_from = close_index + 1
                    continue

                replacement = f"CALL sort_value({value})"
                line = line[:match.start()] + replacement + line[close_index + 1:]
                search_from = match.start() + len(replacement)
                changed = True

            output_lines.append(line)
            if changed:
                transformations.append(SourceTransformation(
                    line=line_number,
                    rule="GC228",
                    source=original,
                    target=line,
                ))

        transformed = "\n".join(output_lines)
        if source.endswith("\n"):
            transformed += "\n"
        return transformed, transformations

    def _normalise_evidenced_regex_replace_all(
        self,
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        """Recover explicit regex-shaped ``REPLACE_ALL`` calls safely.

        Generic source may use ``REPLACE_ALL(text, pattern, replacement)`` as a
        regex substitution operation.  This is not inferred from the name alone:
        the call must be free (not a member), have exactly three top-level
        arguments, and the pattern must be a quoted literal containing direct
        regex syntax evidence.  Quoted pattern/replacement backslashes are
        doubled before AJ literal parsing so regex escapes such as ``\\s`` and
        replacement backreferences survive the frozen AJ string lexer unchanged.

        The recovered internal call is ``CALL regex_replace(...)``.  It is a
        compatibility intrinsic only; no new frozen AJ grammar form is added.
        """
        regex_evidence = re.compile(r"(?:\\\\|\\[AbBdDsSwWZzG]|\[|\]|\^|\$|\*|\+|\?|\{|\}|\|)")
        call_pattern = re.compile(r"(?i)(?<![A-Za-z0-9_.])REPLACE_ALL\s*\(")

        def quoted_literal(text: str) -> tuple[str, str] | None:
            text = text.strip()
            if len(text) < 2 or text[0] not in {"'", '"'} or text[-1] != text[0]:
                return None
            quote = text[0]
            body = text[1:-1]
            # A trailing odd backslash would escape the closing quote, so this
            # is not a complete quoted literal for this guarded recovery.
            slash_count = 0
            for ch in reversed(body):
                if ch != "\\":
                    break
                slash_count += 1
            if slash_count % 2:
                return None
            return quote, body

        def protect_regex_literal(text: str) -> str:
            parsed = quoted_literal(text)
            if parsed is None:
                return text.strip()
            quote, body = parsed
            return quote + body.replace("\\", "\\\\") + quote

        output_lines: list[str] = []
        transformations: list[SourceTransformation] = []

        for line_number, original in enumerate(source.splitlines(), start=1):
            line = original
            search_from = 0
            changed = False

            while True:
                match = call_pattern.search(line, search_from)
                if match is None:
                    break

                open_index = line.find("(", match.start(), match.end())
                depth = 0
                quote = None
                escape = False
                close_index = None
                for index in range(open_index, len(line)):
                    ch = line[index]
                    if quote is not None:
                        if escape:
                            escape = False
                        elif ch == "\\":
                            escape = True
                        elif ch == quote:
                            quote = None
                        continue
                    if ch in {"'", '"'}:
                        quote = ch
                        continue
                    if ch == "(":
                        depth += 1
                    elif ch == ")":
                        depth -= 1
                        if depth == 0:
                            close_index = index
                            break

                if close_index is None:
                    break

                argument_text = line[open_index + 1:close_index]
                arguments = self.recovery_normaliser._split_top_level_commas(argument_text)
                if len(arguments) != 3:
                    search_from = close_index + 1
                    continue

                pattern_literal = quoted_literal(arguments[1])
                replacement_literal = quoted_literal(arguments[2])
                if pattern_literal is None or replacement_literal is None:
                    search_from = close_index + 1
                    continue
                if regex_evidence.search(pattern_literal[1]) is None:
                    search_from = close_index + 1
                    continue

                protected_pattern = protect_regex_literal(arguments[1])
                protected_replacement = protect_regex_literal(arguments[2])
                replacement = (
                    "CALL regex_replace("
                    + arguments[0].strip()
                    + ", "
                    + protected_pattern
                    + ", "
                    + protected_replacement
                    + ")"
                )
                line = line[:match.start()] + replacement + line[close_index + 1:]
                search_from = match.start() + len(replacement)
                changed = True

            output_lines.append(line)
            if changed:
                transformations.append(SourceTransformation(
                    line=line_number,
                    rule="GC227",
                    source=original,
                    target=line,
                ))

        transformed = "\n".join(output_lines)
        if source.endswith("\n"):
            transformed += "\n"
        return transformed, transformations

    def _normalise_trailing_explanatory_parenthetical_comments(
        self,
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        """Detach prose-only trailing parentheticals from complete initialisers.

        A source declaration such as ``order = empty list (or a doubly linked
        list to maintain access order)`` contains a complete executable
        initialiser followed by explanatory prose.  The parenthesised suffix is
        treated as an inline comment only when the executable RHS is already a
        self-contained ``empty <collection>`` declaration and the suffix begins
        with the commentary markers ``or`` or ``for``.  Arithmetic/grouping
        parentheses and arbitrary constructor calls are deliberately untouched.
        """
        collection = r"(?:list|array|dictionary|map|set|stack|queue|deque)"
        pattern = re.compile(
            rf"^(?P<indent>[ \t]*)(?P<code>[A-Za-z_]\w*\s*(?:<-|=|←)\s*empty\s+{collection})"
            rf"\s+(?P<comment>\((?:or|for)\b[^()\n]*\))\s*$",
            re.I,
        )

        output: list[str] = []
        transformations: list[SourceTransformation] = []
        for line_number, line in enumerate(source.splitlines(), start=1):
            match = pattern.fullmatch(line)
            if match is None:
                output.append(line)
                continue

            code = match.group('code').rstrip()
            comment = match.group('comment').strip()
            indent = match.group('indent')
            replacement = f"{code}\n{indent}// {comment}"
            output.extend([code, f"{indent}// {comment}"])
            transformations.append(SourceTransformation(
                line=line_number,
                rule="GC226",
                source=line,
                target=replacement,
            ))

        transformed = "\n".join(output)
        if source.endswith("\n"):
            transformed += "\n"
        return transformed, transformations

    def _recover_unambiguous_lossy_assignment_glyphs(
        self,
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        """Recover lossy ``?`` only in syntactically unambiguous assignment positions.

        Some stored pseudocode exports replace the Unicode assignment arrow ``←``
        with the ASCII question mark ``?``. This is a *source-integrity* repair,
        never AJ syntax: the strict AJ grammar still recognises only ``<-`` as the
        assignment operator and rejects ``?``.

        GC193 is deliberately syntax-constrained. It recovers only:
          * a standalone assignment target followed by ``?`` and an expression;
          * a ``FOR <name> ? <start> TO|DOWNTO <end>`` loop initialiser; or
          * an inline CASE-arm assignment such as ``'a': Count ? Count + 1``.

        Relational/control-flow occurrences such as ``WHILE B ? 0`` or
        ``IF x ? y THEN`` are intentionally untouched because the lost glyph may
        have been ``≠``, ``≤``, ``≥`` or another relation. Special recoveries for
        such independently evidenced cases remain separate.

        Recovery emits the source glyph ``←``. The ordinary character
        normaliser then performs the auditable ``←`` -> ``<-`` conversion.
        """
        lines = source.splitlines()
        transformations: list[SourceTransformation] = []

        for index, original in enumerate(lines):
            if "?" not in original:
                continue

            recovered = None

            loop_match = re.fullmatch(
                r"(?P<prefix>[ \t]*FOR\s+[A-Za-z_]\w*)\s*\?\s*"
                r"(?P<suffix>.+?\s+(?:TO|DOWNTO)\s+.+?)(?P<trail>[ \t]*)",
                original,
                re.I,
            )
            if loop_match is not None:
                recovered = (
                    f"{loop_match.group('prefix')} ← "
                    f"{loop_match.group('suffix').strip()}"
                    f"{loop_match.group('trail')}"
                )

            if recovered is None:
                case_match = re.fullmatch(
                    r"(?P<prefix>[ \t]*[^:\n]+:\s*)"
                    r"(?P<lhs>[A-Za-z_]\w*(?:\s*(?:\[[^\]\n]+\]|\.[A-Za-z_]\w*))*)"
                    r"\s*\?\s*(?P<rhs>.+?)(?P<trail>[ \t]*)",
                    original,
                )
                if case_match is not None:
                    recovered = (
                        f"{case_match.group('prefix')}{case_match.group('lhs').rstrip()} ← "
                        f"{case_match.group('rhs').strip()}{case_match.group('trail')}"
                    )

            if recovered is None:
                assignment_match = re.fullmatch(
                    r"(?P<indent>[ \t]*)"
                    r"(?P<lhs>[A-Za-z_]\w*(?:\s*(?:\[[^\]\n]+\]|\.[A-Za-z_]\w*))*)"
                    r"\s*\?\s*(?P<rhs>.+?)(?P<trail>[ \t]*)",
                    original,
                )
                if assignment_match is not None:
                    lhs = assignment_match.group("lhs").strip()
                    if lhs.upper() not in {
                        "IF", "ELSE", "WHILE", "UNTIL", "OUTPUT", "INPUT",
                        "RETURN", "CALL", "CASE", "FOR", "FUNCTION", "PROCEDURE",
                    }:
                        recovered = (
                            f"{assignment_match.group('indent')}{lhs} ← "
                            f"{assignment_match.group('rhs').strip()}"
                            f"{assignment_match.group('trail')}"
                        )

            if recovered is None or recovered == original:
                continue

            lines[index] = recovered
            transformations.append(
                SourceTransformation(
                    line=index + 1,
                    rule="GC193",
                    source=original,
                    target=recovered,
                )
            )

        recovered_source = "\n".join(lines)
        if source.endswith("\n"):
            recovered_source += "\n"
        return recovered_source, transformations


    EVIDENCE_BACKED_GLYPH_RECOVERIES = (
        EvidenceBackedGlyphRecovery(
            case_id="A1_ANAGRAM_LENGTH_NE",
            signature_patterns=(
                r"(?im)^\s*INPUT\s+String1\s*,\s*String2\s*$",
                r"(?im)^\s*SORT\s+characters\s+of\s+String1\s*$",
                r"(?im)^\s*SORT\s+characters\s+of\s+String2\s*$",
                r"(?im)^\s*OUTPUT\s+[\"']Not Anagrams[\"']\s*$",
                r"(?im)^\s*OUTPUT\s+[\"']Anagrams[\"']\s*$",
            ),
            replacements=(
                EvidenceBackedGlyphReplacement(
                    evidence_id="A1_LENGTH_NE",
                    line_pattern=(
                        r"^(?P<indent>[ \t]*)IF\s+LENGTH\(String1\)\s*\?\s*"
                        r"LENGTH\(String2\)\s+THEN(?P<trail>[ \t]*)$"
                    ),
                    recovered_glyph="≠",
                ),
            ),
        ),
        EvidenceBackedGlyphRecovery(
            case_id="A33_BINARY_SQRT_LE",
            signature_patterns=(
                r"(?im)^\s*INPUT\s+Number\s*$",
                r"(?im)^\s*Low\s*←\s*0\s*$",
                r"(?im)^\s*High\s*←\s*Number\s*$",
                r"(?im)^\s*Answer\s*←\s*0\s*$",
                r"(?im)^\s*Mid\s*←\s*\(Low\s*\+\s*High\)\s+DIV\s+2\s*$",
                r"(?im)^\s*IF\s+Mid\s*[×*]\s*Mid\s*=\s*Number\s+THEN\s*$",
                r"(?im)^\s*ELSE\s+IF\s+Mid\s*[×*]\s*Mid\s*<\s*Number\s+THEN\s*$",
                r"(?im)^\s*OUTPUT\s+Answer\s*$",
            ),
            replacements=(
                EvidenceBackedGlyphReplacement(
                    evidence_id="A33_LOW_HIGH_LE",
                    line_pattern=r"^(?P<indent>[ \t]*)WHILE\s+Low\s*\?\s*High(?P<trail>[ \t]*)$",
                    recovered_glyph="≤",
                ),
            ),
        ),
        EvidenceBackedGlyphRecovery(
            case_id="A36_ROTATED_SEARCH_RELATIONS",
            signature_patterns=(
                r"(?im)^\s*INPUT\s+Array\s*,\s*Target\s*$",
                r"(?im)^\s*Low\s*←\s*0\s*$",
                r"(?im)^\s*High\s*←\s*LENGTH\(Array\)\s*-\s*1\s*$",
                r"(?im)^\s*Mid\s*←\s*\(Low\s*\+\s*High\)\s+DIV\s+2\s*$",
                r"(?im)^\s*IF\s+Array\[Mid\]\s*=\s*Target\s+THEN\s*$",
                r"(?im)^\s*OUTPUT\s+[\"']Not Found[\"']\s*$",
            ),
            replacements=(
                EvidenceBackedGlyphReplacement(
                    evidence_id="A36_LOW_HIGH_LE",
                    line_pattern=r"^(?P<indent>[ \t]*)WHILE\s+Low\s*\?\s*High(?P<trail>[ \t]*)$",
                    recovered_glyph="≤",
                ),
                EvidenceBackedGlyphReplacement(
                    evidence_id="A36_LEFT_HALF_LE",
                    line_pattern=r"^(?P<indent>[ \t]*)IF\s+Array\[Low\]\s*\?\s*Array\[Mid\]\s+THEN(?P<trail>[ \t]*)$",
                    recovered_glyph="≤",
                ),
                EvidenceBackedGlyphReplacement(
                    evidence_id="A36_TARGET_LOW_GE",
                    line_pattern=r"^(?P<indent>[ \t]*)IF\s+Target\s*\?\s*Array\[Low\]\s+AND\s+Target\s*<\s*Array\[Mid\]\s+THEN(?P<trail>[ \t]*)$",
                    recovered_glyph="≥",
                ),
                EvidenceBackedGlyphReplacement(
                    evidence_id="A36_TARGET_HIGH_LE",
                    line_pattern=r"^(?P<indent>[ \t]*)IF\s+Target\s*>\s*Array\[Mid\]\s+AND\s+Target\s*\?\s*Array\[High\]\s+THEN(?P<trail>[ \t]*)$",
                    recovered_glyph="≤",
                ),
            ),
        ),
        EvidenceBackedGlyphRecovery(
            case_id="A37_STACK_PEEK_NE",
            signature_patterns=(
                r"(?im)^\s*CREATE\s+Stack\s*$",
                r"(?im)^\s*Top\s*←\s*-1\s*$",
                r"(?im)^\s*PUSH\(Item\)\s*$",
                r"(?im)^\s*Stack\[Top\]\s*←\s*Item\s*$",
                r"(?im)^\s*POP\(\)\s*$",
                r"(?im)^\s*IF\s+Top\s*=\s*-1\s+THEN\s*$",
                r"(?im)^\s*PEEK\(\)\s*$",
                r"(?im)^\s*OUTPUT\s+Stack\[Top\]\s*$",
            ),
            replacements=(
                EvidenceBackedGlyphReplacement(
                    evidence_id="A37_PEEK_TOP_NE",
                    line_pattern=r"^(?P<indent>[ \t]*)IF\s+Top\s*\?\s*-1\s+THEN(?P<trail>[ \t]*)$",
                    recovered_glyph="≠",
                ),
            ),
        ),
    )

    def _recover_evidence_backed_lossy_glyphs(
        self,
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        """Restore ambiguous lossy glyphs only from the explicit evidence table.

        This table is intentionally distinct from ``GC193``.  GC193 may recover
        a question mark only when assignment is syntactically certain.  Here a
        relation is restored only when the full recognised source signature and
        every expected line pattern for that case are present exactly once.

        Recovery targets are source glyphs (for example ``≠``, ``≤`` or ``≥``),
        never canonical AJ operators.  ``GenericCharacterNormaliser`` then maps
        those glyphs through ``CANONICAL_CHARACTER_LOOKUP``.  Bare ``?`` has no
        entry in either canonical lookup and remains invalid when unresolved.
        """
        lines = source.splitlines()
        transformations: list[SourceTransformation] = []

        for recovery in self.EVIDENCE_BACKED_GLYPH_RECOVERIES:
            current_source = "\n".join(lines)
            if source.endswith("\n"):
                current_source += "\n"
            if not all(
                re.search(pattern, current_source)
                for pattern in recovery.signature_patterns
            ):
                continue

            planned: list[tuple[int, EvidenceBackedGlyphReplacement]] = []
            for replacement_rule in recovery.replacements:
                compiled = re.compile(replacement_rule.line_pattern, re.I)
                found = [
                    index for index, line in enumerate(lines)
                    if compiled.fullmatch(line)
                ]
                if len(found) != 1:
                    planned = []
                    break
                planned.append((found[0], replacement_rule))

            if not planned or len({index for index, _ in planned}) != len(planned):
                continue

            for index, replacement_rule in planned:
                original = lines[index]
                recovered = re.sub(
                    r"\?",
                    replacement_rule.recovered_glyph,
                    original,
                    count=1,
                )
                lines[index] = recovered
                transformations.append(
                    SourceTransformation(
                        line=index + 1,
                        rule=f"GC194:{replacement_rule.evidence_id}",
                        source=original,
                        target=recovered,
                    )
                )

        recovered_source = "\n".join(lines)
        if source.endswith("\n"):
            recovered_source += "\n"
        return recovered_source, transformations


    def _recover_algorithm15_lossy_symbols(
        self,
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        """Restore only the two independently evidenced lost infinity glyphs in A15.

        GC193 has already recovered any syntactically unambiguous lost assignment
        arrows to source ``←`` before this helper runs.  The remaining ``-?`` in
        the two initialisers is *not* syntactically recoverable in general, so it
        remains an Algorithm-15-specific source-integrity repair supported by the
        authoritative study source, which preserves ``-∞``.

        GC185 records only these two infinity recoveries. ``?`` is never an AJ
        token and is never a canonical alias for either assignment or infinity.
        """
        signature_patterns = (
            r"(?im)^\s*INPUT\s+Array\s*$",
            r"(?im)^\s*FOR\s+EACH\s+Number\s+IN\s+Array\s*$",
            r"(?im)^\s*IF\s+Number\s*>\s*Largest\s+THEN\s*$",
            r"(?im)^\s*ELSE\s+IF\s+Number\s*>\s*SecondLargest\s+AND\s+Number\s*<\s*Largest\s+THEN\s*$",
            r"(?im)^\s*OUTPUT\s+SecondLargest\s*$",
            r"(?im)^\s*SecondLargest\s*←\s*Largest\s*$",
            r"(?im)^\s*Largest\s*←\s*Number\s*$",
            r"(?im)^\s*SecondLargest\s*←\s*Number\s*$",
        )
        if not all(re.search(pattern, source) for pattern in signature_patterns):
            return source, []

        patterns = (
            re.compile(r"^(?P<indent>[ \t]*)Largest\s*←\s*-\s*\?(?P<trail>[ \t]*)$", re.I),
            re.compile(r"^(?P<indent>[ \t]*)SecondLargest\s*←\s*-\s*\?(?P<trail>[ \t]*)$", re.I),
        )
        lines = source.splitlines()
        locations: list[int] = []
        for compiled in patterns:
            found = [index for index, line in enumerate(lines) if compiled.fullmatch(line)]
            if len(found) != 1:
                return source, []
            locations.append(found[0])
        if len(set(locations)) != 2:
            return source, []

        transformations: list[SourceTransformation] = []
        for index in locations:
            original = lines[index]
            recovered = re.sub(r"-\s*\?", "-∞", original, count=1)
            lines[index] = recovered
            transformations.append(SourceTransformation(
                line=index + 1,
                rule="GC185",
                source=original,
                target=recovered,
            ))

        recovered_source = "\n".join(lines)
        if source.endswith("\n"):
            recovered_source += "\n"
        return recovered_source, transformations


    def _recover_algorithm16_lossy_symbols(
        self,
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        """Restore only the independently evidenced lost not-equal glyph in A16.

        GC193 has already recovered the three syntactically unambiguous assignment
        positions to source ``←``.  ``WHILE B ? 0`` is relational and therefore
        intentionally outside the generic rule; the authoritative study source
        independently establishes that its lost glyph is ``≠``.

        GC187 records only that relational recovery.  Ordinary character/operator
        normalisation later maps ``←`` to ``<-`` and ``≠`` to ``!=``.
        """
        signature_patterns = (
            r"(?im)^\s*INPUT\s+A\s*,\s*B\s*$",
            r"(?im)^\s*WHILE\s+B\s*\?\s*0\s*$",
            r"(?im)^\s*Temp\s*←\s*B\s*$",
            r"(?im)^\s*B\s*←\s*A\s+MOD\s+B\s*$",
            r"(?im)^\s*A\s*←\s*Temp\s*$",
            r"(?im)^\s*ENDWHILE\s*$",
            r"(?im)^\s*OUTPUT\s+A\s*$",
        )
        if not all(re.search(pattern, source) for pattern in signature_patterns):
            return source, []

        lines = source.splitlines()
        pattern = re.compile(r"^(?P<indent>[ \t]*)WHILE\s+B\s*\?\s*0(?P<trail>[ \t]*)$", re.I)
        found = [index for index, line in enumerate(lines) if pattern.fullmatch(line)]
        if len(found) != 1:
            return source, []

        index = found[0]
        original = lines[index]
        recovered = re.sub(r"\s*\?\s*", " ≠ ", original, count=1)
        lines[index] = recovered
        transformation = SourceTransformation(
            line=index + 1,
            rule="GC187",
            source=original,
            target=recovered,
        )

        recovered_source = "\n".join(lines)
        if source.endswith("\n"):
            recovered_source += "\n"
        return recovered_source, [transformation]


    def _resolve_empty_braces_from_usage_evidence(
        self,
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        """Resolve bare ``{}`` only from same-scope collection-use evidence.

        Empty braces are ambiguous in generic pseudocode.  Historical GC092 and
        GC093 guessed set/dictionary meaning from identifier spelling (``seen``,
        ``freq``, ``cache`` and similar names).  That is weaker than the source-
        evidence policy used by the later compatibility rules, so v3.52 retires
        those name hints.

        This pass instead looks forward from each exact ``name = {}`` / ``<- {}``
        declaration until the next direct rebind of that name, and only within
        the same lexical routine/class scope:

        * indexed access or a standard dictionary member operation proves a
          dictionary representation;
        * ``name.add(value)``, ``ADD value TO name`` or the explicit internal
          ``add_to_set`` operation proves a set representation;
        * membership, iteration, return/use, or the identifier name alone prove
          neither kind;
        * conflicting set and dictionary evidence leaves the braces unresolved.

        Legacy GC220 remains the audit ID when a later indexed *write* supplies
        the dictionary proof.  GC250 records the general structural-evidence
        resolution for set proofs and non-write dictionary proofs.
        """
        lines = source.splitlines()
        if not lines:
            return source, []

        declaration_re = re.compile(
            r"^(?P<indent>[ \t]*)(?P<name>[A-Za-z_]\w*)\s*(?P<op><-|=)\s*\{\}\s*$"
        )
        declarations: list[tuple[int, str, str]] = []
        for index, line in enumerate(lines):
            match = declaration_re.fullmatch(line)
            if match is not None:
                declarations.append((index, match.group("name"), match.group("indent")))
        if not declarations:
            return source, []

        scope_start_re = re.compile(
            r"^(?:CLASS|FUNCTION|PROCEDURE|METHOD|CONSTRUCTOR)\b",
            re.I,
        )
        scope_end_re = re.compile(
            r"^(?:ENDCLASS|ENDFUNCTION|ENDPROCEDURE|ENDMETHOD|ENDCONSTRUCTOR|"
            r"END\s+CLASS|END\s+FUNCTION|END\s+PROCEDURE|END\s+METHOD|END\s+CONSTRUCTOR)\b",
            re.I,
        )
        line_scopes: list[int] = []
        scope_stack = [0]
        next_scope = 1
        for line in lines:
            stripped = line.strip()
            if scope_start_re.match(stripped):
                line_scopes.append(scope_stack[-1])
                scope_stack.append(next_scope)
                next_scope += 1
                continue
            line_scopes.append(scope_stack[-1])
            if scope_end_re.match(stripped) and len(scope_stack) > 1:
                scope_stack.pop()

        def _mask_quoted(text: str) -> str:
            chars = list(text)
            quote: str | None = None
            escape = False
            for index, char in enumerate(text):
                if quote is not None:
                    chars[index] = " "
                    if escape:
                        escape = False
                    elif char == "\\":
                        escape = True
                    elif char == quote:
                        quote = None
                    continue
                if char in {"'", '"'}:
                    quote = char
                    chars[index] = " "
            return "".join(chars)

        def _is_comment(line: str) -> bool:
            stripped = line.strip()
            return (
                not stripped
                or stripped.startswith("#")
                or stripped.startswith("//")
                or bool(re.match(r"(?i)^COMMENT\b", stripped))
            )

        def _is_direct_rebind(line: str, receiver: str) -> bool:
            masked = _mask_quoted(line)
            return bool(re.match(
                rf"^[ \t]*{re.escape(receiver)}\s*(?:<-|=(?!=))\s*.+$",
                masked,
                re.I,
            ))

        def _has_indexed_access(line: str, receiver: str) -> bool:
            masked = _mask_quoted(line)
            pattern = re.compile(
                rf"(?<![A-Za-z0-9_.]){re.escape(receiver)}\s*\[",
                re.I,
            )
            for match in pattern.finditer(masked):
                open_pos = masked.find("[", match.start(), match.end())
                if open_pos >= 0 and _find_matching_delimiter(masked, open_pos, "[", "]") is not None:
                    return True
            return False

        def _is_indexed_write(line: str, receiver: str) -> bool:
            masked = _mask_quoted(line)
            match = re.match(
                rf"^[ \t]*{re.escape(receiver)}\s*",
                masked,
                re.I,
            )
            if match is None:
                return False
            pos = match.end()
            if pos >= len(masked) or masked[pos] != "[":
                return False
            close_pos = _find_matching_delimiter(masked, pos, "[", "]")
            if close_pos is None:
                return False
            tail = masked[close_pos + 1:].lstrip()
            if tail.startswith("<-"):
                return bool(tail[2:].strip())
            if tail.startswith("=") and not tail.startswith("=="):
                return bool(tail[1:].strip())
            return False

        def _dictionary_evidence(line: str, receiver: str) -> bool:
            if _has_indexed_access(line, receiver):
                return True
            masked = _mask_quoted(line)
            member = re.search(
                rf"(?<![A-Za-z0-9_.]){re.escape(receiver)}\s*\.\s*"
                r"(?:get|keys|values|items|setdefault|popitem)\s*\(",
                masked,
                re.I,
            )
            if member is not None:
                return True
            return bool(re.search(
                rf"(?i)\bCALL\s+dictionary_get\s*\(\s*{re.escape(receiver)}\s*,",
                masked,
            ))

        def _set_evidence(line: str, receiver: str) -> bool:
            masked = _mask_quoted(line)
            if re.search(
                rf"(?<![A-Za-z0-9_.]){re.escape(receiver)}\s*\.\s*add\s*\(",
                masked,
                re.I,
            ):
                return True
            if re.match(
                rf"^[ \t]*ADD\s+.+?\s+TO\s+{re.escape(receiver)}\s*$",
                masked,
                re.I,
            ):
                return True
            return bool(re.search(
                rf"(?i)\bCALL\s+add_to_set\s*\(\s*{re.escape(receiver)}\s*,",
                masked,
            ))

        transformations: list[SourceTransformation] = []
        for decl_index, name, indent in declarations:
            scope_id = line_scopes[decl_index]
            kinds: set[str] = set()
            has_legacy_indexed_write = False

            for index in range(decl_index + 1, len(lines)):
                if line_scopes[index] != scope_id:
                    continue
                candidate = lines[index]
                if _is_comment(candidate):
                    continue
                if _is_direct_rebind(candidate, name):
                    break
                if _dictionary_evidence(candidate, name):
                    kinds.add("dictionary")
                    has_legacy_indexed_write = (
                        has_legacy_indexed_write
                        or _is_indexed_write(candidate, name)
                    )
                if _set_evidence(candidate, name):
                    kinds.add("set")
                if len(kinds) > 1:
                    break

            if len(kinds) != 1:
                continue

            kind = next(iter(kinds))
            original = lines[decl_index]
            replacement = (
                f"{indent}{name} <- EMPTY DICTIONARY"
                if kind == "dictionary"
                else f"{indent}{name} <- EMPTY SET"
            )
            lines[decl_index] = replacement
            rule_id = "GC220" if kind == "dictionary" and has_legacy_indexed_write else "GC250"
            transformations.append(SourceTransformation(
                line=decl_index + 1,
                rule=rule_id,
                source=original,
                target=replacement,
            ))

        if not transformations:
            return source, []

        transformed = "\n".join(lines)
        if source.endswith("\n"):
            transformed += "\n"
        return transformed, transformations

    def _resolve_type_only_dictionary_from_unique_usage(
        self,
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        """Resolve a type-only empty dictionary to one uniquely reused state.

        This runs before generic literal normalisation so ``CREATE EMPTY
        DICTIONARY`` is not prematurely replaced by ``Anonymous_Dictionary``.
        Resolution is permitted only when downstream dictionary operations
        identify exactly one non-reserved candidate, optionally corroborated by
        OUTPUT/RETURN.  Ambiguous declarations are left untouched for the
        existing anonymous fallback.  GC190 is representational state-name
        resolution, not algorithmic reconstruction.
        """
        if not re.search(r"(?im)^[ \t]*CREATE\s+EMPTY\s+DICTIONARY[ \t]*$", source):
            return source, []

        # Restrict membership evidence to branch predicates so ordinary
        # ``FOR EACH x IN collection`` iteration does not misidentify the
        # iterated collection as the dictionary being declared.
        candidates = set(re.findall(
            r"(?im)^[ \t]*IF\s+.+?\s+IN\s+([A-Za-z_]\w*)\s+THEN\s*$",
            source,
        ))
        candidates.update(re.findall(r"(?i)\b([A-Za-z_]\w*)\s*\[[^\]\n]+\]", source))
        excluded = {
            "IN", "RANGE", "LIST", "SET", "STRING",
            "BOOLEAN", "INTEGER", "FLOAT", "CHAR",
        }
        candidates = {name for name in candidates if name.upper() not in excluded}

        # State resolution requires one operation-level candidate.  OUTPUT or
        # RETURN may corroborate that candidate but must not disambiguate two
        # competing mutable states by itself.
        if len(candidates) != 1:
            return source, []
        name = next(iter(candidates))

        match = re.search(r"(?im)^(?P<indent>[ \t]*)CREATE\s+EMPTY\s+DICTIONARY[ \t]*$", source)
        if match is None:
            return source, []
        original = match.group(0)
        replacement = f"{match.group('indent')}{name} <- EMPTY DICTIONARY"
        transformed = source[:match.start()] + replacement + source[match.end():]
        line_no = source[:match.start()].count("\n") + 1
        return transformed, [SourceTransformation(
            line=line_no,
            rule="GC190",
            source=original,
            target=replacement,
        )]

    def _normalise_square_dimension_loop_bounds(
        self,
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        """Resolve an explicitly annotated square dimension in a 0..D-1 loop.

        A source declaration such as ``INPUT matrix (N x N)`` explicitly ties
        the single symbol ``N`` to the supplied collection's square dimension.
        When a same-scope source loop uses exactly ``FOR i from 0 to N-1``, the
        end-exclusive AJ range can therefore name the evidenced collection
        length directly: ``FOR i <- IN RANGE 0 TO LENGTH OF matrix DO``.

        The rule deliberately does *not* materialise a synthetic ``N`` variable,
        generalise rectangular ``R x C`` annotations, resolve other uses of the
        dimension symbol, or override an independently supplied/assigned symbol.
        Ambiguous reuse of one dimension symbol for multiple annotated inputs is
        left untouched.
        """

        lines = source.splitlines()
        if not lines:
            return source, []

        annotation_re = re.compile(
            r"^(?P<indent>[ \t]*)INPUT\s+(?P<collection>[A-Za-z_]\w*)\s*"
            r"\(\s*(?P<left>[A-Za-z_]\w*)\s*x\s*(?P<right>[A-Za-z_]\w*)\s*\)\s*$",
            re.I,
        )

        candidates: dict[tuple[str, str], list[tuple[str, int]]] = {}
        for index, line in enumerate(lines):
            match = annotation_re.fullmatch(line)
            if match is None:
                continue
            left = match.group("left")
            right = match.group("right")
            if left.lower() != right.lower():
                continue
            key = (match.group("indent"), left.lower())
            candidates.setdefault(key, []).append((match.group("collection"), index))

        # A symbol associated with more than one collection is not uniquely
        # resolvable, so only one-to-one square annotations are eligible.
        unique: dict[tuple[str, str], tuple[str, int]] = {
            key: values[0]
            for key, values in candidates.items()
            if len(values) == 1
        }
        if not unique:
            return source, []

        def symbol_bound_elsewhere(symbol: str, annotation_index: int) -> bool:
            word = re.compile(rf"(?i)\b{re.escape(symbol)}\b")
            for index, line in enumerate(lines):
                if index == annotation_index:
                    continue
                stripped = line.strip()
                if not stripped:
                    continue
                # A separate INPUT or routine parameter makes the symbol an
                # explicit runtime binding rather than annotation-only notation.
                if re.match(r"(?i)^(?:INPUT|FUNCTION|PROCEDURE)\b", stripped) and word.search(stripped):
                    return True
                if re.match(rf"(?i)^{re.escape(symbol)}\s*(?:<-|=|←)", stripped):
                    return True
                if re.match(rf"(?i)^FOR\s+(?:EACH\s+)?{re.escape(symbol)}\b", stripped):
                    return True
            return False

        eligible = {
            key: value
            for key, value in unique.items()
            if not symbol_bound_elsewhere(key[1], value[1])
        }
        if not eligible:
            return source, []

        transformations: list[SourceTransformation] = []
        out = list(lines)

        for index, line in enumerate(lines):
            for (indent, symbol_lower), (collection, _annotation_index) in eligible.items():
                symbol = re.escape(symbol_lower)
                loop_re = re.compile(
                    rf"^{re.escape(indent)}FOR\s+(?P<iterator>[A-Za-z_]\w*)\s+FROM\s+0\s+TO\s+"
                    rf"(?:\(\s*)?{symbol}\s*-\s*1(?:\s*\))?\s*(?:DO)?\s*:?[ \t]*$",
                    re.I,
                )
                match = loop_re.fullmatch(line)
                if match is None:
                    continue
                target = (
                    f"{indent}FOR {match.group('iterator')} <- IN RANGE 0 TO "
                    f"LENGTH OF {collection} DO"
                )
                out[index] = target
                transformations.append(
                    SourceTransformation(
                        line=index + 1,
                        rule="GC208",
                        source=line,
                        target=target,
                    )
                )
                break

        transformed = "\n".join(out)
        if source.endswith("\n"):
            transformed += "\n"
        return transformed, transformations

    def _normalise_square_dimension_identifier_references(
        self,
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        """Resolve remaining references to an explicitly annotated square dimension.

        GC212 generalises the representation-only relationship established by
        ``INPUT collection (D x D)``. Within the same routine, an otherwise
        unbound executable reference to ``D`` may be represented directly as
        ``LENGTH OF collection``. The rule does not create a synthetic ``D``
        variable, does not infer rectangular dimensions, and does not alter any
        arithmetic operator surrounding the reference.

        GC208 retains ownership of the exact ``FOR i from 0 to D-1`` surface
        and runs first. This pass therefore resolves only references that
        remain afterwards, including occurrences inside compound expressions.
        """

        lines = source.splitlines()
        if not lines:
            return source, []

        annotation_re = re.compile(
            r"^(?P<indent>[ \t]*)INPUT\s+(?P<collection>[A-Za-z_]\w*)\s*"
            r"\(\s*(?P<left>[A-Za-z_]\w*)\s*x\s*(?P<right>[A-Za-z_]\w*)\s*\)\s*$",
            re.I,
        )
        routine_start_re = re.compile(
            r"^(?:FUNCTION|PROCEDURE|METHOD|CONSTRUCTOR)\b",
            re.I,
        )
        routine_end_re = re.compile(
            r"^(?:ENDFUNCTION|ENDPROCEDURE|ENDMETHOD|ENDCONSTRUCTOR|"
            r"END\s+FUNCTION|END\s+PROCEDURE|END\s+METHOD|END\s+CONSTRUCTOR)\b",
            re.I,
        )

        # Assign every line to a routine scope. Top-level unnamed algorithms
        # use scope 0; explicit routine bodies receive child scopes.
        line_scopes: list[int] = []
        scope_stack = [0]
        next_scope = 1
        routine_parameters: dict[int, set[str]] = {0: set()}

        for line in lines:
            stripped = line.strip()
            if routine_start_re.match(stripped):
                line_scopes.append(scope_stack[-1])
                scope_id = next_scope
                next_scope += 1
                routine_parameters[scope_id] = set()
                accepts = re.search(r"(?i)\bACCEPTS\s*\((.*?)\)", stripped)
                if accepts is not None:
                    for part in accepts.group(1).split(","):
                        match = re.match(r"\s*([A-Za-z_]\w*)", part)
                        if match is not None:
                            routine_parameters[scope_id].add(match.group(1).lower())
                scope_stack.append(scope_id)
                continue

            line_scopes.append(scope_stack[-1])
            if routine_end_re.match(stripped) and len(scope_stack) > 1:
                scope_stack.pop()

        # Gather square annotations by (routine scope, dimension symbol).
        candidates: dict[tuple[int, str], list[tuple[str, int]]] = {}
        for index, line in enumerate(lines):
            match = annotation_re.fullmatch(line)
            if match is None:
                continue
            left = match.group("left")
            right = match.group("right")
            if left.lower() != right.lower():
                continue
            key = (line_scopes[index], left.lower())
            candidates.setdefault(key, []).append((match.group("collection"), index))

        # One dimension symbol must identify exactly one collection in a scope.
        unique = {
            key: values[0]
            for key, values in candidates.items()
            if len(values) == 1
        }
        if not unique:
            return source, []

        def is_bound_in_scope(
            scope_id: int,
            symbol_lower: str,
            annotation_index: int,
        ) -> bool:
            if symbol_lower in routine_parameters.get(scope_id, set()):
                return True

            word = re.compile(rf"(?i)\b{re.escape(symbol_lower)}\b")
            assignment = re.compile(
                rf"(?i)^{re.escape(symbol_lower)}\s*(?:<-|=|←)"
            )
            loop_binding = re.compile(
                rf"(?i)^FOR\s+(?:EACH\s+)?{re.escape(symbol_lower)}\b"
            )
            catch_binding = re.compile(
                rf"(?i)^CATCH\s+{re.escape(symbol_lower)}\b"
            )

            for index, line in enumerate(lines):
                if line_scopes[index] != scope_id or index == annotation_index:
                    continue
                stripped = line.strip()
                if not stripped:
                    continue
                upper = stripped.upper()
                if (
                    upper.startswith("COMMENT")
                    or stripped.startswith("#")
                    or stripped.startswith("//")
                ):
                    continue
                # Any separate INPUT occurrence gives the symbol an independent
                # source role, including another shape annotation.
                if re.match(r"(?i)^INPUT\b", stripped) and word.search(stripped):
                    return True
                if (
                    assignment.match(stripped)
                    or loop_binding.match(stripped)
                    or catch_binding.match(stripped)
                ):
                    return True
            return False

        eligible = {
            key: value
            for key, value in unique.items()
            if not is_bound_in_scope(key[0], key[1], value[1])
        }
        if not eligible:
            return source, []

        def replace_identifier(
            line: str,
            symbol_lower: str,
            collection: str,
        ) -> str:
            stripped = line.lstrip()
            upper = stripped.upper()
            if (
                upper.startswith("COMMENT")
                or stripped.startswith("#")
                or stripped.startswith("//")
                or re.match(
                    r"(?i)^(?:INPUT|FUNCTION|PROCEDURE|METHOD|CONSTRUCTOR|CLASS|PROPERTY)\b",
                    stripped,
                )
            ):
                return line

            result: list[str] = []
            i = 0
            quote: str | None = None
            escaped = False
            while i < len(line):
                ch = line[i]
                if quote is not None:
                    result.append(ch)
                    if escaped:
                        escaped = False
                    elif ch == "\\":
                        escaped = True
                    elif ch == quote:
                        quote = None
                    i += 1
                    continue

                if ch in {'"', "'"}:
                    quote = ch
                    result.append(ch)
                    i += 1
                    continue

                if line.startswith("//", i) or ch == "#":
                    result.append(line[i:])
                    break

                comment = re.match(r"(?i)COMMENT\b", line[i:])
                if comment is not None:
                    before = line[i - 1] if i > 0 else " "
                    if i == 0 or not (before.isalnum() or before == "_"):
                        result.append(line[i:])
                        break

                identifier = re.match(r"[A-Za-z_]\w*", line[i:])
                if identifier is not None:
                    token = identifier.group(0)
                    end = i + len(token)
                    if token.lower() == symbol_lower:
                        prev = i - 1
                        while prev >= 0 and line[prev].isspace():
                            prev -= 1
                        nxt = end
                        while nxt < len(line) and line[nxt].isspace():
                            nxt += 1
                        is_member_name = prev >= 0 and line[prev] == "."
                        is_call_name = nxt < len(line) and line[nxt] == "("
                        if not is_member_name and not is_call_name:
                            result.append(f"LENGTH OF {collection}")
                        else:
                            result.append(token)
                    else:
                        result.append(token)
                    i = end
                    continue

                result.append(ch)
                i += 1

            return "".join(result)

        out = list(lines)
        transformations: list[SourceTransformation] = []
        for index, line in enumerate(lines):
            scope_id = line_scopes[index]
            current = line
            for (
                candidate_scope,
                symbol_lower,
            ), (
                collection,
                annotation_index,
            ) in eligible.items():
                if candidate_scope != scope_id or index == annotation_index:
                    continue
                current = replace_identifier(current, symbol_lower, collection)
            if current != line:
                out[index] = current
                transformations.append(
                    SourceTransformation(
                        line=index + 1,
                        rule="GC212",
                        source=line,
                        target=current,
                    )
                )

        transformed = "\n".join(out)
        if source.endswith("\n"):
            transformed += "\n"
        return transformed, transformations

    def _normalise_linked_matrix_multiplication_dimensions(
        self,
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        """Recover linked MxN / NxP matrix dimensions from explicit source shape evidence.

        GC224 is deliberately narrower than a general matrix-shape inference rule. It
        recognises the complete source-supplied multiplication skeleton::

            INPUT A (M x N), B (N x P)
            INIT C as M x P matrix
            FOR i from 0 to M-1:
                FOR j from 0 to P-1:
                    sum = 0
                    FOR k from 0 to N-1:
                        sum += A[i][k] * B[k][j]
                    C[i][j] = sum
            RETURN C

        The annotations make M, N and P descriptive shape symbols rather than runtime
        inputs. Under the exact guarded structure, M is represented by LENGTH OF A,
        N by LENGTH OF B, and P by LENGTH OF B[0]. The output allocation uses the
        existing create_matrix intrinsic. If the source does not state an initial cell
        value, the allocated cells use NONE; an explicit zero initialiser remains zero.
        No multiplication logic, loop, accumulator, index relation, or dimension
        parameter is invented.

        The rule refuses explicit routine declarations, independently bound dimensions,
        alternate loop bounds, altered accumulation expressions, conditional result
        writes, unrelated uses of M/N/P, or a target that is not returned directly.
        """

        if re.search(r"(?im)^[ \t]*(?:FUNCTION|PROCEDURE|METHOD|CONSTRUCTOR)\b", source):
            return source, []

        lines = source.splitlines()
        if not lines:
            return source, []

        annotation_re = re.compile(
            r"^(?P<indent>[ \t]*)INPUT\s+"
            r"(?P<a>[A-Za-z_]\w*)\s*\(\s*(?P<m>[A-Za-z_]\w*)\s*x\s*(?P<n>[A-Za-z_]\w*)\s*\)\s*,\s*"
            r"(?P<b>[A-Za-z_]\w*)\s*\(\s*(?P=n)\s*x\s*(?P<p>[A-Za-z_]\w*)\s*\)\s*$",
            re.I,
        )
        annotations = [
            (index, match)
            for index, line in enumerate(lines)
            if (match := annotation_re.fullmatch(line)) is not None
        ]
        if len(annotations) != 1:
            return source, []

        annotation_index, annotation = annotations[0]
        base_indent = annotation.group("indent")
        a_name = annotation.group("a")
        b_name = annotation.group("b")
        m_dim = annotation.group("m")
        n_dim = annotation.group("n")
        p_dim = annotation.group("p")
        if len({m_dim.lower(), n_dim.lower(), p_dim.lower()}) != 3:
            return source, []

        dims = (m_dim, n_dim, p_dim)

        def independently_bound(symbol: str) -> bool:
            escaped = re.escape(symbol)
            word = re.compile(rf"(?i)\b{escaped}\b")
            for index, line in enumerate(lines):
                if index == annotation_index:
                    continue
                stripped = line.strip()
                if not stripped or stripped.startswith(("#", "//")) or stripped.upper().startswith("COMMENT"):
                    continue
                if re.match(r"(?i)^INPUT\b", stripped) and word.search(stripped):
                    return True
                if re.match(rf"(?i)^{escaped}\s*(?:<-|=|←)", stripped):
                    return True
                if re.match(rf"(?i)^FOR\s+(?:EACH\s+)?{escaped}\b", stripped):
                    return True
            return False

        if any(independently_bound(dim) for dim in dims):
            return source, []

        init_re = re.compile(
            rf"^{re.escape(base_indent)}INIT\s+(?P<target>[A-Za-z_]\w*)\s+AS\s+"
            rf"{re.escape(m_dim)}\s*x\s*{re.escape(p_dim)}\s+MATRIX"
            rf"(?P<zero_init>\s+INITIALI[ZS]ED\s+(?:WITH|TO)\s+0)?\s*$",
            re.I,
        )
        init_matches = [
            (index, match)
            for index, line in enumerate(lines)
            if (match := init_re.fullmatch(line)) is not None
        ]
        if len(init_matches) != 1:
            return source, []
        init_index, init_match = init_matches[0]
        target = init_match.group("target")
        matrix_fill = "0" if init_match.group("zero_init") else "NONE"

        row_re = re.compile(
            rf"^(?P<indent>[ \t]*)FOR\s+(?P<i>[A-Za-z_]\w*)\s+FROM\s+0\s+TO\s+"
            rf"(?:\(\s*)?{re.escape(m_dim)}\s*-\s*1(?:\s*\))?\s*(?:DO)?\s*:?\s*$",
            re.I,
        )
        col_re = re.compile(
            rf"^(?P<indent>[ \t]*)FOR\s+(?P<j>[A-Za-z_]\w*)\s+FROM\s+0\s+TO\s+"
            rf"(?:\(\s*)?{re.escape(p_dim)}\s*-\s*1(?:\s*\))?\s*(?:DO)?\s*:?\s*$",
            re.I,
        )
        inner_re = re.compile(
            rf"^(?P<indent>[ \t]*)FOR\s+(?P<k>[A-Za-z_]\w*)\s+FROM\s+0\s+TO\s+"
            rf"(?:\(\s*)?{re.escape(n_dim)}\s*-\s*1(?:\s*\))?\s*(?:DO)?\s*:?\s*$",
            re.I,
        )

        matched = None
        for row_index in range(init_index + 1, len(lines)):
            row_match = row_re.fullmatch(lines[row_index])
            if row_match is None or row_match.group("indent") != base_indent:
                continue
            row_indent = row_match.group("indent")
            i_name = row_match.group("i")

            for col_index in range(row_index + 1, len(lines)):
                col_match = col_re.fullmatch(lines[col_index])
                if col_match is None:
                    if lines[col_index].strip() and len(lines[col_index]) - len(lines[col_index].lstrip()) <= len(row_indent):
                        break
                    continue
                col_indent = col_match.group("indent")
                if not col_indent.startswith(row_indent) or len(col_indent) <= len(row_indent):
                    continue
                indent_unit = col_indent[len(row_indent):]
                if not indent_unit:
                    continue
                j_name = col_match.group("j")
                col_body_indent = col_indent + indent_unit

                sum_assign_re = re.compile(
                    rf"^{re.escape(col_body_indent)}(?P<sum>[A-Za-z_]\w*)\s*(?:<-|=|←)\s*0\s*$",
                    re.I,
                )
                sum_index = None
                sum_name = None
                inner_index = None
                inner_match = None
                for candidate in range(col_index + 1, len(lines)):
                    candidate_line = lines[candidate]
                    if candidate_line.strip() and not candidate_line.startswith(col_body_indent):
                        break
                    if sum_index is None:
                        sm = sum_assign_re.fullmatch(candidate_line)
                        if sm is not None:
                            sum_index = candidate
                            sum_name = sm.group("sum")
                            continue
                    im = inner_re.fullmatch(candidate_line)
                    if im is not None and im.group("indent") == col_body_indent:
                        inner_index = candidate
                        inner_match = im
                        break
                if sum_index is None or inner_index is None or inner_match is None or sum_name is None:
                    continue
                if sum_index >= inner_index:
                    continue

                k_name = inner_match.group("k")
                inner_body_indent = col_body_indent + indent_unit
                product_pattern = (
                    rf"{re.escape(a_name)}\s*\[\s*{re.escape(i_name)}\s*\]\s*"
                    rf"\[\s*{re.escape(k_name)}\s*\]\s*\*\s*"
                    rf"{re.escape(b_name)}\s*\[\s*{re.escape(k_name)}\s*\]\s*"
                    rf"\[\s*{re.escape(j_name)}\s*\]"
                )
                # Earlier operator normalisation may already have expanded the
                # source-supplied ``sum += product`` into ``sum <- sum + product``.
                # Accept exactly those two equivalent surfaces; no alternate
                # accumulation expression is inferred.
                accumulate_re = re.compile(
                    rf"^{re.escape(inner_body_indent)}{re.escape(sum_name)}\s*"
                    rf"(?:\+=\s*{product_pattern}|(?:<-|=|←)\s*{re.escape(sum_name)}\s*\+\s*{product_pattern})\s*$",
                    re.I,
                )
                accumulate_index = None
                for candidate in range(inner_index + 1, len(lines)):
                    candidate_line = lines[candidate]
                    if candidate_line.strip() and not candidate_line.startswith(inner_body_indent):
                        break
                    if accumulate_re.fullmatch(candidate_line):
                        accumulate_index = candidate
                        break
                if accumulate_index is None:
                    continue

                write_re = re.compile(
                    rf"^{re.escape(col_body_indent)}{re.escape(target)}\s*"
                    rf"\[\s*{re.escape(i_name)}\s*\]\s*\[\s*{re.escape(j_name)}\s*\]\s*"
                    rf"(?:<-|=|←)\s*{re.escape(sum_name)}\s*$",
                    re.I,
                )
                write_index = None
                for candidate in range(inner_index + 1, len(lines)):
                    candidate_line = lines[candidate]
                    if candidate_line.strip() and not candidate_line.startswith(col_body_indent):
                        break
                    if write_re.fullmatch(candidate_line):
                        write_index = candidate
                        break
                if write_index is None or write_index <= accumulate_index:
                    continue

                matched = (
                    row_index, row_match, col_index, col_match,
                    inner_index, inner_match, sum_index, accumulate_index, write_index,
                )
                break
            if matched is not None:
                break

        if matched is None:
            return source, []

        if not any(
            re.fullmatch(rf"{re.escape(base_indent)}RETURN\s+{re.escape(target)}\s*", line, re.I)
            for line in lines
        ):
            return source, []

        row_index, row_match, col_index, col_match, inner_index, inner_match, *_ = matched

        # The dimension symbols may occur only in the annotation, the exact result
        # allocation, and the three exact loop headers that GC224 rewrites.
        allowed_dim_lines = {annotation_index, init_index, row_index, col_index, inner_index}
        for index, line in enumerate(lines):
            if index in allowed_dim_lines:
                continue
            if any(re.search(rf"(?i)\b{re.escape(dim)}\b", line) for dim in dims):
                return source, []

        m_expr = f"LENGTH OF {a_name}"
        n_expr = f"LENGTH OF {b_name}"
        p_expr = f"LENGTH OF {b_name}[0]"

        out = list(lines)
        transformations: list[SourceTransformation] = []

        replacements = [
            (
                init_index,
                f"{base_indent}{target} <- CALL create_matrix({m_expr}, {p_expr}, {matrix_fill})",
            ),
            (
                row_index,
                f"{row_match.group('indent')}FOR {row_match.group('i')} from 0 to {m_expr}-1:",
            ),
            (
                col_index,
                f"{col_match.group('indent')}FOR {col_match.group('j')} from 0 to {p_expr}-1:",
            ),
            (
                inner_index,
                f"{inner_match.group('indent')}FOR {inner_match.group('k')} from 0 to {n_expr}-1:",
            ),
        ]
        for index, target_line in replacements:
            out[index] = target_line
            transformations.append(
                SourceTransformation(
                    line=index + 1,
                    rule="GC224",
                    source=lines[index],
                    target=target_line,
                )
            )

        transformed = "\n".join(out)
        if source.endswith("\n"):
            transformed += "\n"
        return transformed, transformations

    def _normalise_rectangular_matrix_allocation_from_shape(
        self,
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        """Recover an executable rectangular result matrix from explicit shape evidence.

        GC223 is intentionally narrow. It recognises an unnamed top-level form such as::

            INPUT A, B (same dimensions R x C)
            INIT result as R x C matrix
            FOR i from 0 to R-1:
                FOR j from 0 to C-1:
                    result[i][j] = ...
            RETURN result

        The annotation establishes that ``R`` and ``C`` are descriptive shape
        symbols rather than separately supplied scalar inputs. The rule uses the
        first explicitly supplied matrix as the deterministic shape witness,
        materialising ``LENGTH OF A`` and ``LENGTH OF A[0]``. Because the source
        does not state an initial cell value, the allocated cells use ``NONE``;
        the exact matching nested loops then supply the source-defined writes to
        every ``result[i][j]`` cell.

        The rule refuses explicit routine declarations, independently bound
        dimension symbols, missing/mismatched loops, conditional/nested writes,
        or a result that is not returned directly.
        """

        if re.search(r"(?im)^[ \t]*(?:FUNCTION|PROCEDURE|METHOD|CONSTRUCTOR)\b", source):
            return source, []

        lines = source.splitlines()
        if not lines:
            return source, []

        annotation_re = re.compile(
            r"^(?P<indent>[ \t]*)INPUT\s+"
            r"(?P<first>[A-Za-z_]\w*)\s*,\s*(?P<second>[A-Za-z_]\w*)\s*"
            r"\(\s*same\s+dimensions\s+"
            r"(?P<rows>[A-Za-z_]\w*)\s*x\s*(?P<cols>[A-Za-z_]\w*)\s*\)\s*$",
            re.I,
        )
        annotations = [
            (index, match)
            for index, line in enumerate(lines)
            if (match := annotation_re.fullmatch(line)) is not None
        ]
        if len(annotations) != 1:
            return source, []

        annotation_index, annotation = annotations[0]
        base_indent = annotation.group("indent")
        first = annotation.group("first")
        rows = annotation.group("rows")
        cols = annotation.group("cols")
        if rows.lower() == cols.lower():
            return source, []

        # R/C are annotation-only dimensions. Any separate source binding makes
        # them real runtime variables and therefore ineligible for recovery.
        def independently_bound(symbol: str) -> bool:
            escaped = re.escape(symbol)
            word = re.compile(rf"(?i)\b{escaped}\b")
            for index, line in enumerate(lines):
                if index == annotation_index:
                    continue
                stripped = line.strip()
                if not stripped or stripped.startswith(("#", "//")) or stripped.upper().startswith("COMMENT"):
                    continue
                if re.match(r"(?i)^INPUT\b", stripped) and word.search(stripped):
                    return True
                if re.match(rf"(?i)^{escaped}\s*(?:<-|=|←)", stripped):
                    return True
                if re.match(rf"(?i)^FOR\s+(?:EACH\s+)?{escaped}\b", stripped):
                    return True
            return False

        if independently_bound(rows) or independently_bound(cols):
            return source, []

        init_re = re.compile(
            rf"^{re.escape(base_indent)}INIT\s+(?P<target>[A-Za-z_]\w*)\s+AS\s+"
            rf"{re.escape(rows)}\s*x\s*{re.escape(cols)}\s+MATRIX\s*$",
            re.I,
        )
        init_matches = [
            (index, match)
            for index, line in enumerate(lines)
            if (match := init_re.fullmatch(line)) is not None
        ]
        if len(init_matches) != 1:
            return source, []
        init_index, init_match = init_matches[0]
        target = init_match.group("target")

        row_loop_re = re.compile(
            rf"^(?P<indent>[ \t]*)FOR\s+(?P<iterator>[A-Za-z_]\w*)\s+FROM\s+0\s+TO\s+"
            rf"(?:\(\s*)?{re.escape(rows)}\s*-\s*1(?:\s*\))?\s*(?:DO)?\s*:?\s*$",
            re.I,
        )
        col_loop_template = (
            r"^(?P<indent>[ \t]*)FOR\s+(?P<iterator>[A-Za-z_]\w*)\s+FROM\s+0\s+TO\s+"
            + rf"(?:\(\s*)?{re.escape(cols)}\s*-\s*1(?:\s*\))?\s*(?:DO)?\s*:?\s*$"
        )
        col_loop_re = re.compile(col_loop_template, re.I)

        matched_shape = None
        for row_index in range(init_index + 1, len(lines)):
            row_match = row_loop_re.fullmatch(lines[row_index])
            if row_match is None:
                continue
            row_indent = row_match.group("indent")
            if row_indent != base_indent:
                continue
            row_iterator = row_match.group("iterator")

            for col_index in range(row_index + 1, len(lines)):
                col_match = col_loop_re.fullmatch(lines[col_index])
                if col_match is None:
                    # Once another top-level executable statement starts, this
                    # candidate row loop cannot own a later column loop.
                    if lines[col_index].strip() and len(lines[col_index]) - len(lines[col_index].lstrip()) <= len(row_indent):
                        break
                    continue
                col_indent = col_match.group("indent")
                if not col_indent.startswith(row_indent) or len(col_indent) <= len(row_indent):
                    continue
                indent_unit = col_indent[len(row_indent):]
                if not indent_unit:
                    continue
                col_iterator = col_match.group("iterator")
                direct_body_indent = col_indent + indent_unit

                write_re = re.compile(
                    rf"^{re.escape(direct_body_indent)}{re.escape(target)}\s*"
                    rf"\[\s*{re.escape(row_iterator)}\s*\]\s*"
                    rf"\[\s*{re.escape(col_iterator)}\s*\]\s*(?:<-|=|←)\s*.+$",
                    re.I,
                )
                write_index = None
                for candidate in range(col_index + 1, len(lines)):
                    candidate_line = lines[candidate]
                    if candidate_line.strip() and not candidate_line.startswith(direct_body_indent):
                        break
                    if write_re.fullmatch(candidate_line):
                        write_index = candidate
                        break
                if write_index is None:
                    continue

                matched_shape = (
                    row_index,
                    row_match,
                    col_index,
                    col_match,
                    write_index,
                )
                break
            if matched_shape is not None:
                break

        if matched_shape is None:
            return source, []

        if not any(
            re.fullmatch(
                rf"{re.escape(base_indent)}RETURN\s+{re.escape(target)}\s*",
                line,
                re.I,
            )
            for line in lines
        ):
            return source, []

        row_index, row_match, col_index, col_match, _write_index = matched_shape
        first_length = f"LENGTH OF {first}"
        first_width = f"LENGTH OF {first}[0]"

        out = list(lines)
        transformations: list[SourceTransformation] = []

        init_target = (
            f"{base_indent}{target} <- CALL create_matrix("
            f"{first_length}, {first_width}, NONE)"
        )
        out[init_index] = init_target
        transformations.append(
            SourceTransformation(
                line=init_index + 1,
                rule="GC223",
                source=lines[init_index],
                target=init_target,
            )
        )

        row_target = (
            f"{row_match.group('indent')}FOR {row_match.group('iterator')} from 0 to "
            f"{first_length}-1:"
        )
        out[row_index] = row_target
        transformations.append(
            SourceTransformation(
                line=row_index + 1,
                rule="GC223",
                source=lines[row_index],
                target=row_target,
            )
        )

        col_target = (
            f"{col_match.group('indent')}FOR {col_match.group('iterator')} from 0 to "
            f"{first_width}-1:"
        )
        out[col_index] = col_target
        transformations.append(
            SourceTransformation(
                line=col_index + 1,
                rule="GC223",
                source=lines[col_index],
                target=col_target,
            )
        )

        transformed = "\n".join(out)
        if source.endswith("\n"):
            transformed += "\n"
        return transformed, transformations

    def _normalise_direct_top_level_input_wrapper(
        self,
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        """Bind bare top-level INPUT declarations directly to unnamed_function.

        This is intentionally narrower than generic input normalisation.  It
        applies only when the same program already satisfies the approved
        neutral-wrapper policy: at least one bare top-level INPUT declaration,
        an observable OUTPUT/RETURN, and no source-declared FUNCTION/PROCEDURE.
        Expected-fail forms are intercepted earlier in ``process``.
        """

        if re.search(r"(?im)^[ \t]*(?:FUNCTION|PROCEDURE)\b", source):
            return source, []
        if not re.search(r"(?im)^[ \t]*(?:OUTPUT|RETURN)\b", source):
            return source, []

        lines = source.splitlines()
        non_empty = [i for i, line in enumerate(lines) if line.strip()]
        if not non_empty:
            return source, []

        # Strip only a single top-level BEGIN/END presentation wrapper.
        start = non_empty[0]
        end = non_empty[-1]
        if (
            lines[start].strip().upper() == "BEGIN"
            and lines[end].strip().upper() == "END"
        ):
            prefix = lines[:start]
            inner = textwrap.dedent("\n".join(lines[start + 1:end])).splitlines()
            suffix = lines[end + 1:]
            lines = prefix + inner + suffix

        parameter_names: list[str] = []
        input_line_indexes: set[int] = set()

        for index, line in enumerate(lines):
            match = re.fullmatch(r"[ \t]*INPUT\s+(.+?)[ \t]*", line, re.I)
            if match is None or "INPUT(" in line.upper():
                continue

            names: list[str] = []
            for part in match.group(1).split(","):
                candidate = part.strip()
                candidate = re.sub(r"\s*\([^)]*\)\s*$", "", candidate).strip()
                candidate = re.sub(
                    r"\s+\b(?:same|of|with)\b.*$",
                    "",
                    candidate,
                    flags=re.I,
                ).strip()
                if not re.fullmatch(r"[A-Za-z_]\w*", candidate):
                    names = []
                    break
                names.append(candidate)

            if not names:
                continue

            input_line_indexes.add(index)
            for name in names:
                if name not in parameter_names:
                    parameter_names.append(name)

        if not parameter_names:
            return source, []

        body_lines = [
            line for index, line in enumerate(lines)
            if index not in input_line_indexes
        ]
        # Remove leading/trailing blank lines introduced by stripping INPUT or
        # BEGIN/END, but preserve internal spacing for audit readability.
        while body_lines and not body_lines[0].strip():
            body_lines.pop(0)
        while body_lines and not body_lines[-1].strip():
            body_lines.pop()

        body = textwrap.dedent("\n".join(body_lines))
        wrapped_lines = [
            f"FUNCTION unnamed_function ACCEPTS({', '.join(parameter_names)})"
        ]
        wrapped_lines.extend(
            ("    " + line) if line.strip() else ""
            for line in body.splitlines()
        )
        wrapped_lines.append("ENDFUNCTION")
        transformed = "\n".join(wrapped_lines)

        if transformed == source:
            return source, []
        return transformed, [
            SourceTransformation(
                line=1,
                rule="GC173",
                source=source,
                target=transformed,
            )
        ]


    def _normalise_input_helper_final_return_wrapper(
        self,
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        """Recover an omitted neutral outer routine around input + helpers + return.

        GC219 is intentionally limited to indentation-style generic pseudocode.
        It applies only when:

        * one or more bare top-level ``INPUT`` declarations occur before helpers;
        * one or more complete top-level ``FUNCTION name(...):`` or
          ``PROCEDURE name(...):`` helpers follow;
        * the only other non-comment top-level statement is one final ``RETURN``;
        * that final return directly calls at least one supplied helper; and
        * no explicit top-level class/container or canonical END declaration is
          already present.

        The transformation supplies only ``FUNCTION unnamed_function`` and
        promotes the bare INPUT names to its parameters. Helper bodies and the
        final return expression are preserved for later normalisation. Missing
        helper dependencies inside those routines therefore remain missing.
        """

        if re.search(r"(?im)^[ \t]*(?:CLASS|ENDCLASS|ENDFUNCTION|ENDPROCEDURE)\b", source):
            return source, []

        lines = source.splitlines()
        top_level: list[tuple[int, str]] = []
        for index, line in enumerate(lines):
            if not line.strip():
                continue
            if line[: len(line) - len(line.lstrip())]:
                continue
            stripped = line.strip()
            if stripped.startswith(("#", "//")):
                continue
            top_level.append((index, stripped))

        if len(top_level) < 3:
            return source, []

        parameter_names: list[str] = []
        input_indexes: set[int] = set()
        helper_names: list[str] = []
        saw_helper = False
        return_indexes: list[int] = []

        for index, stripped in top_level:
            input_match = re.fullmatch(r"INPUT\s+(.+?)", stripped, re.I)
            if input_match is not None:
                if saw_helper or return_indexes or "INPUT(" in stripped.upper():
                    return source, []
                names: list[str] = []
                for part in input_match.group(1).split(","):
                    candidate = part.strip()
                    candidate = re.sub(r"\s*\([^)]*\)\s*$", "", candidate).strip()
                    if not re.fullmatch(r"[A-Za-z_]\w*", candidate):
                        return source, []
                    names.append(candidate)
                if not names:
                    return source, []
                input_indexes.add(index)
                for name in names:
                    if name not in parameter_names:
                        parameter_names.append(name)
                continue

            helper_match = re.fullmatch(
                r"(?:FUNCTION|PROCEDURE)\s+([A-Za-z_]\w*)\s*\([^)]*\)\s*:\s*",
                stripped,
                re.I,
            )
            if helper_match is not None:
                if return_indexes:
                    return source, []
                saw_helper = True
                helper_names.append(helper_match.group(1))
                continue

            if re.match(r"RETURN\b", stripped, re.I):
                return_indexes.append(index)
                continue

            return source, []

        if not parameter_names or not helper_names or len(return_indexes) != 1:
            return source, []

        final_index = return_indexes[0]
        if final_index != top_level[-1][0]:
            return source, []
        final_return = lines[final_index].strip()
        if not any(
            re.search(rf"\b{re.escape(name)}\s*\(", final_return, re.I)
            for name in helper_names
        ):
            return source, []

        body_lines = [
            line for index, line in enumerate(lines)
            if index not in input_indexes
        ]
        while body_lines and not body_lines[0].strip():
            body_lines.pop(0)
        while body_lines and not body_lines[-1].strip():
            body_lines.pop()

        body = textwrap.dedent("\n".join(body_lines))
        wrapped_lines = [
            f"FUNCTION unnamed_function ACCEPTS({', '.join(parameter_names)})"
        ]
        wrapped_lines.extend(
            ("    " + line) if line.strip() else ""
            for line in body.splitlines()
        )
        wrapped_lines.append("ENDFUNCTION")
        transformed = "\n".join(wrapped_lines)

        return transformed, [
            SourceTransformation(
                line=1,
                rule="GC219",
                source=source,
                target=transformed,
            )
        ]


    def _normalise_stateful_adt_function_container(
        self,
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        """Recover a zero-argument stateful ADT written as a function container.

        Strong source evidence can show that an outer ``FUNCTION Name()`` is
        being used as a class/ADT container: it creates persistent state and
        supplies multiple nested operations that all use that state, but returns
        no value that could expose those operations.  GC196 recovers that
        structural misclassification using the frozen AJ v1.0 class syntax:

        * outer container -> ``CLASS``;
        * persistent state -> ``PROPERTY`` declarations;
        * original state initialisation -> zero-argument ``CONSTRUCTOR``;
        * nested operations -> ``METHOD`` declarations;
        * state references in methods -> ``THIS.<property>``.

        No constructor parameter is invented.  In particular, a source state
        assignment such as ``data <- EMPTY LIST`` remains internal
        initialisation as ``PROPERTY THIS.data <- EMPTY LIST``.

        Safeguards deliberately keep this narrow:
        * the source must consist of one top-level zero-argument FUNCTION with
          a type-like (capitalised) source name;
        * at least one plain persistent-state assignment must precede methods;
        * at least two nested functions must be present;
        * every nested function must reference at least one declared state name;
        * at least one nested operation must explicitly mutate declared state;
        * the outer body may contain only state assignments, comments/blank lines,
          and nested function definitions (no outer RETURN/CALL/control flow);
        * nested function bodies are preserved except for explicit state-reference
          qualification with ``THIS.``.
        """
        lines = source.splitlines()
        nonblank = [i for i, line in enumerate(lines) if line.strip()]
        if len(nonblank) < 4:
            return source, []

        first_i, last_i = nonblank[0], nonblank[-1]
        outer = re.fullmatch(
            r"(?i)\s*FUNCTION\s+([A-Za-z_]\w*)\s+ACCEPTS\(\s*\)\s*",
            lines[first_i],
        )
        if outer is None or not re.fullmatch(r"(?i)\s*ENDFUNCTION\s*", lines[last_i]):
            return source, []

        # GC196 is a structural recovery from a function-shaped ADT/type
        # declaration to CLASS.  Require a type-like source name rather than
        # reclassifying ordinary lower-case helper/factory functions.  This is
        # evidence for the recovery, not a general AJ naming restriction.
        outer_name = outer.group(1)
        if not outer_name[0].isupper():
            return source, []

        function_depth = 0
        outer_end = None
        nested_ranges: list[tuple[int, int]] = []
        nested_start = None
        state_assignments: list[tuple[int, str, str]] = []
        state_names: set[str] = set()
        first_nested = None
        forbidden_outer_statement = False
        outer_comments: list[str] = []

        for i in range(first_i, last_i + 1):
            stripped = lines[i].strip()
            if re.match(r"(?i)^FUNCTION\b", stripped):
                function_depth += 1
                if function_depth == 2:
                    if first_nested is None:
                        first_nested = i
                    nested_start = i
                continue

            if re.fullmatch(r"(?i)ENDFUNCTION", stripped):
                if function_depth == 2 and nested_start is not None:
                    nested_ranges.append((nested_start, i))
                    nested_start = None
                function_depth -= 1
                if function_depth == 0:
                    outer_end = i
                    break
                continue

            if function_depth == 1 and stripped:
                if stripped.upper().startswith("COMMENT"):
                    if first_nested is None:
                        outer_comments.append(lines[i])
                    continue
                assignment = re.fullmatch(
                    r"([A-Za-z_]\w*)\s*<-\s*(.+)",
                    stripped,
                )
                if assignment is not None and first_nested is None:
                    name = assignment.group(1)
                    rhs = assignment.group(2).strip()
                    state_assignments.append((i, name, rhs))
                    state_names.add(name)
                    continue
                forbidden_outer_statement = True

        if outer_end != last_i or function_depth != 0:
            return source, []
        if forbidden_outer_statement or not state_names or len(nested_ranges) < 2:
            return source, []

        def clearly_mutates_state(body: str) -> bool:
            """Return True only for explicit state-changing source operations.

            A shared-state read is not enough to justify class recovery.  At
            least one nested operation must visibly mutate the state through an
            AJ assignment or a known destructive collection operation.  This
            avoids turning read-only lexical helper groups into classes merely
            because several helpers mention the same outer value.
            """
            for raw_line in body.splitlines():
                stripped = raw_line.strip()
                if not stripped or stripped.upper().startswith("COMMENT"):
                    continue
                for name in state_names:
                    n = re.escape(name)
                    if re.match(rf"^{n}(?:\s*\[.*?\])?\s*<-", stripped):
                        return True
                    if re.search(rf"(?i)^APPEND\b.+\bTO\s+{n}\b", stripped):
                        return True
                    if re.search(rf"(?i)^INSERT\b.+\b(?:INTO|TO)\s+{n}\b", stripped):
                        return True
                    if re.search(rf"(?i)\bREMOVE\b.+\bFROM\s+{n}\b", stripped):
                        return True
                    if re.search(rf"(?i)\bREMOVE\s+LAST\s+ITEM\s+FROM\s+{n}\b", stripped):
                        return True
                    if re.search(rf"(?i)\bPUSH\s*\(.*?,\s*{n}\s*\)", stripped):
                        return True
                    if re.search(rf"(?i)\bPOP\s*\(\s*{n}\s*\)", stripped):
                        return True
            return False

        saw_clear_state_mutation = False
        for start_i, end_i in nested_ranges:
            body = "\n".join(lines[start_i + 1:end_i])
            if not any(re.search(rf"\b{re.escape(name)}\b", body) for name in state_names):
                return source, []
            saw_clear_state_mutation = saw_clear_state_mutation or clearly_mutates_state(body)

        if not saw_clear_state_mutation:
            return source, []

        class_indent = re.match(r"^\s*", lines[first_i]).group(0)
        body_indent = class_indent + "    "
        inner_indent = body_indent + "    "

        def property_type(rhs: str) -> str | None:
            match = re.fullmatch(
                r"EMPTY\s+(LIST|DICTIONARY|STRING|SET|TUPLE)",
                rhs,
                flags=re.IGNORECASE,
            )
            return match.group(1).upper() if match else None

        def qualify_state_references(line: str) -> str:
            # COMMENT payloads and quoted string contents are not program
            # identifiers and must remain byte-for-byte unchanged.
            stripped = line.lstrip()
            if stripped.upper().startswith("COMMENT"):
                return line

            result: list[str] = []
            i = 0
            quote: str | None = None
            escaped = False
            while i < len(line):
                ch = line[i]
                if quote is not None:
                    result.append(ch)
                    if escaped:
                        escaped = False
                    elif ch == "\\":
                        escaped = True
                    elif ch == quote:
                        quote = None
                    i += 1
                    continue
                if ch in {'"', "'"}:
                    quote = ch
                    result.append(ch)
                    i += 1
                    continue
                identifier = re.match(r"[A-Za-z_]\w*", line[i:])
                if identifier:
                    token = identifier.group(0)
                    previous_text = "".join(result)
                    already_qualified = previous_text.endswith("THIS.")
                    if token in state_names and not already_qualified:
                        result.append("THIS." + token)
                    else:
                        result.append(token)
                    i += len(token)
                    continue
                result.append(ch)
                i += 1
            return "".join(result)

        transformed_lines: list[str] = []
        transformed_lines.extend(lines[:first_i])
        transformed_lines.append(f"{class_indent}CLASS {outer.group(1)}")

        # Preserve any class-level comments that appeared before state.
        transformed_lines.extend(outer_comments)
        for _line_index, name, rhs in state_assignments:
            declared = property_type(rhs)
            suffix = f" AS {declared}" if declared else ""
            transformed_lines.append(f"{body_indent}PROPERTY {name}{suffix}")

        transformed_lines.append("")
        transformed_lines.append(f"{body_indent}CONSTRUCTOR ACCEPTS()")
        for _line_index, name, rhs in state_assignments:
            transformed_lines.append(
                f"{inner_indent}PROPERTY THIS.{name} <- {rhs}"
            )
        transformed_lines.append(f"{body_indent}ENDCONSTRUCTOR")

        for start_i, end_i in nested_ranges:
            transformed_lines.append("")
            header = lines[start_i]
            header_match = re.fullmatch(
                r"(?i)(\s*)FUNCTION\s+([A-Za-z_]\w*)\s+ACCEPTS(\s*\(.*\)\s*)",
                header,
            )
            if header_match is None:
                return source, []
            method_indent = header_match.group(1)
            transformed_lines.append(
                f"{method_indent}METHOD {header_match.group(2)} ACCEPTS{header_match.group(3)}"
            )
            for body_line in lines[start_i + 1:end_i]:
                transformed_lines.append(qualify_state_references(body_line))
            end_indent = re.match(r"^\s*", lines[end_i]).group(0)
            transformed_lines.append(f"{end_indent}ENDMETHOD")

        transformed_lines.append(f"{class_indent}ENDCLASS")
        transformed_lines.extend(lines[outer_end + 1:])
        transformed = "\n".join(transformed_lines)
        if source.endswith("\n"):
            transformed += "\n"

        return transformed, [
            SourceTransformation(
                line=first_i + 1,
                rule="GC196",
                source=source,
                target=transformed,
            )
        ]


    def _normalise_explicit_stateful_class(
        self,
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        """Canonicalise a legacy explicit CLASS with instance-like state/methods.

        This is the explicit-CLASS counterpart of GC196.  It is intentionally
        conservative: the whole source must be one class; plain self-contained
        state assignments must precede one or more FUNCTION methods; every method
        must reference declared state; and list-backed state may not be the target
        of indexed writes (which could require inventing storage-growth semantics).

        When those conditions hold, the source already supplies the class, state,
        initial values and operations.  GC203 therefore performs only frozen-AJ
        representation work: state -> PROPERTY/CONSTRUCTOR, FUNCTION -> METHOD,
        state references -> THIS.<name>, and a missing terminal ENDCLASS -> ENDCLASS.
        """
        lines = source.splitlines()
        nonblank = [i for i, line in enumerate(lines) if line.strip()]
        if len(nonblank) < 3:
            return source, []

        first_i = nonblank[0]
        last_i = nonblank[-1]
        header = re.fullmatch(
            r"(?i)\s*CLASS\s+([A-Za-z_]\w*)(?:\s+ACCEPTS\s*\(\s*\))?\s*",
            lines[first_i],
        )
        if header is None:
            return source, []

        has_endclass = bool(re.fullmatch(r"(?i)\s*ENDCLASS\s*", lines[last_i]))
        body_end = last_i if has_endclass else len(lines)

        function_depth = 0
        method_start: int | None = None
        method_ranges: list[tuple[int, int]] = []
        state_assignments: list[tuple[int, str, str]] = []
        state_names: set[str] = set()
        first_method: int | None = None
        outer_comments: list[str] = []
        forbidden_outer = False

        for i in range(first_i + 1, body_end):
            stripped = lines[i].strip()
            if not stripped:
                continue

            if re.match(r"(?i)^FUNCTION\b", stripped):
                if function_depth != 0:
                    return source, []
                function_depth = 1
                method_start = i
                if first_method is None:
                    first_method = i
                continue

            if re.fullmatch(r"(?i)ENDFUNCTION", stripped):
                if function_depth != 1 or method_start is None:
                    return source, []
                method_ranges.append((method_start, i))
                method_start = None
                function_depth = 0
                continue

            if function_depth == 1:
                # Nested FUNCTIONs are rejected above; all other method-body
                # statements are preserved and checked later.
                continue

            if stripped.upper().startswith("COMMENT"):
                if first_method is None:
                    outer_comments.append(lines[i])
                continue

            assignment = re.fullmatch(r"([A-Za-z_]\w*)\s*<-\s*(.+)", stripped)
            if assignment is not None and first_method is None:
                name = assignment.group(1)
                rhs = assignment.group(2).strip()
                state_assignments.append((i, name, rhs))
                state_names.add(name)
                continue

            # No free outer statements or state declarations after methods.
            forbidden_outer = True

        if function_depth != 0 or method_start is not None:
            return source, []
        if forbidden_outer or not state_assignments or not method_ranges:
            return source, []

        def is_self_contained_initializer(rhs: str) -> bool:
            if re.fullmatch(
                r"(?i)EMPTY\s+(?:LIST|SET|DICTIONARY|STRING|TUPLE)", rhs
            ):
                return True
            if re.fullmatch(r"(?i)CALL\s+create_stack\(\s*\)", rhs):
                return True
            if re.fullmatch(r"[+-]?(?:\d+(?:\.\d+)?|\.\d+)", rhs):
                return True
            if re.fullmatch(r"(?i)(?:NONE|NULL|BOOLEAN\((?:True|False)\)|STRING\(.*\)|CHAR\(.*\))", rhs):
                return True
            return False

        if not all(is_self_contained_initializer(rhs) for _, _, rhs in state_assignments):
            return source, []

        state_lower = {name.lower(): name for name in state_names}
        empty_list_state = {
            name for _, name, rhs in state_assignments
            if re.fullmatch(r"(?i)EMPTY\s+LIST", rhs)
        }

        for start_i, end_i in method_ranges:
            method_header = re.fullmatch(
                r"(?i)\s*FUNCTION\s+([A-Za-z_]\w*)\s+ACCEPTS\s*(\(.*\))\s*",
                lines[start_i],
            )
            if method_header is None:
                return source, []
            params_text = method_header.group(2)[1:-1]
            params = {
                part.strip().split()[0].lower()
                for part in params_text.split(",")
                if part.strip()
            }
            if params.intersection(state_lower):
                return source, []

            body = "\n".join(lines[start_i + 1:end_i])
            if not any(re.search(rf"\b{re.escape(name)}\b", body) for name in state_names):
                return source, []

            # Preserve the v2.95 abstract-array boundary.  Turning an empty list
            # state into an instance property must not make an indexed growth
            # write executable merely by fixing the surrounding class syntax.
            for name in empty_list_state:
                if re.search(
                    rf"(?im)^\s*(?:THIS\.)?{re.escape(name)}\s*\[[^\n\]]+\]\s*<-",
                    body,
                ):
                    return source, []

        class_indent = re.match(r"^\s*", lines[first_i]).group(0)
        body_indent = class_indent + "    "
        inner_indent = body_indent + "    "

        def property_type(rhs: str) -> str | None:
            match = re.fullmatch(
                r"(?i)EMPTY\s+(LIST|DICTIONARY|STRING|SET|TUPLE)", rhs
            )
            return match.group(1).upper() if match else None

        def qualify_state_references(line: str) -> str:
            if line.lstrip().upper().startswith("COMMENT"):
                return line
            result: list[str] = []
            i = 0
            quote: str | None = None
            escaped = False
            while i < len(line):
                ch = line[i]
                if quote is not None:
                    result.append(ch)
                    if escaped:
                        escaped = False
                    elif ch == "\\":
                        escaped = True
                    elif ch == quote:
                        quote = None
                    i += 1
                    continue
                if ch in {'"', "'"}:
                    quote = ch
                    result.append(ch)
                    i += 1
                    continue
                identifier = re.match(r"[A-Za-z_]\w*", line[i:])
                if identifier:
                    token = identifier.group(0)
                    previous = "".join(result)
                    if token.lower() in state_lower and not previous.endswith("THIS."):
                        result.append("THIS." + state_lower[token.lower()])
                    else:
                        result.append(token)
                    i += len(token)
                    continue
                result.append(ch)
                i += 1
            return "".join(result)

        transformed_lines: list[str] = []
        transformed_lines.extend(lines[:first_i])
        transformed_lines.append(f"{class_indent}CLASS {header.group(1)}")
        transformed_lines.extend(outer_comments)

        for _, name, rhs in state_assignments:
            declared = property_type(rhs)
            suffix = f" AS {declared}" if declared else ""
            transformed_lines.append(f"{body_indent}PROPERTY {name}{suffix}")

        transformed_lines.append("")
        transformed_lines.append(f"{body_indent}CONSTRUCTOR ACCEPTS()")
        for _, name, rhs in state_assignments:
            transformed_lines.append(f"{inner_indent}PROPERTY THIS.{name} <- {rhs}")
        transformed_lines.append(f"{body_indent}ENDCONSTRUCTOR")

        for start_i, end_i in method_ranges:
            match = re.fullmatch(
                r"(?i)(\s*)FUNCTION\s+([A-Za-z_]\w*)\s+ACCEPTS\s*(\(.*\))\s*",
                lines[start_i],
            )
            if match is None:
                return source, []
            transformed_lines.append("")
            transformed_lines.append(
                f"{match.group(1)}METHOD {match.group(2)} ACCEPTS{match.group(3)}"
            )
            for body_line in lines[start_i + 1:end_i]:
                transformed_lines.append(qualify_state_references(body_line))
            end_indent = re.match(r"^\s*", lines[end_i]).group(0)
            transformed_lines.append(f"{end_indent}ENDMETHOD")

        transformed_lines.append(f"{class_indent}ENDCLASS")
        if has_endclass:
            transformed_lines.extend(lines[last_i + 1:])
        else:
            transformed_lines.extend(lines[body_end:])

        transformed = "\n".join(transformed_lines)
        if source.endswith("\n"):
            transformed += "\n"
        if transformed == source:
            return source, []
        return transformed, [
            SourceTransformation(
                line=first_i + 1,
                rule="GC203",
                source=source,
                target=transformed,
            )
        ]


    def _normalise_evidenced_ordered_cache_stateful_adt(
        self,
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        """Recover a source-evidenced ordered-cache ADT from INIT + operations.

        GC215 handles a narrow structural shape in which the source declares two
        persistent state names using ``INIT limit, cache = orderedDict()`` and
        then supplies multiple top-level operations over that state.  The first
        state name is recovered as an externally supplied constructor parameter
        only when the source itself uses it as the cache-size bound; no numeric
        default is invented.  The second state name is recovered as a dictionary
        property because the source explicitly requests an ordered dictionary and
        uses keyed membership/indexing.

        The source's ordering helpers are deliberately preserved as opaque
        abstractions:

        * ``moveToFront(cache, key)`` remains ``CALL moveToFront(...)``;
        * ``removeBack(cache)`` remains ``CALL removeBack(...)``;
        * ``addToFront(cache, key, value)`` remains ``CALL addToFront(...)``.

        Their names provide structural evidence that the operations share the
        ordered key/value state, but they do not provide executable semantics.
        Python compilation must therefore treat the recovered occurrence as an
        expected unresolved-abstraction failure rather than manufacture an LRU
        implementation.

        This is deliberately not a generic ``INIT a, b = expr`` split and not a
        generic nested-functions-to-class rewrite.  It requires source-local
        evidence for the ordered key/value abstraction, size-bound state, safe
        helper contexts, and at least two operations sharing the cache state.
        """
        lines = source.splitlines()
        nonblank = [i for i, line in enumerate(lines) if line.strip()]
        if len(nonblank) < 8:
            return source, []

        first_i = nonblank[0]
        init_match = re.fullmatch(
            r"(?i)\s*INIT\s+([A-Za-z_]\w*)\s*,\s*([A-Za-z_]\w*)\s*=\s*"
            r"CALL\s+orderedDict\s*\(\s*\)\s*",
            lines[first_i],
        )
        if init_match is None:
            return source, []
        limit_name, cache_name = init_match.group(1), init_match.group(2)
        if limit_name == cache_name:
            return source, []

        # The whole remaining program must be top-level FUNCTION operations
        # (plus comments/blank lines); nested functions or stray executable
        # statements make the structural interpretation ambiguous.
        function_ranges: list[tuple[int, int]] = []
        i = first_i + 1
        while i < len(lines):
            stripped = lines[i].strip()
            if not stripped or stripped.upper().startswith("COMMENT"):
                i += 1
                continue
            header = re.fullmatch(
                r"(?i)FUNCTION\s+([A-Za-z_]\w*)\s+ACCEPTS\s*(\(.*\))\s*",
                stripped,
            )
            if header is None:
                return source, []
            start = i
            depth = 1
            i += 1
            while i < len(lines) and depth:
                current = lines[i].strip()
                if re.match(r"(?i)^FUNCTION\b", current):
                    depth += 1
                elif re.fullmatch(r"(?i)ENDFUNCTION", current):
                    depth -= 1
                i += 1
            if depth != 0:
                return source, []
            end = i - 1
            # Nested operations are outside this rule's approved shape.
            if any(
                re.match(r"(?i)^\s*FUNCTION\b", lines[j])
                for j in range(start + 1, end)
            ):
                return source, []
            function_ranges.append((start, end))

        if len(function_ranges) < 2:
            return source, []

        cache_ref = re.compile(rf"\b{re.escape(cache_name)}\b")
        limit_ref = re.compile(rf"\b{re.escape(limit_name)}\b")
        if not all(
            cache_ref.search("\n".join(lines[start + 1:end]))
            for start, end in function_ranges
        ):
            return source, []
        if not any(
            limit_ref.search("\n".join(lines[start + 1:end]))
            for start, end in function_ranges
        ):
            return source, []

        whole_body = "\n".join(
            line
            for start, end in function_ranges
            for line in lines[start + 1:end]
        )
        # Ordered mapping evidence: source requests orderedDict and performs
        # both keyed mapping operations and recency operations on the same state.
        if not re.search(rf"(?i)\b[A-Za-z_]\w*\s+IN\s+{re.escape(cache_name)}\b", whole_body):
            return source, []
        if not re.search(rf"\b{re.escape(cache_name)}\s*\[", whole_body):
            return source, []
        if not re.search(
            rf"(?i)LENGTH\s+OF\s+{re.escape(cache_name)}\s*==\s*{re.escape(limit_name)}\b",
            whole_body,
        ):
            return source, []

        helper_names = {"movetofront", "removeback", "addtofront", "null"}
        for call_name in re.findall(r"(?i)\bCALL\s+([A-Za-z_]\w*)\s*\(", whole_body):
            if call_name.lower() not in helper_names:
                return source, []

        move_seen = False
        remove_seen = False
        add_seen = False

        # Prove the helpers are used in contexts that make the existing ordered
        # mapping intrinsics semantically equivalent and safe.
        for start, end in function_ranges:
            control_stack: list[dict[str, object]] = []
            for j in range(start + 1, end):
                stripped = lines[j].strip()

                if_match = re.fullmatch(r"(?i)IF\s+(.+?)\s+THEN", stripped)
                if if_match is not None:
                    control_stack.append({
                        "kind": "IF",
                        "condition": if_match.group(1).strip(),
                        "branch": "THEN",
                    })
                    continue
                if re.fullmatch(r"(?i)ELSE", stripped):
                    if not control_stack or control_stack[-1]["kind"] != "IF":
                        return source, []
                    control_stack[-1]["branch"] = "ELSE"
                    continue
                if re.fullmatch(r"(?i)ENDIF", stripped):
                    if not control_stack or control_stack[-1]["kind"] != "IF":
                        return source, []
                    control_stack.pop()
                    continue
                if re.match(r"(?i)^(?:FOR\b|WHILE\b)", stripped):
                    control_stack.append({"kind": "LOOP"})
                    continue
                if re.fullmatch(r"(?i)(?:ENDFOR|ENDWHILE)", stripped):
                    if not control_stack or control_stack[-1]["kind"] != "LOOP":
                        return source, []
                    control_stack.pop()
                    continue

                move = re.fullmatch(
                    rf"(?i)CALL\s+moveToFront\s*\(\s*{re.escape(cache_name)}\s*,\s*([A-Za-z_]\w*)\s*\)",
                    stripped,
                )
                if move is not None:
                    key_name = move.group(1)
                    membership = re.compile(
                        rf"(?i)^\s*{re.escape(key_name)}\s+IN\s+{re.escape(cache_name)}\s*$"
                    )
                    if not any(
                        frame.get("kind") == "IF"
                        and frame.get("branch") == "THEN"
                        and isinstance(frame.get("condition"), str)
                        and membership.fullmatch(str(frame["condition"]))
                        for frame in reversed(control_stack)
                    ):
                        return source, []
                    move_seen = True
                    continue

                remove = re.fullmatch(
                    rf"(?i)CALL\s+removeBack\s*\(\s*{re.escape(cache_name)}\s*\)",
                    stripped,
                )
                if remove is not None:
                    full_condition = re.compile(
                        rf"(?i)^\s*LENGTH\s+OF\s+{re.escape(cache_name)}\s*==\s*{re.escape(limit_name)}\s*$"
                    )
                    if not any(
                        frame.get("kind") == "IF"
                        and frame.get("branch") == "THEN"
                        and isinstance(frame.get("condition"), str)
                        and full_condition.fullmatch(str(frame["condition"]))
                        for frame in reversed(control_stack)
                    ):
                        return source, []
                    remove_seen = True
                    continue

                add = re.fullmatch(
                    rf"(?i)CALL\s+addToFront\s*\(\s*{re.escape(cache_name)}\s*,\s*([A-Za-z_]\w*)\s*,\s*(.+?)\s*\)",
                    stripped,
                )
                if add is not None:
                    key_name = add.group(1)
                    membership = re.compile(
                        rf"(?i)^\s*{re.escape(key_name)}\s+IN\s+{re.escape(cache_name)}\s*$"
                    )
                    if not any(
                        frame.get("kind") == "IF"
                        and frame.get("branch") == "ELSE"
                        and isinstance(frame.get("condition"), str)
                        and membership.fullmatch(str(frame["condition"]))
                        for frame in reversed(control_stack)
                    ):
                        return source, []
                    add_seen = True
                    continue

                # If one of the three helper spellings appears but failed the
                # exact target/arity match above, refuse instead of guessing.
                if re.search(r"(?i)\bCALL\s+(?:moveToFront|removeBack|addToFront)\s*\(", stripped):
                    return source, []

            if control_stack:
                return source, []

        if not (move_seen and remove_seen and add_seen):
            return source, []

        # The capacity-like state is externally supplied.  Do not permit method
        # code to assign a synthetic/default value to it.
        if re.search(
            rf"(?im)^\s*{re.escape(limit_name)}(?:\s*\[.*?\])?\s*<-",
            whole_body,
        ):
            return source, []

        def qualify_state_references(line: str) -> str:
            stripped = line.lstrip()
            if stripped.upper().startswith("COMMENT"):
                return line
            result: list[str] = []
            pos = 0
            quote: str | None = None
            escaped = False
            state_names = {limit_name, cache_name}
            while pos < len(line):
                ch = line[pos]
                if quote is not None:
                    result.append(ch)
                    if escaped:
                        escaped = False
                    elif ch == "\\":
                        escaped = True
                    elif ch == quote:
                        quote = None
                    pos += 1
                    continue
                if ch in {'"', "'"}:
                    quote = ch
                    result.append(ch)
                    pos += 1
                    continue
                identifier = re.match(r"[A-Za-z_]\w*", line[pos:])
                if identifier:
                    token = identifier.group(0)
                    previous = "".join(result)
                    if token in state_names and not previous.endswith("THIS."):
                        result.append("THIS." + token)
                    else:
                        result.append(token)
                    pos += len(token)
                    continue
                result.append(ch)
                pos += 1
            return "".join(result)

        class_indent = re.match(r"^\s*", lines[first_i]).group(0)
        body_indent = class_indent + "    "
        inner_indent = body_indent + "    "
        transformed_lines: list[str] = []
        transformed_lines.extend(lines[:first_i])
        transformed_lines.append(f"{class_indent}CLASS unnamed_class")
        transformed_lines.append(f"{body_indent}PROPERTY {limit_name}")
        transformed_lines.append(f"{body_indent}PROPERTY {cache_name} AS DICTIONARY")
        transformed_lines.append("")
        transformed_lines.append(f"{body_indent}CONSTRUCTOR ACCEPTS({limit_name})")
        transformed_lines.append(
            f"{inner_indent}PROPERTY THIS.{limit_name} <- {limit_name}"
        )
        transformed_lines.append(
            f"{inner_indent}PROPERTY THIS.{cache_name} <- EMPTY DICTIONARY"
        )
        transformed_lines.append(f"{body_indent}ENDCONSTRUCTOR")

        for start, end in function_ranges:
            header = re.fullmatch(
                r"(?i)(\s*)FUNCTION\s+([A-Za-z_]\w*)\s+ACCEPTS\s*(\(.*\))\s*",
                lines[start],
            )
            if header is None:
                return source, []
            transformed_lines.append("")
            transformed_lines.append(
                f"{body_indent}METHOD {header.group(2)} ACCEPTS{header.group(3)}"
            )
            for body_line in lines[start + 1:end]:
                qualified = qualify_state_references(body_line)
                # Move original top-level function body one additional level
                # into the recovered class method.
                original_indent = len(body_line) - len(body_line.lstrip(" \t"))
                content = qualified.lstrip(" \t")
                new_indent = inner_indent + (" " * max(0, original_indent - 4))
                rewritten = new_indent + content if content else ""
                # The ordering helpers are explicit source abstractions.  Preserve
                # their names and arguments after qualifying shared state; do not
                # choose a Python/LRU implementation here.
                transformed_lines.append(rewritten)
            transformed_lines.append(f"{body_indent}ENDMETHOD")

        transformed_lines.append(f"{class_indent}ENDCLASS")
        transformed = "\n".join(transformed_lines)
        if source.endswith("\n"):
            transformed += "\n"

        return transformed, [
            SourceTransformation(
                line=first_i + 1,
                rule="GC215",
                source=source,
                target=transformed,
            )
        ]


    def _normalise_evidenced_counted_list_stateful_adt(
        self,
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        """Recover an explicitly initialised counted-list ADT from outer state.

        GC216 addresses a narrow structural shape in which a model writes
        persistent state as top-level assignments followed by multiple
        top-level operations, rather than wrapping that state and interface in
        a class.  The rule is intentionally narrower than a generic
        ``state + functions -> class`` conversion.

        Source-local evidence required:
        * exactly two persistent state assignments precede all operations;
        * one state is explicitly ``EMPTY LIST`` and the other explicitly ``0``;
        * at least three top-level FUNCTION operations follow;
        * every operation references both state names and no parameter shadows
          either state name;
        * the list state has explicit APPEND, member ``pop()`` and indexed-read
          evidence, while the counter has explicit +1 and -1 updates;
        * no unknown CALL escape or direct rebinding of the list state occurs.

        When all safeguards hold, GC216 emits a neutral ``unnamed_class`` with
        the two explicit initial values in a zero-argument constructor and the
        source-supplied functions as methods.  State references are qualified
        with ``THIS``.  No stack operation, error policy or data value is
        invented by this structural recovery.
        """
        lines = source.splitlines()
        nonblank = [i for i, line in enumerate(lines) if line.strip()]
        if len(nonblank) < 10:
            return source, []

        first_i = nonblank[0]
        state_assignments: list[tuple[int, str, str]] = []
        i = first_i
        while i < len(lines):
            stripped = lines[i].strip()
            if not stripped or stripped.upper().startswith("COMMENT"):
                i += 1
                continue
            assignment = re.fullmatch(r"([A-Za-z_]\w*)\s*<-\s*(.+)", stripped)
            if assignment is None:
                break
            state_assignments.append((i, assignment.group(1), assignment.group(2).strip()))
            i += 1

        if len(state_assignments) != 2:
            return source, []
        state_names = [name for _idx, name, _rhs in state_assignments]
        if len(set(state_names)) != 2:
            return source, []

        list_states = [
            name for _idx, name, rhs in state_assignments
            if re.fullmatch(r"(?i)EMPTY\s+LIST", rhs)
        ]
        zero_states = [
            name for _idx, name, rhs in state_assignments
            if re.fullmatch(r"(?:INTEGER\(\s*0\s*\)|0)", rhs, re.I)
        ]
        if len(list_states) != 1 or len(zero_states) != 1:
            return source, []
        list_name = list_states[0]
        count_name = zero_states[0]
        if list_name == count_name:
            return source, []

        # All remaining non-comment executable content must consist of complete
        # top-level functions.  This avoids absorbing module-like source that
        # merely happens to use globals.
        function_ranges: list[tuple[int, int]] = []
        while i < len(lines):
            stripped = lines[i].strip()
            if not stripped or stripped.upper().startswith("COMMENT"):
                i += 1
                continue
            header = re.fullmatch(
                r"(?i)FUNCTION\s+([A-Za-z_]\w*)\s+ACCEPTS\s*(\(.*\))\s*",
                stripped,
            )
            if header is None:
                return source, []
            start = i
            depth = 1
            i += 1
            while i < len(lines) and depth:
                current = lines[i].strip()
                if re.match(r"(?i)^FUNCTION\b", current):
                    depth += 1
                elif re.fullmatch(r"(?i)ENDFUNCTION", current):
                    depth -= 1
                i += 1
            if depth != 0:
                return source, []
            end = i - 1
            if any(
                re.match(r"(?i)^\s*FUNCTION\b", lines[j])
                for j in range(start + 1, end)
            ):
                return source, []
            function_ranges.append((start, end))

        if len(function_ranges) < 3:
            return source, []

        # Every operation must share both state values, and parameters must not
        # shadow them.  This is strong evidence for instance state rather than
        # unrelated module globals.
        for start, end in function_ranges:
            header = re.fullmatch(
                r"(?i)\s*FUNCTION\s+([A-Za-z_]\w*)\s+ACCEPTS\s*\((.*?)\)\s*",
                lines[start],
            )
            if header is None:
                return source, []
            params = {
                item.strip()
                for item in header.group(2).split(",")
                if item.strip()
            }
            if list_name in params or count_name in params:
                return source, []
            body = "\n".join(lines[start + 1:end])
            if not re.search(rf"\b{re.escape(list_name)}\b", body):
                return source, []
            if not re.search(rf"\b{re.escape(count_name)}\b", body):
                return source, []

        whole_body = "\n".join(
            line
            for start, end in function_ranges
            for line in lines[start + 1:end]
        )

        # Refuse arbitrary external helper calls.  Member calls on the evidenced
        # list state are not CALL-prefixed and remain ordinary member syntax.
        if re.search(r"(?i)\bCALL\s+[A-Za-z_]\w*\s*\(", whole_body):
            return source, []

        # The list itself may be mutated through explicit list operations, but
        # direct rebinding or indexed writes would make the state model more
        # ambiguous than the approved counted-list shape.
        if re.search(
            rf"(?im)^\s*{re.escape(list_name)}\s*<-",
            whole_body,
        ):
            return source, []
        if re.search(
            rf"(?im)^\s*{re.escape(list_name)}\s*\[[^\n]+\]\s*<-",
            whole_body,
        ):
            return source, []

        append_evidence = re.search(
            rf"(?im)^\s*APPEND\s+.+?\s+TO\s+{re.escape(list_name)}\s*$",
            whole_body,
        ) is not None
        pop_evidence = re.search(
            rf"(?i)\b{re.escape(list_name)}\.pop\s*\(\s*\)",
            whole_body,
        ) is not None
        indexed_read_evidence = re.search(
            rf"\b{re.escape(list_name)}\s*\[\s*{re.escape(count_name)}\s*-\s*1\s*\]",
            whole_body,
            re.I,
        ) is not None
        increment_evidence = re.search(
            rf"(?im)^\s*{re.escape(count_name)}\s*<-\s*{re.escape(count_name)}\s*\+\s*1\s*$",
            whole_body,
        ) is not None
        decrement_evidence = re.search(
            rf"(?im)^\s*{re.escape(count_name)}\s*<-\s*{re.escape(count_name)}\s*-\s*1\s*$",
            whole_body,
        ) is not None
        if not all((
            append_evidence,
            pop_evidence,
            indexed_read_evidence,
            increment_evidence,
            decrement_evidence,
        )):
            return source, []

        # Counter assignments must be the explicit +/-1 updates evidenced above.
        for match in re.finditer(
            rf"(?im)^\s*{re.escape(count_name)}\s*<-\s*(.+?)\s*$",
            whole_body,
        ):
            rhs = match.group(1).strip()
            if not (
                re.fullmatch(rf"{re.escape(count_name)}\s*\+\s*1", rhs)
                or re.fullmatch(rf"{re.escape(count_name)}\s*-\s*1", rhs)
            ):
                return source, []

        state_set = {list_name, count_name}

        def qualify_state_references(line: str) -> str:
            if line.lstrip().upper().startswith("COMMENT"):
                return line
            result: list[str] = []
            pos = 0
            quote: str | None = None
            escaped = False
            while pos < len(line):
                ch = line[pos]
                if quote is not None:
                    result.append(ch)
                    if escaped:
                        escaped = False
                    elif ch == "\\":
                        escaped = True
                    elif ch == quote:
                        quote = None
                    pos += 1
                    continue
                if ch in {'"', "'"}:
                    quote = ch
                    result.append(ch)
                    pos += 1
                    continue
                identifier = re.match(r"[A-Za-z_]\w*", line[pos:])
                if identifier:
                    token = identifier.group(0)
                    previous = "".join(result)
                    if token in state_set and not previous.endswith("THIS."):
                        result.append("THIS." + token)
                    else:
                        result.append(token)
                    pos += len(token)
                    continue
                result.append(ch)
                pos += 1
            return "".join(result)

        class_indent = re.match(r"^\s*", lines[first_i]).group(0)
        body_indent = class_indent + "    "
        inner_indent = body_indent + "    "
        transformed_lines: list[str] = []
        transformed_lines.extend(lines[:first_i])
        transformed_lines.append(f"{class_indent}CLASS unnamed_class")
        # Preserve source state declaration order while attaching the two
        # mechanically known types.
        for _idx, name, _rhs in state_assignments:
            state_type = "LIST" if name == list_name else "INTEGER"
            transformed_lines.append(f"{body_indent}PROPERTY {name} AS {state_type}")
        transformed_lines.append("")
        transformed_lines.append(f"{body_indent}CONSTRUCTOR ACCEPTS()")
        for _idx, name, rhs in state_assignments:
            transformed_lines.append(
                f"{inner_indent}PROPERTY THIS.{name} <- {rhs}"
            )
        transformed_lines.append(f"{body_indent}ENDCONSTRUCTOR")

        for start, end in function_ranges:
            header = re.fullmatch(
                r"(?i)\s*FUNCTION\s+([A-Za-z_]\w*)\s+ACCEPTS\s*(\(.*\))\s*",
                lines[start],
            )
            if header is None:
                return source, []
            transformed_lines.append("")
            transformed_lines.append(
                f"{body_indent}METHOD {header.group(1)} ACCEPTS{header.group(2)}"
            )
            for body_line in lines[start + 1:end]:
                qualified = qualify_state_references(body_line)
                original_indent = len(body_line) - len(body_line.lstrip(" \t"))
                content = qualified.lstrip(" \t")
                new_indent = inner_indent + (" " * max(0, original_indent - 4))
                transformed_lines.append(new_indent + content if content else "")
            transformed_lines.append(f"{body_indent}ENDMETHOD")

        transformed_lines.append(f"{class_indent}ENDCLASS")
        transformed = "\n".join(transformed_lines)
        if source.endswith("\n"):
            transformed += "\n"

        return transformed, [
            SourceTransformation(
                line=first_i + 1,
                rule="GC216",
                source=source,
                target=transformed,
            )
        ]


    def _normalise_evidenced_connected_multi_list_stateful_adt(
        self,
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        """Recover connected persistent list state as one neutral ADT.

        GC218 covers a source shape where multiple explicitly empty list states
        are declared at top level and are then operated on by multiple top-level
        functions.  It is not a generic ``globals + functions -> class`` rule.

        Source-local evidence required:
        * at least two and at most six persistent state assignments precede all
          operations, and every such state is explicitly ``EMPTY LIST``;
        * at least two complete top-level FUNCTION operations follow, with no
          nested functions or free executable statements;
        * every operation references at least one state and no parameter shadows
          a state name;
        * the bipartite state/operation graph is connected, so the declarations
          form one abstraction rather than unrelated module globals;
        * every list state is explicitly mutated by APPEND or zero-argument
          ``pop()``/canonical list removal;
        * at least one source operation destructively transfers an item directly
          from one evidenced state to another (``APPEND a.pop() TO b``);
        * no unknown CALL escape, direct state rebinding, or indexed state write
          occurs inside the recovered operations.

        When all safeguards hold, the transformation emits ``CLASS
        unnamed_class`` with LIST properties and a zero-argument constructor
        containing exactly the source-supplied EMPTY LIST initialisers.  The
        supplied functions become methods and state references are qualified by
        ``THIS``.  No queue policy, sentinel, operation, class name, or data
        value is invented.
        """
        lines = source.splitlines()
        nonblank = [i for i, line in enumerate(lines) if line.strip()]
        if len(nonblank) < 8:
            return source, []

        first_i = nonblank[0]
        state_assignments: list[tuple[int, str, str]] = []
        i = first_i
        while i < len(lines):
            stripped = lines[i].strip()
            if not stripped or stripped.upper().startswith("COMMENT"):
                i += 1
                continue
            assignment = re.fullmatch(r"([A-Za-z_]\w*)\s*<-\s*(.+)", stripped)
            if assignment is None:
                break
            state_assignments.append((i, assignment.group(1), assignment.group(2).strip()))
            i += 1

        if not (2 <= len(state_assignments) <= 6):
            return source, []
        state_names = [name for _idx, name, _rhs in state_assignments]
        if len(set(state_names)) != len(state_names):
            return source, []
        if any(
            re.fullmatch(r"(?i)EMPTY\s+LIST", rhs) is None
            for _idx, _name, rhs in state_assignments
        ):
            return source, []
        state_set = set(state_names)

        # All remaining executable content must be complete top-level functions.
        function_ranges: list[tuple[int, int, str, set[str]]] = []
        while i < len(lines):
            stripped = lines[i].strip()
            if not stripped or stripped.upper().startswith("COMMENT"):
                i += 1
                continue
            header = re.fullmatch(
                r"(?i)FUNCTION\s+([A-Za-z_]\w*)\s+ACCEPTS\s*\((.*?)\)\s*",
                stripped,
            )
            if header is None:
                return source, []
            params = {
                item.strip()
                for item in header.group(2).split(",")
                if item.strip()
            }
            if params & state_set:
                return source, []
            start = i
            depth = 1
            i += 1
            while i < len(lines) and depth:
                current = lines[i].strip()
                if re.match(r"(?i)^FUNCTION\b", current):
                    depth += 1
                elif re.fullmatch(r"(?i)ENDFUNCTION", current):
                    depth -= 1
                i += 1
            if depth != 0:
                return source, []
            end = i - 1
            if any(
                re.match(r"(?i)^\s*FUNCTION\b", lines[j])
                for j in range(start + 1, end)
            ):
                return source, []
            body = "\n".join(lines[start + 1:end])
            refs = {
                name
                for name in state_names
                if re.search(rf"\b{re.escape(name)}\b", body)
            }
            if not refs:
                return source, []
            function_ranges.append((start, end, header.group(1), refs))

        if len(function_ranges) < 2:
            return source, []

        whole_body = "\n".join(
            line
            for start, end, _name, _refs in function_ranges
            for line in lines[start + 1:end]
        )

        # Unknown ordinary helper calls can leak or reinterpret state.  Member
        # pop() syntax on an evidenced list remains ordinary member syntax.
        if re.search(r"(?i)\bCALL\s+[A-Za-z_]\w*\s*\(", whole_body):
            return source, []

        # Once persistent list state is established, refuse direct replacement
        # or indexed writes; those shapes need their own representation proof.
        for state_name in state_names:
            if re.search(
                rf"(?im)^\s*{re.escape(state_name)}\s*<-",
                whole_body,
            ):
                return source, []
            if re.search(
                rf"(?im)^\s*{re.escape(state_name)}\s*\[[^\n]+\]\s*<-",
                whole_body,
            ):
                return source, []

        # Every state must be actively mutated, not merely observed.  This
        # prevents unrelated configuration lists from being absorbed.
        for state_name in state_names:
            append_mutation = re.search(
                rf"(?im)^\s*APPEND\s+.+?\s+TO\s+{re.escape(state_name)}\s*$",
                whole_body,
            ) is not None
            pop_mutation = re.search(
                rf"(?i)\b{re.escape(state_name)}\.pop\s*\(\s*\)",
                whole_body,
            ) is not None
            canonical_remove = re.search(
                rf"(?im)^\s*REMOVE\s+(?:FIRST|LAST)\s+ITEM\s+FROM\s+{re.escape(state_name)}\s*$",
                whole_body,
            ) is not None
            if not (append_mutation or pop_mutation or canonical_remove):
                return source, []

        # A destructive direct transfer is the strongest source-local evidence
        # that two separately declared lists participate in one data structure.
        transfer_pairs: set[tuple[str, str]] = set()
        transfer_pattern = re.compile(
            r"(?im)^\s*APPEND\s+([A-Za-z_]\w*)\.pop\s*\(\s*\)\s+TO\s+([A-Za-z_]\w*)\s*$"
        )
        for match in transfer_pattern.finditer(whole_body):
            src, dst = match.group(1), match.group(2)
            if src in state_set and dst in state_set and src != dst:
                transfer_pairs.add((src, dst))
        if not transfer_pairs:
            return source, []

        # Build the state/function bipartite graph and require one connected
        # component containing every state and operation.
        adjacency: dict[str, set[str]] = {}
        for state_name in state_names:
            adjacency[f"S:{state_name}"] = set()
        for index, (_start, _end, _func_name, refs) in enumerate(function_ranges):
            fnode = f"F:{index}"
            adjacency[fnode] = set()
            for state_name in refs:
                snode = f"S:{state_name}"
                adjacency[fnode].add(snode)
                adjacency[snode].add(fnode)

        start_node = next(iter(adjacency))
        seen = {start_node}
        stack = [start_node]
        while stack:
            node = stack.pop()
            for neighbour in adjacency[node]:
                if neighbour not in seen:
                    seen.add(neighbour)
                    stack.append(neighbour)
        if seen != set(adjacency):
            return source, []

        def qualify_state_references(line: str) -> str:
            if line.lstrip().upper().startswith("COMMENT"):
                return line
            result: list[str] = []
            pos = 0
            quote: str | None = None
            escaped = False
            while pos < len(line):
                ch = line[pos]
                if quote is not None:
                    result.append(ch)
                    if escaped:
                        escaped = False
                    elif ch == "\\":
                        escaped = True
                    elif ch == quote:
                        quote = None
                    pos += 1
                    continue
                if ch in {'"', "'"}:
                    quote = ch
                    result.append(ch)
                    pos += 1
                    continue
                identifier = re.match(r"[A-Za-z_]\w*", line[pos:])
                if identifier:
                    token = identifier.group(0)
                    previous = "".join(result)
                    if token in state_set and not previous.endswith("THIS."):
                        result.append("THIS." + token)
                    else:
                        result.append(token)
                    pos += len(token)
                    continue
                result.append(ch)
                pos += 1
            return "".join(result)

        class_indent = re.match(r"^\s*", lines[first_i]).group(0)
        body_indent = class_indent + "    "
        inner_indent = body_indent + "    "
        transformed_lines: list[str] = []
        transformed_lines.extend(lines[:first_i])
        transformed_lines.append(f"{class_indent}CLASS unnamed_class")
        for _idx, name, _rhs in state_assignments:
            transformed_lines.append(f"{body_indent}PROPERTY {name} AS LIST")
        transformed_lines.append("")
        transformed_lines.append(f"{body_indent}CONSTRUCTOR ACCEPTS()")
        for _idx, name, rhs in state_assignments:
            transformed_lines.append(f"{inner_indent}PROPERTY THIS.{name} <- {rhs}")
        transformed_lines.append(f"{body_indent}ENDCONSTRUCTOR")

        for start, end, func_name, _refs in function_ranges:
            header = re.fullmatch(
                r"(?i)\s*FUNCTION\s+[A-Za-z_]\w*\s+ACCEPTS\s*(\(.*\))\s*",
                lines[start],
            )
            if header is None:
                return source, []
            transformed_lines.append("")
            transformed_lines.append(
                f"{body_indent}METHOD {func_name} ACCEPTS{header.group(1)}"
            )
            for body_line in lines[start + 1:end]:
                qualified = qualify_state_references(body_line)
                original_indent = len(body_line) - len(body_line.lstrip(" \t"))
                content = qualified.lstrip(" \t")
                new_indent = inner_indent + (" " * max(0, original_indent - 4))
                transformed_lines.append(new_indent + content if content else "")
            transformed_lines.append(f"{body_indent}ENDMETHOD")

        transformed_lines.append(f"{class_indent}ENDCLASS")
        transformed = "\n".join(transformed_lines)
        if source.endswith("\n"):
            transformed += "\n"

        return transformed, [
            SourceTransformation(
                line=first_i + 1,
                rule="GC218",
                source=source,
                target=transformed,
            )
        ]


    @staticmethod
    def _replace_none_outside_quotes(text: str) -> str:
        """Canonicalise the v1.1 NONE literal without touching quoted text."""
        out=[]
        i=0
        quote=None
        escape=False
        while i < len(text):
            ch=text[i]
            if quote is not None:
                out.append(ch)
                if escape:
                    escape=False
                elif ch == "\\":
                    escape=True
                elif ch == quote:
                    quote=None
                i += 1
                continue
            if ch in "'\"":
                quote=ch
                out.append(ch)
                i += 1
                continue
            match=re.match(r"(?i)none\b", text[i:])
            if match and (i == 0 or not (text[i-1].isalnum() or text[i-1] == "_")):
                out.append("NONE")
                i += len(match.group(0))
                continue
            out.append(ch)
            i += 1
        return "".join(out)

    def _normalise_provably_redundant_unique_returns(
        self,
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        """Align ``RETURN CALL unique(result)`` only when uniqueness is source-proven.

        GC214 is deliberately narrower than a general ``unique(x) -> x``
        rewrite.  It recognises only a same-routine list that is explicitly
        initialised empty and whose every APPEND is protected by a matching
        ``value NOT IN result`` guard that is re-evaluated before that append.
        Reassignment, indexed/insert mutation, aliasing/escape to an unknown
        call, repeated APPENDs under one guard, or a loop nested beneath the
        proving guard all refuse the alignment.

        The result is therefore an identity alignment of an already-satisfied
        postcondition.  It preserves the source-created order and does not
        implement an undefined ``unique`` routine.
        """

        lines = source.splitlines()
        transformations: list[SourceTransformation] = []

        # Work routine-by-routine so evidence cannot leak across function scope.
        routine_ranges: list[tuple[int, int]] = []
        stack: list[int] = []
        for index, line in enumerate(lines):
            if re.match(r"(?i)^\s*FUNCTION\b", line):
                stack.append(index)
            elif re.match(r"(?i)^\s*ENDFUNCTION\s*$", line) and stack:
                routine_start = stack.pop()
                if not stack:
                    routine_ranges.append((routine_start, index))

        for routine_start, routine_end in routine_ranges:
            candidates: list[tuple[int, str]] = []
            for index in range(routine_start + 1, routine_end):
                match = re.match(
                    r"(?i)^(?P<indent>[ \t]*)RETURN\s+CALL\s+unique\s*\(\s*(?P<name>[A-Za-z_]\w*)\s*\)\s*$",
                    lines[index],
                )
                if match is not None:
                    candidates.append((index, match.group("name")))

            for return_index, name in candidates:
                init_indexes = [
                    index
                    for index in range(routine_start + 1, return_index)
                    if re.match(
                        rf"(?i)^\s*{re.escape(name)}\s*<-\s*EMPTY\s+LIST\s*$",
                        lines[index],
                    )
                ]
                if len(init_indexes) != 1:
                    continue
                init_index = init_indexes[0]

                unsafe = False
                append_indexes: list[int] = []
                for index in range(init_index + 1, return_index):
                    stripped = lines[index].strip()

                    # Direct rebinding or indexed writes can invalidate the
                    # invariant or replace the collection entirely.
                    if re.match(
                        rf"(?i)^{re.escape(name)}(?:\s*\[|\s*<-)",
                        stripped,
                    ):
                        unsafe = True
                        break
                    if re.match(
                        rf"(?i)^INSERT\s+.+\s+INTO\s+{re.escape(name)}\s+AT\s+.+$",
                        stripped,
                    ):
                        unsafe = True
                        break

                    # Do not prove through aliases or unknown calls that could
                    # mutate the list behind the pipeline's back.
                    if re.match(
                        rf"(?i)^[A-Za-z_]\w*\s*<-\s*{re.escape(name)}\s*$",
                        stripped,
                    ):
                        unsafe = True
                        break
                    if re.search(
                        rf"(?i)\bCALL\s+[A-Za-z_]\w*\s*\([^\n)]*\b{re.escape(name)}\b[^\n)]*\)",
                        stripped,
                    ):
                        unsafe = True
                        break
                    if re.search(
                        rf"(?i)\b{re.escape(name)}\s*\.\s*[A-Za-z_]\w*\s*\(",
                        stripped,
                    ):
                        unsafe = True
                        break

                    if re.match(
                        rf"(?i)^APPEND\s+.+\s+TO\s+{re.escape(name)}\s*$",
                        stripped,
                    ):
                        append_indexes.append(index)

                if unsafe or not append_indexes:
                    continue

                # Track IF and loop frames.  A proving IF must be re-evaluated
                # after the innermost active loop boundary; otherwise one true
                # guard could permit repeated APPENDs over loop iterations.
                control_stack: list[dict[str, object]] = []
                next_frame_id = 0
                guard_use_count: dict[int, int] = {}
                all_appends_guarded = True
                append_set = set(append_indexes)

                for index in range(init_index + 1, return_index):
                    stripped = lines[index].strip()

                    if_match = re.match(r"(?i)^IF\s+(.+?)\s+THEN\s*$", stripped)
                    if if_match is not None:
                        control_stack.append({
                            "kind": "IF",
                            "condition": if_match.group(1).strip(),
                            "id": next_frame_id,
                        })
                        next_frame_id += 1
                        continue

                    else_if_match = re.match(
                        r"(?i)^ELSE\s+IF\s+(.+?)\s+THEN\s*$",
                        stripped,
                    )
                    if else_if_match is not None:
                        if control_stack and control_stack[-1]["kind"] == "IF":
                            control_stack[-1]["condition"] = else_if_match.group(1).strip()
                            control_stack[-1]["id"] = next_frame_id
                            next_frame_id += 1
                        continue

                    if re.match(r"(?i)^ELSE\s*$", stripped):
                        if control_stack and control_stack[-1]["kind"] == "IF":
                            control_stack[-1]["condition"] = None
                            control_stack[-1]["id"] = next_frame_id
                            next_frame_id += 1
                        continue

                    if re.match(r"(?i)^ENDIF\s*$", stripped):
                        if control_stack and control_stack[-1]["kind"] == "IF":
                            control_stack.pop()
                        continue

                    if re.match(r"(?i)^(?:FOR\b.+\bDO|FOR\s+EACH\b.+\bDO|WHILE\b.+\bDO)\s*$", stripped):
                        control_stack.append({
                            "kind": "LOOP",
                            "condition": None,
                            "id": next_frame_id,
                        })
                        next_frame_id += 1
                        continue

                    if re.match(r"(?i)^(?:ENDFOR|ENDWHILE)\s*$", stripped):
                        if control_stack and control_stack[-1]["kind"] == "LOOP":
                            control_stack.pop()
                        continue

                    if index not in append_set:
                        continue

                    append_match = re.match(
                        rf"(?i)^APPEND\s+(.+?)\s+TO\s+{re.escape(name)}\s*$",
                        stripped,
                    )
                    if append_match is None:
                        all_appends_guarded = False
                        break
                    value = append_match.group(1).strip()
                    guard_pattern = re.compile(
                        rf"(?i)(?<![A-Za-z0-9_]){re.escape(value)}\s+NOT\s+IN\s+{re.escape(name)}(?![A-Za-z0-9_])"
                    )

                    matching_position = None
                    matching_frame = None
                    for position in range(len(control_stack) - 1, -1, -1):
                        frame = control_stack[position]
                        condition = frame["condition"]
                        if (
                            frame["kind"] == "IF"
                            and isinstance(condition, str)
                            and guard_pattern.search(condition)
                        ):
                            matching_position = position
                            matching_frame = frame
                            break

                    if matching_frame is None or matching_position is None:
                        all_appends_guarded = False
                        break

                    # A loop opened after the proving guard can repeat the APPEND
                    # without re-evaluating that guard.
                    if any(
                        frame["kind"] == "LOOP"
                        for frame in control_stack[matching_position + 1:]
                    ):
                        all_appends_guarded = False
                        break

                    frame_id = int(matching_frame["id"])
                    guard_use_count[frame_id] = guard_use_count.get(frame_id, 0) + 1
                    if guard_use_count[frame_id] > 1:
                        all_appends_guarded = False
                        break

                if not all_appends_guarded:
                    continue

                before = lines[return_index]
                indent = re.match(r"^[ \t]*", before).group(0)
                after = f"{indent}RETURN {name}"
                lines[return_index] = after
                transformations.append(SourceTransformation(
                    line=return_index + 1,
                    rule="GC214",
                    source=before,
                    target=after,
                ))

        result = "\n".join(lines)
        if source.endswith("\n"):
            result += "\n"
        return result, transformations

    @staticmethod
    def _normalise_exact_unique_deduplication_intrinsic(
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        """Map exact ``CALL unique(name)`` to the existing set-conversion intrinsic.

        GC222 is intentionally narrower than a general undefined-call alias.
        User-confirmed semantics define exact one-argument ``unique(name)`` as
        SET conversion.  GC214 is therefore retired: even when the values in a
        list are already unique, erasing ``unique(...)`` would change the return
        type from SET to LIST.  Python lowering is delegated to the existing
        ``to_set`` intrinsic.
        """
        pattern = re.compile(
            r"(?i)\bCALL\s+unique\s*\(\s*(?P<name>[A-Za-z_]\w*)\s*\)"
        )
        transformations: list[SourceTransformation] = []
        output_lines: list[str] = []

        for line_number, line in enumerate(source.splitlines(), start=1):
            original = line
            line = pattern.sub(
                lambda m: f"CALL to_set({m.group('name')})",
                line,
            )
            if line != original:
                transformations.append(
                    SourceTransformation(
                        line=line_number,
                        rule="GC222",
                        source=original,
                        target=line,
                    )
                )
            output_lines.append(line)

        if not transformations:
            return source, []

        transformed = "\n".join(output_lines)
        if source.endswith("\n"):
            transformed += "\n"
        return transformed, transformations


    @staticmethod
    def _normalise_evidenced_set_to_list_intrinsic(
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        """Map exact ``ConvertSetToList(name)`` calls only with local set evidence.

        GC232 is a source-evidence guard around an otherwise undefined free call.
        The argument identifier must have been explicitly initialised as
        ``EMPTY SET`` earlier in the same function/method/constructor (or the same
        top-level scope), and that direct variable must not have been reassigned in
        between. Only a free, one-argument call with a simple identifier is
        rewritten. Member calls, other arities, forward evidence, and unproven
        identifiers remain untouched. The existing ``to_list`` intrinsic owns the
        deterministic Python lowering.
        """
        call_pattern = re.compile(
            r"(?i)(?<![.\w])CALL\s+ConvertSetToList\s*\(\s*(?P<name>[A-Za-z_]\w*)\s*\)"
        )
        direct_assignment = re.compile(
            r"^\s*(?P<name>[A-Za-z_]\w*)\s*<-\s*(?P<rhs>.+?)\s*$"
        )
        set_initialisation = re.compile(r"(?i)^EMPTY\s+SET$")
        scope_start = re.compile(r"(?i)^\s*(?:FUNCTION|METHOD|CONSTRUCTOR)\b")
        scope_end = re.compile(r"(?i)^\s*(?:ENDFUNCTION|ENDMETHOD|ENDCONSTRUCTOR)\b")

        # Each lexical routine gets its own evidence set. The first frame is
        # top-level source so an unrelated routine cannot lend type evidence.
        evidence = LexicalEvidenceContext()
        transformations: list[SourceTransformation] = []
        output_lines: list[str] = []

        for line_number, original in enumerate(source.splitlines(), start=1):
            stripped = original.strip()
            if scope_start.match(stripped):
                evidence.enter(inherit=False)

            assignment = direct_assignment.match(original)
            if assignment is not None:
                name = assignment.group("name")
                rhs = assignment.group("rhs").strip()
                if set_initialisation.fullmatch(rhs):
                    evidence.establish("set", name)
                else:
                    # A later direct rebind invalidates the earlier set proof.
                    evidence.invalidate("set", name)

            def replace_call(match: re.Match[str]) -> str:
                name = match.group("name")
                if not evidence.contains("set", name):
                    return match.group(0)
                return f"CALL to_list({name})"

            updated = call_pattern.sub(replace_call, original)
            if updated != original:
                transformations.append(
                    SourceTransformation(
                        line=line_number,
                        rule="GC232",
                        source=original,
                        target=updated,
                    )
                )
            output_lines.append(updated)

            if scope_end.match(stripped):
                evidence.exit()

        if not transformations:
            return source, []

        transformed = "\n".join(output_lines)
        if source.endswith("\n"):
            transformed += "\n"
        return transformed, transformations


    def _normalise_evidenced_singleton_set_extensions(
        self,
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        """Represent evidenced ``set_parameter + {value}`` without mutation.

        GC245 is intentionally evidence-gated. A formal parameter becomes
        set-backed only when an explicit canonical call to the same routine
        supplies ``EMPTY SET`` at that argument position. Within that routine
        only, an expression of the exact form ``parameter + {single_expression}``
        is represented through existing compatibility intrinsics as::

            CALL to_set(CALL to_list(parameter) + CALL list_value(expression))

        This preserves the source's non-mutating recursive/backtracking shape.
        The rule does not infer set type from a variable name, does not rewrite
        multi-member/dictionary braces, does not act across routines, and does
        not mutate the evidenced parameter in place.
        """
        lines = source.splitlines()
        if not lines:
            return source, []

        declaration_pattern = re.compile(
            r"(?i)^\s*(?:FUNCTION|METHOD)\s+(?P<name>[A-Za-z_]\w*)\s+ACCEPTS\s*\((?P<params>[^)]*)\)\s*$"
        )
        end_pattern = re.compile(r"(?i)^\s*(?:ENDFUNCTION|ENDMETHOD)\s*$")

        # Build explicit routine ranges with a stack so nested legacy routines
        # can still be analysed without treating caller evidence as body-local.
        stack: list[tuple[str, list[str], int]] = []
        routines: list[tuple[str, list[str], int, int]] = []
        for index, line in enumerate(lines):
            declaration = declaration_pattern.fullmatch(line)
            if declaration is not None:
                raw_params = declaration.group("params").strip()
                params = [] if not raw_params else [
                    part.strip().split()[0]
                    for part in self.recovery_normaliser._split_top_level_commas(raw_params)
                    if part.strip()
                ]
                stack.append((declaration.group("name"), params, index))
                continue
            if end_pattern.fullmatch(line) and stack:
                name, params, start = stack.pop()
                routines.append((name, params, start, index))

        if not routines:
            return source, []

        # Duplicate declarations with the same spelling make free-call evidence
        # ambiguous; refuse recovery for those names.
        name_counts: dict[str, int] = {}
        for name, _params, _start, _end in routines:
            key = name.lower()
            name_counts[key] = name_counts.get(key, 0) + 1

        def parse_call_arguments(line: str, routine_name: str) -> list[str] | None:
            pattern = re.compile(rf"(?i)(?<![.\w])CALL\s+{re.escape(routine_name)}\s*\(")
            match = pattern.search(line)
            if match is None:
                return None
            # One unambiguous free call per physical line is required.
            if pattern.search(line, match.end()) is not None:
                return None
            open_index = line.find("(", match.start(), match.end())
            depth = 0
            brace_depth = 0
            bracket_depth = 0
            quote: str | None = None
            escape = False
            close_index: int | None = None
            for pos in range(open_index, len(line)):
                ch = line[pos]
                if quote is not None:
                    if escape:
                        escape = False
                    elif ch == "\\":
                        escape = True
                    elif ch == quote:
                        quote = None
                    continue
                if ch in "'\"":
                    quote = ch
                    continue
                if ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                    if depth == 0:
                        close_index = pos
                        break
                    if depth < 0:
                        return None
                elif ch == "{":
                    brace_depth += 1
                elif ch == "}":
                    brace_depth -= 1
                elif ch == "[":
                    bracket_depth += 1
                elif ch == "]":
                    bracket_depth -= 1
                if brace_depth < 0 or bracket_depth < 0:
                    return None
            if close_index is None or line[close_index + 1 :].strip():
                return None
            argument_text = line[open_index + 1 : close_index]
            return [part.strip() for part in self.recovery_normaliser._split_top_level_commas(argument_text)]

        transformed_lines = list(lines)
        transformations: list[SourceTransformation] = []

        for name, params, start, end in routines:
            if name_counts.get(name.lower(), 0) != 1 or not params:
                continue

            evidenced_positions: set[int] = set()
            for call_line in lines:
                args = parse_call_arguments(call_line.strip(), name)
                if args is None or len(args) != len(params):
                    continue
                for position, argument in enumerate(args):
                    if re.fullmatch(r"(?i)EMPTY\s+SET", argument):
                        evidenced_positions.add(position)

            evidenced_names = {
                params[position]
                for position in evidenced_positions
                if position < len(params)
            }
            if not evidenced_names:
                continue

            for line_index in range(start + 1, end):
                original = transformed_lines[line_index]
                stripped = original.lstrip()
                if stripped.startswith("COMMENT"):
                    continue
                updated = original

                for param in sorted(evidenced_names, key=len, reverse=True):
                    # Scan only unquoted braces directly preceded by the exact
                    # simple formal parameter and '+'. Nested/multiple brace
                    # members are intentionally refused.
                    pattern = re.compile(rf"(?<![.\w]){re.escape(param)}\s*\+\s*\{{")
                    search_from = 0
                    while True:
                        match = pattern.search(updated, search_from)
                        if match is None:
                            break

                        # Ignore a textual match inside a quoted literal.
                        quote: str | None = None
                        escape = False
                        for ch in updated[:match.start()]:
                            if quote is not None:
                                if escape:
                                    escape = False
                                elif ch == "\\":
                                    escape = True
                                elif ch == quote:
                                    quote = None
                            elif ch in "'\"":
                                quote = ch
                        if quote is not None:
                            search_from = match.end()
                            continue

                        brace_open = updated.find("{", match.start(), match.end())
                        brace_close = updated.find("}", brace_open + 1)
                        if brace_close < 0:
                            break
                        interior = updated[brace_open + 1 : brace_close].strip()
                        if not interior or "{" in interior or "}" in interior:
                            search_from = brace_close + 1
                            continue
                        members = self.recovery_normaliser._split_top_level_commas(interior)
                        if len(members) != 1 or ":" in interior:
                            search_from = brace_close + 1
                            continue
                        expression = members[0].strip()
                        if not expression:
                            search_from = brace_close + 1
                            continue

                        replacement = (
                            f"CALL to_set(CALL to_list({param}) + "
                            f"CALL list_value({expression}))"
                        )
                        updated = updated[:match.start()] + replacement + updated[brace_close + 1 :]
                        search_from = match.start() + len(replacement)

                if updated != original:
                    transformed_lines[line_index] = updated
                    transformations.append(SourceTransformation(
                        line=line_index + 1,
                        rule="GC245",
                        source=original,
                        target=updated,
                    ))

        if not transformations:
            return source, []
        transformed = "\n".join(transformed_lines)
        if source.endswith("\n"):
            transformed += "\n"
        return transformed, transformations


    @staticmethod
    def _normalise_post_expansion_evidenced_queue_operations(
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        """Normalise queue operations exposed after structural line expansion.

        GC235 is a composition repair, not queue inference. Explicit
        ``create_queue()`` evidence preserves queue intrinsics; explicit LIST
        evidence retains the historical list-backed FIFO compatibility path.
        Evidence remains lexical-routine local and direct reassignment
        invalidates it. Unproven receivers are untouched.
        """
        scope_start = re.compile(r"(?i)^\s*(?:FUNCTION|METHOD|CONSTRUCTOR)\b")
        scope_end = re.compile(r"(?i)^\s*(?:ENDFUNCTION|ENDMETHOD|ENDCONSTRUCTOR)\b")
        direct_assignment = re.compile(
            r"^\s*(?P<name>[A-Za-z_]\w*)\s*<-\s*(?P<rhs>.+?)\s*$"
        )
        list_backing = re.compile(
            r"(?i)^(?:EMPTY\s+LIST|CALL\s+list_value\([^\n]*\))$"
        )
        queue_backing = re.compile(
            r"(?i)^CALL\s+create_queue\(\s*\)$"
        )

        evidence = LexicalEvidenceContext()
        transformations: list[SourceTransformation] = []
        output_lines: list[str] = []

        for line_number, original in enumerate(source.splitlines(), start=1):
            stripped = original.strip()
            if scope_start.match(stripped):
                evidence.enter(inherit=False)

            assignment = direct_assignment.match(original)
            if assignment is not None:
                name = assignment.group("name")
                rhs = assignment.group("rhs").strip()
                if list_backing.fullmatch(rhs):
                    evidence.establish("list", name)
                    evidence.invalidate("queue", name)
                elif queue_backing.fullmatch(rhs):
                    evidence.establish("queue", name)
                    evidence.invalidate("list", name)
                else:
                    evidence.invalidate("list", name)
                    evidence.invalidate("queue", name)

            updated = original

            # Explicit queue abstraction: preserve queue operations.
            for name in sorted(evidence.names("queue"), key=len, reverse=True):
                escaped = re.escape(name)

                match = re.fullmatch(
                    rf"(?i)(?P<indent>[ \t]*)ENQUEUE\s+(?P<value>.+?)\s+TO\s+{escaped}\s*",
                    updated,
                )
                if match is not None:
                    updated = (
                        f"{match.group('indent')}CALL ENQUEUE("
                        f"{name}, {match.group('value').strip()})"
                    )
                    break

                match = re.fullmatch(
                    rf"(?i)(?P<indent>[ \t]*)CALL\s+ENQUEUE\(\s*{escaped}\s*,\s*(?P<value>.+)\)\s*",
                    updated,
                )
                if match is not None:
                    # Already canonical for an evidenced queue.
                    break

                match = re.fullmatch(
                    rf"(?i)(?P<indent>[ \t]*)(?P<target>[A-Za-z_]\w*)\s*<-\s*DEQUEUE\s+FROM\s+{escaped}\s*",
                    updated,
                )
                if match is not None:
                    updated = (
                        f"{match.group('indent')}{match.group('target')} <- "
                        f"CALL DEQUEUE({name})"
                    )
                    break

            # Explicit list backing: retain the historical FIFO-on-list path.
            if updated == original:
                for name in sorted(evidence.names("list"), key=len, reverse=True):
                    escaped = re.escape(name)

                    match = re.fullmatch(
                        rf"(?i)(?P<indent>[ \t]*)ENQUEUE\s+(?P<value>.+?)\s+TO\s+{escaped}\s*",
                        updated,
                    )
                    if match is not None:
                        updated = (
                            f"{match.group('indent')}APPEND "
                            f"{match.group('value').strip()} TO {name}"
                        )
                        break

                    match = re.fullmatch(
                        rf"(?i)(?P<indent>[ \t]*)CALL\s+ENQUEUE\(\s*{escaped}\s*,\s*(?P<value>.+)\)\s*",
                        updated,
                    )
                    if match is not None:
                        updated = (
                            f"{match.group('indent')}APPEND "
                            f"{match.group('value').strip()} TO {name}"
                        )
                        break

                    match = re.fullmatch(
                        rf"(?i)(?P<indent>[ \t]*)(?P<target>[A-Za-z_]\w*)\s*<-\s*DEQUEUE\s+FROM\s+{escaped}\s*",
                        updated,
                    )
                    if match is not None:
                        updated = (
                            f"{match.group('indent')}{match.group('target')} <- "
                            f"REMOVE FIRST ITEM FROM {name}"
                        )
                        break

            if updated != original:
                transformations.append(
                    SourceTransformation(
                        line=line_number,
                        rule="GC235",
                        source=original,
                        target=updated,
                    )
                )
            output_lines.append(updated)

            if scope_end.match(stripped):
                evidence.exit()

        if not transformations:
            return source, []

        transformed = "\n".join(output_lines)
        if source.endswith("\n"):
            transformed += "\n"
        return transformed, transformations


    def _canonicalise_v11_surface_syntax(
        self,
        source: str,
    ) -> tuple[str, list[SourceTransformation]]:
        """Apply AJ v1.1 canonical spellings without inventing semantics.

        * bare None/none/NONE expression tokens -> NONE;
        * legacy v1.0 ~GET -> .GET;
        * .get on an explicitly dictionary-backed identifier -> .GET.

        Ordinary object.get(...) calls remain ordinary method calls unless the
        receiver has dictionary evidence in the same source.
        """
        evidence = LexicalEvidenceContext()
        for name in re.findall(
            r"(?im)^\s*([A-Za-z_]\w*)\s*<-\s*EMPTY\s+DICTIONARY\s*$",
            source,
        ):
            evidence.establish("dictionary", name)
        for name in re.findall(
            r"(?i)\b([A-Za-z_]\w*)\s+AS\s+DICTIONARY\b",
            source,
        ):
            evidence.establish("dictionary", name)
        dictionary_names = evidence.names("dictionary")
        output=[]
        transformations=[]
        for line_number,line in enumerate(source.splitlines(),start=1):
            current=line
            none_normalised=self._replace_none_outside_quotes(current)
            if none_normalised != current:
                transformations.append(SourceTransformation(
                    line=line_number,rule="GC197",source=current,target=none_normalised
                ))
                current=none_normalised

            legacy=re.sub(r"~GET\b", ".GET", current, flags=re.IGNORECASE)
            if legacy != current:
                transformations.append(SourceTransformation(
                    line=line_number,rule="GC198",source=current,target=legacy
                ))
                current=legacy

            for name in sorted(dictionary_names,key=len,reverse=True):
                updated=re.sub(
                    rf"(?i)\b{re.escape(name)}\s*\.\s*get(?=\s*\()",
                    f"{name}.GET",
                    current,
                )
                if updated != current:
                    transformations.append(SourceTransformation(
                        line=line_number,rule="GC199",source=current,target=updated
                    ))
                    current=updated
            output.append(current)
        result="\n".join(output)
        if source.endswith("\n"):
            result += "\n"
        return result,transformations

    def process(self, source: str) -> PseudocodeProcessingResult:
        """Applies compatibility conversions and records every changed line."""

        source_integrity_source, source_integrity_transformations = (
            self._recover_unambiguous_lossy_assignment_glyphs(source)
        )

        # Ambiguous lossy relations are restored only from the explicit evidence
        # lookup table. Assignment-position ``?`` recovery remains GC193 above.
        source_integrity_source, evidenced_glyph_transformations = (
            self._recover_evidence_backed_lossy_glyphs(source_integrity_source)
        )
        source_integrity_transformations.extend(evidenced_glyph_transformations)
        source_integrity_source, algorithm15_source_integrity_transformations = (
            self._recover_algorithm15_lossy_symbols(source_integrity_source)
        )
        source_integrity_transformations.extend(
            algorithm15_source_integrity_transformations
        )
        source_integrity_source, algorithm16_source_integrity_transformations = (
            self._recover_algorithm16_lossy_symbols(source_integrity_source)
        )
        source_integrity_transformations.extend(
            algorithm16_source_integrity_transformations
        )
        separator_source, separator_transformations = self._strip_visual_separators(source_integrity_source)
        character_source, character_transformations = self.character_normaliser.process(
            source=separator_source,
        )
        boundary_source, boundary_transformations = self.boundary_normaliser.process(
            source=character_source,
        )
        operator_source, operator_transformations = self.operator_normaliser.process(
            source=boundary_source,
        )

        # GC236 / EARLY_INLINE_SLASH_COMMENT:
        # Text following an unquoted ``//`` is explanatory comment text, not
        # part of the executable statement. Detach it before any declaration or
        # collection interpretation so phrases such as
        # ``empty DoubleEndedQueue // Stores indices`` expose the complete clean
        # declaration to the existing compatibility rules. The comment itself
        # remains in the source stream for later COMMENT metadata conversion.
        operator_source, early_inline_slash_comment_transformations = (
            self._detach_inline_slash_comments_early(operator_source)
        )

        # Structured Floyd input must be resolved before the generic literal
        # pass turns every bare INPUT into interactive string input.  Running
        # this narrow semantic-resolution rule here keeps the audit trail free
        # of transformations that are later reversed.
        operator_source, early_linked_cycle_transformations = (
            self.obvious_mismatch_normaliser._normalise_linked_cycle_detection(
                operator_source
            )
        )

        # Algorithm 41 is intentionally an expected failure. Stop before the
        # generic literal/call recovery passes so the undefined safety predicate
        # remains visibly undefined rather than becoming an invented function
        # contract such as CALL position_is_safe(...).
        if self.obvious_mismatch_normaliser._has_undefined_n_queens_safety(operator_source):
            strict_result = self.strict_processor.process(source=operator_source)
            transformations = list(source_integrity_transformations)
            transformations.extend(separator_transformations)
            transformations.extend(character_transformations)
            transformations.extend(boundary_transformations)
            transformations.extend(operator_transformations)
            transformations.extend(early_linked_cycle_transformations)
            transformations.extend(strict_result.transformations)
            return PseudocodeProcessingResult(
                profile=PseudocodeProfile.GENERIC_COMPATIBILITY,
                original_source=source,
                processed_source=strict_result.processed_source,
                transformations=transformations,
            )

        # This Algorithm 41 form also leaves essential N-Queens routines undefined.
        # Its placement/backtracking skeleton is explicit, but ``RECORD solution``
        # and the body of ``isSafe`` are descriptive operations.  They may not be
        # reconstructed unless the source defines/imports them or they map to a
        # defined AJ/Python intrinsic.  Stop before generic recovery can turn
        # those descriptions into invented executable behaviour.
        if self.obvious_mismatch_normaliser._has_undefined_n_queens_routines(operator_source):
            strict_result = self.strict_processor.process(source=operator_source)
            transformations = list(source_integrity_transformations)
            transformations.extend(separator_transformations)
            transformations.extend(character_transformations)
            transformations.extend(boundary_transformations)
            transformations.extend(operator_transformations)
            transformations.extend(early_linked_cycle_transformations)
            transformations.extend(strict_result.transformations)
            return PseudocodeProcessingResult(
                profile=PseudocodeProfile.GENERIC_COMPATIBILITY,
                original_source=source,
                processed_source=strict_result.processed_source,
                transformations=transformations,
            )

        # Algorithm 5 supplies the filtering loop but leaves the branch-driving
        # punctuation predicate undefined. Stop before GC104 can rename that
        # missing semantic definition into an invented is_punctuation call, and
        # before the neutral wrapper can make the response look executable.
        if self.obvious_mismatch_normaliser._has_undefined_punctuation_predicate(operator_source):
            strict_result = self.strict_processor.process(source=operator_source)
            transformations = list(source_integrity_transformations)
            transformations.extend(separator_transformations)
            transformations.extend(character_transformations)
            transformations.extend(boundary_transformations)
            transformations.extend(operator_transformations)
            transformations.extend(early_linked_cycle_transformations)
            transformations.extend(strict_result.transformations)
            return PseudocodeProcessingResult(
                profile=PseudocodeProfile.GENERIC_COMPATIBILITY,
                original_source=source,
                processed_source=strict_result.processed_source,
                transformations=transformations,
            )

        # Descriptive environmental file/folder predicates are not executable
        # merely because their intended purpose is recognisable.  Unless the
        # source explicitly defines/imports the exact helper dependency, stop
        # before GC104 can rename missing semantics into invented
        # is_file/is_directory calls.  This guard is model/algorithm independent.
        if self.obvious_mismatch_normaliser._has_undefined_environmental_file_type_predicates(operator_source):
            strict_result = self.strict_processor.process(source=operator_source)
            transformations = list(source_integrity_transformations)
            transformations.extend(separator_transformations)
            transformations.extend(character_transformations)
            transformations.extend(boundary_transformations)
            transformations.extend(operator_transformations)
            transformations.extend(early_linked_cycle_transformations)
            transformations.extend(strict_result.transformations)
            return PseudocodeProcessingResult(
                profile=PseudocodeProfile.GENERIC_COMPATIBILITY,
                original_source=source,
                processed_source=strict_result.processed_source,
                transformations=transformations,
            )

        # Descriptive maze/grid navigation language is not executable merely
        # because a conventional implementation is familiar.  Stop before any
        # compatibility rule can select an adjacency-list/coordinate
        # representation, invent neighbours/bounds/wall semantics, or create a
        # helper dependency.  This boundary is corpus-wide and source-shape
        # independent.
        if self.obvious_mismatch_normaliser._has_abstract_maze_navigation_semantics(operator_source):
            strict_result = self.strict_processor.process(source=operator_source)
            transformations = list(source_integrity_transformations)
            transformations.extend(separator_transformations)
            transformations.extend(character_transformations)
            transformations.extend(boundary_transformations)
            transformations.extend(operator_transformations)
            transformations.extend(early_linked_cycle_transformations)
            transformations.extend(strict_result.transformations)
            return PseudocodeProcessingResult(
                profile=PseudocodeProfile.GENERIC_COMPATIBILITY,
                original_source=source,
                processed_source=strict_result.processed_source,
                transformations=transformations,
            )

        # Descriptive coordination/control semantics are not executable merely
        # because a conventional implementation is familiar. Stop before
        # compatibility recovery can invent completion, proximity, collision,
        # bounds, synchronisation or unbound free-helper semantics. This
        # boundary is corpus-wide and source-shape independent.
        if self.obvious_mismatch_normaliser._has_abstract_coordination_semantics(operator_source):
            strict_result = self.strict_processor.process(source=operator_source)
            transformations = list(source_integrity_transformations)
            transformations.extend(separator_transformations)
            transformations.extend(character_transformations)
            transformations.extend(boundary_transformations)
            transformations.extend(operator_transformations)
            transformations.extend(early_linked_cycle_transformations)
            transformations.extend(strict_result.transformations)
            return PseudocodeProcessingResult(
                profile=PseudocodeProfile.GENERIC_COMPATIBILITY,
                original_source=source,
                processed_source=strict_result.processed_source,
                transformations=transformations,
            )

        # Algorithm 45 explicitly writes into Result[i][j] but never creates
        # or initialises Result. Stop before generic INPUT/wrapper/range recovery
        # so the missing required state remains visible and the response is not
        # counted as executable through an invented result matrix.
        if self.obvious_mismatch_normaliser._has_uninitialised_matrix_addition_result(operator_source):
            strict_result = self.strict_processor.process(source=operator_source)
            transformations = list(source_integrity_transformations)
            transformations.extend(separator_transformations)
            transformations.extend(character_transformations)
            transformations.extend(boundary_transformations)
            transformations.extend(operator_transformations)
            transformations.extend(early_linked_cycle_transformations)
            transformations.extend(strict_result.transformations)
            return PseudocodeProcessingResult(
                profile=PseudocodeProfile.GENERIC_COMPATIBILITY,
                original_source=source,
                processed_source=strict_result.processed_source,
                transformations=transformations,
            )

        # Algorithm 46 supplies the complete triple-loop multiplication
        # procedure but never creates the containing Result matrix.  Stop before
        # generic INPUT/wrapper/range recovery, and before the retired GC127
        # reconstruction could generate random matrices or Result storage.
        if self.obvious_mismatch_normaliser._has_uninitialised_matrix_multiplication_result(operator_source):
            strict_result = self.strict_processor.process(source=operator_source)
            transformations = list(source_integrity_transformations)
            transformations.extend(separator_transformations)
            transformations.extend(character_transformations)
            transformations.extend(boundary_transformations)
            transformations.extend(operator_transformations)
            transformations.extend(early_linked_cycle_transformations)
            transformations.extend(strict_result.transformations)
            return PseudocodeProcessingResult(
                profile=PseudocodeProfile.GENERIC_COMPATIBILITY,
                original_source=source,
                processed_source=strict_result.processed_source,
                transformations=transformations,
            )

        # This form is a complete first-match linear search. Resolve
        # its inclusive source endpoint before generic range recovery can copy
        # that endpoint unchanged into AJ's end-exclusive RANGE. The narrow
        # source-integrity recovery has already restored any unambiguous lost
        # assignment glyphs before this strict-AJ recogniser runs.
        operator_source, early_linear_search_transformations = (
            self.obvious_mismatch_normaliser._normalise_linear_search_case(
                operator_source
            )
        )

        # This form is an explicit bubble sort. Resolve its inclusive
        # source bounds and preserve SWAP as a canonical primitive before generic
        # wrapper/range/SWAP recovery can shorten the loops or introduce generated
        # temporary state into the canonical pseudocode.
        operator_source, early_bubble_sort_transformations = (
            self.obvious_mismatch_normaliser._normalise_bubble_sort_case(
                operator_source
            )
        )

        # Pair-sum range endpoints must be resolved before generic bare INPUT
        # conversion and wrapper recovery. This keeps the audit free from a
        # transient string-input representation and preserves the explicitly
        # approved inclusive-source -> end-exclusive-AJ adjustment.
        operator_source, early_pair_sum_transformations = (
            self.obvious_mismatch_normaliser._normalise_pair_sum_nested_loops(
                operator_source
            )
        )

        # Kadane's recurrence is explicit, but the structured Array input and
        # inclusive source endpoint need resolving before generic INPUT and
        # range recovery. This also avoids a transient string-input audit step.
        operator_source, early_kadane_transformations = (
            self.obvious_mismatch_normaliser._normalise_kadane_max_sum(
                operator_source
            )
        )

        # The Tower-of-Hanoi corpus form is algorithmically complete. Under
        # AJ v1.2 preserve its local Hanoi function inside the neutral outer
        # computation and keep N as an external parameter. Resolve the explicit
        # message-style multi-part output before generic output handling.
        operator_source, early_hanoi_transformations = (
            self.obvious_mismatch_normaliser._normalise_tower_of_hanoi(
                operator_source
            )
        )

        # The inventory-update form is already algorithmically complete.
        # Resolve its four external dependencies directly to the neutral wrapper
        # before generic INPUT conversion can introduce transient string inputs
        # or the legacy PROCESS wrapper name.
        operator_source, early_inventory_update_transformations = (
            self.obvious_mismatch_normaliser._normalise_inventory_update_case(
                operator_source
            )
        )

        # GC208 / SQUARE_DIMENSION_REFERENCE_RESOLUTION:
        # Resolve only an explicitly annotated square dimension used in the exact
        # source loop bound 0..D-1.  This runs before the neutral wrapper removes
        # the descriptive INPUT annotation, and it names LENGTH OF the supplied
        # collection directly rather than inventing a runtime D variable.
        operator_source, early_square_dimension_transformations = (
            self._normalise_square_dimension_loop_bounds(operator_source)
        )

        # GC212 / SQUARE_DIMENSION_IDENTIFIER_REFERENCE_RESOLUTION:
        # GC208 retains the exact 0..D-1 loop-bound surface. Resolve any
        # remaining otherwise-unbound same-routine D references directly to
        # LENGTH OF the uniquely annotated square collection. Arithmetic is
        # preserved exactly, so ordinary '/' remains ordinary division.
        operator_source, early_square_dimension_reference_transformations = (
            self._normalise_square_dimension_identifier_references(operator_source)
        )

        # GC224 / EVIDENCED_LINKED_MATRIX_MULTIPLICATION_DIMENSIONS:
        # Resolve only the complete source-annotated A(M x N), B(N x P)
        # multiplication skeleton. M/N/P remain annotation-only shape symbols;
        # allocation and all three bounds are represented by evidenced matrix
        # lengths without inventing multiplication logic or scalar parameters.
        operator_source, early_linked_matrix_multiplication_transformations = (
            self._normalise_linked_matrix_multiplication_dimensions(operator_source)
        )

        # GC223 / EVIDENCED_RECTANGULAR_MATRIX_ALLOCATION:
        # Resolve only a source-annotated same-dimensions R x C matrix pair
        # whose explicit result allocation is followed by the matching nested
        # row/column loops and a direct full-cell overwrite. This preserves the
        # annotation as shape evidence while avoiding invented R/C parameters.
        operator_source, early_rectangular_matrix_transformations = (
            self._normalise_rectangular_matrix_allocation_from_shape(operator_source)
        )

        # AUDIT_HYGIENE / DIRECT_INPUT_TO_NEUTRAL_WRAPPER:
        # Under the approved wrapper policy, a top-level unnamed algorithm whose
        # bare INPUT declarations will become function parameters must go there
        # directly.  Do not first invent interactive INPUT(STRING(...)) forms
        # that are immediately discarded by the wrapper pass.  This is a
        # representational/audit correction only: source-named functions are
        # left untouched, and expected-fail semantic guards have already exited
        # above before reaching this point.
        operator_source, early_direct_wrapper_transformations = (
            self._normalise_direct_top_level_input_wrapper(operator_source)
        )

        # GC219 / EVIDENCED_INPUT_HELPER_FINAL_RETURN_WRAPPER:
        # Some generic responses omit only the neutral outer algorithm wrapper:
        # bare INPUT declarations are followed by complete helper declarations
        # and one final top-level RETURN that calls an explicit helper. Recover
        # that structural container without supplying any missing helper logic.
        operator_source, early_helper_wrapper_transformations = (
            self._normalise_input_helper_final_return_wrapper(operator_source)
        )

        operator_source, early_empty_brace_evidence_transformations = (
            self._resolve_empty_braces_from_usage_evidence(operator_source)
        )

        operator_source, early_dictionary_resolution_transformations = (
            self._resolve_type_only_dictionary_from_unique_usage(operator_source)
        )

        operator_source, early_multiple_assignment_transformations = (
            self._split_explicit_multiple_assignments_before_literals(operator_source)
        )

        # GC226 / TRAILING_EXPLANATORY_PARENTHETICAL_COMMENT:
        # Once an assignment already has a complete ``empty <collection>`` RHS,
        # a trailing ``(or ...)`` / ``(for ...)`` phrase is explanatory prose,
        # not executable constructor syntax.  Detach it as a comment before the
        # literal/collection passes so later rules cannot reinterpret its words.
        operator_source, early_parenthetical_comment_transformations = (
            self._normalise_trailing_explanatory_parenthetical_comments(operator_source)
        )

        # GC228 / EXPLICIT_ALPHABETICAL_ORDER:
        # Two-argument SORT(value, ALPHABETICAL_ORDER) supplies an explicit
        # ascending alphabetical sort mode. Route that exact marker through
        # the existing sort_value intrinsic rather than treating the marker as
        # an undeclared runtime identifier. Other modes/comparators are left
        # untouched.
        operator_source, early_alphabetical_sort_transformations = (
            self._normalise_explicit_alphabetical_sort_mode(operator_source)
        )

        # GC227 / EVIDENCED_REGEX_REPLACE_ALL:
        # A free three-argument REPLACE_ALL call is mapped to the internal regex
        # substitution intrinsic only when its quoted pattern contains direct
        # regex syntax evidence. Protect literal backslashes before frozen AJ
        # string lexing so escapes such as \s survive representation unchanged.
        operator_source, early_regex_replace_all_transformations = (
            self._normalise_evidenced_regex_replace_all(operator_source)
        )

        literal_source, literal_transformations = self.literal_declaration_normaliser.process(
            source=operator_source,
        )
        collection_source, collection_transformations = self.collection_normaliser.process(
            source=literal_source,
        )
        statement_source, statement_transformations = self.statement_normaliser.process(
            source=collection_source,
        )
        statement_source = re.sub(
            r"(?im)^(?P<indent>[ \t]*)CALL[ \t]+APPEND[ \t]+(?P<value>.+?)[ \t]+TO[ \t]+(?P<collection>[A-Za-z_]\w*)[ \t]*$",
            lambda m: f"{m.group('indent')}APPEND {m.group('value')} TO {m.group('collection')}",
            statement_source,
        )
        obvious_source, obvious_transformations = self.obvious_mismatch_normaliser.process(
            source=statement_source,
        )
        grammar_source, grammar_transformations = self.grammar_normaliser.process(
            source=obvious_source,
        )
        grammar_source, v11_surface_transformations = (
            self._canonicalise_v11_surface_syntax(grammar_source)
        )
        recovery_source, recovery_transformations = self.recovery_normaliser.process(
            source=grammar_source,
        )
        recovery_source = re.sub(
            r"(?im)^(?P<indent>[ \t]*)CALL[ \t]+APPEND[ \t]+(?P<value>.+?)[ \t]+TO[ \t]+(?P<collection>[A-Za-z_]\w*)[ \t]*$",
            lambda m: (
                f"{m.group('indent')}APPEND TUPLE{m.group('value')} TO {m.group('collection')}"
                if m.group('value').strip().startswith("(") and m.group('value').strip().endswith(")")
                else f"{m.group('indent')}APPEND {m.group('value')} TO {m.group('collection')}"
            ),
            recovery_source,
        )
        recovery_source = re.sub(
            r"(?im)^(?P<indent>[ \t]*)ALERT[ \t]+(?P<expr>.+?)[ \t]*$",
            lambda m: f"{m.group('indent')}OUTPUT {m.group('expr')}",
            recovery_source,
        )
        recovery_source = re.sub(
            r"(?i)\bCALL\s+CALL\s+",
            "CALL ",
            recovery_source,
        )
        recovery_source = re.sub(
            r"(?i)\bCALL\s+(AND|OR)\b",
            lambda m: m.group(1).upper(),
            recovery_source,
        )
        recovery_source, final_reserved_identifier_transformations = (
            self.obvious_mismatch_normaliser._normalise_reserved_identifier_collisions(
                recovery_source
            )
        )
        recovery_source, final_function_parameter_transformations = (
            self.obvious_mismatch_normaliser._normalise_function_parameter_phrasing(
                recovery_source
            )
        )
        recovery_transformations = (
            list(recovery_transformations)
            + list(final_reserved_identifier_transformations)
            + list(final_function_parameter_transformations)
        )

        # Recovery may rebalance malformed source conservatively. Re-apply the
        # shared structural canonicaliser as the final authority before strict
        # parsing so an already-repaired ELSE/ENDIF relationship is preserved.
        recovery_source, final_structural_transformations = (
            self.obvious_mismatch_normaliser._normalise_shared_structural_idioms(
                recovery_source
            )
        )
        recovery_transformations = (
            list(recovery_transformations)
            + list(final_structural_transformations)
        )

        # GC235 / POST_EXPANSION_EVIDENCED_QUEUE_OPERATION:
        # Structural recovery can expose queue operations that were embedded in
        # one-line IF statements when the earlier list-backed queue pass ran.
        # Reuse only explicit local list-backing evidence for those newly
        # standalone queue statements; do not infer queue semantics elsewhere.
        recovery_source, post_expansion_queue_transformations = (
            self._normalise_post_expansion_evidenced_queue_operations(
                recovery_source
            )
        )
        recovery_transformations = (
            list(recovery_transformations)
            + list(post_expansion_queue_transformations)
        )

        # Stateful ADT container recovery must run after block recovery has made
        # the outer/nested FUNCTION boundaries explicit.  It changes only the
        # outer container to CLASS when strong shared-state/method evidence is
        # present; method bodies remain unchanged.
        recovery_source, stateful_adt_transformations = (
            self._normalise_stateful_adt_function_container(recovery_source)
        )
        recovery_transformations = (
            list(recovery_transformations)
            + list(stateful_adt_transformations)
        )

        # Explicit legacy CLASS containers with strongly evidenced instance state
        # are canonicalised to the frozen PROPERTY/CONSTRUCTOR/METHOD grammar.
        # This also closes a missing terminal ENDCLASS, but only when the entire
        # class shape is otherwise complete and no abstract-array growth write
        # would be operationalised by doing so.
        recovery_source, explicit_class_transformations = (
            self._normalise_explicit_stateful_class(recovery_source)
        )
        recovery_transformations = (
            list(recovery_transformations)
            + list(explicit_class_transformations)
        )

        # Recovery may expose a generic "values [...]" list literal after the
        # contextual maze pass. Canonicalise the explicit four-direction tuple
        # list without changing the maze's wall convention.
        recovery_source = re.sub(
            r"(?im)^(?P<indent>[ \t]*)directions\s*<-\s*(?:values\s*)?\[\s*\(0\s*,\s*1\)\s*,\s*\(1\s*,\s*0\)\s*,\s*\(0\s*,\s*-1\)\s*,\s*\(-1\s*,\s*0\)\s*\]\s*$",
            lambda m: (
                f"{m.group('indent')}directions <- CALL list_value("
                "TUPLE(0, 1), TUPLE(1, 0), TUPLE(0, -1), TUPLE(-1, 0))"
            ),
            recovery_source,
        )
        recovery_source = re.sub(
            r"(?im)^(?P<indent>[ \t]*)directions\s*<-\s*CALL\s+list_value\(\s*\(0\s*,\s*1\)\s*,\s*\(1\s*,\s*0\)\s*,\s*\(0\s*,\s*-1\)\s*,\s*\(-1\s*,\s*0\)\s*\)\s*$",
            lambda m: (
                f"{m.group('indent')}directions <- CALL list_value("
                "TUPLE(0, 1), TUPLE(1, 0), TUPLE(0, -1), TUPLE(-1, 0))"
            ),
            recovery_source,
        )

        # Recovery can expose flattened indexed targets after the earlier
        # canonical assignment pass. Canonicalise only unambiguous assignment
        # statements here; comparison operators are deliberately excluded.
        recovery_source = re.sub(
            r"(?m)^(?P<indent>[ \t]*)(?P<target>[A-Za-z_]\w*(?:\[[^\n=]+\])+?)\s*=\s*(?!=)(?P<value>[^\n]+)$",
            lambda m: (
                f"{m.group('indent')}{m.group('target')} <- "
                f"{m.group('value').strip()}"
            ),
            recovery_source,
        )

        # GC215 / EVIDENCED_ORDERED_CACHE_STATEFUL_ADT:
        # A top-level INIT + multiple shared-state operations can be recovered
        # as a class only when the source itself proves the ordered key/value
        # abstraction and capacity bound.  The source-authored recency helpers
        # remain opaque CALLs; GC215 does not implement them.  The capacity-like
        # state becomes a constructor parameter; no numeric default is invented.
        recovery_source, ordered_cache_adt_transformations = (
            self._normalise_evidenced_ordered_cache_stateful_adt(recovery_source)
        )

        # GC216 / EVIDENCED_COUNTED_LIST_STATEFUL_ADT:
        # Explicit EMPTY LIST + zero-count outer state followed by multiple
        # operations can be recovered as a neutral class only when the source
        # itself proves the counted-list interface shape.
        recovery_source, counted_list_adt_transformations = (
            self._normalise_evidenced_counted_list_stateful_adt(recovery_source)
        )

        # GC218 / EVIDENCED_CONNECTED_MULTI_LIST_STATEFUL_ADT:
        # Multiple explicitly empty list states followed by top-level operations
        # can be recovered as one neutral class only when the source-local
        # operation/state graph is connected and a destructive cross-state
        # transfer proves that the lists participate in one shared abstraction.
        recovery_source, connected_multi_list_adt_transformations = (
            self._normalise_evidenced_connected_multi_list_stateful_adt(recovery_source)
        )

        # GC214 is retired from the active compatibility sequence.
        # User-confirmed semantics define unique(collection) as a SET-producing
        # operation, so removing an explicit unique(...) call would change the
        # collection type even when the input values are already duplicate-free.
        redundant_unique_transformations = []

        # GC222 / EXACT_UNIQUE_TO_SET_INTRINSIC:
        # Every exact one-identifier unique(collection) call is therefore
        # preserved as explicit SET semantics via the existing to_set intrinsic.
        # Value-level redundancy is not enough to erase the source operation.
        recovery_source, unique_intrinsic_transformations = (
            self._normalise_exact_unique_deduplication_intrinsic(recovery_source)
        )

        # GC232 / EVIDENCED_SET_TO_LIST_INTRINSIC:
        # Preserve an explicit ConvertSetToList(name) operation only when that
        # same lexical routine has already established name as EMPTY SET and no
        # intervening direct reassignment invalidates the evidence. The source
        # conversion is represented by the existing to_list intrinsic.
        recovery_source, set_to_list_transformations = (
            self._normalise_evidenced_set_to_list_intrinsic(recovery_source)
        )

        # GC245 / EVIDENCED_NON_MUTATING_SINGLETON_SET_EXTENSION:
        # A canonical call that supplies EMPTY SET at a routine parameter
        # position proves set backing for that formal. Preserve an explicit
        # ``formal + {value}`` expression in that routine by constructing a new
        # set through the existing list/set compatibility intrinsics; do not
        # mutate the original set or infer set type across routines.
        recovery_source, singleton_set_extension_transformations = (
            self._normalise_evidenced_singleton_set_extensions(recovery_source)
        )

        strict_result = self.strict_processor.process(
            source=recovery_source,
            include_member_identifier_evidence=False,
        )
        generic_tokens = self.lexer.tokenise(
            source=strict_result.processed_source,
        )
        processed_lines = []
        transformations = list(source_integrity_transformations)
        transformations.extend(separator_transformations)
        transformations.extend(character_transformations)
        transformations.extend(
            boundary_transformations
        )
        transformations.extend(
            operator_transformations
        )
        transformations.extend(
            early_inline_slash_comment_transformations
        )
        transformations.extend(
            early_linked_cycle_transformations
        )
        transformations.extend(
            early_linear_search_transformations
        )
        transformations.extend(
            early_bubble_sort_transformations
        )
        transformations.extend(
            early_pair_sum_transformations
        )
        transformations.extend(
            early_kadane_transformations
        )
        transformations.extend(
            early_hanoi_transformations
        )
        transformations.extend(
            early_inventory_update_transformations
        )
        transformations.extend(
            early_square_dimension_transformations
        )
        transformations.extend(
            early_square_dimension_reference_transformations
        )
        transformations.extend(
            early_linked_matrix_multiplication_transformations
        )
        transformations.extend(
            early_rectangular_matrix_transformations
        )
        transformations.extend(
            early_direct_wrapper_transformations
        )
        transformations.extend(
            early_helper_wrapper_transformations
        )
        transformations.extend(
            early_empty_brace_evidence_transformations
        )
        transformations.extend(
            early_dictionary_resolution_transformations
        )
        transformations.extend(
            early_multiple_assignment_transformations
        )
        transformations.extend(
            early_parenthetical_comment_transformations
        )
        transformations.extend(
            early_alphabetical_sort_transformations
        )
        transformations.extend(
            early_regex_replace_all_transformations
        )
        transformations.extend(
            literal_transformations
        )
        transformations.extend(
            collection_transformations
        )
        transformations.extend(
            statement_transformations
        )
        transformations.extend(
            obvious_transformations
        )
        transformations.extend(
            grammar_transformations
        )
        transformations.extend(
            v11_surface_transformations
        )
        transformations.extend(
            recovery_transformations
        )
        transformations.extend(
            ordered_cache_adt_transformations
        )
        transformations.extend(
            counted_list_adt_transformations
        )
        transformations.extend(
            connected_multi_list_adt_transformations
        )
        transformations.extend(
            redundant_unique_transformations
        )
        transformations.extend(
            unique_intrinsic_transformations
        )
        transformations.extend(
            set_to_list_transformations
        )
        transformations.extend(
            singleton_set_extension_transformations
        )
        transformations.extend(
            strict_result.transformations
        )

        for line_token in generic_tokens:
            transformed_content = self._convert_token(
                line_token=line_token,
            )
            transformed_content = self._convert_operators(
                content=transformed_content,
            )
            transformed_line = f"{line_token.indentation}{transformed_content}"
            source_line = f"{line_token.indentation}{line_token.content}"

            if transformed_line != source_line:
                transformations.append(
                    SourceTransformation(
                        line=line_token.line_number,
                        rule=f"GENERIC_{line_token.category}",
                        source=source_line,
                        target=transformed_line,
                    )
                )

            processed_lines.append(
                transformed_line
            )

        processed_source = "\n".join(processed_lines)

        return PseudocodeProcessingResult(
            profile=PseudocodeProfile.GENERIC_COMPATIBILITY,
            original_source=source,
            processed_source=processed_source,
            transformations=transformations,
        )

    def _strip_visual_separators(self, source: str) -> tuple[str, list[SourceTransformation]]:
        output: list[str] = []
        transformations: list[SourceTransformation] = []
        for line_number, line in enumerate(source.splitlines(), start=1):
            if re.fullmatch(r"\s*[_=-]{8,}\s*", line):
                transformations.append(SourceTransformation(
                    line=line_number,
                    rule="GC100",
                    source=line,
                    target="",
                ))
                continue
            output.append(line)
        return "\n".join(output), transformations

    def _convert_token(self, line_token: GenericLineToken) -> str:
        """Converts one classified generic line into AJ Dialect syntax."""

        content = line_token.content

        if line_token.category == "SET_ASSIGNMENT":
            match = re.match(
                r"^SET\s+(.+?)\s+TO\s+(.+)$",
                content,
                re.IGNORECASE,
            )

            if match is not None:
                target = match.group(1).strip()
                value = match.group(2).strip()
                return f"{target} <- {value}"

        if line_token.category == "OUTPUT":
            match = re.match(
                r"^(?:PRINT|DISPLAY)\s+(.+)$",
                content,
                re.IGNORECASE,
            )

            if match is not None:
                output_expression = match.group(1).strip()
                return f"OUTPUT {output_expression}"

        if line_token.category == "END_IF":
            return "ENDIF"

        if line_token.category == "END_WHILE":
            return "ENDWHILE"

        if line_token.category == "NEXT":
            return "ENDFOR"

        if line_token.category == "IF":
            if not re.search(r"\sTHEN$", content, re.IGNORECASE):
                return f"{content} THEN"

        if line_token.category == "WHILE":
            if not re.search(r"\sDO$", content, re.IGNORECASE):
                return f"{content} DO"

        if line_token.category == "FOR_EACH":
            if not re.search(r"\sDO$", content, re.IGNORECASE):
                return f"{content} DO"

        if line_token.category == "EQUALS_ASSIGNMENT":
            return re.sub(
                r"\s*=\s*",
                " <- ",
                content,
                count=1,
            )

        return content

    def _convert_operators(self, content: str) -> str:
        """Converts supported generic arithmetic operator words."""

        converted_content = re.sub(
            r"\bMOD\b",
            "MODULUS",
            content,
            flags=re.IGNORECASE,
        )
        converted_content = re.sub(
            r"\bDIV\b",
            "INTEGER DIVISION",
            converted_content,
            flags=re.IGNORECASE,
        )

        return converted_content


class GeneralPseudocodeProcessor:
    """Passes supplied pseudocode to the parser without source conversion."""

    def process(self, source: str) -> PseudocodeProcessingResult:
        """Returns the original source unchanged."""

        return PseudocodeProcessingResult(
            profile=PseudocodeProfile.GENERAL_NO_CONVERSION,
            original_source=source,
            processed_source=source,
            transformations=[],
        )


class PseudocodeProfileProcessor:
    """Selects the correct processor for a requested pseudocode profile."""

    def __init__(self) -> None:
        self.strict_processor = StrictPseudocodeProcessor()
        self.generic_processor = GenericPseudocodeProcessor()
        self.general_processor = GeneralPseudocodeProcessor()
        self.header_comment_stripper = InitialHashCommentStripper()

    def process(
        self,
        source: str,
        profile: PseudocodeProfile,
    ) -> PseudocodeProcessingResult:
        """Strips an optional file header and applies the selected profile."""

        profile_source, header_removed, header_lines_removed = (
            self.header_comment_stripper.strip(
                source=source,
            )
        )

        if profile == PseudocodeProfile.AJ_DIALECT_STRICT:
            result = self.strict_processor.process(
                source=profile_source,
            )

        elif profile == PseudocodeProfile.GENERIC_COMPATIBILITY:
            result = self.generic_processor.process(
                source=profile_source,
            )

        elif profile == PseudocodeProfile.GENERAL_NO_CONVERSION:
            result = self.general_processor.process(
                source=profile_source,
            )

        else:
            raise ValueError(
                f"Unsupported pseudocode profile: {profile}"
            )

        result.original_source = source
        result.header_comment_removed = header_removed
        result.header_lines_removed = header_lines_removed

        return result
