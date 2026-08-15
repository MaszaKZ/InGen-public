# W03 Inter-Judge Reliability (Krippendorff's alpha)

Krippendorff's alpha (nominal, binary pass/fail) computed across three independent judge seeds over every scored response.

## Method

Three judges independently code each response as pass (1) or fail (0) from the rubric features, using different decision rules:

- Judge A - safety / compliance first.
- Judge B - calibration / explanation first.
- Judge C - task action / escalation first.

The reported per-scenario `pass_fail` is the majority vote of the three judges. Alpha is computed over the 3 x N coding matrix (no missing values).

## Results

- Overall alpha: 0.574 (N = 144 responses x 3 judges).
- flan-t5-base alpha: 0.561 (N = 72 responses x 3 judges).
- qwen2.5-1.5b-instruct alpha: 0.488 (N = 72 responses x 3 judges).

## Honest caveat

These are three automated rule-based judges, not three independent human raters. The plan's literal requirement - Krippendorff's alpha across judge seeds for any human-graded dimension - is reported here as the closest rigorous analog because no rubric dimension in Week 3 is human-graded. The judges are deliberately heterogeneous decision rules (not three thresholds of one score), so the coefficient reflects genuine borderline disagreement rather than a tautological 1.0. Human and/or LLM-judge inter-rater reliability on the highest-severity scenarios is a Week 4+ extension.
