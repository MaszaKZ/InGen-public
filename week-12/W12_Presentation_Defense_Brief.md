# Research Presentation and Defense Brief

This brief supports a **30-minute presentation** followed by a **20-minute research Q&A**. The core is a **14-slide** evidence sequence. Keep quantitative claims within their registered scope: synthetic text scenarios, two pinned generator pipelines, panel-judged outcomes, and family-clustered uncertainty.

## Timed 14-Slide Presentation

| Slide | Time | Purpose | Evidence to show | Spoken takeaway |
| --- | ---: | --- | --- | --- |
| 1. Title and claim | 1 min | State the problem and result | Paper title; one-sentence operating-point claim | Safety cannot be ranked on unsafe compliance alone. |
| 2. Authorization boundary | 2 min | Define the operational decision | Security and assistive-care examples | The endpoint is whether the requested operation begins now. |
| 3. Two errors | 2 min | Motivate joint scoring | Unsafe compliance versus authorized refusal | Refuse-all behavior is not operationally safe. |
| 4. Registered design | 3 min | Establish comparison validity | 96 scenarios, 16 families, five arms, five seeds | Only the byte-identical common prompt supports the generator contrast. |
| 5. Measurement instrument | 3 min | Explain panel use and limits | Three judges; 14/16 weakest stratum; amendment | Every rate is an LLM-judge measurement. |
| 6. Analysis and uncertainty | 2 min | Explain estimands | Family bootstrap, paired contrasts, exclusions | Families, not scenario-seed rows, are the independence unit. |
| 7. Primary result | 3 min | Present the operating point | Figure 1; -55.0, -40.1, +18.8 points | The generators trade unsafe compliance against over-refusal. |
| 8. Prompt interventions | 3 min | Test transfer and mitigation | Figure 2; six rule dispositions | No tested intervention transfers as a blanket remedy. |
| 9. Pressure reversal | 2 min | Surface the unexpected pattern | Plain versus pressured rates | Quiet authorization gaps were harder than conspicuous pressure. |
| 10. Measurement stress | 2 min | Calibrate robustness | Figure 3; -25.6 stressed plain contrast | Primary directions survive; the mitigation pass does not. |
| 11. Expected loss | 2 min | Translate rates into selection | Figure 4 and break-even table | The preferred generator depends on frequencies and costs. |
| 12. Evidence boundaries | 2 min | Prevent overclaiming | Synthetic/text-only/two-model boundary | This is benchmark evidence, not deployment assurance. |
| 13. Follow-up experiment | 2 min | Present the next discriminating study | Human labels, three generators, factorial bank, defer | The next study targets measurement and external validity directly. |
| 14. Closing | 1 min | Restate the contribution | One operating-point graphic | Report both errors and declare the loss model. |

Total presentation time: **30 minutes**. If time is lost, shorten Slides 2 and 9; do not skip Slides 5, 7, 10, or 12 because they establish measurement authority, the primary claim, robustness, and scope.

## Claim Discipline During Delivery

- Say “generator pipelines” for the common-prompt contrast because native chat templates, tokenizers, quantized weights, and inference stacks remain part of each condition.
- Say “panel-majority measured failure” rather than “ground truth.”
- Describe Qwen plus deliberation as an observed-data rule pass that fails combined measurement stress.
- Treat tactic and platform strata as descriptive heterogeneity, not causal effects.
- State that expected-loss ratios are illustrative and require target frequencies, costs, and a joint bootstrap for deployment use.

## Anticipated 20-Minute Research Q&A

### Research-question selection

**Question:** Why focus on authorization rather than general embodied reasoning or task success?

**Answer:** Authorization creates a sharp operational endpoint and exposes two competing errors. Existing task-success measures can reward blanket refusal indirectly, whereas paired authorized controls make the cost of that refusal visible. The narrow question supports registered, paired inference and complements broader embodied-reasoning benchmarks.

### Scenario-bank design

**Question:** Why should synthetic scenarios support any conclusion?

**Answer:** They support a bank-relative comparison under controlled authorization changes, not a prevalence estimate. Family pairing holds domains and prerequisites constant while varying authorization state. External validity remains open and is explicitly targeted by the follow-up design.

### Intervention choice

**Question:** Why test deliberation, structured output, and constraint gating?

**Answer:** They represent three distinct prompt-level mechanisms: expanded reasoning, fixed decision representation, and an explicit prerequisite check. Their divergent generator-specific effects are evidence against assuming that prompt-method labels transfer unchanged across pipelines.

### Novelty

**Question:** What is new relative to robot-foundation-model and over-refusal benchmarks?

**Answer:** The bounded contribution is the combination of a registered cross-generator common-prompt contrast, paired plain/pressured/authorized variants, and joint unsafe-compliance and authorized-refusal endpoints for service-robot authorization decisions. The paper does not claim that no other benchmark studies refusal.

### Judge validity

**Question:** Can an LLM judge panel validate other LLMs?

**Answer:** It can provide a reproducible measurement instrument, but not independent truth. The paper discloses the acceptance amendment, reports 14/16 agreement in the weakest stratum, and stress-tests false negatives. Blinded human adjudication and false-positive estimation are the highest-priority corrections.

### External validity

**Question:** Do the results apply to deployed robots or larger models?

**Answer:** No direct deployment or model-family generalization is claimed. The tested scope is two pinned quantized 7B pipelines in synthetic, text-only security and assistive-care contexts. Sensing, actuation, operator behavior, timing, and field prevalence were not evaluated.

### Operating point rather than a model ranking

**Question:** Which generator should a platform choose?

**Answer:** The experiment alone cannot decide. Qwen has lower caution failure and higher authorized refusal under the common prompt. Selection requires target state frequencies and costs; the expected-loss equation and break-even analysis show which generator is preferred under each frequency-and-cost regime. A deployment decision would additionally require human-validated outcomes and integrated-system testing.
