# Week 10 — Paper Revision, Reproducibility Package & Capstone Draft

Week 10 delivers the internship plan's Phase D revision milestone under the
review recorded in [`W10_Feedback.md`](W10_Feedback.md): reproducibility,
auditability, paper refinement, and the capstone evidence base.

## Plan deliverables

| Artifact | Content |
| --- | --- |
| [`W10_Paper_Draft_v2.md`](W10_Paper_Draft_v2.md) | Revised paper superseding v1; addresses all four self-critique points: blunter judge dependence (abstract, §1), conditional judge-measurement stress (§4.5), full FoMER engagement (§2.1), and the finding that the sole observed-data mitigation pass is not measurement-robust (§4.2, §6) |
| [`W10_Reproducibility_Package/`](W10_Reproducibility_Package/README.md) | Pinned requirements, hash-verified raw-evidence restoration (`fetch_data.py` + `data_manifest.json`), per-script documentation for weeks 3–10, deterministic one-command regeneration (`regenerate_all.py`), isolated fresh inference (`reproduce_fresh.py`), and the clean-environment test record |
| [`W10_Capstone_Outline.md`](W10_Capstone_Outline.md) | The eleven-section Weeks 11–12 capstone structure with per-section evidence artifacts, plus drafted sections (ii) and (iii) |
| [`Wk-10-ResearchLog.md`](Wk-10-ResearchLog.md) | Weekly research log with the deliverable-conformance table and verification record |

## Supplementary artifacts

| Artifact | Content |
| --- | --- |
| [`analyze_w10_judge_sensitivity.py`](analyze_w10_judge_sensitivity.py) | Deterministic conditional false-negative stress analysis for C1 and the mitigation-rule pass |
| [`W10_Judge_Sensitivity.json`](W10_Judge_Sensitivity.json) | Conditional false-negative stress results for all three C1 contrasts and both sides of the observed-data mitigation pass |
| [`verify_w10.py`](verify_w10.py) | Eleven-section independent verifier of every Week 10 deliverable |
| [`W10_Reproducibility_Package/reproduce_fresh.py`](W10_Reproducibility_Package/reproduce_fresh.py) | Plan, smoke-test, or execute an isolated revision-locked fresh evidence run |
| [`W10_Reproducibility_Package/model_lock.json`](W10_Reproducibility_Package/model_lock.json) | Immutable model repository IDs and revisions for fresh inference |
| [`W10_Reproducibility_Package/prefetch_models.py`](W10_Reproducibility_Package/prefetch_models.py) | Locked model acquisition into the full run's local cache |
| [`W10_Reproducibility_Package/verify_fresh_run.py`](W10_Reproducibility_Package/verify_fresh_run.py) | Structural, provenance, count, notebook, and derived-artifact verification for a full fresh run |

## Verification

From the repository root (restore an independently supplied bundle first when
raw evidence is needed):

```powershell
python week-10\W10_Reproducibility_Package\fetch_data.py --from-path BUNDLE.zip
python week-10\W10_Reproducibility_Package\fetch_data.py --check
python week-10\analyze_w10_judge_sensitivity.py
python week-10\verify_w10.py
python week-10\W10_Reproducibility_Package\regenerate_all.py --tier 1 --with-tests
```

The fresh workflow is separate from deterministic restoration and regeneration.
Inspect it without filesystem writes, exercise its isolated smoke path, or
deliberately start the compute-intensive full workflow with:

```powershell
python week-10/W10_Reproducibility_Package/reproduce_fresh.py --mode plan
python week-10/W10_Reproducibility_Package/reproduce_fresh.py --mode mock
python week-10/W10_Reproducibility_Package/reproduce_fresh.py --mode full --accept-compute-cost --bundle BUNDLE.zip
```

The implementation and synthetic orchestration tests are verified, but the
full Tier 2 GPU campaign has not been run. A fresh completion exists only when
the full command exits zero and `verify_fresh_run.py` records a `complete`
`run-receipt.json`; plan and mock results are not inference evidence.

`verify_w10.py` recomputes the measurement stress analysis end-to-end from the
committed amendment, analysis JSON, and results CSV; re-derives the checked
table rows and prose statistics in draft v2; and checks the package's manifest
hashes, pinned requirements, capstone structure, and clean-environment test
record. It prints `PASS: Week 10 verification complete` only when every
section passes.
