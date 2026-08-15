# Week 8 Research Log

Date: 2026-07-26

## Weekly summary (300–500 words)

Week 8 translated the empirical work from Weeks 3–7 into the internship plan's two required synthesis documents: a six-class PIC 2.0 analysis and a five-platform application framework. I first traced every quantitative statement to the decisive version of its evidence. This mattered because the program had corrected several earlier interpretations: the Week 5 semantic audit invalidated a lexical improvement claim, the canonical Week 6 study replaced preliminary explorations, and Week 7 accepted its judge panel through a disclosed amendment. The resulting PIC analysis distinguishes direct behavioral evidence from bridged analogy, gives every class a taxonomy-linked risk, platform scenario, status-labeled mitigation, and unanswered question, and avoids implying that a proprietary module or deployed robot was tested.

The application framework treats generator and intervention choices as operating points between unsafe compliance and authorized-control refusal. Recommendations are therefore platform-and-task-risk research gates, not deployment approvals. During paper preparation I rechecked a proposed explanation for Week 7's surprising plain-versus-pressured reversal. The intended stratification was not feasible: all 32 plain items state a governing prerequisite, but none says that the prerequisite is missing. I recorded the contrast as non-estimable instead of forcing an analysis. Coding the pressured arm the same way then exposed a confound the first pass had missed: 8 of 32 pressured items, all in one tactic arm, name the absent prerequisite outright, so salience varies across the pair rather than within the intended stratifier. A replacement post-outcome audit pairs existing outcomes by generator, family, variant, and seed. It reports 317 complete pairs, lists three unparsed Qwen pairs, and uses deterministic family-clustered bootstrap intervals. Cue-specific rows remain descriptive because tactic, family, wording, variant, setting, and — in that one arm — salience are confounded. The salience explanation is left untested, not refuted.

I also prepared a supplementary handoff for the Week 9 paper: a machine-readable claim registry, figure and table map, shared BibTeX bibliography, section budget, limitation language, and reproducibility preflight. These files do not expand the Week 8 master deliverables. They make the evidence hierarchy explicit: the common-prompt generator contrast is confirmatory within its tested scope; mitigation transfer is descriptive; the pressure-cue audit is exploratory; and application guidance is proposed. The final verification independently recomputes source counts, contrasts, audit rows and intervals; checks plan conformance, links, figures, citekeys, word budgets, and publication boundaries; and confirms that the research log is current.

## Detailed chronological audit trail

### 2026-07-26 — canonical deliverable synthesis

- I reconstructed the decisive-version map from the committed Week 3–7 artifacts and logs. Superseded Week 4 rates, the unaudited Week 5 lexical effect, preliminary Week 6 explorations, and the removed first Week 7 replication were excluded as current evidence.
- I completed [`W08_PIC20_Analysis.md`](W08_PIC20_Analysis.md). Every GRPO, STUM, SEOM, AMDC, HTD-IRL, and CRL-MRS section contains an observed taxonomy-linked risk, a named platform scenario, a status-labeled mitigation, and an open question.
- I kept AMDC, HTD-IRL, and CRL-MRS explicitly bridged because the bank contains no multimodal sensor input, long-horizon execution, or multi-agent policy. CRL-MRS remains the thinnest mapping: two scenarios and seven tagged failure rows.
- I completed [`W08_Application_Framework.md`](W08_Application_Framework.md) with ten platform/task-risk cells, experiment-specific evidence, intervention status, and advancement gates. The framework separates unsafe compliance from authorized-control refusal and preserves the Week 2 gap update.

### 2026-07-26 — terminology, evidence, and publication decisions

- I used the public Origami names and roles consistently. The Sentinel page's product-level STUM expansion remains distinguished from the Origami class-level name.
- I kept the two public SEOM descriptions unresolved: training-time constitutional penalties and runtime hardware governance may be complementary, but the public pages do not establish that relationship.
- I treated public product pages as sources of terminology and stated design intent, never independent validation.
- I preserved the publication boundary: the public-facing Week 8 documents contain no restricted-source terminology or unsupported performance guarantee.

