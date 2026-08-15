# W09 Meeting Feedback — Week 8 Review

Date received: 2026-08-03
Applies to: Week 9 paper draft and all subsequent Weeks 9–12 documents
Status: implemented in the Week 9 draft and checked by the Week 9 verifier

## Feedback as received

Written note, verbatim:

> Good Work! As discussed, please include more supporting quantitative results and references to the underlying source artifacts wherever possible. This will make it easier to validate your conclusions. All the very best with your manuscript preparation!

From the meeting discussion, as relayed: quantitative supports, and a distinct literature analysis separated from research-supported contents.

## Interpretation

Three directives, whose stated purpose is that conclusions can be validated directly against committed evidence:

1. **More supporting quantitative results** — statements carry explicit quantitative backing.
2. **References to the underlying source artifacts wherever possible** — each conclusion points to the committed artifact that produced it, so a reader can validate it directly.
3. **Distinct literature analysis versus research-supported contents** (from the discussion) — literature-derived analysis must be clearly separated from contents supported by this program's own empirical research. This admits two readings that converge in practice and are both adopted: every statement is attributable on sight to either the literature or program evidence, and the paper's Related Work stands as a distinct literature-analysis component rather than being folded into the empirical contribution.

## Action items for the Week 9 draft

### Quantitative supports

- Every claim in the draft carries its exact estimate, denominator, and family-clustered interval, generated from [`W07_Analysis.json`](../week-07/W07_Analysis.json) — never transcribed from prose. This extends the existing handoff rule for tables T1/T2 to *all* quantitative statements, including Discussion.
- Class-tagged and platform-level counts always appear with their denominators and the taxonomy-anchor qualification from [`W08_PIC20_Analysis.md`](../week-08/W08_PIC20_Analysis.md).
- Statements that currently have no number attached are either given one from committed evidence or explicitly labeled as qualitative.

### References to underlying source artifacts

- Every central quantitative claim is traceable to the committed artifact that produced it — through a repo-relative inline link or the supplementary claim-to-artifact map and, where practical, the specific JSON field, CSV column, or table row — following the evidence-path pattern already used in the [claim registry](../week-08/W08_Paper_Claim_Registry.json).
- Figures and tables cite their generating script and input files (e.g., `analyze_w07.py` over `W07_Results.csv`), not only the rendered asset.
- Conclusions in Discussion cite the decisive week's artifact directly, not a prose document that paraphrases it.
- Where the manuscript format cannot carry file paths, the supplementary material maps each claim ID to its artifact so the chain stays checkable.

### Distinct literature analysis

- Related Work (§2, 1.25 pages in the [handoff budget](../week-08/W08_Paper_Handoff.md)) is written as a standalone literature analysis: what each cited line of work establishes, on what evidence, and where this program's question sits relative to it — not a citation list.
- The evidence-status discipline from the [claim registry](../week-08/W08_Paper_Claim_Registry.json) (`confirmatory` / `descriptive` / `exploratory` / `proposed`) is extended with an explicit distinction for literature-derived material: a statement supported only by cited work is marked as such and never presented alongside program results as if co-equal evidence.
- The application framework's existing `literature-only / proposed` status label is the model; the paper carries the same discipline throughout, including Discussion and Limitations.

## Traceability

Week 8 documents already partially satisfy both directives (evidence-status labels, exact CIs in the claim hierarchy, the framework's `literature-only` marker). This note raises them from partial conventions to binding requirements for every Weeks 9–12 document. Conformance is checked at Week 9 verification alongside the existing handoff checklist.
