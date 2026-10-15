from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_v4_37_release_metadata_is_current():
    assert (ROOT / "VERSION").read_text(encoding="utf-8").strip() == "4.37"
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    release = (ROOT / "docs" / "release_v4_37.md").read_text(encoding="utf-8")
    manifest = (ROOT / "manifests" / "manifest_v4_37.txt").read_text(encoding="utf-8")
    assert readme.startswith("# NL Flow Diagram Encoder Pipeline v4.37")
    assert "Runtime pipeline version is `4.37`" in release
    assert "Pipeline: 4.37" in manifest


def test_v4_37_release_notes_cover_promoted_fixes():
    release = (ROOT / "docs" / "release_v4_37.md").read_text(encoding="utf-8")
    assert "crossing-aware" in release
    assert "Loop-exit paths are explicitly labelled `No`" in release
    assert "backup `human_review.json`" in release
    assert "Reviewer ID and Reviewer Name" in release
    assert "Baseline resume compatibility" in release
    assert "does not recalibrate an already-current v4.36 baseline" in release
