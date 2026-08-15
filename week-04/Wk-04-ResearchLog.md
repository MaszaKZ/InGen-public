# Wk-04 Research Log

Date: 2026-07-05

## Work Completed

- Added `week-04/run_w04_extended.py`, a Week 4 runner that reuses the Week 3 scenario bank exactly and preserves Week 3 baseline rows for `google/flan-t5-base` and `Qwen/Qwen2.5-1.5B-Instruct`.
- Ran the full 36-scenario benchmark with two prompt variants per scenario across three models: 216 scored rows total.
- Downloaded and ran the preferred third model, `mistralai/Mistral-7B-Instruct-v0.3`; the fallback `Qwen/Qwen2.5-3B-Instruct` was not needed.
- Generated `W04_Three_Model_Results.csv`, `W04_Raw_Model_Outputs.jsonl`, `W04_Failure_Cases.csv`, `W04_Failure_Analysis.md`, `W04_Reliability_Summary.md`, and `W04_Run_Metadata.json`.
- Created and executed `W04_Extended_Benchmark.ipynb`, which reports per-cluster pass scores, per-dimension aggregate scores, failure rate by severity, severity-weighted leaderboard, taxonomy coverage, and Krippendorff's alpha.

## What I Built

The Week 4 runner turns the Week 3 benchmark into a three-model comparison without changing the scenario bank. It reads the Week 3 baseline CSV for the two existing models, runs the third model against the same 36 scenarios and paraphrases, recomputes robustness, writes a combined 216-row result file, and creates row-level failure-case documentation for every failed response.

The failure taxonomy is three-level by design: top-level category, subtype, and InGen platform mapping. The four top categories are factual/task error, reasoning/calibration failure, safety/alignment failure, and robustness/over-caution failure. Each failed row also includes a likely mechanism, platform implication, and mitigation class.

After the first pass I tightened two things so the taxonomy is a principled hierarchy rather than a labelled list. First, the largest bucket (factual/task error, 101/152) was an undifferentiated catch-all, so I split it into four evidence-based subtypes — degenerate or non-response, wrong or unacceptable action, incomplete or partial action, and acceptable action with weak justification — separating the 50 degenerate flan-t5 non-responses from the substantive wrong and partial decisions of the larger models. Second, the per-failure mechanism was one templated string per failure mode; it is now scenario-specific (106 distinct mechanisms across 152 failures), naming the expected action and quoting the model's actual decision so each row states why the failure happened. Both refinements are regenerated from the existing scored rows via `python run_w04_extended.py --reclassify`, with no model re-run.

## What I Found

The preferred 7B extension model ran successfully on the local RTX 3080 Ti Laptop GPU with CPU offload. Mistral produced the best Week 4 score, but the margin over Qwen was modest under this rule-based benchmark.

| Model | Pass / Total | Pass rate | Severity-weighted score |
| --- | ---: | ---: | ---: |
| `mistral-7b-instruct-v0.3` | 31 / 72 | 43.1% | 39.3 |
| `qwen2.5-1.5b-instruct` | 29 / 72 | 40.3% | 36.0 |
| `flan-t5-base` | 4 / 72 | 5.6% | 2.1 |

Across all three models, there were 152 failed rows out of 216. Most failures were factual/task errors under the automatic rubric, but the highest product risk remains safety/alignment failures and missed escalation in severity-4 and severity-5 cases.

## Failure Taxonomy Notes

The taxonomy treats privacy, medication access, physical safety, and child-safety boundary crossings as safety/alignment failures. It treats missed caregiver, operator, clinician, or authorized-adult review as reasoning/calibration failures because the model often recognizes some risk but fails to route it correctly. Over-caution is kept as a separate robustness category because the proceed controls show a different deployment failure: needless refusal or escalation when the robot should continue a benign task.

Sentinel Prime AI is represented through the security/anomaly-triage analogs, especially the uncertain glass-break scenario. Senpai implications appear in learner-state ambiguity and routine tutoring controls. Fari implications appear in fall detection, medication access, caregiver escalation, and user-facing trust calibration.

## Reliability and Honesty Note

Krippendorff's alpha across the three automated judge rules was 0.529 overall. Per-model alpha was 0.561 for flan-t5-base, 0.488 for Qwen2.5-1.5B, and 0.429 for Mistral-7B. These are not human-rater reliability scores. They are rule-based, heterogeneous judge estimates used for reproducible auditability and borderline-disagreement tracking.

## Open Questions

- Whether Week 5 should target missed escalation or safety-boundary violations as the first intervention; both are more deployment-relevant than improving low-severity task errors.
- Whether the scoring rubric should be tightened for Mistral-style longer responses, since longer outputs can mention a correct boundary while still failing to make a crisp operational decision.
- Whether to add a small expert-review subset before the Week 6 midpoint review to validate the automated taxonomy on severity-4 and severity-5 cases.

## AI Assistance Note

AI assistance was used to structure the Week 4 runner, notebook, failure taxonomy, and research-log prose. All benchmark scores, failure counts, model-selection status, and reliability values come from the generated Week 4 CSV and metadata artifacts.
