# Week 7 confirmation methods and run record (addendum)

This addendum records the executed confirmation run; the full campaign
narrative (calibration arc, five single-shot holdouts, ceiling analysis, and
the acceptance amendment) remains in `W07_Methods_and_Run.md`.

## Executed design

- Generators: `mistralai/Mistral-7B-Instruct-v0.3` at `c170c708c41dac9275d15a8fff4eca08d52bab71` and `Qwen/Qwen2.5-7B-Instruct` at `a09a35458c702b33eeacc393d103063234e8bc28`.
- Bank: 96 scenarios in 16 complete families.
- Conditions: common baseline, adapted baseline, deliberation, structured output, and constraint gated.
- Seeds: `20260801, 20260802, 20260803, 20260804, 20260805`.
- Decoding: temperature `0.2`, top-p `0.9`, top-k `0`, maximum `256` new tokens.
- Loading: NF4, double quantization, float16 compute on `NVIDIA GeForce RTX 3080 Ti Laptop GPU` for both generators.
- Rows: `4800` generations and `14400` judgments.

## Preflight and prompts

The 24-scenario preflight used seed `20260731`. It recorded `6` explicitly reviewed corrections, never more than one per registered model-condition. Prompt method `w07-corrective-v4-locked` was methodologically locked before confirmation. No separate freeze manifest was created.

## Judging

The common panel was `granite8b, phi4_14b, falcon3_10b`. Candidates were evaluated in the fixed order recorded in calibration metadata; the reviewed set's reuse count and every between-round instrument change are disclosed in the calibration iteration record and the campaign narrative.

Judges extracted body-only evidence predicates; the study estimand is the binary executes-now outcome (PROCEED_NOW versus WITHHOLD, with AMBIGUOUS reserved for a header/body execution conflict), and the exact four-class action survives only as an ungated diagnostic. Code separately applied the deterministic action-to-outcome rule. All simple gate proportions include exact binomial intervals.

Header-contract measurement rule: the independent verifier prefix-matches the decision header, while the judge instrument requires an exact single-line declaration (fullmatch); responses that fold the declaration into a longer first line are measured body-only with no header by design. This is a registered measurement rule, not a data defect.

## Analysis

Observations were paired by scenario and seed. Intervals used 10,000 complete-family bootstrap draws. The common baseline is the primary cross-model endpoint; adaptation and interventions are within-model. Scenario-majority sensitivity uses at least three failures among five samples.

## Commands

- `.conda-w01/python.exe week-07/run_w07_replication.py --phase confirmation --batch-size 8`
- `.conda-w01/python.exe week-07/judge_w07_replication.py --phase confirmation`
- `.conda-w01/python.exe week-07/analyze_w07.py`
- `.conda-w01/python.exe week-07/build_w07_notebook.py`
- `.conda-w01/python.exe -m jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=900 week-07/W07_Analysis_Notebook.ipynb`
- `.conda-w01/python.exe week-07/write_w07_report.py`
- `.conda-w01/python.exe week-07/verify_w07_independent.py --phase confirmation`
- `.conda-w01/python.exe week-07/test_w07_replication.py`

## QA and disclosure

The executed notebook and three PNG/SVG figure pairs passed independent integrity checks and visual inspection. Figure labels are above neutral uncertainty bars with consistent scales.

The study is synthetic, two-model, quantized, and pipeline-level. Gold labels are AI-assisted and human-verified. Detailed provenance graphs and duplicate artifact trees are outside this weekly scope.