### 2026-07-26 — salience feasibility check and replacement audit

- I inspected all 32 Week 7 plain items against a recorded coding definition. Each states its governing prerequisite; none states that the prerequisite is missing, absent, unavailable, unrecorded, unverified, or unconfirmed.
- I withdrew the earlier statement that the salience stratification was ready for Week 9. The registered contrast is **non-estimable**, not null and not refuted.
- I applied the same coding to the pressured arm, which my first pass had not done. It flags 8 of 32 items, all in the `false_clearance` arm, whose wording names the absent prerequisite outright. Salience therefore does vary across the pair — nested inside one tactic instead of crossed with pressure — so that arm's difference is confounded with the factor the withdrawn contrast meant to isolate. The audit, framework, registry, handoff, and both READMEs now disclose this rather than folding it into generic "bundled wording".
- I corrected a line that read as though the salience explanation had been eliminated. The audit now states that it cannot be tested here and is neither supported nor ruled out; the verifier rejects the earlier phrasing.
- I added [`analyze_w08_pressure_cues.py`](analyze_w08_pressure_cues.py), [`W08_Pressure_Cue_Audit.json`](W08_Pressure_Cue_Audit.json), and [`W08_Pressure_Cue_Audit.md`](W08_Pressure_Cue_Audit.md).
- I paired common-baseline plain and pressured outcomes by generator, family, pair variant, and seed. The audit contains 317 complete pairs and identifies all three excluded Qwen pressured endpoints.
- I used 10,000 family-cluster bootstrap draws with seed `20260726`. Cue rows are explicitly post-outcome descriptive heterogeneity; no causal tactic effect, tactic ranking, confirmatory p-value, or multiplicity claim is made.
- I specified, but did not run, an estimable 2×2 salience-by-pressure experiment with tactic and setting counterbalanced within family and authorized controls retained.

### 2026-07-26 — paper and reproducibility preparation

- I added supplementary [`W08_Paper_Handoff.md`](W08_Paper_Handoff.md), which fixes the paper-versus-capstone boundary, claim hierarchy, 8–10-page section budget, figure/table manifest, limitation language, reproducibility preflight, and Week 9 readiness checklist.
- I added supplementary [`W08_Paper_Claim_Registry.json`](W08_Paper_Claim_Registry.json). Its only permitted statuses are `confirmatory`, `descriptive`, `exploratory`, and `proposed`.
- I added the shared root [`references.bib`](../references.bib). The 18 Week 2 arXiv identifiers, author lists, titles, and first-submission years were checked against the primary arXiv records; the two public InGen pages are separately labeled as design-intent sources.
- I added [week-08/README.md](README.md) and updated the root README so the canonical deliverables, supplementary artifacts, commands, and evidence boundaries are discoverable.
- I recorded the remaining Week 10 reproducibility gaps: no pinned root environment and no one-command clean-environment package. Existing raw model outputs were not deleted or moved.

## Deliverable conformance

| Plan requirement | Repository artifact and section | Evidence of completion | Verification result | Status |
| --- | --- | --- | --- | --- |
| Approximately three-page analysis of all six PIC 2.0 classes | `W08_PIC20_Analysis.md`, six class sections | Each section includes risk, scenario, mitigation, and open question; 1,541 prose words | Structural and source checks pass | **complete** |
| Approximately two-page five-platform application framework | `W08_Application_Framework.md`, priority matrix, intervention table, gap update | Ten task-risk cells; seven intervention rows; addressed/open/new gaps; 721 prose words outside tables | Platform, evidence-status, and budget checks pass | **complete with limitation** — application guidance is not deployment evidence |
| Current weekly research log | `Wk-08-ResearchLog.md`, summary through completion entry | 300–500-word summary, chronological decisions, conformance, open items, verification, final mapping | Log completeness and word-budget checks pass | **complete** |
| Paper preparation supporting Week 9 | Handoff, registry, bibliography, exploratory audit | Claims map to evidence, figures, limitations, sections, and citekeys | Registry, BibTeX, local-link, and independent audit checks pass | **complete with limitation** — supplementary, not a Week 8 master deliverable |
| Week 9 paper draft | No Week 9 draft created | The handoff prepares the draft without writing it early | Scope boundary confirmed | **deferred by plan** |
| Pinned clean-environment package | No root lockfile or Week 10 package created | Gap recorded in the reproducibility preflight | Scope boundary confirmed | **deferred by plan** |

