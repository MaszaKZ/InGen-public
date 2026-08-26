# Contested-Authority Robustness: Reproducibility Package

This package contains the admitted evidence, analysis code, publication figures, capstone report, and research-review deck. It can be reviewed and verified offline with Python's standard library. Model weights are acquired separately only when live inference is required.

## Contents

| Path | Contents |
|---|---|
| `artifacts/report/` | LaTeX source, figure inputs, and compiled report |
| `artifacts/slides/` | 14-slide research-review deck with source notes |
| `artifacts/figures/` | Publication figures in PNG, PDF, and JSON form |
| `analysis/` | Deterministic evidence and figure builders |
| `source/` | Admitted evidence and the original analysis and inference code |
| `model_lock.json` | Ten pinned Hugging Face revisions |
| `models/huggingface/hub/` | Package-local model cache |
| `verify_package.py` | Package, evidence, and artifact verification |
| `verify_models.py` | Model layout, revision, completeness, and checksum verification |
| `run_acceptance.py` | Offline CPU acceptance runner |
| `run_minimal_pipeline_smoke.py` | Minimal generation-to-panel GPU runner |
| `receipts/` | Manifest-pinned verification receipts |
| `package_manifest.json` | SHA-256 and byte size of every distributed file except model weights |

## Verify the package

Run these commands from the package root:

```powershell
python verify_package.py
python -m unittest discover -s tests -v
python run_acceptance.py --model-policy allow-missing
```

The acceptance runner verifies the distributed files, recomputes the reported evidence on CPU, and writes `generated-receipts/cpu-mock-receipt.json`. Its expected status is `mock_only`; no network connection or model files are used.

Two receipts accompany the package. `receipts/isolated-cpu-mock.json` records a clean offline acceptance run. `receipts/isolated-short-inference.json` records an offline NF4 load of the pinned Qwen2.5-7B-Instruct generator and five nonblank generations, one for each registered prompt condition. The second receipt covers that generator only; it does not cover Mistral, the judge panel, or the registered confirmation run.

Files ending in `.snapshot.jsonl` are immutable copies of the admitted raw outputs. New inference runs use the original script-generated filenames and remain separate from those snapshots.

## Download and verify the models

On a networked Windows machine with Python 3.13, open PowerShell in the package root and create an acquisition environment:

```powershell
py -3.13 -m venv .venv-models
$ModelPython = ".\.venv-models\Scripts\python.exe"
$Hf = ".\.venv-models\Scripts\hf.exe"
& $ModelPython -m pip install huggingface_hub==1.19.0

# Use only when a repository requires authentication.
& $Hf auth login

& $Hf download google/flan-t5-base --revision 7bcac572ce56db69c1ea7c8af255c5d7c9672fc2 --cache-dir .\models\huggingface\hub
& $Hf download Qwen/Qwen2.5-1.5B-Instruct --revision 989aa7980e4cf806f80c7fef2b1adb7bc71aa306 --cache-dir .\models\huggingface\hub
& $Hf download Qwen/Qwen2.5-3B-Instruct --revision aa8e72537993ba99e69dfaafa59ed015b17504d1 --cache-dir .\models\huggingface\hub
& $Hf download mistralai/Mistral-7B-Instruct-v0.3 --revision c170c708c41dac9275d15a8fff4eca08d52bab71 --cache-dir .\models\huggingface\hub
& $Hf download Qwen/Qwen2.5-7B-Instruct --revision a09a35458c702b33eeacc393d103063234e8bc28 --cache-dir .\models\huggingface\hub
& $Hf download microsoft/Phi-3.5-mini-instruct --revision 2fe192450127e6a83f7441aef6e3ca586c338b77 --cache-dir .\models\huggingface\hub
& $Hf download ibm-granite/granite-3.3-8b-instruct --revision 51dd4bc2ade4059a6bd87649d68aa11e4fb2529b --cache-dir .\models\huggingface\hub
& $Hf download microsoft/phi-4 --revision 2db69c1c3e91a05d2c64a3185acfbaf36f744e25 --cache-dir .\models\huggingface\hub
& $Hf download tiiuae/Falcon3-10B-Instruct --revision 8799bc6aec0152757221dc6b272d824642db6202 --cache-dir .\models\huggingface\hub
& $Hf download tiiuae/Falcon3-7B-Instruct --revision 1e57a0ecd176c7c139f289c60a74e57f887c3dfb --cache-dir .\models\huggingface\hub
```

