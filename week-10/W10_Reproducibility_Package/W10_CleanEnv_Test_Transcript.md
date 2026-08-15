# W10 Clean-Environment Test Record

Record of the reproducibility package's end-to-end test on a clean clone and
clean Python environment (plan self-check: "tested, not just claimed"),
2026-08-11. This document contains selected console output and contemporaneous
summaries; it is not a complete raw terminal transcript. The test ran in three rounds;
the first two surfaced reproducibility defects that were fixed before the
definitive third round.

## Environment record

- Clone: a clean repository snapshot copied into a scratch directory. Each
  correction round used a fresh snapshot containing the preceding fixes.
- Interpreter: fresh `python -m venv` → **Python 3.11.15** (no conda, no
  site-packages inheritance).
- Installs (all exit 0, exact pins): `requirements-analysis.txt`;
  `torch==2.11.0` from the `cpu` wheel index (`torch 2.11.0+cpu`);
  `transformers==5.12.0`, `accelerate==1.14.0`, `huggingface_hub==1.19.0`,
  `tokenizers==0.22.2`, `safetensors==0.8.0`; `bitsandbytes==0.49.2`
  (added after the round 1 finding below — it installs and imports on a
  CPU-only environment).
- Data: `fetch_data.py --from-path` read a separately supplied local bundle,
  verified the bundle hash, and restored all six files:
  `PASS: all 6 raw-evidence files verified against the manifest`.

## Round 1 — three findings, all fixed

The driver (`regenerate_all.py --tier 1`) restored and regenerated
successfully but **failed the byte-identity check**: `W09_Paper_Tables.md`
was flagged modified in the fresh checkout. Diagnosis: content was
byte-identical; the generator writes LF (`newline="\n"`) while
`core.autocrlf` smudges the fresh checkout to CRLF, leaving a
renormalization-pending state. Fix: `.gitattributes` now pins
`week-09/W09_Paper_Tables.md eol=lf`.

The inference smoke pass surfaced two more:

1. `run_w05_experiment.py --mock --smoke` completed all 24 mock generations
   but crashed writing run metadata: `PackageNotFoundError: bitsandbytes`
   (the script records that package's version even in mock mode). Fix:
   `bitsandbytes` joined the CPU verification-tier install — confirmed to
   install and import without a GPU.
2. `run_w06_experiment2.py --dry-run` loads the real NF4-quantized model on
   the holdout families — the dry-run gate is **GPU-tier**, not a CPU mock;
   the CPU mock path is `--smoke`. Additionally, `build_w06_bank.py`
   regenerates the bank content-identically **except its `created_utc`
   timestamp** (single-line diff), so the committed, hash-pinned bank is
   never rebuilt in place. Both reclassifications are documented in the
   package README; the disposable clone's rewritten files
   were restored from the index.

## Round 2 — one finding, fixed

Byte-identity now held (`OK: working tree byte-identical after
regeneration`), both test suites passed, and every corrected smoke path
exited 0: `run_w03_baseline.py --validate-only` (36 scenarios),
`run_w04_extended.py --validate-only`, `run_w05_experiment.py --mock
--smoke` (isolated output directory), `run_w06_experiment2.py --smoke`,
`judge_w06_experiment2.py --smoke`, `test_w06_experiment2.py --dry-run`.

`verify_w07_independent.py --phase precalibration` then failed its Week 6
immutability guard: the guard diffs `week-06/` against its registered
checkpoint commit, and the Week 10 externalization's index **deletions** of
`W06_Judge_Ratings.csv` and `W06_Raw_Model_Outputs.jsonl` tripped it even
though the restored bytes are hash-identical. The corrected guard accepts a
deletion of a manifest-listed file if and only if the
restored on-disk bytes hash-match the committed Week 10 data manifest; any
modification or unverified deletion still fails.

## Round 3 — definitive run

`regenerate_all.py --tier 1 --with-tests`, selected key lines:

```
PASS: all 6 raw-evidence files verified against the manifest
OK: working tree byte-identical after regeneration
W06 Experiment 2 integrity tests passed.
Ran 55 tests in 6.601s
ALL CHECKS PASSED
PASS: Week 8 verification complete
PASS: Week 9 verification complete
```

In detail: fetch check passed; Tier 1 regenerated `W07_Analysis.json`, all
Week 7 and Week 9 figures, the Week 8 audit, the paper tables, and the
judge-sensitivity JSON with the tracked tree **byte-identical**;
`test_w06_experiment2.py` and the 55-test `test_w07_replication` suite
passed; `verify_w06_independent.py` recomputed every Week 6 statistic from
the restored ratings (`ALL CHECKS PASSED`); `verify_w07_independent.py`
passed **both** phases (precalibration with the maintained guard reporting
the two externalized files as hash-verified; confirmation recomputing the
full analysis); `verify_w08.py` and `verify_w09.py` passed every section.
`verify_w10.py` failed **only** its three test-record checks — two references
to this document plus an existence check — which could not pass before this
document was written; every other section (v2 tables, abstract, all recomputed prose
values, the stress analysis recomputed end-to-end, FoMER engagement,
structure, package integrity, capstone outline) passed in the clean
environment. The only tracked-file modification at the end was the
documented `verified_utc` timestamp rewrite of the verification receipt.

Skipped by design (GPU-tier, documented in the package README): the Week 6
dry-run gate and any real quantized inference; the full Week 7 rerun
(4,800 generations / 14,400 judgments) remains the guarded Tier 2 path.

## Final confirmation

After this record was committed, `verify_w10.py` ran successfully end-to-end
— `PASS: Week 10 verification complete` — locally and in a fresh re-clone
at the final commit executing the same driver command (appendix below).

## Appendix — definitive re-clone run

Recorded after the test-record commit: a fresh clone at the final Week 10
commit, reusing the round 1–3 venv, ran
`regenerate_all.py --tier 1 --with-tests` to completion with every step
green, ending in `PASS: tier 1 regeneration and verification complete`.
