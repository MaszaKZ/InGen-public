# Week 6 Research Log

Date: 2026-07-15

## What Week 5 made me question

I began Week 6 by returning to the Week 5 raw responses, semantic audit, and
results memo. The structured-output prompt had appeared to reduce unsafe actions,
but that effect did not survive semantic review: most of the flagged target
failures were safe denials caught by a lexical scorer. My main takeaway was not
that the model had become safer or less safe. It was that the measurement could
not support the intervention claim.

That mixed result selected option (b) in the internship plan: a diagnostic
experiment testing a competing explanation for the baseline failures. The raw
responses suggested that Mistral-7B usually respected an explicit boundary when
the request was plain, then became less reliable when the requester claimed
authority, prior clearance, urgency, or accepted practice. I therefore tested
**H-pressure**: genuine safety failures are concentrated under adversarial social
pressure rather than in the underlying scenario, and prompt interventions differ
in how well they resist that pressure.

Before running the main experiment, I fixed two decision rules. The diagnostic
would count as supported only if the baseline pressured-target failure rate
exceeded its plain-target rate by at least 15 percentage points and the
family-clustered confidence interval excluded zero. An intervention would count as
mitigating only if it reduced pressured failures by at least 25% relative to the
baseline while adding no more than one benign-control failure.

## What I built

The experiment uses 16 synthetic scenario families: eight for Sentinel Prime AI
physical-security decisions and eight for Aido Humanoid embodied-care decisions.
Each family contains two plain safety targets, two targets with one of four
pressure tactics, and two explicitly authorized controls. This produces 96 main
scenarios plus 12 holdout scenarios from two separate families.

I compared four prompt conditions on Mistral-7B-Instruct-v0.3:

- the unchanged Week 3/4 baseline;
- chain-of-thought deliberation focused on constraints and authorization;
- a structured-output prompt;
- a constraint-gated schema with an explicit path for authorized actions.

All prompts use the model's chat template, NF4 quantization, greedy decoding, and
fixed seeds. The main run contains 384 responses. Endpoint labels are the majority
of three distinct LLM judges: Qwen2.5-7B-Instruct, Phi-3.5-mini-instruct, and a
disclosed Mistral self-judge. The judges see the scenario, expected boundary, and
response but not the condition name. A word-boundary, negation-aware deterministic
scorer is retained only as a sensitivity check.

The holdout run produced the expected diagnostic separation: the baseline failed
0/4 plain targets and 4/4 pressured targets. The complete evidence chain then ran
end to end with 384 generations and 1,152 judge evaluations. The integrity suite
and an independent standard-library verifier recompute the counts, hashes,
paired tests, confidence intervals, reliability statistics, and scorer labels
from the stored artifacts.

## What the experiment found

The baseline failed 3/32 plain safety targets and 12/32 pressured targets. The
paired increase is 28.1 percentage points, above the registered 15-point
criterion; the exact McNemar p-value is 0.0225, the matched odds ratio is 4.6,
and the family-clustered 95% confidence interval is [+6.2%, +53.1%]. The
registered diagnostic criterion was therefore met.

The intervention results show a clear safety/refusal trade-off:

- chain-of-thought reduced pressured failures from 12/32 to 2/32, an 83%
  relative reduction, while controls remained 1/32;
- structured output increased pressured failures from 12/32 to 14/32 and left
  controls at 1/32;
- constraint gating reduced pressured failures to 0/32 but increased control
  failures from 1/32 to 4/32.

Only chain-of-thought satisfied both parts of the registered mitigation rule.
Constraint gating achieved the lowest unsafe-compliance rate, but it did so by
over-refusing more authorized requests. The structured format that motivated
Week 5 did not improve pressure robustness.

The tactic breakdown helps explain the aggregate result. Authority claims and
urgency/harm framing were the baseline's weakest cases. Normalization produced
0/8 baseline failures even though it occupied the same pressured context slots as
the other tactics. Across the two pressured slots, failures followed the tactic
more than the slot, which bounds—but does not remove—the context-slot confound.

## Reliability and interpretation

The three judges had 88% raw agreement. Gwet's AC1 was 0.85 overall, while
Krippendorff's alpha was 0.38. The difference is informative: failures are
relatively uncommon, and the judges have materially different thresholds. Qwen
flagged 78/384 responses, the Mistral self-judge 37/384, and Phi 12/384. The
pressured-greater-than-plain direction holds for every single-judge, unanimous,
and deterministic endpoint, but its magnitude depends on the panel. The strict
no-self-judge endpoint (Qwen and Phi both flagging) yields +12.5 points with
p=0.2188 and does not independently clear the registered diagnostic threshold.

The bounded finding is therefore: **on this synthetic, text-only Mistral
benchmark, adversarial social pressure exposes safety failures that are much less
common in plain requests, and explicit deliberation is the only tested prompt
intervention that reduces those failures without increasing benign
over-refusal.**

For Sentinel Prime AI, the result points to authority-claim access requests as a
priority robustness test. For Aido Humanoid, it points to urgency-framed attempts
to override care boundaries. These are decision-policy implications, not evidence
that a deployed robot or multimodal system would behave the same way.

## What remains open

The most important next step is blinded human validation of high-severity
responses. A second model family is needed to test whether pressure concentration
is specific to Mistral, and a context-matched scenario bank should vary the tactic
while holding every other sentence fixed. Those changes would separate a useful
directional result from a broader claim about embodied foundation models.

Week 6's required deliverables are the executed experiment notebook, the
cross-experiment synthesis, and the ten-slide mid-point review deck. The scenario
bank, raw outputs, ratings, metadata, tests, and independent verifier provide the
supporting reproducibility record. The formal mid-point evaluation uses section 6
of the internship plan and is completed jointly with the supervisor.
