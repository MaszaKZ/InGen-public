# Wk-02 Research Log

Date: 2026-06-23

## Work Completed

- Wrote `W02_Literature_Review.md`: eighteen annotated public papers across embodied foundation-model evaluation, safety/uncertainty/OOD behavior, and HRI trust calibration, with three evidence-backed research gaps and candidate research questions.
- Wrote `W02_PIC20_Mapping.md`: a role-based mapping of the six PIC 2.0 model classes to their closest open-literature method families, each with a structural analogy, an open research gap, and a Week 3 benchmark implication.
- Wrote `W02_Research_Questions.md`: three measurable research questions, each with a hypothesis, methodology sketch, and success criteria, designed to feed directly into Week 3 benchmark scenarios.

## What I Read

The most important group of papers this week was the safety and uncertainty cluster: Tolle et al. on safe robot foundation models, Lekeufack et al. on Conformal Decision Theory, and the OOD safety-assurance review by Hodge et al. Together, they clarify a central issue for physical AI: a model can be generally capable and still unsafe if it does not know when its observation, action, or operating context has moved outside reliable bounds. This issue motivates the sharper, evidence-backed research gaps developed this week and the role-based PIC 2.0 mapping that ties each gap to a Week 3 benchmark item.

The most important single paper I read was Lekeufack et al.'s "Conformal Decision Theory." Its contribution is that it calibrates decisions rather than only predictions, which matches the actual robot question: should the agent act, defer, ask for review, or switch to a backup policy? The gap it left open is operationalization for service-robot benchmarks. The paper gives a strong statistical frame, but a 12-week internship still needs a compact public scenario set with measurable decisions, risk labels, and failure modes.

## What I Found

Three themes run through this week's reading, and each resolves into a measurable form. "Safety-constrained policy learning" becomes measurable as safety-violation reduction under explicit constraints. "Calibrated uncertainty gates" becomes measurable as defer/review accuracy and unsafe-overconfidence rate. "Human interaction and trust" becomes measurable as whether explanations communicate uncertainty, evidence, boundaries, and escalation paths without over-reassurance.

## Open Questions

- Which public models should be used as Week 3 baselines: one text-only LLM plus one multimodal model, or two text-only models for faster evaluation?
- Should the first benchmark use only text scenarios, or include a small number of static images to test visual ambiguity?
- How much human rating is feasible for Week 3 without slowing down the baseline evaluation?

## AI Assistance Note

AI assistance was used for literature organization, drafting, and consistency checking. The final Week 2 claims are grounded in public papers or stated as open research questions.
