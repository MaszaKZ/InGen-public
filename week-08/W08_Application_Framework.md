# W08 Application Framework: Choosing Operating Points on the Two-Error Curve

Date: 2026-07-26

## Organizing principle

The [Week 7 confirmation study](../week-07/W07_Confirmation_Results.md) showed that, under a byte-identical prompt, generator choice traded unsafe compliance against authorized-control refusal rather than improving both endpoints (−55.0pp plain caution, −40.1pp pressured, +18.8pp control refusal; family-clustered 95% CIs excluded zero). This framework therefore treats every platform-and-task-risk cell as an **operating-point choice on a two-error curve**. The framing follows [Lekeufack et al. (2023), *Conformal Decision Theory*](https://arxiv.org/abs/2310.05921): the registered mitigation rule (≥25% relative pressured-failure reduction at ≤3.125pp added control failure) is one program-specific operating point, while calibrated deferral is an untested third action that might improve the trade-off.

Two evidence regimes remain separate: Weeks 3–5 used a lexical rubric without chat templates and the [Week 5 semantic audit](../week-05/W05_Results_Memo.md) demonstrated material endpoint bias; Weeks 6–7 used chat templates, registered designs, and LLM judge panels. All scenarios were synthetic and text-only. Accordingly, **the rows below are research and evaluation priorities, not production deployment approvals**.

## (a) Per-platform priority matrix

Each platform splits into low-risk authorized work and high-risk boundary work, because a single operating point per platform is too coarse — Fari's benign self-requests and its medication boundaries favor opposite error costs.

| Platform · task-risk cell | Costlier error and priority taxonomy | Evidence | Research action (status) | Advancement gate |
| --- | --- | --- | --- | --- |
| Sentinel · boundary | Unsafe compliance: unsafe output; missed escalation | W6–7. Mistral failed 29/80 Sentinel pressured rows and Qwen failed 5/78 evaluable rows. Cue-specific counts are descriptive and confounded with scenario family, variant, wording, setting, and prerequisite salience | Evaluate tested Qwen2.5-7B + deliberation; no blanket gate (**tested, text analogue**) | Security-specific replication with operator deferral and both endpoints |
| Sentinel · authorized ops | Over-refusal: excessive refusal | W7 controls: Mistral 0/80, Qwen 15/80 | Make control refusal co-primary; avoid blanket gating (**tested, text analogue**) | Predeclared refusal budget on operator workflows |
| Aido Humanoid · care boundary | Unsafe compliance: unsafe output | W7 Qwen plain 39/80; Mistral pressured 40/80 | Evaluate tested Qwen2.5-7B + deliberation behind human authorization (**tested, text analogue**) | Multimodal state, actuation constraints, human override |
| Aido Humanoid · authorized care | Over-refusal: excessive refusal | W7 Qwen controls 15/80 | Avoid blanket gating; tune against both errors (**tested, text analogue**) | Separate care-task refusal and unsafe-action budgets |
| Fari · medication/privacy boundary | Unsafe compliance: unsafe; missed escalation; incomplete | W4 anchors: 8 unsafe, 5 missed, 12 incomplete among 47 rows; not prevalence | Test RAG over versioned authorization records (**proposed—untested**) | Blinded paired caution/control trial under W7 endpoint |
| Fari · benign self-request | Over-refusal: excessive refusal | W3–5 lexical regime; semantic handling better than labels implied | Test retrieval to verify entitlement; do not rely on persona (**proposed—untested**) | No unsafe gain or material self-service refusal regression |
| Senpai · routine tutoring | Over-refusal: incomplete; weak justification | W4 anchors: 12 incomplete, 7 weak, 6 refusal | Test interruption/recovery fine-tuning; do not claim structured-output safety (**proposed—untested**) | Completion improves without safeguarding regression |
| Senpai · safeguarding boundary | Unsafe compliance: unsafe; missed escalation | W4 anchors: 3 unsafe and 3 missed platform-wide | Registered prompt-vs-RAG-vs-fine-tuning comparison (**proposed—untested**) | Predeclare unsafe and routine-refusal budgets |
| Aido Rover · degraded perception | Unsafe overconfidence: unsafe; missed; incomplete | W4 anchors: 10 unsafe, 6 missed, 10 incomplete; text only | Sensor calibration/OOD test plus scored fallback; no text prompt supported (**literature-only / proposed**) | Multimodal conflict benchmark with calibration and action outcomes |
| Aido Rover · fleet coordination | Both: missed escalation; incomplete action | 2 scenarios, 7 tagged rows; single-agent text proxy | Build multi-agent evaluation before choosing an intervention (**proposed—untested**) | Fleet safety, coverage, and reassigned-risk endpoints |

## (b) Intervention recommendations with evidence basis

### Cross-cutting evidence

| Intervention | Status | Applicable platforms / failure types | Evidence (decisive versions) |
| --- | --- | --- | --- |
| Generator selection | Tested — largest observed operating-point shift | Tested on Sentinel + Aido Humanoid; unsafe compliance vs. control refusal | W7: −55.0pp plain / −40.1pp pressured at +18.8pp control refusal |
| Deliberation / CoT | Tested — conditional, generator-dependent | Tested on Sentinel + Aido Humanoid (W6–7); W5 CoT cells inconclusive because 64/72 outputs hit the output-token cap | W6: 12/32→2/32, only rule-meeting arm. W7: transferred only for Qwen (2.5%→0.0% pressured at +1.25pp control, the sole rule-meeting arm); Mistral 19.4% vs 18.8% adapted baseline |
| Structured output | Tested — negative under pressure | Tested on Sentinel + Aido Humanoid (W6); W5 result is a rubric effect | W5 measurement-inconclusive; W6 pressured 12/32→14/32 |
| Constraint gating | Tested — one-sided and non-uniform | Tested on Sentinel + Aido Humanoid (W6–7); Fari is an extrapolation | W6 pressured 12/32→0/32 but controls 1/32→4/32. W7 Qwen reached 0% pressured at +7.5pp control (rule failed); Mistral pressured worsened 18.8%→36.2% |
| Persona grounding | Inconclusive | Fari/Senpai/Rover bank, W3–5 lexical regime only | W5 lexical target flags fell 8→5 at a flat pass rate, but persona rows were not semantically adjudicated and the same scorer was shown to be biased |
| RAG | Proposed — untested in this program | Candidate for authorization-fact grounding (Fari/Sentinel boundaries) | Filling experiment: retrieval over an authorization registry, scored on the W7 two-error endpoint |
| Fine-tuning / PEFT / LoRA | Proposed — untested in this program | Candidate for the tested Mistral setup, where prompt effects failed to transfer | Filling experiment: LoRA on paired caution/control data, judged by the calibrated W7 panel |

Only prompt engineering and generator selection were run; RAG and fine-tuning remain experiment proposals.

## (c) Unresolved questions and gap-analysis update

**Week 2 gaps, reclassified.**

- *Gap 1 — calibrated deferral under uncertainty:* **partially addressed.** Deferral was behaviorally scored in Weeks 3–4, but no calibrated policy or explicit third-action intervention was evaluated under the registered Weeks 6–7 endpoint, and no calibration quantity was estimated.
- *Gap 2 — safety constraints under edge cases:* **substantially addressed, not closed.** Constraint gating reduced unsafe decisions in some model–bank cells, but the benefit did not generalize and sometimes reversed; refusal cost was more consistent than safety benefit.
- *Gap 3 — trust calibration from explanations:* **fully open at the construct level.** Weeks 3–5 used biased lexical proxies, Weeks 6–7 dropped the endpoint, and no human trust outcome was measured.

**New gaps the Week 2 review did not surface** (observations, not general laws):

1. Generator identity appears to be a safety lever in its own right — the two-error operating point differed sharply between two pinned generators under a common prompt.
2. Intervention effects appear generator- and experiment-stack-dependent (Week 6 deliberation did not transfer additively in Week 7).
3. The observed pressure-effect sign appears bank-sensitive (Week 6's pressured-greater-than-plain reversed in Week 7).
4. LLM-judge certification is itself a research bottleneck: five single-shot holdouts and a pre-registered ceiling analysis showed the registered certification rule had low power — not that judge quality was definitively non-binding.

**Open items carried forward.**

- *Prerequisite-salience contrast: non-estimable; replacement audit exploratory.* The planned stratification was checked before paper drafting. All 32 plain items state the governing prerequisite and none states that it is missing, so the stratifier has no variation. Salience is not constant across the pair either: 8 of 32 pressured items, all in the `false_clearance` arm, name the absent prerequisite outright, which confounds that arm with the very factor the contrast meant to isolate. The supplementary [pressure-cue audit](W08_Pressure_Cue_Audit.md) therefore reports post-outcome paired descriptive differences with family-clustered intervals only. Tactics remain bundled with family, variant, wording, and setting; the rows identify neither causal tactic effects nor a priority ranking, and the salience explanation is left untested rather than refuted. The estimable follow-up is a registered 2×2 salience-by-pressure experiment that crosses salience with pressure across all tactics, counterbalances tactic and setting within family, and retains authorized controls.
- *Blinded human validation* of the judge panel's weakest measured stratum (pooled unsafe declares-then-hedges detection, 14/16) — the highest-value measurement step.
- *Calibrated deferral* ("escalate to operator") as a scored third action: proposed, not recommended — never evaluated. The experiment: add a deferral outcome to the W7 endpoint, calibrate its trigger, and test whether it dominates both generators' corner solutions.
- *A third generator family*, to test whether the two-error trade-off is a two-model accident.

The supplementary [paper handoff](W08_Paper_Handoff.md) and [claim registry](W08_Paper_Claim_Registry.json) constrain use of this framework in Weeks 9–12. Application statements remain **proposed** research guidance, not additional confirmatory results or deployment approvals.
