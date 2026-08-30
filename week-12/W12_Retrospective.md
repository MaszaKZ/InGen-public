# Research Retrospective

## Most Important Finding and Why It Was Surprising

The most important finding is that generator choice set a two-error operating point rather than a simple safety ranking. Under the byte-identical common prompt, Qwen reduced plain unsafe-compliance failure by 55.0 percentage points and pressured failure by 40.1 points relative to Mistral, yet increased refusal of authorized controls by 18.8 points. A reader who looked only at caution scenarios would judge Qwen safer; one who looked only at authorized controls would judge Mistral safer. The joint result changes the decision question from “Which model is safest?” to “Which error balance fits the target loss model?”

The result was surprising for two reasons. First, both generators failed quiet, unpressured boundary requests more often than adversarially pressured ones. Pressure cues sometimes acted as refusal cues, so the benchmark’s neutral requests exposed more unsafe compliance than its conspicuous attacks. Second, prompt interventions did not transfer consistently. Deliberation passed the registered observed-data rule only for Qwen, while constraint gating helped one endpoint for Qwen but worsened outcomes for Mistral. These patterns undermine any assumption that an intervention name carries a stable effect across generator stacks.

The practical lesson is to evaluate unsafe compliance, authorized-control refusal, and defer behavior together. A system that refuses everything is not safe in an operational sense, and a system that escalates everything merely replaces refusal cost with operator load and delay. Model selection therefore requires declared state frequencies and error costs, not a context-free leaderboard.

## Weakest Part of the Paper and What Would Strengthen It

The weakest part is measurement validity. All 14,400 labels come from an LLM judge panel accepted through a disclosed pooled-evidence amendment. Agreement is high, and agreement in the weakest unsafe-compliance validation stratum was 14/16, but agreement measures consistency, not truth. The conditional false-negative analysis shows that the three primary contrast directions survive specified measurement stress while the only mitigation pass does not; however, it does not estimate false positives or form a joint uncertainty region.

Blinded human adjudication would strengthen the paper most. Reviewers should independently label a stratified sample containing both error directions, every generator-condition cell, borderline cases, and the three unparsed outcomes. The study should report human-panel agreement, judge sensitivity and specificity, adjudication rules, and how corrected labels change clustered contrasts. A held-out test set should remain sealed until prompts, judge rules, and decision thresholds are fixed.

External validity is the second weakness. The bank is synthetic and text-only, with two quantized 7B generators and two platform contexts. It contains no sensing, actuation, operator behavior, timing, or field prevalence. The paper therefore supports a benchmark result and an evaluation method, not deployment assurance.

## Six-Month Follow-Up Experiment

The follow-up should be a preregistered study that uses three generators and spans security, assistive-care, and a third operational domain. It should retain matched authorized controls while adding a scored defer action. A registered two-by-two salience-by-pressure factorial should counterbalance pressure tactic, prerequisite salience, wording, and setting within each scenario family, eliminating the salience-pressure confound in the current bank.

Power and uncertainty should be defined at the family level. The design should increase the number of independent families, reserve a held-out test set, and use family-clustered intervals plus a joint bootstrap distribution for expected-loss comparisons. Blinded human adjudication should establish the primary endpoint; the LLM panel can remain as a lower-cost secondary instrument whose errors are measured against humans.

Before data collection, the protocol should declare model revisions, native templates, decoding seeds, exclusion rules, minimum unsafe-compliance improvement, maximum authorized-refusal increase, and maximum unnecessary-defer rate. It should also declare loss grids for the three platform contexts rather than selecting a cost ratio after results are known. Success would mean identifying at least one operating point whose advantage survives clustered uncertainty, human-label correction, the held-out test set, and the registered measurement-stress analysis.
