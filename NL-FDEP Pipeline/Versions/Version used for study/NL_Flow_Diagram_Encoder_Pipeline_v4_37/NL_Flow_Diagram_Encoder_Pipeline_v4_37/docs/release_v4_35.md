# NL-FDEP v4.35 release

This build is the neutral v4.35 release (no RC or FINAL suffix). It retains the transformation, baseline-readiness, Semantic Boundary Variance, rubric and dashboard methodology from RC14. Common Tests v1.4.2 is the active pack and differs from RC14's v1.4.1 pack only by the Algorithm 1 semantic-contract wording correction described below. The release Human Review workflow remains authoritative and now includes the questionnaire-efficiency change described below.

## Authoritative HTML Human Review

The Tk Human Review window is now a launcher/status manager rather than a second copy of the questionnaire. It provides:

- AI-agent dataset selection across the current/discovered study;
- algorithms in numeric order;
- study-wide Reviewer ID lookup and automatic next ID generation (`REV001`, `REV002`, ...);
- Reviewer Name associated with the Reviewer ID and retained throughout the live review session;
- Pending / In progress / Complete status and review ownership;
- Add LLM dataset and Refresh Review Status controls;
- baseline exclusion.

`human_review_questionnaire.html` is the single authoritative evaluation interface. When opened from NL-FDEP, it is served through a local-only `127.0.0.1` review service. Reviewer ID and Reviewer Name are pre-populated, existing answers are restored for the same reviewer, and Save writes directly to the algorithm's `pipeline_artifacts/scoring/human_review.json` before re-running adjudication.

## Review ownership protection

A review cannot be overwritten by another reviewer. Save is blocked when:

- an existing `human_review.json` belongs to a different Reviewer ID; or
- the same Reviewer ID is already associated with a different non-empty Reviewer Name.

The same Reviewer ID/name pair may resume and update its own review. Existing legacy reviews that have an ID but no name may acquire a name when resumed by the same ID. This is an accidental-overwrite safeguard, not user authentication.

## Preserved v4.35 study controls

- Baseline algorithms do not require Human Review.
- Baseline processing must succeed for 50/50 algorithms; every behaviourally evaluable calibration must be 100%.
- A genuine `BEHAVIOURAL_NOT_EVALUATED` case remains separate from pipeline readiness.
- Baseline activation remains session-scoped and is never silently restored across ordinary restarts.
- Common Tests v1.4.2 remains the active pack: 156 declared cases (129 core, 8 pre-freeze validation, 19 semantic-boundary probes).
- Semantic Boundary Variance remains a separate descriptive measure and does not alter core behavioural or rubric scoring.
- Automated and human rubric streams remain separate; a Combined Rubric Score is produced only after all 16 human criteria are explicitly complete/evaluable under the established rules.
- Automatic dependency verification/installation, automatic dashboards and cross-session Human Review study discovery are retained.

## Validation

Release validation includes the complete pytest and unittest suites, local Human Review HTTP save/resume/ownership tests, HTML JavaScript syntax validation, Common Test provenance comparison, checksum verification and ZIP integrity validation.

## Questionnaire efficiency and Common Test wording correction

- Stage-criterion Reviewer justification now defaults to a preset selector. “Other — add specific comment” reveals a free-text box. The selected/custom text continues to save in the existing `reviewer_justification` field, so saved review schema compatibility is preserved.
- Existing free-text reviews reopen as `Other` with their previous comment restored.
- Common Tests v1.4.2 is the active pack. It is functionally identical to v1.4.1 except for the Algorithm 1 semantic-contract wording correction: `True if both strings contain the same multiset of characters.` Historical v1.4.1 remains retained unchanged for provenance.
