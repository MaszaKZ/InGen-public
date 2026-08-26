# W08 Paper Handoff: Claim, Evidence, Figure, and Reproducibility Map

Date: 2026-07-26

> **Status: supplementary Week 8 preparation for the plan-specified Week 9 paper.** This handoff is not an addition to, or replacement for, the Week 8 master deliverables. Those remain [`W08_PIC20_Analysis.md`](W08_PIC20_Analysis.md), [`W08_Application_Framework.md`](W08_Application_Framework.md), and [`Wk-08-ResearchLog.md`](Wk-08-ResearchLog.md).

## Paper versus capstone boundary

The Week 9 paper should grow from the [Week 7 research note](../week-07/W07_Research_Note.md), because that is where the primary contribution was registered and independently checked. Its main result is a common-prompt generator contrast on a synthetic decision-safety benchmark, not a validation of PIC 2.0 or any deployed platform. The paper may use the Week 8 operating-point interpretation in its discussion, supported by conformal decision theory [@lekeufack2023conformal], but it should devote no more than roughly one page to application implications.

The complete six-class PIC analysis, five-platform matrix, and product-specific research gates belong in the Week 11 capstone. Public Origami and Sentinel pages establish names and stated design intent [@ingen2026origami; @ingen2026sentinel]; they are not independent empirical evidence.

## Canonical claim hierarchy

The machine-readable source of truth is [`W08_Paper_Claim_Registry.json`](W08_Paper_Claim_Registry.json). Status words below are evidentiary labels, not rhetorical emphasis.

| ID | Status | Paper-ready claim | Exact evidence | Required qualification | Paper location |
| --- | --- | --- | --- | --- | --- |
| C1 | **Confirmatory** | Under the byte-identical common prompt, Qwen shifted the tested two-error operating point relative to Mistral: lower plain and pressured unsafe-compliance failure, but higher authorized-control refusal. | Qwen−Mistral: plain −55.0pp, 95% CI [−77.5, −32.5]; pressured −40.1pp [−55.3, −26.0]; control +18.8pp [+6.2, +34.4]. [`W07_Analysis.json`](../week-07/W07_Analysis.json), Figure F1. | Generator effect is causal only for this prompt, bank, and endpoint; no embodied or deployment claim. | Abstract, Results, Discussion |
| C2 | **Descriptive** | Only Qwen with deliberation passed the registered Week 7 mitigation rule; prompt effects did not transfer uniformly across generators. | [`W07_Confirmation_Results.md`](../week-07/W07_Confirmation_Results.md), Figure F2. | Do not turn two tested generators into a universal method ranking. | Results, Discussion |
| C3 | **Descriptive** | Lexical success did not substitute for semantically adjudicated action outcomes, and apparent intervention effects changed with the measurement stack. | [Week 5 audit](../week-05/W05_Results_Memo.md), [Week 6 analysis](../week-06/W06_Analysis.json), [Week 7 note](../week-07/W07_Research_Note.md). | The experiments differ; no pooled causal effect is estimable. | Methods, Discussion |
| C4 | **Exploratory** | Complete Week 7 pairs had fewer failures under pressured than plain wording for both generators, with descriptive heterogeneity across bundled cues. | [`W08_Pressure_Cue_Audit.md`](W08_Pressure_Cue_Audit.md). | Post-outcome; tactic, family, wording, variant, and setting are confounded, and the `false_clearance` arm is additionally confounded with prerequisite salience. The proposed salience stratification is non-estimable. | Discussion, Limitations |
| C5 | **Proposed** | Future platform evaluation should score unsafe compliance and authorized-control refusal jointly and test calibrated deferral as a third action. | C1 plus the [application framework](W08_Application_Framework.md) and decision-calibration literature [@lekeufack2023conformal]. | Research guidance only; deferral and deployed workflows were not tested. | Discussion, Future Work |

The abstract should lead with C1. C2 supports the generator-dependence implication. C3 explains why the final endpoint deserves emphasis. C4 may appear only as a labeled exploratory observation, and C5 belongs only in discussion/future work.

## Week 9 paper architecture

Target approximately 8.75 pages of main text within the plan's 8–10-page range; references may follow the chosen workshop convention.

| Section | Target | Required content |
| --- | ---: | --- |
| Abstract | 150–200 words | Problem, registered comparison, all three C1 contrasts, one limitation, bounded implication. |
| 1. Introduction | 1.0 page | Decision safety as a two-error problem; contribution statement; no PIC performance claim. |
| 2. Related work | 1.25 pages | Robot foundation models and generalization [@openx2023rtx; @kim2024openvla; @octo2024policy]; runtime safety [@tolle2025safe; @tolle2025inductive]; calibrated decisions [@lekeufack2023conformal]; trust calibration [@rezaeikhavas2020trust; @sanneman2020trust]. |
| 3. Methods | 2.0 pages | Synthetic bank, two generators, common versus adapted prompts, registered endpoints, panel construction/amendment, family-clustered intervals, exclusions. |
| 4. Results | 2.0 pages | C1 first with F1 and exact intervals; C2 with F2; robustness and agreement with F3 or a compact table. |
| 5. Discussion | 1.25 pages | Generator-dependent operating points, measurement-stack lesson, no blanket mitigation, at most one page of Week 8 application framing. |
| 6. Limitations and future work | 0.75 page | All registry limitations; C4 feasibility result; proposed factorial salience study and calibrated deferral. |
| 7. Conclusion | 0.25 page | Restate C1 without expanding scope. |

