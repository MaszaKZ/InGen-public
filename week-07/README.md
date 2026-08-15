# Week 7: corrective confirmation study (amended panel acceptance)

Week 7 compares pinned Mistral-7B-Instruct-v0.3 and Qwen2.5-7B-Instruct on a 96-scenario bank with five prompt arms, judged by one common operational-action panel. The bank anchors 48 scenarios (8 families) to Sentinel Prime AI security decisions and 48 to Aido Humanoid care decisions; findings and testing priorities are stated per platform in `W07_Research_Note.md`. The panel is **Granite 3.3 8B, Phi-4 14B, Falcon3 10B** (`granite8b`, `phi4_14b`, `falcon3_10b`), selected after an Attempt-2 upgrade of both non-Granite seats; all three pass the 11 outcome-focused gates (`w07-judge-gates-v5-outcome-focused`) on the reviewed set at use count 9, with first-exposure validation accuracy 1.000 for both new seats.

Five single-shot independent holdouts were run and every result stands as recorded: rounds 1-2 failed broadly and drove the estimand-aligned redesign; rounds 3-5 each failed **exactly one** gate on one borderline row (parse 27/28; unsafe 4/5; unsafe 3/4), with a different judge subset missing the row each time. A pre-registered ceiling analysis (`analyze_w07_panel_ceiling.py`) showed the single-shot design's zero-miss floors certify even a strong panel with probability well below one, and round 5 ran under a pre-registered count-slack design (`W07_Holdout_v5_Design_Registration.json`) that still left the critical detectors at 100%. The confirmation run proceeds under the human-authorized pooled-evidence amendment `W07_Panel_Acceptance_Amendment.json` (pooled fresh binary 80/83, CP95 [0.898, 0.993]; pooled unsafe 14/16 disclosed as the weak stratum); the holdout-failure records are unchanged.

## Key artifacts

Measurement and pipeline:

- `w07_common.py`: shared config - generators, judge specs and revisions, versions, paths, deterministic guards.
- `w07_prompts.py`: locked `w07-corrective-v4-locked` prompt method (shared core, model adapters, arm deltas).
- `w07_judge_measurement.py`: body-only two-axis JSON measurement (`w07-action-judge-v20-evidence-grounded-parse-repair`), evidence grounding, labeled-operative precedence, deterministic estimand-aligned resolution.
- `judge_w07_replication.py`: calibration and confirmation judging, 11 outcome-focused gates, predicate-majority aggregation, the amendment-aware holdout gate, checkpointed resume.
- `run_w07_replication.py`: smoke/preflight/confirmation generation with single-run, batch-alignment, and blank-retry deviation guards.
- `build_w07_holdout.py`, `generate_w07_holdout_pool.py`, `judge_w07_holdout.py`: fresh-holdout construction (disjoint by response hash and scenario ID from all spent sets) and the single-shot composition-adaptive evaluator with the registered round-5 count-slack.
- `analyze_w07_panel_ceiling.py`: the pre-Attempt-2 design ceiling analysis (replay-validated posterior-predictive simulation through the production gate code).
- `analyze_w07.py`, `build_w07_notebook.py`, `write_w07_report.py`, `verify_w07_independent.py`, `test_w07_replication.py`: analysis, executed notebook, confirmation report (new files; never overwrites the narrative docs), independent verification (writes a receipt for the confirmation phase), and the 55-test deterministic suite.

Data and records:

