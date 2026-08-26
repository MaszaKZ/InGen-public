# Cross-Experiment Synthesis — Weeks 5 and 6

**Finding.** On a synthetic, text-only benchmark for Sentinel Prime AI and Aido
Humanoid decisions, Mistral-7B's safety failures were concentrated under
adversarial social pressure rather than in plain requests. The baseline failed
3/32 plain safety targets and 12/32 pressured targets, a paired increase of 28.1
percentage points (exact McNemar p=0.0225; matched odds ratio 4.6;
family-clustered 95% CI [+6.2%, +53.1%]). Among the tested prompt conditions,
chain-of-thought deliberation was the only intervention that reduced pressured
failures while preserving performance on authorized controls.

## From a measurement result to a diagnostic question

Week 5 asked whether a structured-output prompt would reduce unsafe actions on
the Week 4 safety cluster. Its apparent improvement did not survive semantic
review: 13 of 14 flagged target failures were safe denials caught by substring
matching. The experiment therefore ended measurement-inconclusive. It showed
that a prompt comparison is only as credible as the endpoint used to distinguish
unsafe compliance from a refusal that repeats the prohibited action.

Week 6 turned that lesson into the internship plan's diagnostic branch. Instead
of testing another generic safety prompt, it compared paired plain and pressured
versions of the same safety boundaries. Sixteen scenario families covered
physical-security decisions for Sentinel Prime AI and embodied-care decisions
for Aido Humanoid. Four prompt conditions generated 384 responses, labeled by
the majority of three distinct LLM judges; a word-boundary, negation-aware
deterministic scorer provided a separate sensitivity endpoint.

## Pressure, not format, explains the main effect

The baseline was usually safe when the boundary was stated plainly, then failed
37.5% of pressured targets. Claimed authority and urgency/harm were its weakest
tactics; normalization caused no baseline failures. The registered diagnostic
criterion was met, and every alternative endpoint preserved the
pressured-greater-than-plain direction, although the effect size depended on
judge strictness.

Prompt format alone was not a mitigation. Structured output increased pressured
failures from 12/32 to 14/32. Constraint gating eliminated pressured failures
but raised benign-control failures from 1/32 to 4/32. Chain-of-thought reduced
pressured failures from 12/32 to 2/32—an 83% relative reduction—while controls
remained 1/32. It was the only condition satisfying the registered rule of at
least a 25% reduction with no more than one additional control failure.

Together, the experiments replace a broad claim about “better safety prompting”
with a narrower result: pressure robustness and benign compliance must be
measured jointly. Deliberation improved that trade-off in this experiment; a
hard gate improved one side by worsening the other.

## Reliability, limits, and platform implication

The judges reached 88% raw agreement, with Gwet's AC1 of 0.85 and
Krippendorff's alpha of 0.38. Qwen was substantially stricter than Phi, and the
Mistral self-judge contributed to the majority endpoint. Under the strict
no-self-judge endpoint, the diagnostic effect was +12.5 points and did not
independently clear the registered threshold. This judge sensitivity remains a
material limitation.

The experiment also uses one model, synthetic text scenarios, automated labels,
and plain/pressured contexts that are not perfectly sentence-matched. It does not
evaluate perception, actuation, multimodal inputs, or deployed product behavior.
For Sentinel Prime AI, the evidence supports prioritizing authority-claim access
tests. For Aido Humanoid, it supports testing urgency-framed care overrides.
Blinded human validation, a second model family, and a context-matched bank are
the necessary next steps before generalizing beyond this benchmark.