## Figure and table manifest

| ID | Asset | Use | Caption obligation |
| --- | --- | --- | --- |
| F1 | [`W07_Figure1_Common_Baseline_Cross_Model.svg`](../week-07/figures/W07_Figure1_Common_Baseline_Cross_Model.svg) with [PNG fallback](../week-07/figures/W07_Figure1_Common_Baseline_Cross_Model.png) | Main result | Define failure, direction, denominator, family-clustered interval, and three unparsed pressured rows. |
| F2 | [`W07_Figure2_Prompt_Safety_and_Control_Cost.svg`](../week-07/figures/W07_Figure2_Prompt_Safety_and_Control_Cost.svg) with [PNG fallback](../week-07/figures/W07_Figure2_Prompt_Safety_and_Control_Cost.png) | Registered mitigation rule | State adapted-baseline comparator, benefit threshold, refusal-cost ceiling, and that only Qwen deliberation passed. |
| F3 | [`W07_Figure3_Seed_Variability_and_Judge_Agreement.svg`](../week-07/figures/W07_Figure3_Seed_Variability_and_Judge_Agreement.svg) with [PNG fallback](../week-07/figures/W07_Figure3_Seed_Variability_and_Judge_Agreement.png) | Robustness/supporting result | Separate generator variability from judge agreement and disclose the panel-acceptance amendment. |
| T1 | New paper table from `W07_Analysis.json` | Methods | Conditions, endpoints, family count, seeds, generator revisions, and primary estimands. |
| T2 | New paper table from `W07_Analysis.json` | Results | Exact C1 estimates/CIs and C2 mitigation-rule disposition; never transcribe values manually. |
| T3 | Optional compact limitations table | Limitations | Map L1–L6 to affected claims and remedies; omit if prose is clearer. |

## Limitation language to preserve

- **External validity:** synthetic, text-only scenarios; two 7B-class generators; Sentinel and Aido Humanoid contexts; no sensors, actuation, operators, or deployments.
- **Measurement:** the panel was accepted through a disclosed pooled-evidence amendment after the original single-holdout rule proved underpowered; the weakest pooled unsafe stratum was 14/16.
- **Missingness:** three Qwen pressured endpoints were unparsed, and two outputs had nonconforming headers; use the recorded exclusions and denominators.
- **Cross-experiment comparability:** Weeks 5–7 changed banks, templates, and judges. Cross-week synthesis is methodological, not a pooled intervention estimate.
- **Exploratory cue analysis:** the salience contrast has zero variation across plain items, and tactic-specific rows are confounded. Salience is not constant across the pair either — 8 of 32 pressured items, all `false_clearance`, name the absent prerequisite outright — so that arm's difference cannot be read as a pure tactic effect. State that the salience explanation is untestable here, never that it was ruled out. No causal salience or tactic-priority statement is allowed.
- **Untested actions:** calibrated deferral, RAG, fine-tuning, multimodal inputs, and deployed workflows remain proposals.

## Reproducibility preflight

| Component | Current state | Week 9 use | Remaining Week 10 action |
| --- | --- | --- | --- |
| Bank and prompt construction | Committed scripts and locked artifacts | Cite version and hashes from `W07_Run_Metadata.json` | Package generation path and document expected outputs. |
| Model generation | `run_w07_replication.py` plus committed metadata/raw outputs | Report pinned generator revisions and decoding settings | Re-run from a clean pinned environment; public package will provide scripts, not raw completion JSONL. |
| Panel adjudication | `judge_w07_replication.py`, ratings, calibration and amendment committed | Describe the accepted panel and amendment | Pin judge/runtime dependencies and test clean regeneration. |
| Analysis and figures | `analyze_w07.py`, executed notebook, JSON, figures, report writer | Generate paper values from JSON/CSV, not prose | Add one-command regeneration of all paper tables and figures. |
| Independent verification | Week 7 verification receipt and Week 8 verifier | Cite PASS status and rerun before drafting | Integrate into the clean-environment command. |
| Environment | Project Python 3.11 environment exists, but no root pinned manifest | Record this as a limitation, not as reproducibility completion | Add `requirements.txt` or `environment.yml` with pinned dependencies. |
| Paper bibliography | Root [`references.bib`](../references.bib) | Use stable citekeys | Freeze formatting for the selected submission venue. |

## Week 9 readiness checklist

- [ ] Draft the abstract from C1, including all three directions and the synthetic/text-only boundary.
- [ ] Build T1 and T2 directly from `W07_Analysis.json`; do not copy rounded prose values.
- [ ] Use F1 and F2 in the main text; place F3 according to the final page budget.
- [ ] Cite only keys present in `references.bib`; preserve primary-source links.
- [ ] Describe the judge amendment before using panel outcomes as evidence.
- [ ] Label C2/C3 descriptive, C4 exploratory, and C5 proposed everywhere.
- [ ] State that the salience contrast is non-estimable; do not say it was confirmed or rejected.
- [ ] Disclose the `false_clearance` salience confound wherever cue-specific rows appear.
- [ ] Run `verify_w08.py` before drafting and the Week 7 independent verifier before freezing results.
- [ ] Keep the detailed PIC/platform framework for the capstone rather than expanding the paper.

AI assistance was used to organize this handoff and check consistency. Quantitative statements are linked to committed evidence and are validated by `verify_w08.py`.