Each model is stored at:

```text
models\huggingface\hub\models--ORG--REPO\snapshots\REVISION\
```

Verify the downloads against their pinned Hub revisions, then create a portable checksum manifest:

```powershell
& $Hf cache verify google/flan-t5-base --revision 7bcac572ce56db69c1ea7c8af255c5d7c9672fc2 --cache-dir .\models\huggingface\hub --fail-on-missing-files
& $Hf cache verify Qwen/Qwen2.5-1.5B-Instruct --revision 989aa7980e4cf806f80c7fef2b1adb7bc71aa306 --cache-dir .\models\huggingface\hub --fail-on-missing-files
& $Hf cache verify Qwen/Qwen2.5-3B-Instruct --revision aa8e72537993ba99e69dfaafa59ed015b17504d1 --cache-dir .\models\huggingface\hub --fail-on-missing-files
& $Hf cache verify mistralai/Mistral-7B-Instruct-v0.3 --revision c170c708c41dac9275d15a8fff4eca08d52bab71 --cache-dir .\models\huggingface\hub --fail-on-missing-files
& $Hf cache verify Qwen/Qwen2.5-7B-Instruct --revision a09a35458c702b33eeacc393d103063234e8bc28 --cache-dir .\models\huggingface\hub --fail-on-missing-files
& $Hf cache verify microsoft/Phi-3.5-mini-instruct --revision 2fe192450127e6a83f7441aef6e3ca586c338b77 --cache-dir .\models\huggingface\hub --fail-on-missing-files
& $Hf cache verify ibm-granite/granite-3.3-8b-instruct --revision 51dd4bc2ade4059a6bd87649d68aa11e4fb2529b --cache-dir .\models\huggingface\hub --fail-on-missing-files
& $Hf cache verify microsoft/phi-4 --revision 2db69c1c3e91a05d2c64a3185acfbaf36f744e25 --cache-dir .\models\huggingface\hub --fail-on-missing-files
& $Hf cache verify tiiuae/Falcon3-10B-Instruct --revision 8799bc6aec0152757221dc6b272d824642db6202 --cache-dir .\models\huggingface\hub --fail-on-missing-files
& $Hf cache verify tiiuae/Falcon3-7B-Instruct --revision 1e57a0ecd176c7c139f289c60a74e57f887c3dfb --cache-dir .\models\huggingface\hub --fail-on-missing-files

& $ModelPython verify_models.py --write-checksum-manifest .\models\model-checksums.json
```

For an offline review machine, copy the complete cache and its checksum manifest from the transfer location (`X:\InGen-package` below) without rearranging the snapshot directories:

```powershell
robocopy X:\InGen-package\models\huggingface\hub .\models\huggingface\hub /E
Copy-Item X:\InGen-package\models\model-checksums.json .\models\model-checksums.json
python verify_models.py
```

Before running inference from the package-local cache, enable offline mode and verify the transferred bytes:

```powershell
$env:HF_HOME = (Resolve-Path .\models\huggingface).Path
$env:HF_HUB_CACHE = (Resolve-Path .\models\huggingface\hub).Path
$env:HUGGINGFACE_HUB_CACHE = (Resolve-Path .\models\huggingface\hub).Path
$env:HF_HUB_OFFLINE = "1"
$env:TRANSFORMERS_OFFLINE = "1"
python verify_models.py
```

## Run the minimal GPU pipeline

The tested inference environment uses Windows, Python 3.13.14, PyTorch 2.11.0+cu126, CUDA 12.6, Transformers 5.12.0, Accelerate 1.14.0, and bitsandbytes 0.49.2:

```powershell
py -3.13 -m venv .venv-inference
$InferencePython = ".\.venv-inference\Scripts\python.exe"
& $InferencePython -m pip install --upgrade pip
& $InferencePython -m pip install torch==2.11.0 --index-url https://download.pytorch.org/whl/cu126
& $InferencePython -m pip install -r requirements-inference.txt
& $InferencePython -m pip install -r requirements-figures.txt
& $InferencePython -c "import torch; assert torch.cuda.is_available(); print(torch.__version__, torch.version.cuda, torch.cuda.get_device_name(0))"
```

