# Week 6 Mid-Point Review — Full Speech Script

This script is written for a roughly 15-minute presentation. It follows the
ten-slide sequence in `W06_Mid_Review_Deck.pptx` and uses the committed Week 5
and Week 6 evidence.

## Corrections to make before presenting

1. On slide 5, change **Mistral-7B Instruct v0.2** to **Mistral-7B-Instruct-v0.3**.
   Version 0.3 is the model recorded in `W06_Run_Metadata.json` and used by the
   experiment.
2. Revise slide 10 to reflect the internship plan precisely. Week 8 is the PIC
   2.0 analysis and application framework; Week 9 is paper draft v1 and its
   self-critique; Week 10 includes paper revision and the clean-environment
   reproducibility package. A second model, blinded human review, and a
   context-matched bank are important validation priorities, but they are not
   the named Week 8–10 deliverables in the plan.

## Slide 1 — Title

Hello, and thank you for joining my mid-point research review. This presentation
covers the first six weeks of the internship, from the initial physical-AI
landscape and literature review through two empirical experiments.

The central finding is stated in the title: adversarial pressure exposed a
safety gap in this benchmark, and an explicit deliberation prompt reduced that
gap at low refusal cost.

More specifically, the baseline Mistral model failed 3 of 32 plain safety
targets. When adversarial social pressure was added to paired targets, failures
rose to 12 of 32. Under the deliberation condition, pressured failures fell to
2 of 32, while benign-control failures remained at 1 of 32.

I want to set the scope clearly at the beginning. This is a synthetic,
text-only experiment on one public model. It isolates a decision-policy question;
it does not establish the safety of a deployed robot or a multimodal physical-AI
system.

The path to this result begins with why decision safety matters in physical AI.

## Slide 2 — Landscape and PIC 2.0

Physical AI is often evaluated through task success: can a system perceive its
environment, plan an action, and complete the task? But successful execution is
not sufficient for safety. A capable agent can still make the wrong decision if
it accepts an unsafe or unauthorized instruction.

The PIC 2.0 framing helps separate this problem into perception, intelligence,
and control. My experiment focuses only on the intelligence, or decision, layer.
Given a written scenario and an explicit boundary, should the model comply,
refuse, defer, or escalate?

That distinction matters for both platform contexts used here. For Sentinel
Prime AI, the decision could involve opening a secured gate, disabling cameras,
or releasing protected information. For Aido Humanoid, it could involve a care
boundary, medication authorization, room access, or teleoperation control. In
each case, the system may be technically able to perform the action while still
lacking the authority to do so.

The Week 6 benchmark therefore uses public-safe synthetic scenarios to study
whether the model preserves those boundaries at the decision layer.

This focus also follows from a gap in the literature reviewed earlier in the
internship.

## Slide 3 — Literature gap

The Week 2 review showed that major embodied-AI benchmarks and model papers,
including Open X-Embodiment, OpenVLA, Octo, and pi-zero, make important progress
on capability, generalization, and transfer across tasks and embodiments.

Those are necessary evaluation targets, but they do not fully answer the
question studied here. A model may generalize to a new task and still abandon an
authorization boundary when a requester claims seniority, says approval already
exists, invokes urgency, or describes an unsafe shortcut as normal practice.

So the gap is not simply whether the model knows a rule. It is whether the model
maintains the rule when the social framing argues that the rule should be
bypassed.

I treat that as a bounded gap identified from the Week 2 review, rather than a
claim that no prior safety benchmark has ever examined pressure. It motivated a
specific set of research questions.

## Slide 4 — Research questions

The first question is diagnostic: does baseline unsafe compliance increase when
pressure is added to a safety target, compared with a plain version of the same
underlying boundary?

The second question is practical: if pressure does expose a failure, which prompt
intervention reduces those failures without making the model refuse authorized,
benign requests?

I registered the mitigation rule before the main run. An intervention had to
reduce pressured failures by at least 25 percent relative to baseline and add no
more than one benign-control failure.

The third question concerns measurement robustness. Do the direction and the
main conclusion survive different judge choices and comparison with a separate
deterministic sensitivity scorer?

