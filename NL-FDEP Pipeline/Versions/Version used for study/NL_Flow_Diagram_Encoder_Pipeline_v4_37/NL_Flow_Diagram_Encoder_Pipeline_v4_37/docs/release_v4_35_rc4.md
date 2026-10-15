# NL-FDEP v4.35 Release Candidate 4

v4.35 RC4 retains Common Tests v1.3 / test-spec schema v1.4 and the model-neutral, static semantic evaluation introduced in the v4.35 candidate. RC4 changes only the interactive runner workflow and its regression coverage.

## First LLM-run baseline decision

The baseline remains a **procedural study-readiness prerequisite only**. On the first `LLM_RESULTS_FOLDER` operation in a runner process:

1. The runner checks whether a previously selected baseline path is recorded.
2. If a previous baseline is detected and still structurally valid, the runner explicitly offers:
   - **Use detected baseline**;
   - **Choose baseline folder and recalibrate**;
   - **Quit**.
3. Choosing **Use detected baseline** revalidates the benchmark against the current v4.35/Common Tests v1.3 build. If its calibration is stale or incomplete, the existing calibration prompt is shown and the LLM operation remains blocked until readiness is achieved.
4. Choosing **Choose baseline folder and recalibrate** opens the baseline-folder chooser and deliberately performs a fresh baseline calibration, even if the selected folder already contains a current calibration.
5. If no previous baseline is detected, the runner goes directly to the baseline-folder chooser. The selected benchmark is validated and calibrated when required.
6. The LLM dataset chooser opens only after the session baseline satisfies 50/50 current terminal calibration runs, 50/50 behaviourally evaluated calibrations, and 50/50 calibration scores at 100%.

The successfully established baseline is retained in memory for the remainder of that runner process. Subsequent LLM batches in the same session do not repeat the baseline choice unless readiness is lost.

## Post-LLM workflow

After each completed LLM-results batch the runner offers exactly:

- **Choose another LLM results folder**;
- **Proceed with human evaluation**;
- **Quit**.

Choosing another LLM results folder reuses the already established in-session readiness gate. Choosing human evaluation opens the review workflow for the current LLM dataset and returns to the same post-batch choice when the review session closes.

## Academic-integrity separation

The established baseline path is retained by the interactive runner only for readiness verification and to prevent accidentally selecting the benchmark itself as an experimental dataset. It is not accepted by `run_llm_results_folder()` and is not forwarded into experimental semantic scoring.

Experimental scoring continues to use only the static frozen Common Tests v1.3 fixtures and expected semantic values. No baseline Python, reference implementation, or executable oracle is used to generate an expected result from an LLM input at runtime.

## RC4 regression coverage

RC4 adds tests proving that:

- a detected ready baseline requires an explicit reuse choice and is not silently activated;
- the user can replace a detected baseline and force a fresh calibration;
- absence of a detected baseline directs the user to the baseline-folder chooser;
- a second LLM dataset in the same runner process reuses the established session gate without repeating baseline selection;
- fewer than 50/50 100% calibration outcomes still blocks the LLM operation;
- the baseline path is not forwarded into the experimental scorer;
- static frozen expectations, algorithm-agnostic semantic observation, and model-neutral release integrity remain unchanged.

This build remains a release candidate for cross-dataset stress testing and is not the final study freeze.
