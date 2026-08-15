# W02 Research Questions: From Gaps to Measurable Benchmarks

Date: 2026-06-23

## Selection Rationale

The literature review surfaces three research gaps in embodied AI: calibrated deferral under uncertainty, safety-constrained decision behavior, and trust calibration through model explanations. Each gap is open, tractable with public models and data, and tied to the InGen platform anchors. This document turns each gap into a research question that can be tested with public models, scenario prompts, and human-readable scoring rubrics before any expensive robot simulation is required.

## RQ1: Uncertainty-Gated Embodied Decisions

Research question: Can a public foundation model reliably choose when to act, defer, ask for human review, or switch to a safer fallback in embodied robot scenarios with ambiguous, degraded, or shifted observations?

Hypothesis: Models will often produce plausible actions under ambiguous observations, but their self-reported uncertainty will be poorly calibrated to the severity of possible physical or operational failure. Explicit deferral options and risk labels will reduce unsafe overconfident actions.

Methodology sketch: Build 10-12 Week 3 benchmark scenarios grounded in mobile service-robot contexts: clear scene, visual ambiguity, sensor conflict, stale observation, degraded lighting/weather, and adversarial distractor. Run two or more public text or multimodal models on each scenario using a fixed prompt template. Score each response for action validity, uncertainty acknowledgement, correct defer/review behavior, and unsafe overconfidence.

Success criteria: The question is answerable if the benchmark reports a defer/review accuracy score, unsafe-overconfidence rate, and calibration proxy for each model. A positive result would show at least a 25% reduction in unsafe-overconfident responses when explicit uncertainty-gating instructions are included, without more than a 15% drop in valid task-progress decisions.

## RQ2: Safety Constraints Under Embodied Edge Cases

Research question: Do explicit safety constraints improve foundation-model decisions in embodied service-robot edge cases without causing excessive refusal or task abandonment?

Hypothesis: Constraint-aware prompting will reduce unsafe recommendations in high-severity scenarios, but may also increase overly conservative responses in medium-severity scenarios. The best-performing configuration will separate hard safety constraints from review-triggering uncertainty, instead of treating all ambiguity as a full stop.

Methodology sketch: Create paired benchmark versions for 10-12 scenarios: one with only a task goal, and one with task goal plus explicit safety constraints. Scenarios should include human proximity, privacy-sensitive sensing, false alarm risk, hazardous environment cues, operator escalation, and interrupted task execution. Score responses for safety violation, task-progress preservation, escalation correctness, and explanation specificity.

Success criteria: The question is answerable if each model has a safety violation rate, excessive-refusal rate, and task-progress preservation score. A positive result would show at least a 40% reduction in safety violations with constraint-aware prompting while keeping excessive refusal below 25% on non-critical or reviewable scenarios.

## RQ3: Trust Calibration in Service-Robot Explanations

Research question: Can model-generated service-robot explanations calibrate user trust after uncertain or mistaken behavior, rather than simply increasing confidence or apologizing generically?

Hypothesis: Generic explanations will tend to reassure users without clearly stating limits, while structured explanations that include uncertainty, evidence source, action boundary, and escalation path will better support calibrated reliance. The effect should be strongest in eldercare-style and security-style scenarios where user harm can result from overtrust.

Methodology sketch: Build 10-12 explanation scenarios in which a robot reports a detection, health/status alert, navigation interruption, or prior mistake. Ask public models to generate operator- or caregiver-facing explanations under two prompt conditions: generic helpful assistant and calibrated-trust assistant. Score each explanation for uncertainty disclosure, evidence specificity, non-overclaiming, user control, escalation guidance, and avoidance of inappropriate reassurance.

Success criteria: The question is answerable if each response receives a calibrated-trust score and an over-reassurance flag. A positive result would show at least a 30% improvement in calibrated-trust score under the structured prompt, with fewer than 10% of responses hiding uncertainty or discouraging appropriate human review.

## Week 3 Translation

The three questions will become one benchmark document with at least 30 scenarios (10-12 per cluster):

- 10-12 uncertainty-gating scenarios for RQ1.
- 10-12 safety-constraint scenarios for RQ2.
- 10-12 trust-calibration explanation scenarios for RQ3.

Each scenario should include platform context, input stimulus, acceptable behavior range, failure conditions, and severity rating. The scoring rubric should include at minimum: task validity, safety, uncertainty calibration, escalation correctness, and explanation quality.

