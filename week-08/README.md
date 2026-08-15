# Week 8 — PIC 2.0 Analysis, Application Framework, and Paper Handoff

Week 8 is the internship plan's PIC 2.0 synthesis week. The three master deliverables are unchanged:

1. [`W08_PIC20_Analysis.md`](W08_PIC20_Analysis.md) — approximately three pages covering all six PIC 2.0 classes; each section contains a taxonomy-linked risk, platform scenario, evidence-status-labeled mitigation, and open question.
2. [`W08_Application_Framework.md`](W08_Application_Framework.md) — approximately two pages covering five platforms, intervention evidence, advancement gates, and the Week 2 gap update.
3. [`Wk-08-ResearchLog.md`](Wk-08-ResearchLog.md) — current weekly summary, chronological decisions, deliverable conformance, open items, and verification record.

## Supplementary Weeks 9–12 preparation

These artifacts prepare later paper and capstone work. They do not replace or expand the Week 8 master deliverables.

- [`W08_Paper_Handoff.md`](W08_Paper_Handoff.md) — paper/capstone boundary, claim-to-evidence map, page budget, figure/table manifest, limitations, reproducibility preflight, and Week 9 checklist.
- [`W08_Paper_Claim_Registry.json`](W08_Paper_Claim_Registry.json) — machine-readable claim statuses, evidence paths, figures, limitations, and intended paper sections.
- [`W08_Pressure_Cue_Audit.md`](W08_Pressure_Cue_Audit.md) and [`W08_Pressure_Cue_Audit.json`](W08_Pressure_Cue_Audit.json) — post-outcome exploratory audit. The proposed prerequisite-salience contrast is non-estimable because no plain item states that the prerequisite is missing. The audit also records the reverse asymmetry: 8 of 32 pressured items, all `false_clearance`, name the absent prerequisite outright.
- [`analyze_w08_pressure_cues.py`](analyze_w08_pressure_cues.py) — deterministic regeneration from the Week 7 confirmation bank and results.
- [`../references.bib`](../references.bib) — shared bibliography for the Week 9–12 paper sequence.

Cue-specific failure differences are descriptive heterogeneity only. Tactic, family, pair variant, wording, setting, and — in one arm — prerequisite salience are confounded, so the audit makes no causal tactic claim or priority ranking, and leaves the salience explanation untested rather than refuted.

## Verification

Run from the repository root:

```powershell
.\.conda-w01\python.exe week-08\analyze_w08_pressure_cues.py
.\.conda-w01\python.exe week-08\verify_w08.py
```

`verify_w08.py` independently recomputes the exploratory audit and checks the canonical deliverables, paper handoff, claim registry, figures, local links, bibliography citekeys, word budgets, disclosure, and publication boundary.

AI assistance was used for analysis implementation, bibliography preparation, drafting, and consistency checks. All quantitative values are regenerated from committed sources and independently verified.
