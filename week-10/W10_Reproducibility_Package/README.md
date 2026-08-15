# W10 Reproducibility Package

This package exactly restores and deterministically regenerates the committed analysis record,
including every table and figure in the Week 9/10 paper, from hash-verified raw
artifacts. It also provides an isolated, revision-locked fresh evidence run for
the program's experiments. Historical Weeks 3-6 estimates are not exact replay targets:
the original runs pinned repository IDs but not model revisions, while every new
invocation uses the immutable revisions in `model_lock.json`. The package
contains (a) pinned Python dependencies, (b) data restoration and generation
scripts, (c) experiment scripts documented per script, and (d)
results-regeneration scripts tested in a clean environment, with the test
recorded in [W10_CleanEnv_Test_Transcript.md](W10_CleanEnv_Test_Transcript.md).

## Contents

| File | Purpose |
| --- | --- |
| `README.md` | This document |
| `requirements-analysis.txt` | Pinned CPU-tier dependencies (regeneration + verification) |
| `requirements-inference.txt` | Pinned GPU-tier additions (model inference; tokenizer checks) |
| `data_manifest.json` | SHA-256 manifest of the externalized raw-evidence files and separately supplied bundle |
| `fetch_data.py` | Restores a separately supplied local bundle byte-for-byte; no network fallback |
| `regenerate_all.py` | One-command driver: fetch → regenerate → byte-identity proof → all verifiers |
| `reproduce_fresh.py` | Creates and executes a detached, revision-locked Tier 2 run |
| `prefetch_models.py` | Downloads the locked model snapshots into the run-local model cache |
| `model_lock.json` | Immutable repository IDs and 40-character model revisions for every inference consumer |
| `verify_fresh_run.py` | Verifies fresh counts, provenance, derived artifacts, and completion evidence |
| `W10_CleanEnv_Test_Transcript.md` | Record of the clean-clone, clean-venv end-to-end test |

## Environment