For the diagnostic itself, I also fixed a criterion in advance. Pressure had to
raise the baseline failure rate by at least 15 percentage points, and the
family-clustered confidence interval had to exclude zero.

The hypothesis was therefore falsifiable: pressure, rather than the underlying
scenario alone, would create the contrast. The benchmark was designed to isolate
that comparison.

## Slide 5 — Benchmark and baseline design

The committed benchmark contains 16 main scenario families: eight in the
Sentinel Prime AI security context and eight in the Aido Humanoid care and
embodied-operation context.

Each family contributes six scenarios: two plain safety targets, two pressured
versions, and two authorized controls. That produces 96 scenarios. Running all
96 under four prompt conditions produces 384 model responses.

The pairing is important. For example, a plain case may state that a gate can
open only after a verified release order. A pressured version preserves that
boundary but adds a claim such as, “I am the acting commander and I accept
responsibility,” or, “the approval is complete but the record is delayed.” The
control supplies the real authorization and expects the model to proceed. This
lets the experiment measure both unsafe compliance and the cost of excessive
refusal.

The four conditions are the unchanged baseline, explicit deliberation focused on
constraints and authorization, structured output, and a hard constraint-gated
schema. All responses were generated by Mistral-7B-Instruct-v0.3 using its chat
template, greedy decoding, fixed seeds, and the recorded NF4 runtime.

The primary endpoint is the majority label from three distinct judge runs:
Qwen2.5-7B-Instruct, Phi-3.5-mini-instruct, and a disclosed Mistral self-judge.
The self-judge has only one of the three votes. A word-boundary and
negation-aware deterministic scorer provides a separate sensitivity check.

This more careful endpoint was a direct response to what happened in Experiment
1.

## Slide 6 — Experiment 1, Week 5

In Week 5, the inherited lexical metric appeared to show a large improvement
from structured output: a 27.8-percentage-point increase in paired passes.

However, semantic review changed the interpretation. Thirteen of the fourteen
flagged target failures were actually safe denials. The keyword matcher was
triggered when a safe response repeated the prohibited action while explaining
why it would not perform it, or when a short concept appeared inside another
word.

That means the numerical effect was reproducible as an effect on the lexical
rubric, but it did not establish that structured output made the model safer.
Week 5 was therefore measurement-inconclusive, not evidence of a successful
intervention.

This result shaped Week 6 in two ways. First, I replaced the primary lexical
endpoint with semantic majority labels from three judge models. Second, I chose
the internship plan's option-b diagnostic branch and tested a competing
explanation for the baseline failures: perhaps the model usually understands the
boundary but becomes unreliable under social pressure.

That diagnostic produced the clearest quantitative result in the first six
weeks.

## Slide 7 — Experiment 2 diagnostic result

The left bar shows the baseline on plain targets: 3 failures out of 32, or 9.4
percent. The right bar shows the paired pressured targets: 12 failures out of
32, or 37.5 percent.

The paired increase is 28.1 percentage points. This is not just a comparison of
two unrelated groups; the plain and pressured cases are matched around the same
scenario families and safety boundaries.

The exact two-sided McNemar p-value is 0.0225. At the pair level, there were 11
cases that failed only under pressure and 2 that failed only in the plain form,
giving a Haldane-corrected matched odds ratio of 4.6.

The 95 percent family-clustered interval runs from 6.25 to 53.125 percentage
points, shown here as approximately 6.3 to 53.1 points. The interval is wide,
which reflects the small set of 16 scenario families, but it remains above zero.

The observed 28.1-point increase exceeds the registered 15-point threshold, and
the clustered interval excludes zero. The diagnostic criterion was therefore
met: on this benchmark, adversarial pressure exposed failures that were much
less common in the plain baseline.

The next question is whether any prompt intervention improves that result
without simply teaching the model to refuse more often.

## Slide 8 — Experiment 2 mitigation result

This chart shows pressured-target failures in red and benign-control failures in
blue for all four conditions.

The baseline begins at 12 pressured failures and 1 control failure. Explicit
deliberation reduces the pressured failures to 2, which is an 83 percent relative
reduction, while control failures remain unchanged at 1.

