# W10 Capstone Outline and Drafted Sections

**Ziyue Li** · 2026-08-11 · Week 10 deliverable (internship plan, Phase D)

This document fixes the structure of the Weeks 11–12 capstone report
(`W11_Capstone_Report.docx`, 20–25 pages) and drafts its two
literature-context sections now, as the plan specifies. Every planned section
lists the committed artifacts its claims will cite, so the capstone inherits
the same claim-to-artifact chain as the paper: the report will cite committed
evidence directly rather than paraphrasing weekly documents
([`W10_Feedback.md`](W10_Feedback.md), focus area 4). Claim labels follow the
registered hierarchy ([`W08_Paper_Claim_Registry.json`](../week-08/W08_Paper_Claim_Registry.json)):
**confirmatory**, **descriptive**, **exploratory**, **proposed**, with
**literature-only** marking statements supported solely by cited public work.
The paper/capstone boundary follows
[`W08_Paper_Handoff.md`](../week-08/W08_Paper_Handoff.md): the six-class PIC
analysis, the five-platform matrix, and the product-specific research gates
belong here, not in the paper.

## Planned structure (Week 11 specification, sections i–xi)

### (i) Executive summary

One page for a reader who reads nothing else: three findings and one
recommendation. The three findings are the generator trade-off (C1,
confirmatory), the failure of any tested prompt intervention to transfer
across generators with only one fragile registered pass (C2, descriptive),
and the measurement lesson that lexical safety scoring certified an
improvement that semantic adjudication rejected (C3, descriptive). The one
recommendation: platform evaluation should score unsafe compliance and
authorized-control refusal as joint endpoints, with calibrated deferral as
the proposed third action (C5, proposed).

- Evidence: [`W07_Analysis.json`](../week-07/W07_Analysis.json), [`W07_Confirmation_Results.md`](../week-07/W07_Confirmation_Results.md), [`W05_Results_Memo.md`](../week-05/W05_Results_Memo.md), [`W08_Application_Framework.md`](../week-08/W08_Application_Framework.md)
- Labels: confirmatory ×1, descriptive ×2, proposed ×1 — stated with exact estimates and intervals.

### (ii) Physical-AI research landscape and InGen context

Drafted below. Argues that the safety-critical novelty in InGen's public
product family is the language-mediated authorization layer, not perception
or control, and that this layer is exactly where the program's evidence
applies. Literature-only except where it points forward to program artifacts.

### (iii) Literature review and research-gap justification

Drafted below. Argues that three literature clusters each miss the same
measurement — unsafe compliance and authorized-action refusal as joint
endpoints on authorization-gated operational decisions — and grounds the
program's three registered research questions in that gap. Literature-only,
with the Week 8 gap-status update cited from program artifacts.

### (iv) Benchmark design and methodology

The design story from Week 3's 32-scenario lexical bank to Week 7's
registered 96-scenario confirmation bank: paired plain/pressured/control
subtypes, the byte-identical common prompt as the only registered
cross-model endpoint, the three-judge panel with its calibration record, and
the acceptance amendment with the §4.5 stress analysis as its quantitative
companion. The section presents the instrument honestly: gates passed, the
underpowered single-holdout rule, the disclosed amendment, and the weakest
stratum carried as a limitation.

- Evidence: [`W07_Confirmation_Bank.json`](../week-07/W07_Confirmation_Bank.json), [`W07_Run_Metadata.json`](../week-07/W07_Run_Metadata.json), [`W07_Judge_Calibration.json`](../week-07/W07_Judge_Calibration.json), [`W07_Panel_Acceptance_Amendment.json`](../week-07/W07_Panel_Acceptance_Amendment.json), [`W10_Judge_Sensitivity.json`](W10_Judge_Sensitivity.json), [`W03_Benchmark_Design.md`](../week-03/W03_Benchmark_Design.md)
- Labels: descriptive (design facts), with the amendment disclosure verbatim.

### (v) Baseline evaluation results

Weeks 3–4 baselines as taxonomy anchors, not validated semantic labels: the
class-tagged counts, the three-model comparison, and the failure taxonomy
that motivated the semantic endpoint. Argues that these early numbers were
useful for design and misleading for conclusions — the reason the program
moved to semantically adjudicated outcomes.

- Evidence: [`W03_Baseline_Results.csv`](../week-03/W03_Baseline_Results.csv), [`W04_Three_Model_Results.csv`](../week-04/W04_Three_Model_Results.csv), [`W04_Failure_Analysis.md`](../week-04/W04_Failure_Analysis.md)
- Labels: descriptive, with the Week 8 taxonomy-anchor qualification attached to every count.

### (vi) Empirical experiments (Phase B findings)

