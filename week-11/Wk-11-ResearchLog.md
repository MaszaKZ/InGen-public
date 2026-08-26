# Wk-11 Research Log — Capstone Report, Research Review & Reproducibility Package

Period: 2026-08-24–2026-08-25 · Final capstone submission

## Weekly summary

Week 11 consolidated the registered contested-authority study into a coherent
academic submission. The work followed the four priorities stated in the
[Week 10 review](../week-10/W10_Feedback.md)—reproducibility, auditability,
paper refinement, and preparation of the capstone evidence base—and treated
the verified Week 10 sensitivity analysis and package as the starting point.
The resulting paper,
*Authorization Safety as a Two-Error Operating-Point Problem: A Registered
Evaluation of Language-Model Decision Layers for Service Robots*, is maintained
as [`W11_Capstone_Report.tex`](W11_Capstone_Report.tex) and compiled as a
20-page [`W11_Capstone_Report.pdf`](W11_Capstone_Report.pdf). Its argument is
organized around a two-error operating point: reducing unsafe compliance can
increase refusal of authorized actions, so safety and utility must be assessed
together.

The confirmatory result is unchanged from the admitted evidence. On common
prompts, Qwen minus Mistral produced differences of −55.0 percentage points in
plain-caution failure, −40.1 points in pressured-caution failure, and +18.8
points in authorized-control refusal; every family-clustered confidence
interval excluded zero. The conditional false-negative stress analysis
attenuated these contrasts to −25.6, −35.0, and +18.1 points without changing
their directions. Qwen with deliberation remained the only intervention that
passed the registered rule on observed outcomes, but that disposition did not
survive combined measurement stress. The report therefore distinguishes
confirmatory generator comparisons, descriptive intervention results, and
conditional sensitivity results throughout.

The report’s four figures were rebuilt in a restrained publication style and
checked in their final page context. The 14-slide
[`W11_Research_Review_Deck.pptx`](W11_Research_Review_Deck.pptx) uses the
Mid-Review visual language with result-bearing headlines and follows the
required research narrative from physical-AI context through retrospective.
The standalone [`W11_Reproducibility_Package`](W11_Reproducibility_Package/)
contains admitted evidence, analysis code, figures, the report, the deck,
tests, and manifest-pinned acceptance receipts. Model weights are intentionally
external: its README gives a manual model download procedure, pinned revisions,
checksum checks, and the exact package-local cache layout. Offline CPU
acceptance and short live inference establish the package’s review and loading
paths without claiming a full confirmation rerun. Integrated verification
closed the week with a 141-entry package manifest, 15 Week 11 tests, and 25
package tests passing.

## Detailed chronological audit trail

### 2026-08-24 — Evidence integration and first capstone build

- Established the Week 10 judge-sensitivity output and the registered Week 7
  confirmation record as the quantitative sources for the capstone. The Week
  11 evidence adapter preserves the original estimates, denominators,
  intervals, and claim classifications rather than recomputing them from
  presentation text.
- Structured the report around three precise questions: the generator effect
  under identical instructions, whether prompt interventions improve the
  registered two-error rule, and how those results inform a physical-AI
  application framework.
- Integrated the earlier experiments as design evidence. Experiment 1’s
  apparent lexical gain disappeared under semantic review; 13 of 14 automated
  flags were lexical false positives, the unsafe count remained 1 to 1, and 64
  of 72 chain-of-thought outputs reached the token cap. Experiment 2 then used
  semantic action scoring and authorized controls: deliberation reduced
  pressured failures from 12/32 to 2/32, whereas constraint gating reduced
  them to 0/32 while increasing control failures from 1/32 to 4/32.
- Built the initial report and presentation artifacts and introduced an
  integrated verifier covering evidence continuity, publication figures,
  report and slide outputs, and package integrity.

### 2026-08-25 — Reproducibility and inference path

- Rebuilt the standalone package around a deterministic manifest. The package
  admits the source evidence and exact publication artifacts while excluding
  large model snapshots from distribution.
- Documented all ten pinned model repositories and revisions, the expected
  Hugging Face cache structure, connected acquisition and verification, and
  offline transfer. The model verifier checks revision layout and can bind
  transferred files to a portable checksum manifest.
- Added an offline CPU acceptance route and tested it in an isolated
  environment. The manifest-pinned `isolated-cpu-mock.json` receipt verifies
  orchestration and evidence recomputation without network access or model
  weights.
- Exercised the pinned Qwen generator through a deliberately short live run:
  one preflight scenario, five registered prompt conditions, five nonblank
  outputs, and no token-cap hits. The receipt records the model revision,
  dependency versions, command, output hash, and peak CUDA allocation. Its
  claim boundary is explicit: this run verifies offline loading and short
  generation for one generator, not Mistral, the judge panel, or the registered
  confirmation result.
- Added a separate minimal end-to-end runner for the generation-to-panel path.
  It uses one preflight scenario and one prompt condition, loads both active
  generators and the three active judges sequentially, and produces two
  generations, six judgments, and two panel rows. The package documents a
  reference completion in 296 seconds with 9.48 GiB peak CUDA allocation.

### 2026-08-25 — Report, figures, and page composition

- Expanded the capstone into a 20-page IEEEtran report with a per-family
  appendix, a worked adjudication example, a measurement-sensitivity table,
  and an expected-loss decision figure. These additions make the statistical
  interpretation and the operating-point recommendation inspectable without
  overstating external validity.
- Rebuilt all four figures with consistent type, line weights, legends, and
  panel spacing. The common zero reference was positioned for balanced visual
  comparison, long condition labels were given adequate space, and captions
  remained in LaTeX rather than being embedded as small raster text.
