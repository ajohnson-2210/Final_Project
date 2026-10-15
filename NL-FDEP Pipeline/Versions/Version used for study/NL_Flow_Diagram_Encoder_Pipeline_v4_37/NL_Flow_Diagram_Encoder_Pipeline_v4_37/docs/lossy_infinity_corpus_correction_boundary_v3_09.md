# Corpus transcription boundary — lossy negative-infinity text

v3.09 records a research-corpus correction, not a language recovery.

## Permitted explicit source forms

Existing production behaviour continues to accept explicit negative-infinity representations already covered by the pipeline, including `-infinity`, `NEGATIVE_INFINITY`, and the previously evidenced infinity glyph route.

## Not a language token

```text
-?
```

is not an AJ token and is not introduced as an alias for negative infinity. Outside a separately evidenced corpus-transcription correction, it remains invalid/underspecified source.

## v3.09 scope

The source_f Algorithm 15 TXT occurrence was corrected in the research corpus because the user confirmed the DOCX-to-TXT conversion had corrupted the intended negative-infinity representation. No normaliser, parser, compiler, adapter, or dialect rule is broadened by this release.
