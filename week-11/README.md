# Week 11 Capstone Submission

This directory contains the final capstone report, research-review deck, publication figures, and reproducibility package for the contested-authority robustness study. The submission draws its quantitative results from the registered confirmation record and the admitted measurement-stress analysis.

## Deliverables

| Artifact | Description |
|---|---|
| `W11_Capstone_Report.tex` | IEEEtran LaTeX source |
| `W11_Capstone_Report.pdf` | Compiled 20-page academic report |
| `W11_Research_Review_Deck.pptx` | 14-slide research-review deck in the Mid-Review visual style |
| `figures/` | Four publication figures in PNG, PDF, and JSON form |
| `W11_Reproducibility_Package/` | Standalone review package with source evidence, raw outputs, judge ratings, code, artifacts, and model instructions |
| `W11_Reproducibility_Package/receipts/` | Manifest-pinned acceptance receipts: `isolated-cpu-mock.json` and `isolated-short-inference.json` |
| `Wk-11-ResearchLog.md` | Weekly research record, evidence trail, and verification summary |
| `verify_w11.py` | Integrated submission verifier |

## Study result

On the common prompts, the Qwen-minus-Mistral failure-rate differences are -55.0 percentage points for plain caution (family-clustered 95% CI [-77.5, -32.5]), -40.1 points for pressured caution (CI [-55.3, -26.0]), and +18.8 points for authorized controls (CI [+6.2, +34.4]). Under conditional false-negative stress, they become -25.6, -35.0, and +18.1 points. Qwen with deliberation is the only observed intervention pass, but it does not survive combined measurement stress. Estimates, denominators, and intervals are pinned in `w11_evidence.py` and the packaged source evidence.

These results support a confirmatory common-prompt generator contrast within the registered design. Intervention dispositions and stress results remain descriptive and conditional. The study is limited to a synthetic, text-only benchmark and does not establish field or embodied-system performance.

## Verify the submission

From the repository root:

```powershell
python -m venv .venv-w11-verify
.\.venv-w11-verify\Scripts\python -m pip install -r week-11\W11_Reproducibility_Package\requirements-figures.txt
.\.venv-w11-verify\Scripts\python week-11\verify_w11.py
```

The verifier checks evidence continuity, figures, report and slide artifacts, package hashes, and the isolated CPU acceptance receipt.

Model weights are needed only for live inference. See `W11_Reproducibility_Package/README.md` for the pinned manual downloads, checksum verification, minimal GPU smoke test, and full reproduction procedure.
