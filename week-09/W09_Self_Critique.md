# W09 Self-Critique of the Paper Draft

Date: 2026-08-05

Structured self-review of [`W09_Paper_Draft_v1.md`](W09_Paper_Draft_v1.md), answering the four questions specified by the internship plan. Each answer cites the artifact that grounds it.

## (a) What is the single clearest contribution claim? Could a reviewer evaluate it without running the experiments?

**The claim.** Under a byte-identical common prompt on a registered 96-scenario bank, generator choice traded unsafe compliance against authorized-control refusal rather than improving both: Qwen2.5-7B-Instruct vs Mistral-7B-Instruct-v0.3 shifted plain-caution failure −55.0pp [−77.5, −32.5], pressured-caution failure −40.1pp [−55.3, −26.0], and authorized-control refusal +18.8pp [+6.2, +34.4] (family-clustered 95% CIs; [`W07_Analysis.json`](../week-07/W07_Analysis.json)).

**Evaluability without re-running.** Mostly yes, with one honest boundary. A reviewer can recompute every reported estimate, interval, and denominator from the committed [`W07_Results.csv`](../week-07/W07_Results.csv) and `W07_Judge_Ratings.csv` (separately supplied verification input) using [`analyze_w07.py`](../week-07/analyze_w07.py) or the independent [`verify_w07_independent.py`](../week-07/verify_w07_independent.py) — no GPU or model inference is required to audit the analysis chain. What a reviewer *cannot* evaluate from artifacts alone is the ground truth of the outcome labels themselves: those depend on the LLM judge panel, and trusting them means trusting the calibration and amendment record in §3.3, not human annotations. The draft says this, but the dependence should be stated even more bluntly in the abstract if space allows.

## (b) What is the single most important limitation — and is it currently acknowledged in the draft?

**The limitation.** Every caution-scenario rate rests on an LLM judge panel that was *not* certified by its registered single-holdout rule. The panel repeatedly tripped zero-miss floors, the pre-registered ceiling analysis ([`W07_Panel_Ceiling_Analysis.json`](../week-07/W07_Panel_Ceiling_Analysis.json)) showed the rule was underpowered at that holdout size, and the run proceeded under a disclosed human-authorized amendment ([`W07_Panel_Acceptance_Amendment.json`](../week-07/W07_Panel_Acceptance_Amendment.json)). The weakest measured stratum is exactly the one the headline claim leans on: unsafe-compliance detection on declares-then-hedges responses, 14/16 pooled, CP95 lower bound 0.617. If the panel systematically misses hedged unsafe compliance, the plain-caution gap between the generators could be mismeasured in either direction.

**Acknowledged?** Yes — before any result (§3.3), in the abstract's limitation sentence, and in §6 with the blinded-human-validation follow-up named as highest-value. What the draft does not do is quantify the sensitivity of C1 to judge error in that stratum (e.g., a bounding analysis flipping the 14/16 stratum's plausible miss rate against the result). That sensitivity analysis is a concrete Week 10 revision item.

## (c) Which related work does the paper need to engage with more deeply? Name a specific paper.

**FoMER — Dissanayake et al. (2025), "How Good are Foundation Models in Step-by-Step Embodied Reasoning?" (arXiv:2509.15293).** The draft cites it in one sentence in §2.1 as a benchmark that "scores safety awareness among its dimensions" — that is acknowledgment, not engagement. FoMER is the closest public artifact to our bank: scenario-based, language-mediated, embodied decision scenarios with safety scoring. A careful reviewer will ask two questions the draft currently does not answer: (1) why did we build a new 96-scenario bank instead of adding paired authorized controls to FoMER's existing scenarios — is there something about authorization-gated *operational* decisions that FoMER's step-by-step reasoning format cannot express? (2) Do FoMER's safety-awareness scores correlate with our executes-now endpoint, or do they measure the lexical safety behavior that our Week 5 audit showed can diverge from semantic outcomes ([`W05_Results_Memo.md`](../week-05/W05_Results_Memo.md))? The Week 10 revision should add a paragraph making the comparison explicit: same-format scenario example from each, and the argument that a two-error endpoint with authorized controls is the piece FoMER lacks — refusal is cost-free on any bank without authorized controls.

## (d) What is one result a careful reviewer would question?

**The Qwen + deliberation mitigation-rule pass (§4.2, Table T2c).** It is the only intervention presented as passing the registered rule, and it is the draft's most fragile number: the pass is a 2.5% → 0.0% pressured change resting on **4 discordant pairs** out of 160 (unclustered exact McNemar p = 0.125), with a +1.25pp control cost measured against a 3.125pp ceiling — one additional control refusal in the run would have roughly halved the remaining margin. The rule's relative-reduction threshold is also scale-sensitive: a 100% relative reduction from a 2.5% baseline is 4 rows of absolute change, whereas the same relative reduction for Mistral would have required 30. A reviewer could reasonably say the rule rewards starting near zero. The draft flags the fragility (§6, "should be treated as fragile until replicated") but keeps "**Yes**" in the disposition table because that is the registered rule's verdict; the defensible presentation, which the draft adopts, is verdict-plus-fragility rather than a silent pass. A replication with a third generator or more seeds is the only clean resolution, and it is listed in future work.

**Runner-up.** The plain > pressured reversal (§4.3) — a reviewer may suspect bank construction rather than model behavior, and the draft agrees: the salience explanation is recorded as non-estimable on this bank, with the false-clearance confound disclosed ([`W08_Pressure_Cue_Audit.md`](../week-08/W08_Pressure_Cue_Audit.md)).

---

AI assistance was used for drafting this critique; every factual statement is grounded in the linked included artifacts.
