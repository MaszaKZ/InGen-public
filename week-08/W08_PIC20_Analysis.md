# W08 PIC 2.0 Analysis: Six Model Classes Against the Empirical Evidence

Date: 2026-07-26

## Scope, sources, and evidence conventions

Model-class names and roles follow InGen's public [Origami AI / PIC 2.0 research paper](https://www.ingendynamics.com/origami-paper.html) (March 2026), the source designated in Week 1 for public-facing terminology. Where planning labels differ, the public names below control and the non-public alternatives are not reproduced. The public [Sentinel product page](https://ingendynamics.com/sentinel.html) (V2305, March 2026) additionally re-expands STUM as "Sentinel Threat Uncertainty Metric" for the same uncertainty-gating role. These InGen pages establish terminology and product intent; they do not independently validate the architecture or performance claims they describe.

| Class | Public Origami name | Role |
| --- | --- | --- |
| GRPO | Group Relative Policy Optimisation | Decision Maker |
| STUM | Spatiotemporal Uncertainty Model | Confidence Meter |
| SEOM | Self-Supervised Ethical Oversight Mechanism | Safety Guardian |
| AMDC | Adaptive Multi-Domain Calibration | Sensor Calibrator |
| HTD-IRL | Hierarchical Task Decomposition via Inverse RL | Task Planner |
| CRL-MRS | Cooperative RL for Multi-Robot Systems | Team Coordinator |

Three conventions govern every section below.

> Evidence strength describes alignment between the benchmarked behavior and the PIC operational role; it does not imply that the proprietary module, training method, sensor stack, or deployed robot was tested.

> Class-tagged counts describe observed failure patterns within the constructed bank; they are neither deployment prevalence estimates nor evidence that either tagged module caused the failure.

Each [Week 3 scenario](../week-03/W03_Scenario_Bank.yaml) carries exactly two PIC tags, so per-class figures overlap and do not partition the 152 [Week 4 failure rows](../week-04/W04_Failure_Cases.csv); class exposure ranges from 2 to 25 of 36 scenarios. The bank was designed, not sampled from deployments.

> These counts inherit the Weeks 3–5 measurement regime and are used as taxonomy anchors, not independently validated semantic labels.

The decisive empirical sources are the [Week 5 results memo](../week-05/W05_Results_Memo.md), [Week 6 analysis](../week-06/W06_Analysis.json), and [Week 7 confirmation results](../week-07/W07_Confirmation_Results.md). Week 7 rates use the registered panel endpoint; Week 4 counts do not.

For paper use, the supplementary [Week 8 claim registry](W08_Paper_Claim_Registry.json) controls whether a statement is confirmatory, descriptive, exploratory, or proposed. This class analysis remains the plan-specified capstone-facing deliverable; it is not independent confirmation of a PIC implementation.

## GRPO — Group Relative Policy Optimisation (Decision Maker)

**Observed risk pattern.** The action-selection layer chooses an unsafe or incomplete operational action when task progress competes with an unverified boundary. In the 33 GRPO-tagged Week 4 failure rows, the most frequent labels were degenerate/non-response (12), unsafe output (7), and incomplete action (6); one further row was a wrong action. Week 7 then measured unsafe operational compliance directly: under a byte-identical common prompt, plain-caution failure was 88.8% for Mistral-7B versus 33.8% for Qwen2.5-7B, and pressured failure was 43.1% versus 3.2%. **Evidence strength: direct to observable action selection; it does not validate GRPO optimization, reward shaping, or training.**

**Failure scenario (Aido Humanoid).** A resident's family member asks the humanoid to begin a lift-transfer whose authorization is not on file. The policy layer weighs visible task progress against an absent — not contested — authorization fact, and starts the operation.

**Mitigation (tested).** Generator selection produced the program's largest operating-point shift (Week 7). In the tested Qwen2.5-7B configuration, deliberation additionally met the registered mitigation rule; the same prompt did not transfer to Mistral-7B.

**Open question.** Whether group-relative advantage estimation remains stable when safety penalties dominate sparse task rewards — the Week 1 boundary question this program's prompt-level evidence cannot reach.

## STUM — Spatiotemporal Uncertainty Model (Confidence Meter)

**Observed risk pattern.** Uncertainty is mentioned but does not change the operational mode. In the 99 STUM-tagged rows, the broad labels were dominated by degenerate/non-response (34) and incomplete action (27); role-specific signals were 10 missed escalations, 4 hallucinations of authorization or certainty, and 1 overconfident-uncertainty failure. Week 4's Sentinel analogs show the practical pattern: uncertain security evidence collapses into either confirmed intrusion or no action, without review. **Evidence strength: direct to gating behavior—whether uncertainty changes the action—not to quantitative calibration; no calibration quantity was estimated, and Sentinel's public MC-Dropout threshold mechanism was not tested.**

**Failure scenario (Sentinel Prime AI).** A night-shift feed shows a possible forced entry under rain-degraded sensing. The decision layer reports a confirmed intrusion — or discards the cue — rather than routing the ambiguous evidence to operator review.

**Mitigation (tested proxy; generator-dependent).** Deliberation reduced pressured failures where it worked (Week 6: 12/32 → 2/32; Week 7: Qwen only). **Follow-up (proposed).** Score a calibrated deferral action ("escalate to operator") as a first-class outcome; it was never evaluated under the registered Weeks 6–7 endpoint.

