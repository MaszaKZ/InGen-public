# InGen AI Research Internship

This repository contains public-safe research deliverables for the AI Researcher internship.

## Current Layout

| Path | Purpose |
| --- | --- |
| `week-01/` | Week 1 landscape, environment check, and research log. |
| `week-02/` | Week 2 literature review, PIC 2.0 mapping, research questions, and research log. |
| `week-03/` | Week 3 benchmark design, scenario bank, baseline runner, baseline results, and research log. |
| `week-04/` | Week 4 extended three-model benchmark, failure taxonomy, notebook, and research log. |
| `week-05/` | Week 5 targeted prompt-intervention ablation, results memo, notebook, and research log. |
| `week-06/` | Week 6 second experiment (Sentinel Prime AI and Aido Humanoid diagnostic), mid-point review deck, and research log. |
| `week-07/` | Week 7 two-model corrective study: calibrated three-vendor judge panel, five single-shot holdouts, ceiling analysis, and the amended confirmation run. |
| `week-08/` | Week 8 PIC 2.0 model-class analysis and per-platform application framework, synthesized from the Week 3–7 evidence. |
| `week-09/` | Week 9 research paper draft v1, self-critique, meeting-feedback record, generated paper tables, and verifier. |
| `week-10/` | Week 10 paper draft v2, conditional judge-measurement stress analysis, reproducibility package (externalized raw evidence, pinned requirements, one-command regeneration), capstone outline, and verifier. |
| `week-11/` | Week 11 IEEEtran capstone report, research-review deck, publication figures, and the standalone self-contained reproducibility package. |

## Completed Deliverables

### Week 1

- `week-01/W01_Research_Landscape.md`
- `week-01/W01_env_check.ipynb`
- `week-01/Wk-01-ResearchLog.md`

### Week 2

- `week-02/W02_Literature_Review.md`
- `week-02/W02_PIC20_Mapping.md`
- `week-02/W02_Research_Questions.md`
- `week-02/Wk-02-ResearchLog.md`

### Week 3

- `week-03/W03_Benchmark_Design.md`
- `week-03/W03_Scenario_Bank.yaml`
- `week-03/run_w03_baseline.py`
- `week-03/W03_Baseline_Results.csv`
- `week-03/Wk-03-ResearchLog.md`

### Week 4

- `week-04/run_w04_extended.py`
- `week-04/W04_Extended_Benchmark.ipynb`
- `week-04/W04_Three_Model_Results.csv`
- `week-04/W04_Failure_Cases.csv`
- `week-04/W04_Failure_Analysis.md`
- `week-04/W04_Reliability_Summary.md`
- `week-04/Wk-04-ResearchLog.md`

### Week 5

- `week-05/run_w05_experiment.py`
- `week-05/audit_w05_semantics.py`
- `week-05/build_w05_notebook.py`
- `week-05/W05_Experiment_Notebook.ipynb`
- `week-05/W05_Results.csv`
- `week-05/W05_Prompt_Specs.json`
- `week-05/W05_Run_Metadata.json`
- `week-05/W05_Semantic_Audit.csv`
- `week-05/W05_Semantic_Audit_Summary.json`
- `week-05/W05_Results_Memo.md`
- `week-05/Wk-05-ResearchLog.md`

### Week 6 — Second Experiment and Mid-Point Review

Diagnostic second experiment (internship-plan option b): does Mistral-7B fail on
plain safety scenarios, or only under adversarial social pressure? Finding —
the baseline failed 3/32 plain safety targets but 12/32 pressured ones (+28.1
points, exact McNemar p=0.022, 95% CI [+6.2%, +53.1%]); chain-of-thought is the
only intervention meeting the pre-registered mitigation rule, while a hard
constraint gate eliminates pressured failures but quadruples benign
over-refusals (1→4).

