# Wk-10 Research Log — Paper Revision, Reproducibility Package & Capstone Draft

Period: 2026-08-11 · Deliverables committed on master; this log follows the
[Week 10 review note](W10_Feedback.md) and the plan's Phase D specification.

## Weekly summary

I read the panel-acceptance amendment again as a measurement document rather
than a compliance record, and reread FoMER (arXiv:2509.15293) against our
bank to write an engagement that answers the self-critique's two reviewer
questions instead of acknowledging the paper in passing. I also reread the
plan's reproducibility bullet — "no raw model outputs committed" — against
the repository it described, which committed 46 MB of them.

I built four things. First, a deterministic judge-measurement stress analysis
([`analyze_w10_judge_sensitivity.py`](analyze_w10_judge_sensitivity.py) →
[`W10_Judge_Sensitivity.json`](W10_Judge_Sensitivity.json)): conditional on
false-negative-only detection at the pooled CP95 sensitivity floors, the
plain, pressured, and control contrasts move to −25.6pp, −35.0pp, and
+18.1pp, respectively, without changing sign. The same stress test overturns
the robustness of the only observed-data mitigation pass: its control cost
can rise to +8.1pp, beyond the registered +3.125pp ceiling. Second, the
reproducibility package: two pinned requirement sets, six verifier-consumed
raw-evidence files externalized behind a hash-verified local-bundle contract, and a
one-command driver that regenerates every table and figure and proves the tree
byte-identical. Third,
[`W10_Paper_Draft_v2.md`](W10_Paper_Draft_v2.md), addressing every
self-critique point. Fourth, the capstone outline with drafted landscape and
literature sections. A new eleven-section verifier
([`verify_w10.py`](verify_w10.py)) recomputes all of it from committed
artifacts.

The week's sharpest finding is quantitative honesty about the fragile rule
pass. The 0/160 deliberation cell can hide up to 3 failures in the conditional
false-negative stress, placing its relative reduction exactly at the
registered 25% minimum; independently stressing the control side raises its
cost beyond the ceiling. The configuration therefore remains a registered
observed-data pass but not a measurement-robust mitigation. That distinction
does what the word "fragile" could not.

What I questioned most was the boundary of evidence custody: which raw files
are actually load-bearing for verification, what a release may reveal about
external inputs (only the registered identifiers, sizes, and hashes), and
whether externalizing data weakens the
audit chain (it does not: three manifest hashes equal the run-metadata pins,
and all six files are hash-verified on restoration). The reproducibility
package turned out to be less about packaging than about deciding, file by
file, what the evidence actually is.

## Process decisions (recorded)

- 2026-08-11 (owner direction): externalize raw model outputs behind a fetch
  script rather than keeping them committed; include **only
  verifier-consumed files** in the bundle; and disclose no location for
  undistributed material. The public package accepts an independently
  supplied local bundle and verifies every byte before restoration.
- Additional raw outputs that no verifier consumes remain Tier 2 rerun
  products outside the published artifact inventory.

## Deliverable conformance

| Plan item | State |
| --- | --- |
| `W10_Paper_Draft_v2.md` addressing every self-critique point | Complete — (a) abstract/§1 judge dependence, (b) §4.5 conditional measurement stress, (c) §2.1 FoMER engagement, (d) §4.2/§6 observed pass shown not measurement-robust |
| `W10_Reproducibility_Package/` with pinned dependencies, data scripts, per-script README, regeneration | Complete — tested in a clean clone and virtual environment (test record in the package) |
| Capstone outline + drafted introduction and literature-context sections | Complete — `W10_Capstone_Outline.md`, sections (ii) and (iii) drafted |
| `Wk-10-ResearchLog.md` | This document |
| Registered Week 9 open items owned by Week 10 | Closed — FoMER paragraph (§2.1), judge-measurement stress analysis (§4.5), SVG byte-stability fix (below) |

## SVG byte-stability closure

The Week 9 open item is closed in code: `week-07/analyze_w07.py` now sets
`svg.hashsalt` and a fixed metadata date (matching
`week-09/build_w09_paper_figures.py`), and the three Week 7 SVGs were
regenerated once into their stable form. A double run now reproduces every
figure, `W07_Analysis.json`, and `W07_Run_Metadata.json` **byte-identical**;
the one-time SVG diff touched only `dc:date` and hashed element IDs, with
geometry unchanged.

## Verification record

- Baseline (before any change): `verify_w06_independent`,
  `test_w06_experiment2`, `test_w07_replication` (55 tests),
  `verify_w07_independent --phase precalibration` and
  `--phase confirmation`, `verify_w08`, `verify_w09` — all PASS at `2c5e417`.
- After the SVG fix: double-run hash comparison stable; `verify_w07_independent
  --phase confirmation` and `verify_w09` reran successfully; only the three SVGs
  changed bytes.
- After externalization: `fetch_data.py --check` PASS (all six manifest
  hashes, three provably equal to run-metadata pins); the release-download
  round trip was hash-verified; `verify_w06_independent` reran successfully against
  restored bytes.
- Local full suite: `regenerate_all.py --tier 1 --with-tests` — regeneration
  byte-identical, all verifiers and both test suites green, ending in
  `PASS: Week 10 verification complete`.
- Clean environment: fresh clone + fresh venv (Python 3.11, CPU torch),
  fetch, Tier 1 regeneration, full verifier suite, and the inference
  validate, mock, and smoke paths (the Week 6 dry-run gate loads the real
  model and is GPU-tier) — recorded with selected console output and
  contemporaneous summaries in
  [`W10_CleanEnv_Test_Transcript.md`](W10_Reproducibility_Package/W10_CleanEnv_Test_Transcript.md).
  The first clean-env pass surfaced and fixed two reproducibility findings:
  the generated tables file needed an `eol=lf` attribute to stay
  byte-identical in fresh Windows checkouts, and the Week 6 bank rebuild is
  content-identical except `created_utc`, so the hash-pinned bank is never
  rebuilt in place.

## Reflection

The section of the work I found hardest to write was §4.5. The temptation in
a sensitivity analysis is to pick assumptions that make the headline safe
and call the result a bound. Making it honest meant treating each CP lower
endpoint as a conditional stress input, using a binomial tail rather than a
rate-division shortcut, applying the control stratum to the rule's control
ceiling, and stating that false positives remain unestimated. The result that
goes against us is the important one: the registered observed-data rule pass
does not survive the combined measurement stress. Writing it taught me that
the analysis is useful because it narrows what can be claimed, not because it
turns the amendment into certainty.