Weeks 5–6: the prompt-intervention ablation whose lexical result a semantic
audit overturned (64 of 72 chain-of-thought outputs at the token cap), and
the Week 6 pressure diagnostic that confirmed a pressure effect within
Mistral under the registered scorer. Argues the phase's real product was
methodological: chat templates, semantic endpoints, and inter-rater
reliability became prerequisites for Phase C.

- Evidence: [`W05_Results_Memo.md`](../week-05/W05_Results_Memo.md), [`W05_Semantic_Audit_Summary.json`](../week-05/W05_Semantic_Audit_Summary.json), [`W06_Analysis.json`](../week-06/W06_Analysis.json), [`W06_Reliability`](../week-06/W06_Experiment2_Notebook.ipynb)
- Labels: descriptive and exploratory; cross-week comparisons framed as methodological lessons, never pooled estimates.

### (vii) Cross-experiment synthesis and primary research contribution

The paper's confirmatory core, stated once with full apparatus: the C1
trade-off with family-clustered intervals, the conditional false-negative
measurement stress analysis, and the seed/judge stability record. This is the
only section that carries a confirmatory label, and it carries the stress
analysis's unestimated-false-positive boundary with it.

- Evidence: [`W07_Analysis.json`](../week-07/W07_Analysis.json) (`paired_contrasts.primary_common_baseline`), [`W10_Judge_Sensitivity.json`](W10_Judge_Sensitivity.json), [`W07_Research_Note.md`](../week-07/W07_Research_Note.md), [`W10_Paper_Draft_v2.md`](W10_Paper_Draft_v2.md) §4
- Labels: C1 confirmatory; C2 and the stress analysis descriptive; C4 exploratory.

### (viii) PIC 2.0 analysis and application framework

The capstone-side material the paper deliberately excludes: all six public
model classes against the program's evidence with the evidence-strength
conventions (evidence strength ≠ module tested; class-tagged counts are not
prevalence), and the five-platform × task-risk operating-point matrix with
per-cell research actions and advancement gates. Argues that every
platform-and-task-risk cell is an operating-point choice on the two-error
curve, and that the framework's statuses (tested analogue / proposed–untested
/ literature-only) are the honest interface between program evidence and
product decisions.

- Evidence: [`W08_PIC20_Analysis.md`](../week-08/W08_PIC20_Analysis.md), [`W08_Application_Framework.md`](../week-08/W08_Application_Framework.md), [`W08_Pressure_Cue_Audit.json`](../week-08/W08_Pressure_Cue_Audit.json)
- Labels: descriptive where tested, proposed and literature-only elsewhere — statuses copied from the framework tables, never upgraded.

### (ix) Research paper contribution summary

What the paper (v2) claims, for a reader who will not read the paper:
contribution, evidence, and the boundary of what a reviewer can verify from
committed artifacts. Summarizes rather than re-argues; every number quoted
matches the draft's provenance appendix.

- Evidence: [`W10_Paper_Draft_v2.md`](W10_Paper_Draft_v2.md), [`W08_Paper_Claim_Registry.json`](../week-08/W08_Paper_Claim_Registry.json)
- Labels: as registered per claim (C1–C5).

### (x) Limitations and future research directions

The program-level limitation statement: synthetic text-only scenarios, two
7B generators, LLM-judged outcomes under a disclosed amendment with a
conditional false-negative stress test, non-estimable salience contrast, and
the single observed-data rule pass that fails combined measurement stress.
Future directions inherit the paper's proposed items plus the framework's
advancement gates.

- Evidence: [`W10_Paper_Draft_v2.md`](W10_Paper_Draft_v2.md) §6, [`W10_Judge_Sensitivity.json`](W10_Judge_Sensitivity.json), [`W08_Application_Framework.md`](../week-08/W08_Application_Framework.md) (c)
- Labels: limitations stated as facts with artifact references; directions proposed.

### (xi) Conclusion

One page: the two-error operating-point finding restated, what would change
a deployment decision (the costlier error per cell), and what the program
leaves behind — a registered benchmark, an instrument accepted under a
disclosed amendment together with its conditional stress analysis, a
reproducibility package, and a framework that converts evidence into
per-platform research gates.

- Evidence: the section cites nothing new; every statement traces to sections iv–x.

## Drafted section (ii): Physical-AI research landscape and InGen context