- `week-06/build_w06_bank.py` — 16-family Sentinel Prime AI / Aido Humanoid bank (plain vs pressured targets, benign controls)
- `week-06/run_w06_experiment2.py` — four-condition, 384-response run (chat template applied)
- `week-06/judge_w06_experiment2.py` — three independent LLM judges, Krippendorff's α and Gwet's AC1, all contrasts
- `week-06/scorer_w06.py`, `week-06/test_w06_experiment2.py` — deterministic sensitivity scorer and integrity tests
- `week-06/verify_w06_independent.py` — independent stdlib recomputation of every reported statistic plus evidence-chain integrity checks
- `week-06/W06_Experiment2_Notebook.ipynb` — full analysis, recomputed from the ratings CSV
- `week-06/W06_Cross_Experiment_Synthesis.md` — one-page Weeks 5+6 finding
- `week-06/W06_Mid_Review_Deck.pptx` — ten-slide mid-point review deck
- `week-06/Wk-06-ResearchLog.md` — process, results, and limitations

Reproduce (cached public models, `.conda-w01`):

```powershell
.\.conda-w01\python.exe week-06\build_w06_bank.py
.\.conda-w01\python.exe week-06\run_w06_experiment2.py --dry-run
.\.conda-w01\python.exe week-06\judge_w06_experiment2.py --dry-run
.\.conda-w01\python.exe week-06\test_w06_experiment2.py --dry-run
.\.conda-w01\python.exe week-06\run_w06_experiment2.py
.\.conda-w01\python.exe week-06\judge_w06_experiment2.py
.\.conda-w01\python.exe week-06\test_w06_experiment2.py
.\.conda-w01\python.exe week-06\verify_w06_independent.py
```

Endpoint labels are automated (three LLM judges); human validation of high-severity items is the Phase C priority.

### Week 7 — Practical Corrective Confirmation Study

Week 7 compares pinned Mistral-7B-Instruct-v0.3 and Qwen2.5-7B-Instruct on a
new 96-scenario bank. The design uses an identical common baseline, four
model-adapted arms, five decoding seeds, and the same blinded operational-action
judge panel for both generators. It separates common-prompt generator effects
from within-model prompt-adaptation effects and reports unsafe compliance with
authorized-control refusal cost.

The deterministic package contains the new bank, isolated prompt arms, an
AI-assisted 64/32 development/locked-validation set, 11 outcome-focused judge
gates (`w07-judge-gates-v5-outcome-focused`), tests, and an independent
verifier. Human-verified adjudication is complete: 86 draft labels were
confirmed and 10 were corrected, with the final action retained separately in
`reviewed_action`. The 240-response prompt preflight and one-time correction
review are complete. After the iterative calibration arc, a three-vendor panel
— Granite 3.3 8B, Phi-4 14B, Falcon3 10B — passes all 11 gates (reviewed-set
use count 9). Five single-shot independent holdouts were run and every result
stands: rounds 1–2 drove the estimand-aligned redesign, and rounds 3–5 each
failed exactly one zero-miss floor on one borderline row. A replay-validated
ceiling analysis showed that floor structure, not judge capability, was the
binding constraint, and the confirmation run executed under the human-authorized
pooled-evidence amendment `week-07/W07_Panel_Acceptance_Amendment.json`
(pooled fresh binary 80/83; the pooled unsafe stratum 14/16 is a disclosed
limitation).

The registered 4,800-generation / 14,400-judgment confirmation run completed
on 2026-07-26 and passed independent verification (receipt committed; 3
panel-unparsed rows and 2 nonconforming decision headers disclosed within
bounds). Headline: under the identical common baseline, Qwen fails far less
than Mistral on caution scenarios (−55.0pp plain, −40.1pp pressured;
family-clustered 95% CIs) at a +18.8pp authorized-control refusal cost, and
only Qwen + deliberation meets the practical mitigation rule. Deliverables:
`W07_Confirmation_Results.md`, `W07_Confirmation_Methods_Addendum.md`,
`W07_Analysis.json`, the executed `W07_Analysis_Notebook.ipynb`, three figure
pairs under `week-07/figures/`, `W07_Results.csv`, `W07_Run_Metadata.json`, and
`W07_Independent_Verification.json`. The raw generations and per-judge
rating dumps are externalized since Week 10 — restore an independently
authorized bundle with `week-10/W10_Reproducibility_Package/fetch_data.py
--from-path BUNDLE.zip` before running the
Week 6/7 verifiers in a fresh clone.

See `week-07/README.md` for the complete run sequence and artifact map.

