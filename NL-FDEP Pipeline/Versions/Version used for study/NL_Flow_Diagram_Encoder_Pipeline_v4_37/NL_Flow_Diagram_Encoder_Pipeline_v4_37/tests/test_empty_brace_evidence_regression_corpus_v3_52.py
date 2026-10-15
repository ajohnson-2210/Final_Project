"""Standing regression corpus for ambiguous bare-brace type evidence.

These cases deliberately live in a corpus-shaped fixture rather than only in
rule-unit tests.  They protect the source-evidence policy across future profile
refactors: structural use may prove a collection type; identifier spelling,
membership/iteration alone, conflicting evidence, later rebinding, scope leaks,
and quoted text may not.
"""

from corpus_evaluator import StructuredExportAdapter
from pseudocode_profiles import PseudocodeProfile, PseudocodeProfileProcessor


CORPUS = r'''# source_f Unique IP Addresses
INPUT ipList
uniqueSet = {}
FOR ip in ipList:
    uniqueSet.add(ip)
RETURN list(uniqueSet)

# source_f Character Frequency
INPUT s
freq = {}
FOR char in s:
    freq[char] = freq.get(char, 0) + 1
RETURN freq

# source_f Longest Substring
INPUT s
maxLen = 0
start = 0
seen = {}
FOR i from 0 to length(s)-1:
    IF s[i] in seen AND seen[s[i]] >= start:
        start = seen[s[i]] + 1
    seen[s[i]] = i
    maxLen = MAX(maxLen, i - start + 1)
RETURN maxLen

# source_f Find Pairs
INPUT arr, target
seen = {}
pairs = []
FOR num in arr:
    comp = target - num
    IF comp in seen:
        pairs.add((MIN(num, comp), MAX(num, comp)))
    seen[num] = true
RETURN unique(pairs)

# Name Hint Only
INPUT x
seen = {}
RETURN seen

# Membership Only
INPUT x
visited = {}
IF x in visited:
    RETURN TRUE
RETURN FALSE

# Iteration Only
INPUT xs
values = {}
FOR EACH x IN values DO
    OUTPUT x
ENDFOR
RETURN values

# Conflicting Collection Evidence
INPUT x
state = {}
state.add(x)
value = state[x]
RETURN value

# Rebind Before Evidence
INPUT x, other
cache = {}
cache = other
cache.add(x)
RETURN cache

# Scope Isolation
FUNCTION first ACCEPTS()
    parent = {}
    RETURN parent
END FUNCTION
FUNCTION second ACCEPTS(x)
    parent.add(x)
    RETURN parent
END FUNCTION

# Quoted Operation Text
INPUT x
counts = {}
OUTPUT "counts.add(x)"
RETURN counts
'''


def _examples():
    examples = StructuredExportAdapter().extract(CORPUS, "Evidence Regression Corpus")
    assert len(examples) == 11
    return {example.title: example for example in examples}


def _process(source: str):
    return PseudocodeProfileProcessor().process(
        source, PseudocodeProfile.GENERIC_COMPATIBILITY
    )


def test_regression_corpus_extracts_all_cases_without_source_flattening():
    examples = _examples()
    assert "uniqueSet = {}" in examples["source_f Unique IP Addresses"].source
    assert "    uniqueSet.add(ip)" in examples["source_f Unique IP Addresses"].source
    assert "    parent.add(x)" in examples["Scope Isolation"].source


def test_regression_corpus_real_source_f_set_case_is_structurally_proved():
    result = _process(_examples()["source_f Unique IP Addresses"].source)
    assert "uniqueSet <- EMPTY SET" in result.processed_source
    assert any(item.rule == "GC250" for item in result.transformations)
    assert all(item.rule not in {"GC092", "GC093"} for item in result.transformations)


def test_regression_corpus_real_source_f_dictionary_cases_are_structurally_proved():
    examples = _examples()

    frequency = _process(examples["source_f Character Frequency"].source)
    assert "freq <- EMPTY DICTIONARY" in frequency.processed_source
    assert any(item.rule == "GC220" for item in frequency.transformations)

    substring = _process(examples["source_f Longest Substring"].source)
    assert "seen <- EMPTY DICTIONARY" in substring.processed_source
    assert any(item.rule == "GC220" for item in substring.transformations)

    pairs = _process(examples["source_f Find Pairs"].source)
    assert "seen <- EMPTY DICTIONARY" in pairs.processed_source
    assert any(item.rule == "GC220" for item in pairs.transformations)


def test_regression_corpus_weak_or_ambiguous_cases_remain_unresolved():
    examples = _examples()
    unresolved = {
        "Name Hint Only": "seen",
        "Membership Only": "visited",
        "Iteration Only": "values",
        "Conflicting Collection Evidence": "state",
        "Rebind Before Evidence": "cache",
        "Scope Isolation": "parent",
        "Quoted Operation Text": "counts",
    }

    for title, name in unresolved.items():
        result = _process(examples[title].source)
        assert f"{name} <- {{}}" in result.processed_source, title
        assert f"{name} <- EMPTY SET" not in result.processed_source, title
        assert f"{name} <- EMPTY DICTIONARY" not in result.processed_source, title
        assert all(
            item.rule not in {"GC092", "GC093", "GC220", "GC250"}
            for item in result.transformations
        ), title