Decision assurance is one important constraint among several facing service
robots, alongside perception, mechanics, control, real-time sensor fusion,
generalization, and human-robot interaction. The generalist-policy literature
shows manipulation and locomotion capabilities transferring across
embodiments at scale ([@openx2023rtx; @kim2024openvla; @octo2024policy;
@black2024pi0], surveyed in [`W02_Literature_Review.md`](../week-02/W02_Literature_Review.md)),
and the systematic review of foundation-model service robots catalogues
rapid progress in perception, navigation, and interaction alongside
persistent gaps in real-time decision assurance [@lisondra2025embodied].
What the deployment wave adds is a new layer: language models placed between
human requests and robot actions. In that layer, the operational facts
arrive as language — who is asking, what they claim, which prerequisite is
on file — and the safety-critical question is whether a requested operation
begins now or is withheld pending verification.

InGen Dynamics' public product family makes this concrete, and it is the
program's motivating context: Sentinel Prime AI as an enterprise physical
security platform, the Aido family and Origami's assistive and home robots,
and the PIC 2.0 architecture described in the public Origami research pages
([@ingen2026origami; @ingen2026sentinel];
[`W01_Research_Landscape.md`](../week-01/W01_Research_Landscape.md)). We use
these public materials for terminology and stated design intent only — none
of the program's results validates the described products or their
performance claims, and no proprietary module was tested. Read through the
authorization lens, the portfolio's safety-relevant decisions are exactly
the two-error kind: a security platform that silences an alarm for an
unauthorized caller has failed unsafely, and one that refuses a line
controller's authorized gate release has failed operationally. Every
platform-and-task-risk cell is a choice of operating point between those two
errors ([`W08_Application_Framework.md`](../week-08/W08_Application_Framework.md)),
and the program's experiments — from the Week 3 baselines through the Week 7
registered confirmation study — were built to measure both errors at that
decision layer, on synthetic text scenarios that borrow the platforms'
terminology without touching their systems.

## Drafted section (iii): Literature review and research-gap justification

This section is a literature analysis: every statement in it is derived
from the cited public papers, not from our experiments, except where a
program artifact is named explicitly as the source of a gap-status update.

The Week 2 review ([`W02_Literature_Review.md`](../week-02/W02_Literature_Review.md))
organized the relevant work into three clusters, and each establishes
something the program relies on while missing the same measurement. The
embodied-evaluation cluster (Open X-Embodiment, OpenVLA, Octo, π₀, ReVLA,
FoMER) built generalist policies and benchmarks whose evaluations score task
success, robustness, and — in FoMER's case — the quality of step-by-step
embodied reasoning including safety awareness [@dissanayake2025fomer]. But
stepwise-reasoning scoring does not require distinguishing a safe-sounding
explanation from the action it authorizes. FoMER can penalize blanket refusal
through final-answer and action-validity scores, but it does not expose
over-refusal as a dedicated paired endpoint against matched unauthorized
requests ([`W10_Paper_Draft_v2.md`](W10_Paper_Draft_v2.md) §2.1 develops this
engagement in full). The safety-mechanism cluster includes methods that
enforce mathematically specified state constraints (ATACOM-style action
constraints and control-barrier functions), OOD-assurance methods, and
runtime-governance systems that intercept unauthorized actions in simulation
[@tolle2025safe; @guerrier2024barrier; @hodge2025ood; @qin2026runtime]. The
runtime-governance work reports a false-rejection rate
alongside unauthorized-action interception, but its simulation uses a
deterministic, well-separated policy boundary; language-mediated authorization
facts such as whether a caller has permission remain a different measurement
problem. The trust cluster
establishes that calibrated reliance, not maximal caution, is the goal
[@rezaeikhavas2020trust; @perkins2021trust; @sanneman2020trust], which makes
over-refusal a first-class cost rather than a conservative virtue — but it
supplies no executable benchmark for model decisions.

The review distilled this into three gaps, and the program's registered
research questions ([`W02_Research_Questions.md`](../week-02/W02_Research_Questions.md))
are their measurable forms: calibrated deferral under uncertainty (Gap 1),
safety-constraint behavior at authorization boundaries (Gap 2), and trust
calibration in service-robot decisions (Gap 3). The Week 8 gap-status
update, made after the confirmation study, is recorded in
[`W08_Application_Framework.md`](../week-08/W08_Application_Framework.md)
(c): Gap 2 is substantially addressed but not closed by the two-error
evidence; Gap 1 is partially addressed — deferral was never scored, and
remains the proposed third action; Gap 3 stays fully open at the construct
level. The justification for the program's contribution is therefore
bounded and specific: within the reviewed public literature, no prior work
combines a registered cross-generator contrast under a byte-identical
prompt, joint measurement of unsafe compliance and authorized-action
refusal, and service-robot authorization scenarios with paired controls.
The capstone claims that combination — identified from the Week 2 review,
stated as a bounded gap rather than a universal novelty claim — as the
program's position in the literature.

---

AI assistance was used for drafting and consistency checking. Structural
conformance is checked by [`verify_w10.py`](verify_w10.py).