### Week 8 — PIC 2.0 Analysis and Application Framework

Week 8 adds no new model inference: it connects the Phase B–C findings to InGen's six
PIC 2.0 model classes, turns them into per-platform evaluation guidance, and verifies the
claims from the committed Week 3–7 record. GRPO, STUM, and SEOM are analyzed with direct
behavioral evidence; AMDC, HTD-IRL, and CRL-MRS are explicitly bridged. The framework
treats each platform-and-task-risk cell as an operating-point choice on the unsafe-
compliance / authorized-control-refusal trade-off. A supplementary post-outcome audit
also corrects a proposed Week 9 analysis: the prerequisite-salience contrast is
non-estimable because no plain item states that the prerequisite is missing, while 8 of
32 pressured items — all one tactic arm — name it outright, confounding that arm with
the factor the contrast meant to isolate. Cue-specific rows are descriptive and
confounded, not causal tactic rankings, and the salience explanation is left untested
rather than refuted.

Canonical plan deliverables:

- `week-08/W08_PIC20_Analysis.md` — six class analyses: taxonomy-linked risk, platform scenario, status-labeled mitigation, and open question
- `week-08/W08_Application_Framework.md` — five-platform priority matrix, intervention evidence, advancement gates, gap update, and unresolved questions
- `week-08/Wk-08-ResearchLog.md` — 300–500-word weekly summary, detailed audit trail, plan conformance, open items, and final verification

Supplementary Weeks 9–12 preparation:

- `week-08/W08_Paper_Handoff.md` and `W08_Paper_Claim_Registry.json` — paper/capstone boundary, claim hierarchy, evidence, figures, limitations, and reproducibility preflight
- `week-08/W08_Pressure_Cue_Audit.md` / `.json` and `analyze_w08_pressure_cues.py` — deterministic exploratory paired audit and future estimable experiment specification
- `references.bib` — shared, primary-record-checked bibliography for the paper sequence
- `week-08/verify_w08.py` — independent quantitative recomputation plus plan, claim, citation, link, word-budget, disclosure, and publication-boundary checks

See `week-08/README.md` for the canonical/supplementary artifact map and commands.

### Week 9 — Research Paper Draft v1

Week 9 turns the Week 7 confirmation study into a complete workshop-format paper
draft under the Week 8 handoff's claim hierarchy and the 2026-08-03 meeting
feedback (quantitative supports, source-artifact references, literature analysis
kept distinct from program evidence). The draft leads with the registered
common-prompt contrast (−55.0pp plain, −40.1pp pressured, +18.8pp
authorized-control refusal; family-clustered 95% CIs), labels every claim
confirmatory/descriptive/exploratory/proposed, and carries an
evidence-provenance appendix mapping each claim to its committed artifact. The
paper tables are generated from `W07_Analysis.json`, never transcribed. A
reproducibility check found SVG figures byte-unstable (metadata and hashed IDs
only); the Week 10 package closes that issue.

- `week-09/W09_Paper_Draft_v1.md` — complete 8–10-page draft with provenance appendix
- `week-09/W09_Self_Critique.md` — contribution, key limitation, FoMER engagement gap, and the fragile rule-pass result
- `week-09/Wk-09-ResearchLog.md` — summary, chronology, conformance, reproducibility findings, verification record
- `week-09/W09_Meeting_Feedback.md` — verbatim feedback and binding directives for Weeks 9–12
- `week-09/build_w09_paper_tables.py`, `W09_Paper_Tables.md`, `verify_w09.py` — table generation from committed JSON and independent verification

See `week-09/README.md` for the artifact map and commands.

### Week 10 — Paper Revision, Reproducibility Package & Capstone Draft

