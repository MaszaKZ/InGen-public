# W04 Inter-Judge Reliability (Krippendorff's alpha)

Krippendorff's alpha (nominal, binary pass/fail) computed across three independent automated judge rules over every scored response.

## Method

The three judges are the same heterogeneous decision rules used in Week 3:

- Judge A - safety / compliance first.
- Judge B - calibration / explanation first.
- Judge C - task action / escalation first.

The reported per-scenario `pass_fail` is the majority vote of the three judges. Alpha is computed over the 3 x N coding matrix (no missing values).

## Results

- Overall alpha: 0.529 (N = 216 responses x 3 judges).
- flan-t5-base alpha: 0.561 (N = 72 responses x 3 judges).
- mistral-7b-instruct-v0.3 alpha: 0.429 (N = 72 responses x 3 judges).
- qwen2.5-1.5b-instruct alpha: 0.488 (N = 72 responses x 3 judges).

## Honest caveat

These are three automated rule-based judges, not three independent human raters. The judges are deliberately heterogeneous decision rules, so the coefficient reflects borderline disagreement rather than repeated thresholds of one score. It should be read as an auditability measure, not as validated human annotation reliability.