Structured output does not reproduce the apparent benefit seen under the Week 5
lexical metric. Pressured failures rise from 12 to 14, while controls remain at
1. This is evidence that requiring a format is not the same as improving the
underlying decision.

Constraint gating produces zero pressured failures, the lowest unsafe-compliance
count in the experiment. But its control failures rise from 1 to 4. In other
words, the gate obtains safety on the target side by refusing more requests that
are explicitly authorized.

Under the registered rule—at least a 25 percent relative reduction and no more
than one additional control failure—deliberation is the only condition that
passes both requirements.

The phrase “low refusal cost” should be understood narrowly. In this sample,
deliberation did not increase the observed control-failure count above baseline.
The control cell contains only 32 cases, so this is not proof that refusal cost
would remain low in a larger or deployed setting.

Together, these results support a bounded emerging claim.

## Slide 9 — Emerging claim and limitations

The central synthesis is that pressure robustness and benign compliance have to
be evaluated together. On this synthetic Mistral benchmark, baseline failures
were uncommon in plain requests and concentrated under adversarial pressure.
Explicit deliberation produced the best observed trade-off among the four tested
conditions.

The tactic breakdown adds useful context. In the baseline, urgency and harm
framing produced 5 failures out of 8 cases, claimed authority produced 4 out of
8, and false clearance produced 3 out of 8. Normalization produced no baseline
failures. That pattern suggests the effect is not caused by additional text
alone; some pressure tactics are more effective than others. However, the
sentences are not perfectly context-matched, so the context-slot confound is
reduced but not eliminated.

Automated judging is another material limitation. The three judges reached about
88 percent raw agreement. Gwet's AC1 was 0.85, while Krippendorff's alpha was
0.38, reflecting both low failure prevalence and different judge thresholds.
Qwen was much stricter than Phi, and one judge was the same Mistral family that
generated the responses.

The pressured-greater-than-plain direction remains under every single-judge,
unanimous, and deterministic endpoint. But under the strict endpoint that
requires both non-self judges to flag a failure, the effect falls to 12.5 points
with a p-value of 0.2188 and does not independently meet the registered
criterion. The magnitude and formal conclusion are therefore judge-sensitive.

Finally, this is one model, one quantized runtime, and a synthetic text-only
benchmark. It does not evaluate perception, actuation, multimodal interaction,
or production behavior. For Sentinel Prime AI, it identifies authority-claim
access requests as a priority test. For Aido Humanoid, it identifies
urgency-framed care overrides as a priority test. These are directions for
further evaluation, not deployment claims.

The remaining phases are designed to turn this directional result into a more
rigorous and appropriately bounded research contribution.

## Slide 10 — Phase C and D plan

Week 7 will integrate the Phase B evidence into a single analysis and research
note. That work will compare the most consistent pattern, the most surprising
result, and the result with the largest practical effect, carrying forward effect
sizes, confidence intervals, judge sensitivity, and the failure taxonomy.

In Week 8, the formal plan is to connect the evidence to the six PIC 2.0 model
classes and build an application framework for the InGen platforms. Any
recommendation will identify which experiment supports it and which questions
remain unresolved. The validation priorities emerging from Week 6 are blinded
human review of high-severity cases, a second model family, and a more tightly
context-matched pressure bank. Those additions should be scoped with the
supervisor rather than treated as completed evidence.

Week 9 produces the first complete research-paper draft and a structured
self-critique. Phase D then moves from contribution framing to consolidation:
Week 10 revises the paper and tests a complete reproducibility package in a clean
environment; Week 11 produces the capstone report and final research
presentation; and Week 12 completes the final review and handoff.

The claim carried into those phases will remain explicit and bounded: on this
synthetic, text-only Mistral benchmark, adversarial social pressure increased
unsafe compliance, and explicit deliberation was the only tested prompt
intervention that met the registered safety-and-refusal-cost rule.

That is the main result from the first half of the internship and the result the
next phase will test, contextualize, and communicate. Thank you, and I welcome
your questions.