`run_minimal_pipeline_smoke.py` uses one preflight scenario, the `common_baseline` condition, both generators, all three judges, and panel aggregation. Its fixed result is two generations, six judgments, and two panel rows. Generation is capped at 64 new tokens, and models load sequentially to limit peak GPU memory.

Inspect the plan without loading a model:

```powershell
& $InferencePython run_minimal_pipeline_smoke.py --plan-only
```

With the package-local cache and checksum manifest:

```powershell
& $InferencePython run_minimal_pipeline_smoke.py --checksum-manifest .\models\model-checksums.json
```

An existing verified Hugging Face cache can be used without copying it into the package. Repeat the connected `hf cache verify` command above for the five active models (Mistral-7B-Instruct-v0.3, Qwen2.5-7B-Instruct, Granite-3.3-8B-Instruct, Phi-4, and Falcon3-10B-Instruct) using the shared cache path, then run, with `D:\hf_cache\hub` standing in for that path:

```powershell
$SharedHub = (Resolve-Path D:\hf_cache\hub).Path
& $InferencePython run_minimal_pipeline_smoke.py --plan-only --cache-dir $SharedHub
& $InferencePython run_minimal_pipeline_smoke.py --cache-dir $SharedHub
```

The runner creates a new timestamped directory under `generated-receipts` unless `--output-dir PATH` selects another new directory. It writes the generations, combined judge ratings, panel results, and `smoke_receipt.json` with model revisions, runtime versions, timings, peak CUDA allocation, command provenance, and output hashes.

A reference execution completed in 296 seconds on an NVIDIA GeForce RTX 3080 Ti Laptop GPU and peaked at 9.48 GiB of CUDA allocation. That run used Python 3.11.15 and PyTorch 2.11.0+cu128 as an additional compatibility check; the environment above remains the canonical reproduction environment. The smoke test verifies the live generation-to-judging handoff and panel aggregation, not the registered confirmation dataset or publication estimates.

## Run component checks

These shorter commands load both active generators and all three active judges without connecting the generated responses to the judge panel:

```powershell
Set-Location source
& ..\.venv-inference\Scripts\python.exe week-07\run_w07_replication.py --phase preflight --models mistral qwen --batch-size 1 --limit 1
& ..\.venv-inference\Scripts\python.exe week-07\judge_w07_replication.py --phase gold --judges granite8b phi4_14b falcon3_10b --development-only --limit 1
```

The generator command writes ten rows, one scenario across the five prompt conditions for each generator; the judge command scores one separate development item with each judge. These are compatibility checks, not end-to-end or confirmation results.

## Reproduce the registered study

Full reproduction is optional and GPU-intensive.

1. Make a working copy of the package.
2. Create the canonical inference environment.
3. Download and verify all ten model snapshots, create `models\model-checksums.json`, run `python verify_models.py`, and set the offline cache variables.
4. From the copied package's `source` directory, read `week-07/W07_Replication_Protocol.md` and run:

   ```powershell
   python week-07\run_w07_replication.py --phase confirmation
   python week-07\judge_w07_replication.py --phase confirmation
   python week-07\analyze_w07.py
   python week-07\verify_w07_independent.py --phase confirmation
   ```

5. Compare the new Week 7 outputs with the untouched package. Keep the generated files in the working copy rather than replacing the admitted evidence or publication artifacts.

A full run requires its own provenance record, output hashes, and successful independent verification. The CPU and minimal-smoke receipts do not constitute full-reproduction evidence.

## Regenerate the published artifacts

The figures can be rebuilt on CPU:

```powershell
python -m venv .venv-figures
.\.venv-figures\Scripts\python -m pip install -r requirements-figures.txt
.\.venv-figures\Scripts\python analysis\regenerate_figures.py --output-dir .\regenerated-figures
```

With a TeX runtime installed, compile the report from its self-contained artifact directory:

```powershell
Set-Location artifacts\report
tectonic Capstone_Report.tex
```

## Scope

The package supports claims about a synthetic, text-only authorization benchmark. It does not validate a robot, sensor stack, proprietary module, or field workflow. Common-prompt generator contrasts are confirmatory within the registered design; intervention and measurement-stress results retain their descriptive and conditional scope.
