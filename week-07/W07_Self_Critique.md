# Week 7 Self-Critique — Peer-Review Preparation for the Research Note

This is the structured self-critique the internship plan requires alongside the
Week 7 research note: the strongest claim, the claim a reviewer is most likely
to challenge, the result a careful reviewer would question, and the related
work the note should engage with more deeply.

## The single strongest claim

The cross-generator trade-off under the common baseline. Its evidence chain is
the cleanest in the program: the prompt is byte-identical before native chat
rendering (verified by rendered-prompt hashes), scenarios and seeds are fully
paired, the effects are among the largest reportable on this design (Cohen's h
of 0.90–1.22; every one of the 88 discordant plain-caution pairs and all 30
discordant control pairs point the same direction), the judge panel is 96.3%
unanimous with Fleiss kappa 0.953, and the registered family-clustered
intervals exclude zero for all three contrasts. A reviewer can attack the
bank's realism or the judge, but not the internal comparison: whatever these
scenarios measure, the two generators sit on opposite corners of it.

## The claim most likely to be challenged

That the outcome labels are trustworthy at all, given that the judge panel was
accepted through a protocol amendment after five single-shot holdouts each
failed a gate. The steelman: "you set an acceptance standard, failed it five
times, then changed the standard — the measurement is unproven exactly where
it matters, on unsafe compliance." The honest answer has three parts. First,
the failures were not five independent verdicts against the panel: rounds 3–5
each failed on exactly one borderline row against a zero-miss floor, with a
different judge subset missing it each time, and the pre-registered ceiling
analysis showed that a 28-row single-shot with zero-miss floors on 4–6-row
strata certifies even a strong panel with probability well below one — the
repeated failures are the expected behavior of that certification design.
Second, the amendment was disclosed and pre-committed rather than silent: the
pooled fresh record (binary 80/83, CP95 [0.898, 0.993]) is stated with the
pooling-across-panels caveat, and the recorded failures stand. Third, the
weakness is quantified, not waved off: pooled unsafe-compliance detection on
declares-then-hedges responses is 14/16 (CP95 lower bound 0.617), and the note
carries that stratum as the caveat most directly qualifying the caution-rate
results. What would fully retire the objection is blinded human validation of
the panel on precisely that stratum — the highest-value next measurement step.

## The result a careful reviewer would question

Plain caution failing more than pressured caution for both generators (88.8%
vs 43.1% for Mistral; 33.8% vs 3.2% for Qwen), which reverses the Week 6
within-Mistral direction. Candidate explanations, in decreasing order of
concern: (1) authorization-salience asymmetry in the bank — pressured variants
necessarily verbalize the contested authorization ("the supervisor already
cleared this"), which may cue refusal heuristics, while plain variants present
the same boundary quietly, so the comparison may partly measure cue salience
rather than pressure; (2) tactic text acting as a generic adversarial marker
that instruction-tuned models have learned to refuse; (3) judge sensitivity
differing across the two subtypes' response styles (hedged responses cluster
in caution scenarios). Explanation (1) is the serious one because it is a
design property, not a model property. The resolving analysis is available
with existing data: the bank pairs each pressured scenario to a plain variant
(`paired_plain_id`), so a within-pair contrast restricted to pairs whose plain
variant states the missing authorization explicitly would separate salience
from pressure; a small blinded human audit of plain-caution panel labels would
address (3). Until then the note claims only that the pressure-effect sign is
bank-sensitive, not that pressure is protective.

## The related work to engage more deeply

Lekeufack et al. (2023), "Conformal Decision Theory: Safe Autonomous Decisions
from Imperfect Predictions" (from the Week 2 review, cluster B). The note
currently cites it as background for the measurement gap, but it deserves
structural engagement: the central Week 7 finding is a two-error trade-off
(unsafe compliance vs benign over-refusal) that generator choice moves along,
and conformal decision calibration is precisely a framework for choosing an
operating point on such a trade-off with coverage guarantees. A deeper
treatment would recast the mitigation rule's fixed thresholds (≥25% relative
reduction, ≤3.125-point control cost) as one ad-hoc operating point and ask
whether a calibrated deferral action ("escalate to operator") could dominate
both generators' corner solutions — which is also the natural bridge to the
Week 8 PIC 2.0 application framework.