- Adjusted floats and local spacing after rendering the complete PDF. Tables
  and figures now follow the passages that introduce them, and page density is
  distributed without artificial page stretching or avoidable blank regions.

### 2026-08-25 — Research-review deck

- Rebuilt the deck as a minimal academic presentation rather than a condensed
  poster. The title matches the paper, typography and alignment follow the
  Mid-Review reference, and the visual system is limited to a neutral field,
  restrained blue accents, compact evidence panels, and report figures.
- Implemented the required 14-slide sequence: title; InGen physical-AI context
  and PIC 2.0; research motivation; precise research questions; benchmark and
  baseline; Experiments 1 and 2; cross-experiment synthesis; two PIC 2.0 model
  classes; per-platform recommendations; limitations; paper contribution;
  three findings and one recommendation; retrospective and next steps.
- Rewrote every content-slide headline as a finding with a concrete result.
  Text placement, font consistency, figure legends, source notes, and the final
  package copy were checked after rendering all slides.

### 2026-08-25 — Integrated submission review

- Checked the report, deck, package, and entry-point documentation as one
  submission. Quantitative claims retain the same direction, denominators, and
  evidential status across artifacts.
- Confirmed that the model-download directions point to
  `models/huggingface/hub/models--ORG--REPO/snapshots/REVISION/`, that live
  inference remains optional for evidence review, and that neither acceptance
  receipt is described as a full reproduction.
- Removed temporary render and isolated-test workspaces after their retained
  receipts and hashes had been verified.

## Deliverable conformance

| Week 11 requirement | Final artifact and evidence |
| --- | --- |
| Academic capstone report | [`W11_Capstone_Report.tex`](W11_Capstone_Report.tex) and [`W11_Capstone_Report.pdf`](W11_Capstone_Report.pdf); 20-page IEEEtran paper with four publication figures, limitations, appendices, and reproducibility statement |
| Research presentation | [`W11_Research_Review_Deck.pptx`](W11_Research_Review_Deck.pptx); 14-slide minimal academic deck following the prescribed sequence and using result-bearing headlines |
| Week 10 continuity | The report admits the registered confirmation record, Week 10 conditional measurement stress, application framework, and package evidence; claims remain separated as confirmatory, descriptive, or conditional |
| Reproducibility package | [`W11_Reproducibility_Package/`](W11_Reproducibility_Package/); 141 manifest-pinned files covering source evidence, analysis, artifacts, tests, receipts, and model instructions |
| Model acquisition | [`W11_Reproducibility_Package/README.md`](W11_Reproducibility_Package/README.md) provides manual model download, pinned revisions, checksum verification, correct cache placement, offline transfer, and inference commands |
| Minimal execution evidence | `isolated-cpu-mock.json` records clean offline acceptance; `isolated-short-inference.json` records five Qwen generations and states its partial-inference boundary; the full minimal-pipeline command is documented separately |
| Weekly research record | This document records the evidence chain, completed deliverables, verification, limitations, and reflection |

## Verification record

- `python -m unittest week-11.test_w11 -v` — 15 Week 11 tests passed,
  including report structure and pagination, figure context, the prescribed
  14-slide sequence, deck rendering and bounds, package-copy identity, and this
  log’s submission contract.
- `python -m unittest discover -s week-11/W11_Reproducibility_Package/tests -v`
  — 25 package tests passed, including manifest mutation detection, model-layout
  checks, acceptance receipts, and minimal-pipeline planning and aggregation.
- `python week-11/W11_Reproducibility_Package/verify_package.py` — package
  manifest, admitted evidence, and final artifacts verified across 141 entries.
- `python week-11/verify_w11.py` — evidence continuity, figures, the compiled
  report, all 14 slides, package hashes, and the isolated CPU receipt verified
  as an integrated submission.
- The report was rendered page by page and the deck was rendered slide by
  slide for visual inspection. No clipped content, unintended overlap, or
  out-of-bounds element remained in the final artifacts.
- The package copy of the deck is byte-identical to the canonical Week 11 deck;
  manifest verification also binds the package README and both acceptance
  receipts to their distributed bytes.

## Reflection

The central lesson of the capstone is that authorization safety cannot be
reduced to refusal rate. The strongest observed generator contrast improved
both caution conditions while worsening authorized-control refusal, and the
most aggressive prompt gate showed the same trade-off within an experiment.
This makes the operating-point framing more than a presentation device: it is
the condition required to avoid selecting a model or mitigation on only the
error it was designed to reduce.

The measurement audit was equally important. Experiment 1 showed how a lexical
rubric could manufacture an apparent improvement, and the Week 10 stress
analysis showed how a rule-meeting intervention could lose that status under
plausible false negatives. Neither result invalidates the later benchmark;
both delimit the claim that can be made from it. The final recommendation is
therefore to choose and validate a platform-specific operating point, preserve
authorized controls in every evaluation, and treat calibrated deferral as the
highest-value untested extension. Embodied trials, additional generator
families, blinded validation of the weakest judge stratum, and a directly
measured deferral action remain open research questions.

## AI assistance note

AI-assisted tools supported code and document drafting, deterministic artifact
generation, consistency checks, and visual inspection. Quantitative statements
were traced to admitted repository evidence; generated report and presentation
artifacts were rendered and reviewed; and automated claims were accepted only
after the recorded tests and independent verifiers passed. The researcher
retained responsibility for experimental interpretation, scope boundaries,
and the final academic narrative.

## Final Week 11 completion entry

Week 11 is complete. The report, 14-slide research-review deck, four figure
sets, reproducibility package, acceptance receipts, model-acquisition and
minimal-run instructions, integrated verifier, and weekly research log form a
single evidence-consistent submission. The admitted findings remain bounded to
the synthetic text benchmark and registered measurement design; no artifact
claims embodied-system or field performance.