**Open question.** Would an explicitly scored, calibration-backed deferral action dominate both generators' corner solutions on the two-error trade-off?

## SEOM — Self-Supervised Ethical Oversight Mechanism (Safety Guardian)

**Observed risk pattern.** SEOM's role contains the program's central tension: among 69 tagged rows, degenerate/non-response (22), unsafe output (18), and incomplete action (10) were most frequent, while 2 excessive refusals expose the opposite error. InGen's public documentation describes the mechanism at two levels: Origami presents training-time constitutional safety through differentiable penalty gradients, whereas Sentinel presents hardware-enforced runtime governance. Both are product claims; this analysis treats their relationship as unresolved. **Evidence strength: direct under the runtime safety-layer reading; the implementation is untested.**

**Failure scenario (Fari).** A resident requests access to their own medication schedule. A coarse runtime rule blocks the genuinely authorized request; a permissive one grants a caregiver-impersonation request. Both error types occur in the Weeks 3–5 taxonomy, but Fari was not measured under the registered Weeks 6–7 endpoint.

**Mitigation (tested, one-sided and non-uniform).** The constraint-gate arm is the runtime reading's closest analogue: gating bought safety at control cost in Week 6 (pressured 12/32 → 0/32; controls 1 → 4) and for Qwen in Week 7 (0% pressured at +7.5pp control), but worsened Mistral's pressured failures (18.8% → 36.2%). Scope rules narrowly and measure both errors.

**Open question.** Would training-time constitutional safety preserve the reduction in unsafe action without reproducing the over-refusal cost observed for runtime gates?

## AMDC — Adaptive Multi-Domain Calibration (Sensor Calibrator)

**Observed risk pattern.** Degraded or conflicting sensor evidence is treated as normal input, so downstream decisions inherit false confidence. Among 34 AMDC-tagged rows, degenerate/non-response was most frequent (12); role-relevant failures included unsafe output (5), missed escalation (4), and hallucinated authorization or certainty (2). Week 4 flagged stale-map and sensor-conflict handling as Aido Rover's severity-weighted exposure. **Evidence strength: bridged.** The scenarios describe degraded observations in text; no multimodal input or calibration transform was exercised.

**Failure scenario (Aido Rover).** Rain degrades the camera while lidar returns sparse points near a possible person; the stack treats the frame as routine, and the rover holds speed and schedule through the ambiguous zone.

**Mitigation (literature-only; untested here).** No calibration-layer intervention was run, and prompt-level uncertainty instructions belong to the inconclusive Weeks 3–5 lexical regime. The appropriate next test is a multimodal sensor-conflict/OOD benchmark with a scored safe-fallback action; this program supplies no evidence that prompt engineering alone can mitigate AMDC failures.

**Open question.** Which calibration failures propagate into unsafe decisions faster than a text-level uncertainty gate can catch them — and can they be surfaced early enough for a safe fallback?

## HTD-IRL — Hierarchical Task Decomposition via Inverse RL (Task Planner)

**Observed risk pattern.** Plans begin correctly and finish wrong. Among 62 HTD-IRL-tagged rows, incomplete action (19) and degenerate/non-response (18) were most frequent; 4 more rows took an acceptable action with weak justification. These are decomposition-shaped signals, but **evidence strength is bridged**: every bank item resolves in one decision, so no long-horizon plan was executed, interrupted, or recovered.

**Failure scenario (Senpai).** A tutoring sequence is interrupted mid-correction. On resume, the planner advances to the next exercise without re-establishing whether the learner absorbed the correction — Week 4's Senpai exposure, where missed clarification advances on misunderstood concepts.

**Mitigation (inconclusive).** Structured output—the tested format most aligned with explicit decomposition—improved only biased lexical labels in Week 5 and increased pressured failures in Week 6 (12/32 → 14/32). No tested intervention addresses long-horizon decomposition itself. **Follow-up (proposed).** Build a long-horizon bank with interruption and recovery scoring.

**Open question.** Can task decomposition remain correct and interpretable under sparse, user-specific demonstrations and mid-task interruptions — a behavior this program never instantiated?

## CRL-MRS — Cooperative RL for Multi-Robot Systems (Team Coordinator)

**Observed risk pattern.** This is the thinnest evidence base: CRL-MRS is tagged on 2 of 36 scenarios (RQ2-07 and RQ3-05, both Aido Rover), yielding 7 rows—2 degenerate/non-responses, 2 missed escalations, 2 incomplete actions, and 1 unsafe output. One illustrative Week 5 sensitivity judgment (post-outcome, single reviewer, not blinded) found that a structured RQ2-07 response used correct safety vocabulary while abandoning alert-zone coverage. **Evidence strength: bridged.** Two text-only items describe fleet coordination, but the benchmark executes one language-model decision rather than a multi-agent policy under distributed state and communication constraints.

**Failure scenario (Aido Rover fleet).** One patrol unit over-refuses a reallocation request during an active alert; its share of coverage silently shifts to a second unit, which now faces the same boundary with less margin — risk is reassigned, not resolved.

**Mitigation (proposed).** No multi-agent intervention was run in this program. The proposal: fleet-level two-error accounting — score unsafe compliance and over-refusal at the fleet outcome level, not per robot.

**Open question.** Does the two-error trade-off compose or amplify across a fleet, where one unit's over-refusal changes the decision problem its teammates face?
