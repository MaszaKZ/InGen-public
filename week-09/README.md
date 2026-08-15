# Week 9 — Research Paper Draft v1

Week 9 is the internship plan's paper-drafting week. The three plan deliverables:

1. [`W09_Paper_Draft_v1.md`](W09_Paper_Draft_v1.md) — complete 8–10-page draft (workshop format): abstract, introduction, related work, methods, results, discussion, limitations/future work, conclusion, plus an evidence-provenance appendix mapping claims C1–C5 to committed artifacts.
2. [`W09_Self_Critique.md`](W09_Self_Critique.md) — structured self-review: contribution claim and its evaluability, most important limitation, the specific paper needing deeper engagement (FoMER, arXiv:2509.15293), and the result a careful reviewer would question.
3. [`Wk-09-ResearchLog.md`](Wk-09-ResearchLog.md) — weekly summary with the hardest-section reflection, chronological decisions, conformance, reproducibility-check findings, and verification record.

## Supplementary artifacts

- [`W09_Paper_Draft_v1_IEEE.tex`](W09_Paper_Draft_v1_IEEE.tex) — IEEE conference (two-column) submission derivative of the canonical draft, revised 2026-08-06 for publication style: no claim-status labels, section roadmap, program-internal disclosures, or provenance appendix (all retained in the Markdown draft), listings and run-in headings converted to prose, and the pressured effect size reported under the registered 157-row denominator (h = 1.07). Compiled PDF: [`W09_Paper_Draft_v1_IEEE.pdf`](../output/pdf/W09_Paper_Draft_v1_IEEE.pdf) — eight pages, rebuilt from the revised source on 2026-08-06.
- [`W09_Meeting_Feedback.md`](W09_Meeting_Feedback.md) — verbatim 2026-08-03 review feedback and the three directives binding Weeks 9–12: quantitative supports, source-artifact references, and a distinct literature analysis.
- [`build_w09_paper_tables.py`](build_w09_paper_tables.py) → [`W09_Paper_Tables.md`](W09_Paper_Tables.md) — paper tables T1/T2a/T2b/T2c generated from [`../week-07/W07_Analysis.json`](../week-07/W07_Analysis.json) and [`../week-07/W07_Run_Metadata.json`](../week-07/W07_Run_Metadata.json); the draft embeds these rows verbatim.
- [`verify_w09.py`](verify_w09.py) — independent verifier: re-derives all table rows from committed JSON, recomputes prose values from the Week 6–8 artifacts and `W07_Results.csv` — including exact Clopper–Pearson bounds, Cohen's h under both denominator conventions, and paired discordance counts — and enforces budgets, citations, links, labels, disclosures, and the meeting-feedback requirements.

## Claim discipline

The draft's claim labels follow [`../week-08/W08_Paper_Claim_Registry.json`](../week-08/W08_Paper_Claim_Registry.json): the cross-generator trade-off is **confirmatory**; mitigation non-transfer and the measurement-stack lesson are **descriptive**; the pressure-cue audit is **exploratory** (salience contrast non-estimable; false-clearance arm confounded); application guidance is **proposed**. Nothing in the draft validates a PIC implementation or approves a deployment. The IEEE derivative presents the same claims without the label apparatus; the registry mapping applies to the canonical Markdown draft.

## Verification

Run from the repository root:

```powershell
.\.conda-w01\python.exe week-09\build_w09_paper_tables.py
.\.conda-w01\python.exe week-09\verify_w09.py
```

Reproducibility-check finding (documented in the log): `W07_Analysis.json` and the PNG figures regenerate byte-identically from committed CSVs; the SVG figures differ across runs only in embedded `dc:date` metadata and matplotlib's hashed element IDs — the Week 10 package will pin `svg.hashsalt` and figure metadata.

AI assistance was used for drafting, table generation, and verification implementation. All quantitative values are generated from committed sources and independently verified.