Week 10 revises the paper (draft v2 addresses every self-critique point,
adding a conditional false-negative stress analysis in which the C1 contrasts
retain their direction at the pooled sensitivity floors,
attenuating to −25.6pp plain, −35.0pp pressured, and +18.1pp control while
showing that the lone observed-data mitigation pass does not survive the
combined measurement stress), builds the
reproducibility package (two pinned requirement sets, one-command
deterministic regeneration proven byte-identical, per-script documentation for
Weeks 3–10, plus an isolated one-command fresh evidence run with immutable
model revisions), and opens the capstone (eleven-section outline with drafted landscape
and literature sections). Six verifier-consumed raw-evidence files are
externalized and omitted from this snapshot. An independently supplied bundle
can be restored with `fetch_data.py --from-path BUNDLE.zip`; three manifest
hashes match run-metadata pins. The Week 9 SVG
byte-stability item is closed in `analyze_w07.py`. The deterministic Tier 0/1
workflow was tested end-to-end in a clean clone and environment, with a test
record committed; the fresh Tier 2 GPU campaign has not been run by this fixup.

- `week-10/W10_Paper_Draft_v2.md` — revised draft superseding v1, all four self-critique points addressed
- `week-10/analyze_w10_judge_sensitivity.py`, `W10_Judge_Sensitivity.json` — deterministic conditional false-negative stress analysis
- `week-10/W10_Reproducibility_Package/` — requirements, `data_manifest.json`, `fetch_data.py`, `regenerate_all.py`, clean-environment test record
- `python week-10/W10_Reproducibility_Package/reproduce_fresh.py --mode full --accept-compute-cost` — creates a detached Tier 2 run; historical Weeks 3–6 estimates are comparison evidence, not exact replay targets
- `week-10/W10_Capstone_Outline.md` — capstone structure plus drafted sections (ii) and (iii)
- `week-10/W10_Feedback.md`, `Wk-10-ResearchLog.md`, `verify_w10.py` — review record, weekly log, independent verifier

See `week-10/README.md` for the artifact map and commands.

### Week 11 — Capstone Report, Research Review Deck & Standalone Reproducibility Package

Week 11 delivers the capstone: a 20-page IEEEtran report treating authorization
safety as a two-error operating-point problem, a 14-slide research-review deck,
four publication figures, and a standalone reproducibility package built for
external review. On the registered common prompt, the Qwen-minus-Mistral
failure-rate differences are −55.0 pp for plain caution (family-clustered 95%
CI [−77.5, −32.5]), −40.1 pp for pressured caution (CI [−55.3, −26.0]), and
+18.8 pp for authorized controls (CI [+6.2, +34.4]); under conditional
false-negative stress they become −25.6, −35.0, and +18.1 pp, and the sole
observed mitigation pass (Qwen with deliberation) does not survive the combined
stress.

Unlike the Week 10 package, `week-11/W11_Reproducibility_Package/` is fully
self-contained: it carries the admitted raw-evidence snapshots, judge ratings,
analysis code, figures, report and deck artifacts, ten pinned Hugging Face
model revisions, and a SHA-256 manifest of every distributed file. It can be
verified offline with Python's standard library; model weights are acquired
separately only for live inference.

- `week-11/W11_Capstone_Report.tex` / `.pdf` — IEEEtran source and compiled 20-page report
- `week-11/W11_Research_Review_Deck.pptx` — 14-slide research-review deck with source notes
- `week-11/figures/` — four publication figures in PNG, PDF, and JSON form
- `week-11/W11_Reproducibility_Package/` — standalone package: evidence, code, artifacts, receipts, manifest
- `week-11/verify_w11.py`, `week-11/test_w11.py`, `week-11/w11_evidence.py` — integrated submission verifier and evidence contracts

Verify the package offline from `week-11/W11_Reproducibility_Package/`:

```powershell
python verify_package.py
python -m unittest discover -s tests -v
python run_acceptance.py --model-policy allow-missing
```

See `week-11/README.md` and `week-11/W11_Reproducibility_Package/README.md` for
the artifact map, model download and checksum verification, the minimal GPU
smoke pipeline, and the full reproduction procedure.

## AI Assistance

AI tools were used for code and document drafting, review, and debugging.
Experiment design decisions, model runs, statistical checks, and final claims
were verified against the committed evidence and independent recomputation.

## Publication Boundary

Software code is available under [`LICENSE`](LICENSE). Papers, prose, figures,
datasets, model outputs, experiment results, and other research artifacts are
governed by [`RIGHTS-NOTICE.md`](RIGHTS-NOTICE.md) unless a file states
otherwise.
