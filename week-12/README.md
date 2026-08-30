# Week 12 Final Research Package

This directory contains the final workshop paper, research retrospective, defense brief, research log, figures, and verification entry point for the contested-authority study. The package is technical and evidence-facing: it records the completed analysis and its reproducibility boundary, and specifies the next research experiment.

## Deliverables

| Artifact | Purpose |
| --- | --- |
| `W12_Final_Paper.md` | Canonical audience-facing paper in Markdown |
| `W12_Final_Paper.tex` | Synchronized IEEEtran source |
| `W12_Final_Paper.pdf` | Compiled 10-page workshop paper |
| `build_w12_paper.py` | Deterministic source/figure assembler |
| `figures/` | Four publication figures in PDF, PNG, and machine-readable JSON |
| `W12_Retrospective.md` | Evidence-bounded research reflection and six-month follow-up plan |
| `W12_Presentation_Defense_Brief.md` | Timed 14-slide presentation plan and research Q&A |
| `W12_Reproducibility_Audit.ipynb` | Executed audit of the primary results and artifact consistency |
| `build_w12_notebook.py` | Deterministic notebook cell builder |
| `Wk-12-Final-ResearchLog.md` | Final research record and open questions |
| `test_w12.py` | Acceptance-contract tests |
| `verify_w12.py` | Integrated local verifier |

## Central result

Under the byte-identical common prompt, the Qwen-minus-Mistral contrast is -55.0 percentage points on plain-caution failure (family-clustered 95% CI [-77.5, -32.5]), -40.1 points on pressured-caution failure (CI [-55.3, -26.0]), and +18.8 points on authorized-control refusal (CI [+6.2, +34.4]). The three directions survive the specified conditional false-negative stress, but the only observed intervention pass does not survive combined measurement stress.

All rates are LLM-judge measurements on a synthetic, text-only benchmark. The package does not claim field, embodied-system, or independently human-labeled performance.

## Verify locally

From the repository root:

```powershell
.\.conda-w01\python.exe week-12\verify_w12.py
```

The verifier checks the paper sources and PDF, quantitative authorities, figures, retrospective, defense brief, executed audit notebook, research log, documentation, and release boundary. It also invokes the retained Week 11 verifier and executes all four packaged analysis notebooks in an offline temporary workspace while confirming their source hashes remain unchanged.

Verification needs only the pinned Python environment; the PDF gates parse the document directly, so no external PDF tools are required. Rebuilding `W12_Final_Paper.pdf` from `W12_Final_Paper.tex` is a separate step that requires Tectonic (run with `SOURCE_DATE_EPOCH=0` for byte-stable output); the committed PDF is the verified artifact.