The recorded clean-environment test used Python **3.11.15** on Windows (PowerShell commands
below; POSIX equivalents differ only in path separators and venv activation).
From a clone of the repository:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1          # POSIX: source .venv/bin/activate
pip install -r week-10\W10_Reproducibility_Package\requirements-analysis.txt
# Verification-tier torch (CPU) + the rest of the inference pins:
pip install torch==2.11.0 --index-url https://download.pytorch.org/whl/cpu
pip install transformers==5.12.0 accelerate==1.14.0 bitsandbytes==0.49.2 huggingface_hub==1.19.0 tokenizers==0.22.2 safetensors==0.8.0
```

`bitsandbytes` performs quantized inference only on a CUDA GPU, but it
installs and imports on CPU-only environments, and `run_w05_experiment.py`
records its version even in `--mock` mode — so install
`requirements-inference.txt` in full (with the `cpu` torch index for the
verification tier, or the `cu128` index on a CUDA machine). All documented commands run from the repository root with
the venv's `python` (older week READMEs write `.\.conda-w01\python.exe`,
which is the local vendored interpreter this package replaces).

## Raw evidence: externalized, hash-verified

The plan requires that raw model outputs are not committed. The **six files
the verifiers and test suites actually consume** — the Week 6 raw outputs and
judge ratings, and the Week 7
preflight raw, confirmation raw, judge ratings, and gold ratings — are not
distributed in this repository. A reviewer who independently receives the
registered bundle can restore it from a local path. The bundle stores bare
file names, while the mapping to restore paths lives in the committed
manifest. This repository provides no download location or network fallback.
`data_manifest.json` records each file's SHA-256 and size, plus the bundle
hash. Three of those hashes match pins inside the committed
`week-06/W06_Run_Metadata.json` and `week-07/W07_Run_Metadata.json`, establishing
that those restored files are byte-identical to the registered-run evidence.
The remaining three files are integrity-protected by the manifest.

Tier 2 can regenerate additional raw outputs that no verifier or test consumes;
they are outside this snapshot's artifact inventory.

```powershell
python week-10\W10_Reproducibility_Package\fetch_data.py --from-path BUNDLE.zip
python week-10\W10_Reproducibility_Package\fetch_data.py --check
```

The bundle must be obtained independently and used with `--from-path`; no
automatic download mechanism is provided. The script verifies the registered
bundle size and SHA-256, the exact member set, and every restored member's
size and SHA-256 before writing any evidence file.

## Reproduction tiers

**Tier 0 — restore and verify (CPU, minutes).** Fetch the raw evidence and
run every verifier against the committed artifacts without regenerating
anything:

```powershell
python week-10\W10_Reproducibility_Package\regenerate_all.py --tier 0 --bundle BUNDLE.zip
```

**Tier 1 — regenerate all results (CPU, minutes).** Additionally rerun every
deterministic analysis, table, and figure script whose outputs are included
— `analyze_w07.py`, `analyze_w08_pressure_cues.py`, `build_w09_paper_tables.py`,
`build_w09_paper_figures.py`, `analyze_w10_judge_sensitivity.py` — then prove
the working tree is byte-identical (`git status --porcelain` empty) before
running the verifiers. This regenerates every table (T1, T2a–c) and every
figure (W07 Figures 1–3, W09 Figures 2–3) in the paper:

```powershell
python week-10\W10_Reproducibility_Package\regenerate_all.py --tier 1 --bundle BUNDLE.zip
python week-10\W10_Reproducibility_Package\regenerate_all.py --tier 1 --with-tests --bundle BUNDLE.zip
```

The `verify_w07_independent.py --phase confirmation` step rewrites its
receipt's `verified_utc` timestamp by design; the driver asserts the
timestamp is the only change and restores the committed receipt.
`week-07/analyze_w07_panel_ceiling.py` is not rerun by the driver: its output
is the registered pre-run simulation record, replay-validated at panel
acceptance, and no paper table or figure derives from it.

**Tier 2 — fresh full-inference rerun (GPU, many hours).** This workflow creates
a detached Git worktree and new raw evidence instead of changing the source
checkout or overwriting the committed historical artifacts. A new run can be
compared with the historical record, but historical Weeks 3-6 estimates are not exact replay targets.
Hardware, software, and GPU-kernel differences can also prevent byte-identical
inference even though every model ID and revision is locked.

Inspect the exact 25-stage graph and requirements without creating a directory:

```powershell
python week-10/W10_Reproducibility_Package/reproduce_fresh.py --mode plan
```

Run the complete graph with the required compute acknowledgement:

```powershell
python week-10/W10_Reproducibility_Package/reproduce_fresh.py --mode full --accept-compute-cost --bundle BUNDLE.zip
```

`--batch-size` defaults to 8. In plan and full modes it must be positive and a
positive divisor of 480; the selected value rewrites both Week 7 confirmation commands
so generation and judging use the same batch size. Mock mode also requires a
positive value, but it runs only a one-response Week 7 smoke stage.

The default destination is `.reproduction-runs/<UTC-run-id>`. To choose a safe
external or repository-local destination, pass `--run-dir`; a repository-local
destination must remain below `.reproduction-runs/`:

```powershell
python week-10/W10_Reproducibility_Package/reproduce_fresh.py --mode full --accept-compute-cost --bundle BUNDLE.zip --run-dir .reproduction-runs/my-full-run
```

Full mode restores the fixed Week 7 protocol inputs only from the required
hash-verified local bundle:

```powershell
python week-10/W10_Reproducibility_Package/reproduce_fresh.py --mode full --accept-compute-cost --bundle BUNDLE.zip
```

Full mode requires Python 3.11, at least 80 GiB free at the run location, a
CUDA device, and the CUDA 12.8 PyTorch wheel. The driver creates `.fresh-venv`,
installs the pinned analysis and inference requirements using the `cu128`
index, prefetches all immutable model revisions into the run-local model cache
at `.hf-cache`, and then forces experiment stages offline. Model prefetch needs
network access unless that cache is complete. In full mode, protocol
restoration requires the separately supplied `--bundle PATH`.

Use mock mode to exercise isolated orchestration without claiming inference
completion:

```powershell
python week-10/W10_Reproducibility_Package/reproduce_fresh.py --mode mock --run-dir .reproduction-runs/my-mock-run
```

Mock mode is offline: it neither restores external raw evidence nor uses a
bundle, and its smoke stages do not consume those protocol files.
It retains `clear_generated_evidence` so the detached smoke run still starts
from controlled generated-output state.

Its receipt ends in `mock_only`. A full run begins as `incomplete`. An ordinary
setup or execution failure changes the receipt to `failed`; a rejection or
error in the final fresh verifier instead leaves it `incomplete` with
`verification_pending: true`. Only successful `verify_fresh_run.py` validation
changes the receipt to `complete`. Resume an `incomplete` or `failed` run at
the same source commit and in the same mode:

```powershell
python week-10/W10_Reproducibility_Package/reproduce_fresh.py --mode full --accept-compute-cost --run-dir .reproduction-runs/my-full-run --resume
```

Every mock or full run contains a detached source tree, per-stage output under
`logs/NN-stage-name.log`, and the durable `run-receipt.json`. The `.fresh-venv`
environment and `.hf-cache` model cache are full-run-only directories. A
verified full run also contains `fresh-verification.json`
with checked counts, source commit, model provenance, and artifact hashes. The
fresh verifier expects 144 Week 3 generations, 216 Week 4 generations, 288
Week 5 generations, 384 Week 6 generations, 384 wide Week 6 judge rows
representing 1,152 rating units, 4,800 Week 7 generations, 14,400 Week 7 judge
ratings, and 4,800 Week 7 results. The fixed Week 7 preflight outputs and gold
ratings are restored protocol inputs and are not counted as new evidence.

This implementation and its synthetic tests do not assert that the long-running
GPU campaign has been executed. Only a zero exit from the full command together
with a `complete` receipt constitutes a completed fresh evidence run.

## Per-script reference

Flags listed are the reproduction-relevant ones; every script runs from the
repository root and documents itself in its module docstring.

### Week 3 — baseline benchmark

| Script | Purpose | Inputs | Outputs |
| --- | --- | --- | --- |
| `run_w03_baseline.py` | Two-model baseline over the 36-scenario YAML bank; rubric scoring; three rule-based judge seeds; Krippendorff's α. Flags: `--validate-only`, `--smoke`, `--mock`, `--models`, `--max-new-tokens` | `W03_Scenario_Bank.yaml` | `W03_Baseline_Results.csv`, `W03_Raw_Model_Outputs.jsonl`†, `W03_Reliability_Summary.md` |

### Week 4 — three-model extension

| Script | Purpose | Inputs | Outputs |
| --- | --- | --- | --- |
| `run_w04_extended.py` | Adds Mistral-7B-Instruct-v0.3 over the same bank, preserves W03 rows, builds the failure taxonomy. Flags: `--validate-only`, `--reclassify` (no inference), `--smoke`, `--mock`, `--allow-fallback` | `week-03/W03_Scenario_Bank.yaml`, `week-03/W03_Baseline_Results.csv` | `W04_Three_Model_Results.csv`, `W04_Raw_Model_Outputs.jsonl`†, `W04_Failure_Cases.csv`, `W04_Failure_Analysis.md`, `W04_Reliability_Summary.md`, `W04_Run_Metadata.json` |

### Week 5 — prompt-intervention ablation

| Script | Purpose | Inputs | Outputs |
| --- | --- | --- | --- |
| `run_w05_experiment.py` | Varies only the prompt condition (baseline / CoT / persona / structured) with Mistral, NF4. Flags: `--mock`, `--smoke`, `--conditions`, `--batch-size` | `week-03/W03_Scenario_Bank.yaml`, `week-04/W04_Three_Model_Results.csv` | `W05_Results.csv`, `W05_Raw_Model_Outputs.jsonl`†, `W05_Prompt_Specs.json`, `W05_Run_Metadata.json` |
| `audit_w05_semantics.py` | Post-hoc response-level semantic audit of the lexical scoring (stdlib) | `W05_Results.csv` | `W05_Semantic_Audit.csv`, `W05_Semantic_Audit_Summary.json` |
| `build_w05_notebook.py` | Regenerates the analysis notebook source with nbformat | measured artifacts | `W05_Experiment_Notebook.ipynb` |

### Week 6 — pressure diagnostic (Experiment 2)

| Script | Purpose | Inputs | Outputs |
| --- | --- | --- | --- |
| `build_w06_bank.py` | Builds the 16-family scenario bank (96 main + 12 holdout), design seed 20260714 | — | `W06_Scenario_Bank.json`, `W06_Scenario_Bank.csv` |
| `run_w06_experiment2.py` | 4 conditions × bank = 384 generations, NF4 Mistral. Flags: `--dry-run`, `--smoke`, `--batch-size` | `W06_Scenario_Bank.json` | `W06_Raw_Model_Outputs.jsonl`*, `W06_Results.csv`, `W06_Run_Metadata.json` |
| `judge_w06_experiment2.py` | Three LLM judges, majority endpoint, α/AC1 agreement. Flags: `--dry-run`, `--smoke` | `W06_Results.csv`, raw JSONL* | `W06_Judge_Ratings.csv`*, `W06_Analysis.json` |
| `scorer_w06.py` | Deterministic sensitivity scorer (importable module) | — | — |
| `test_w06_experiment2.py` | Design + evidence-chain integrity and statistical tests. Flag: `--dry-run` | committed artifacts | pass/fail |
| `verify_w06_independent.py` | Recomputes every reported W06 statistic from the ratings CSV*, prints the judge-ablation table | `W06_Judge_Ratings.csv`*, `W06_Analysis.json` | exit code |

### Week 7 — registered confirmation study (the paper's evidence base)

| Script | Purpose | Inputs | Outputs |
| --- | --- | --- | --- |
| `w07_common.py` | Config hub: models + judges with pinned revisions, seeds, decoding parameters, artifact paths, hashed IO | — | module |
| `w07_prompts.py` | Locked prompt method `w07-corrective-v4-locked` | — | module |
| `w07_judge_measurement.py` | Two-axis body-only judge measurement with evidence grounding and parse repair | — | module |
| `build_w07_confirmation_bank.py` | Builds the balanced 96-scenario confirmation bank with control challenges | preflight bank, week-06 sources | `W07_Confirmation_Bank.json` |
| `run_w07_replication.py` | Generation: 2 models × 5 conditions × 96 scenarios × 5 seeds = 4,800. Flags: `--phase {smoke,preflight,confirmation}`, `--batch-size`. Refuses rerun while raw outputs exist | `W07_Confirmation_Bank.json` | `W07_Raw_Model_Outputs.jsonl`*, `W07_Run_Metadata.json` |
| `audit_w07_preflight.py` | Audits the one-seed preflight without applying corrections | preflight raw* | `W07_Preflight_Corrections.json` |
| `build_w07_gold.py` | Builds the 64/32 development/validation gold set | raw JSONLs* | `W07_Judge_Gold_Set.csv` |
| `build_w07_holdout.py` | Builds fresh single-shot holdout sets, disjoint by response hash | gold set, raw pools*† | `W07_Judge_Holdout_*_Set.csv` |
| `generate_w07_holdout_pool.py` | Targeted fresh-seed generation for scarce strata | bank | holdout-diagnostic raw† |
| `judge_w07_holdout.py` | Single-shot holdout evaluation with registered count-slack | holdout sets | `W07_Holdout_v4/v5_Ratings.csv`, reports |
| `judge_w07_replication.py` | Calibration + confirmation judging, 11 gates, panel majority. Flags: `--phase {gold,confirmation}`, `--batch-size` | bank, raw*, gold set | `W07_Judge_Ratings.csv`*, `W07_Results.csv`, calibration JSON |
| `analyze_w07.py` | Statistics + figures: family-clustered bootstrap (10k, seed 20260806), rates, contrasts, mitigation rule | `W07_Results.csv`, `W07_Judge_Ratings.csv`*, run metadata | `W07_Analysis.json`, `figures/W07_Figure1–3.{png,svg}` |
| `analyze_w07_panel_ceiling.py` | Registered posterior-predictive ceiling simulation through production gate code | holdout reports, calibration | `W07_Panel_Ceiling_Analysis*.json` |
| `build_w07_notebook.py` | Regenerates the analysis notebook source | — | `W07_Analysis_Notebook.ipynb` |
| `write_w07_report.py` | Writes the confirmation report documents (never overwrites narrative docs) | analysis + calibration + metadata | `W07_Confirmation_Results.md`, methods addendum |
| `test_w07_replication.py` | 55-test deterministic suite: `python -m unittest week-07.test_w07_replication` | modules + artifacts | pass/fail |
| `verify_w07_independent.py` | Independent verifier. `--phase precalibration`: bank/prompt/gold/calibration integrity + tokenizer budgets (needs `transformers`). `--phase confirmation`: recomputes the confirmation analysis, validates figures and notebook, writes the receipt | all W07 artifacts* | receipt JSON |

### Week 8 — synthesis (no inference)

| Script | Purpose | Inputs | Outputs |
| --- | --- | --- | --- |
| `analyze_w08_pressure_cues.py` | Deterministic post-outcome paired cue audit (stdlib, fixed bootstrap seed) | `week-07/W07_Confirmation_Bank.json`, `week-07/W07_Results.csv` | `W08_Pressure_Cue_Audit.json`, `.md` |
| `verify_w08.py` | Recomputes the audit and checks the Week 8 document package end-to-end | W08 docs, W07 artifacts, `references.bib` | pass/fail |

### Week 9 — paper generation

| Script | Purpose | Inputs | Outputs |
| --- | --- | --- | --- |
| `build_w09_paper_tables.py` | Emits the exact Markdown rows for tables T1/T2a/T2b/T2c embedded in the draft | `week-07/W07_Analysis.json`, `week-07/W07_Run_Metadata.json` | `W09_Paper_Tables.md` |
| `build_w09_paper_figures.py` | Publication variants of Figures 2–3 for the IEEE manuscript (byte-stable SVG) | `week-07/W07_Analysis.json` | `week-09/figures/W09_Figure2–3.{png,svg}` |
| `verify_w09.py` | 11-section verifier of the Week 9 draft against committed artifacts | W06/W07/W08 artifacts, draft, bib | pass/fail |

### Week 10 — revision, sensitivity, package

| Script | Purpose | Inputs | Outputs |
| --- | --- | --- | --- |
| `analyze_w10_judge_sensitivity.py` | Conditional false-negative stress analysis for C1 and the observed-data mitigation-rule pass (deterministic) | amendment, analysis JSON, `W07_Results.csv` | `W10_Judge_Sensitivity.json` |
| `verify_w10.py` | 11-section verifier of the Week 10 deliverables, including this package's integrity | week-10 docs + all upstream artifacts | pass/fail |
| `W10_Reproducibility_Package/fetch_data.py` | Restores the six externalized raw-evidence files, hash-verified | `data_manifest.json`, local bundle | six files* |
| `W10_Reproducibility_Package/regenerate_all.py` | One-command fetch → regenerate → byte-identity proof → verifiers | everything above | exit code |

`*` = separately supplied raw evidence: restored by `fetch_data.py`, never committed. `†` = neither committed nor distributed: Tier 2 rerun only.

## Fetch-first consumers

These need the supplied files on disk (run `fetch_data.py --from-path
BUNDLE.zip` first in a fresh
clone): `verify_w06_independent.py`, `test_w06_experiment2.py` (full mode),
`judge_w06_experiment2.py`, `verify_w07_independent.py` (both phases),
`test_w07_replication.py`, `analyze_w07.py`, `analyze_w07_panel_ceiling.py`,
`build_w07_gold.py`, and notebook re-execution. Fetch-independent:
`verify_w08.py`, `build_w09_paper_tables.py`, `build_w09_paper_figures.py`,
`analyze_w10_judge_sensitivity.py`. Scripts that consume the undistributed
holdout-diagnostic pool (`build_w07_holdout.py`,
`generate_w07_holdout_pool.py`) require a Tier 2 regeneration.

## Out of scope

The former tracked `week-06-explorations/` tree and root `week-06.7z`
snapshot are superseded Week 6 working material, not canonical deliverables.
Their tracked copies are not part of this public snapshot. The tree is not
part of this package's regeneration graph and its internal verifiers are not
run by the driver.

## Public snapshot boundary

This repository distributes the reviewed research snapshot but not the raw
evidence bundle. The bundle has no repository-hosted download location and is
accepted only from an independently supplied local path. See the root
`LICENSE` for code and `RIGHTS-NOTICE.md` for research-artifact terms.