- `W07_Confirmation_Bank.json` (96 scenarios, 16 families), `W07_Preflight_Bank.json`, `W07_Preflight_Run_Metadata.json`, `W07_Preflight_Corrections.json`, `W07_Prompt_Lock_Validation.json`, and `W07_Prompt_Message_Comparison.json`.
- `W07_Judge_Gold_Set.csv` (64 development / 32 locked validation, all externally reviewed).
- `W07_Judge_Calibration.json`: gate metrics for every candidate, `selected_panel`, reviewed-set use count 9, full iteration history v7-v20+Attempt-2.
- `W07_Judge_Holdout_{,v2,v3,v4,v5}_Set.csv`: the five adjudicated single-shot holdout sets; `W07_Holdout_v4/v5_Ratings.csv` and matching report JSON files.
- `W07_Holdout_v5_Design_Registration.json`, `W07_Panel_Ceiling_Analysis{,_PostRecal}.json`, `W07_Panel_Acceptance_Amendment.json`: the registered round-5 design, the ceiling analyses it rests on, and the human-authorized acceptance amendment.
- Narrative and research deliverables: `W07_Research_Note.md` (the 4-page structured research note — the week's primary deliverable), `W07_Self_Critique.md` (peer-review preparation), `W07_Methods_and_Run.md`, `Wk-07-ResearchLog.md`, `W07_Precalibration_Audit.md`, `W07_Replication_Protocol.md`.

The included confirmation record comprises `W07_Run_Metadata.json`, `W07_Results.csv` (4,800), `W07_Analysis.json`, the executed `W07_Analysis_Notebook.ipynb`, three figure pairs under `figures/`, `W07_Confirmation_Results.md`, `W07_Confirmation_Methods_Addendum.md`, and the `W07_Independent_Verification.json` receipt (both verifier phases PASS; 3 panel-unparsed rows and 2 nonconforming headers disclosed within bounds). Inputs required only for full evidence verification are documented by the Week 10 reproduction package rather than presented as included Week 7 artifacts.

## Checkpoint sequence

Run commands from the repository root with `.conda-w01`.

1. Deterministic validation (any time):

   ```powershell
   .\.conda-w01\python.exe -m unittest week-07.test_w07_replication
   .\.conda-w01\python.exe week-07\verify_w07_independent.py --phase precalibration
   ```

2. Completed: gold review (96/96), registered preflight + one-time prompt lock, iterative calibration through v20, Attempt-2 dev screens (`--phase gold --development-only --judges phi4_14b` / `falcon3_10b`), and the use-9 recalibration (`--phase gold`).

3. Completed: five single-shot holdouts (`build_w07_holdout.py` + `judge_w07_holdout.py` per round, external adjudication between build and eval). Every result stands; round 5 ran under the pre-registered count-slack design and failed only unsafe-compliance detection 3/4.

4. Completed: ceiling analysis (`analyze_w07_panel_ceiling.py --draws 20000 --bootstrap 10000`, plus `--update-from-gold phi4_14b` post-recalibration) and the acceptance amendment.

5. Confirmation (single registered run; generation refuses to rerun if `W07_Raw_Model_Outputs.jsonl` exists, judging validates the amendment):

   ```powershell
   .\.conda-w01\python.exe week-07\run_w07_replication.py --phase confirmation --batch-size 8
   .\.conda-w01\python.exe week-07\judge_w07_replication.py --phase confirmation
   .\.conda-w01\python.exe week-07\analyze_w07.py
   .\.conda-w01\python.exe week-07\build_w07_notebook.py
   .\.conda-w01\python.exe -m jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=900 week-07\W07_Analysis_Notebook.ipynb
   .\.conda-w01\python.exe week-07\write_w07_report.py
   .\.conda-w01\python.exe week-07\verify_w07_independent.py --phase confirmation
   ```

## Registered confirmation workflow

The confirmation run uses seeds `20260801-20260805`, temperature `0.2`, top-p `0.9`, `top_k=0`, a 256-token maximum, and NF4/double-quantized/float16-compute loading for both generators: exactly 4,800 generations and 14,400 judgments. Generation is resumable by `(generator_model, condition, scenario_id, seed)` with a pinned batch size; judging is resumable by response and judge with 25-batch checkpoint cadence.

The primary cross-model endpoint is the identical common baseline. Model-adapted minus common effects are reported within each generator, and interventions are compared with that generator's adapted baseline. Adapted Mistral-Qwen differences are descriptive pipeline comparisons. Panel parse failures and decision-header nonconformance are disclosed deviations with hard bounds (1% and 2%), never silent exclusions; judge-panel uncertainty - especially the pooled 14/16 unsafe boundary stratum - is a disclosed limitation of every confirmation result.
