# Wk-03 Research Log

Date: 2026-06-30

## Work Completed

- Designed `W03_Scenario_Bank.yaml`, a 36-scenario text benchmark: 30 caution scenarios (10 per Week 2 research question) plus 6 proceed-mode control scenarios that test the opposite failure — over-conservatism.
- Wrote `W03_Benchmark_Design.md`, including the methodology, scenario-bank structure, action-aware 1-5 scoring rubric, baseline rationale, headline results, reliability, and limitations.
- Added `run_w03_baseline.py`, a reproducible runner that validates the bank, generates responses, scores them on six dimensions, codes pass/fail with three independent judge seeds, and computes Krippendorff's alpha.
- Ran the full baseline for `google/flan-t5-base` and `Qwen/Qwen2.5-1.5B-Instruct`: 144 scored rows in `W03_Baseline_Results.csv`, raw generations in `W03_Raw_Model_Outputs.jsonl`, and inter-judge reliability in `W03_Reliability_Summary.md`. Mistral-7B remains reserved for Week 4.

## What I Built

The benchmark uses platform-specific service-robot scenarios rather than generic NLP prompts. Each scenario names Aido Rover, Fari, or Senpai; maps to one or more PIC 2.0 model classes; defines expected behavior, failure conditions, and severity (1 nuisance to 5 safety-critical); and includes a paraphrased variant for robustness testing. The scoring rubric turns the Week 2 research questions into measurable dimensions: task accuracy, robustness, calibration, safety, escalation correctness, explanation quality, and failure mode.

The most important design change this week was adding proceed-mode control scenarios. In the first draft every scenario rewarded caution, which meant a model that always deferred or escalated would have scored well and the excessive-refusal rates that RQ1 and RQ2 explicitly call for could not be measured. The controls (clear corridor, benign self-request, routine correct decision) make the benchmark distinguish a model that reasons about uncertainty from one that reflexively refuses.

## What I Found

The full baseline exposed a clear tier difference. Under the action-aware rubric and 3-judge majority vote, `flan-t5-base` passed 5.6% of variants (4/72) and usually produced degenerate outputs that echo the `Decision` label, while `Qwen2.5-1.5B-Instruct` passed 40.3% (29/72) with stronger calibration, escalation, and explanation language. The control scenarios were decisive: Qwen passed 11/12 proceed controls, so its caution-scenario passes reflect genuine uncertainty reasoning rather than blanket refusal. Its main weakness was the opposite of over-caution — 12 unsafe or policy-violating outputs on severity 4-5 caution scenarios (e.g., recommending action where deferral or a hard safety boundary was required).

The hardest scenario type to design was trust calibration after a robot made an uncertain or mistaken decision (RQ3). It is easier to label an action as safe or unsafe than to decide whether an explanation calibrates trust correctly. A strong explanation must avoid two opposite failures: over-reassuring the user into blind trust and over-apologizing in a way that destroys appropriate reliance. The RQ3 control scenarios were the hardest to score automatically, because the correct behavior there is confident explanation, so the usual reward for expressed uncertainty has to be inverted.

## Reliability and Honesty Note

Krippendorff's alpha across the three judge seeds was 0.574 overall (flan 0.561, Qwen 0.488) — moderate agreement, computed correctly as a single dataset-level coefficient over the 3 x N coding matrix, not a per-row flag. The three judges are heterogeneous decision rules (safety-first, calibration-first, task-first), so this is genuine agreement across independent judges rather than three runs of the same judge. They are automated judges, not independent human raters: no Week 3 dimension is human-graded, so this is the closest rigorous analog to the plan requirement, and human/LLM-judge reliability on high-severity scenarios is deferred to Week 4+.

## Open Questions

- Whether Week 4 should add a 7B-class model first or add multimodal image prompts first.
- Whether external human or LLM-judge rating is feasible for the highest-severity scenarios before the Week 6 midpoint review.
- Whether the failure taxonomy should treat privacy violations and physical safety violations as separate top-level failure categories, and whether over-caution deserves its own top-level branch alongside over-confidence.

## AI Assistance Note

AI assistance was used to draft scenario variants, maintain rubric consistency, refine the scoring code, and generate the reproducible runner. Final claims remain tied to public-safe Week 1-2 deliverables or labeled as benchmark design choices, and all reported numbers come from the committed CSV and reliability summary.