## Open items

| Item | Current disposition | Owner week | Blocking Week 8? |
| --- | --- | ---: | --- |
| Explicit prerequisite-salience test | Current stratification non-estimable; future counterbalanced 2×2 experiment specified | 12 / future research | No |
| Blinded human validation of the weakest pooled unsafe panel stratum (14/16) | Not run; remains the highest-value measurement follow-up | 9–10 if resources permit | No |
| Calibrated deferral as a third action | Proposed and literature-motivated; not tested | 10–12 / future research | No |
| Third generator family | Needed to test whether the observed trade-off extends beyond two models | Future research | No |
| Pinned dependencies and one-command clean reproduction | Explicitly reserved for the plan-specified reproducibility package | 10 | No |
| Venue-specific citation and page formatting | BibTeX content ready; style depends on the eventual workshop template | 9–12 | No |

## Verification record

All commands ran from the repository root with the project's Python 3.11 environment.

1. `.\.conda-w01\python.exe week-08\analyze_w08_pressure_cues.py` regenerated the exploratory JSON and Markdown. A second run produced identical SHA-256 hashes: JSON `A4106084474ABA706EFED5D41EAD7E5985F3C96AE9651FA87803FADDA0EC4BEE`; Markdown `157C5C0CFB45DFE814BC222E03E46DF7A513EE6427AF1466608F3A5D36FF79DE`.
2. `.\.conda-w01\python.exe -m py_compile week-08\verify_w08.py week-08\analyze_w08_pressure_cues.py` passed syntax checks.
3. The extended verifier independently recomputed Week 4 class counts, Week 6/7 decisive results, Week 7 platform strata, all 317 complete pressure-cue pairs, three exclusions, failure rates, paired differences, and deterministic clustered intervals.
4. It also recomputes the salience coding for both arms from the Week 7 bank, using a deliberately broader absence pattern than the analyzer's, so that an analyzer that under-counted would surface as a mismatch rather than as agreement. Both arms agree exactly: 0 of 32 plain items and 8 of 32 pressured items, all `false_clearance`.
5. It also checked the three canonical deliverables against the internship-plan requirements; validated all evidence paths, figures, local links, claim statuses, and citekeys; confirmed all 18 Week 2 arXiv records are present in `references.bib`; enforced the word budgets and publication boundary; and rejected both the stale feasible-salience wording and the stale "cannot explain" phrasing.
6. Each new salience check was confirmed by mutation: corrupting the per-tactic counts, widening the confounded-tactic list, dropping a coded scenario ID, and reinstating the old wording each made the verifier fail; restoring the files returned it to PASS.
7. `git diff --check` completed without whitespace errors.
8. Latest acceptance result: `PASS: Week 8 verification complete`.

## AI assistance note

AI assistance was used for source organization, deterministic analysis implementation, bibliography preparation, drafting, and consistency checks. Every quantitative result is regenerated from committed evidence, and the extended verifier implements a separate recomputation rather than trusting the generated audit.

## Final Week 8 completion entry

Week 8 is complete as of 2026-07-26. The three master deliverables remain exactly those specified by the internship plan: [`W08_PIC20_Analysis.md`](W08_PIC20_Analysis.md), [`W08_Application_Framework.md`](W08_Application_Framework.md), and this [`Wk-08-ResearchLog.md`](Wk-08-ResearchLog.md). The paper handoff, claim registry, bibliography, and pressure-cue audit are explicitly supplementary inputs to Weeks 9–12. No Week 9 draft, new model inference, pinned Week 10 environment, raw-output deletion, or plan-document amendment was performed. Final status: `PASS: Week 8 verification complete`.
