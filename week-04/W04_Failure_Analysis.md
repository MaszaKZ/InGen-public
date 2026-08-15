# W04 Failure Analysis: Three-Model Benchmark

Date: 2026-07-05

## Third-Model Selection

- Preferred model: `mistralai/Mistral-7B-Instruct-v0.3`.
- Selected model: `mistralai/Mistral-7B-Instruct-v0.3`.
- Fallback used: `False`.

## Severity-Weighted Leaderboard

| Rank | Model | Pass / Total | Pass rate | Severity-weighted score |
| --- | --- | ---: | ---: | ---: |
| 1 | `mistral-7b-instruct-v0.3` | 31 / 72 | 43.1% | 39.3 |
| 2 | `qwen2.5-1.5b-instruct` | 29 / 72 | 40.3% | 36.0 |
| 3 | `flan-t5-base` | 4 / 72 | 5.6% | 2.1 |

The severity-weighted metric is `100 * (1 - sum(severity * failed) / sum(severity))`. This is the primary comparison metric because deployment risk is not uniform: a severity-5 failure on eldercare, patrol, or security triage carries materially more operational risk than a severity-1 nuisance failure.

## Three-Level Failure Taxonomy

The top level is a four-way MECE partition. The `factual/task error` category is split into four evidence-based subtypes so the largest bucket is no longer an undifferentiated default: a degenerate small-model non-response, a wrong action, a partial action, and an acceptable action that failed only on justification are distinct deployment problems.

| Top category | Subtypes | Platform mapping |
| --- | --- | --- |
| factual/task error | degenerate or non-response; wrong or unacceptable action; incomplete or partial action; acceptable action, weak justification; hallucination of authorization or certainty | Aido Rover task selection, Fari caregiver workflow, Senpai tutoring step control |
| reasoning/calibration failure | missed escalation; overconfident uncertainty handling | uncertainty-gated Aido Rover and Fari decisions; Sentinel Prime AI anomaly triage analogs |
| safety/alignment failure | unsafe output; generic refusal | privacy, medication, child-safety, and physical-risk boundaries |
| robustness/over-caution failure | excessive refusal | proceed-control cases where benign action should continue, especially Senpai routine tutoring and Fari self-requests |

## Aggregate Failure Counts

- Failed rows: 152 / 216.
- Failure modes: {'calibration_failure': 2, 'excessive_refusal_or_over_caution': 11, 'missed_escalation': 15, 'task_error': 101, 'unsafe_or_policy_violating_output': 23}.
- Taxonomy categories (top level): {'factual/task error': 101, 'reasoning/calibration failure': 17, 'robustness/over-caution failure': 11, 'safety/alignment failure': 23}.
- Failure severity distribution: {'1': 9, '2': 13, '3': 46, '4': 54, '5': 30}.
- Failures by model: {'flan-t5-base': 68, 'mistral-7b-instruct-v0.3': 41, 'qwen2.5-1.5b-instruct': 43}.

## Taxonomy Subtype Breakdown

| Top category | Subtype | Count |
| --- | --- | ---: |
| factual/task error | degenerate or non-response | 50 |
| factual/task error | incomplete or partial action | 34 |
| factual/task error | acceptable action, weak justification | 10 |
| factual/task error | wrong or unacceptable action | 6 |
| factual/task error | hallucination of authorization or certainty | 1 |
| reasoning/calibration failure | missed escalation | 14 |
| reasoning/calibration failure | overconfident uncertainty handling | 2 |
| reasoning/calibration failure | hallucination of authorization or certainty | 1 |
| robustness/over-caution failure | excessive refusal | 11 |
| safety/alignment failure | unsafe output | 21 |
| safety/alignment failure | hallucination of authorization or certainty | 2 |

## Per-Failure Documentation

Every failed row is documented in `W04_Failure_Cases.csv` with failure mode, likely mechanism, InGen platform implication, and mitigation. Each mechanism is scenario-specific: it names the expected action and quotes the model's actual decision, so it states *why* the failure happened rather than only restating that it did. The analysis is row-level rather than example-only so the taxonomy remains auditable against the benchmark outputs.

## Deployment Implications

- Sentinel Prime AI analogs are most exposed when a model collapses uncertain security evidence into either confirmed intrusion or no action without review.
- Senpai is most exposed to over-caution and learner-state errors: unnecessary refusal interrupts learning, while missed clarification advances on misunderstood concepts.
- Fari is most exposed to privacy, medication-access, and caregiver-escalation failures where a plausible language response can cross an authorization boundary.
- Aido Rover is most exposed to severity-weighted physical risk when stale maps, sensor conflict, or degraded perception are treated as normal routing conditions.

## Reliability Caveat

Krippendorff's alpha is recomputed across the same three automated judge rules used in Week 3. These judges are rule-based and heterogeneous; they are not independent human raters. The coefficient is therefore an auditability and borderline-disagreement measure, not a claim of human annotation reliability.

## AI Assistance Note

AI assistance was used to structure the taxonomy and generate reproducible analysis boilerplate. Reported scores and counts are computed from the benchmark CSV.
