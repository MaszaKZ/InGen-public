# Wk-01 Research Log

Date: 2026-06-13

## Work Completed

- Created a local Python 3.11 Conda environment at `.conda-w01`.
- Installed CUDA-enabled PyTorch, HuggingFace `transformers`, `datasets`, `huggingface_hub`, PEFT, LangChain, W&B, NumPy, pandas, SciPy, and notebook execution dependencies.
- Reviewed the public Origami AI page and the 24-page internship plan PDF, taking the public Origami page as the reference for PIC 2.0 model names and roles.
- Read and annotated the eight anchor references: OpenVLA, safe robot foundation models, AI alignment survey, public Origami documentation, continuous-control GRPO, SNOW, DemPref, and MAGEC, with additional mapping support from conformal decision theory, CBF safe RL, sensor calibration, and hierarchical AIRL papers.
- Wrote `W01_Research_Landscape.md`: physical AI ecosystem map, per-platform AI research angles, PIC 2.0 open-literature mapping, and three candidate research themes.
- Built and ran `W01_env_check.ipynb` to verify the CUDA toolchain reproducibly.

## Source Note

The public Origami AI page is the reference for all public-facing PIC 2.0 model names and roles: https://www.ingendynamics.com/origami-paper.html. It defines the six models as GRPO (Decision Maker), STUM (Confidence Meter), SEOM (Safety Guardian), AMDC (Sensor Calibrator), HTD-IRL (Task Planner), and CRL-MRS (Team Coordinator). The internship plan sets the Week 1 deliverable structure and product anchors; no confidential content from it appears in these public artifacts.

## Hardest PIC 2.0 Mapping

The PIC 2.0 model mapping I found hardest to make was `SEOM`.

Reason: the public Origami page defines `SEOM` as Self-Supervised Ethical Oversight, which overlaps several open areas but does not reduce cleanly to one: constrained policy optimization, control barrier functions, safe RL, constitutional AI, and runtime shielding. The closest structural mapping is safe RL with differentiable safety costs, but the open question is whether domain-specific ethical rules can be encoded as gradients without creating brittle reward hacks.

## Open Questions

- What are the implementation interfaces and training objectives for GRPO, STUM, SEOM, AMDC, HTD-IRL, and CRL-MRS in PIC 2.0?
- Does Aido Rover prioritize navigation-only autonomy, mobile manipulation, human interaction, or fleet coordination in the first research milestone?
- Should Week 2's literature clusters prioritize safety-constrained policy learning, calibrated uncertainty gates, or demo-to-fleet task transfer?

## Toolchain Notes

- Base `python` on PATH is Python 3.13.9.
- Required Python 3.11 is available through `.conda-w01\python.exe`.
- PyTorch is CUDA-enabled: `torch 2.11.0+cu128`, CUDA runtime `12.8`, verified on `NVIDIA GeForce RTX 3080 Ti Laptop GPU`.
- NumPy, pandas, and SciPy are installed for Week 2-6 evaluation/statistics work.
- W&B verification uses disabled/offline mode so the notebook does not require credentials.
- HuggingFace verification avoids downloading models to keep fresh-clone execution lightweight.
