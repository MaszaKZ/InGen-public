# Week 6 Reproduction Instructions

Week 6 tests whether adversarial social pressure changes safety-boundary
compliance in Mistral-7B-Instruct-v0.3 and compares four prompt conditions.
The committed evidence contains 384 model responses and 1,152 independent
judge ratings.

Run the commands below from the repository root. They assume the recorded
Windows environment at `.conda-w01`; if using another environment, replace the
Python executable and match the package versions recorded in
`W06_Run_Metadata.json`. The public generation and judge models must already be
available locally or be downloadable from Hugging Face.

## Dry-run gate

The dry run uses only the holdout families and writes the `*.dry_run` artifacts.

```powershell
.\.conda-w01\python.exe week-06\build_w06_bank.py
.\.conda-w01\python.exe week-06\run_w06_experiment2.py --dry-run
.\.conda-w01\python.exe week-06\judge_w06_experiment2.py --dry-run
.\.conda-w01\python.exe week-06\test_w06_experiment2.py --dry-run
```

## Full experiment

These commands overwrite the canonical full-run outputs in `week-06/`.

```powershell
.\.conda-w01\python.exe week-06\run_w06_experiment2.py
.\.conda-w01\python.exe week-06\judge_w06_experiment2.py
.\.conda-w01\python.exe week-06\test_w06_experiment2.py
.\.conda-w01\python.exe week-06\verify_w06_independent.py
```

A successful rerun contains:

- 384 rows in `W06_Results.csv` and 384 raw response records;
- three judge decisions for every response, or 1,152 individual ratings;
- passing integrity tests; and
- an independent recomputation that agrees with `W06_Analysis.json`.

Exact labels, aggregate tables, and headline findings should match the
committed evidence. Timestamps and free-text judge rationales can differ.

## Execute the analysis notebook

After the ratings and analysis files have been verified, execute the notebook
from the repository root:

```powershell
.\.conda-w01\python.exe -m jupyter nbconvert --to notebook --execute --inplace week-06\W06_Experiment2_Notebook.ipynb --ExecutePreprocessor.timeout=600
```

The notebook reads the committed ratings and analysis artifacts; it does not
rerun model generation or judging. `W06_Mid_Review_Deck.pptx` is a reviewed,
static presentation and is not part of the automated reproduction sequence.

## Evidence map

- `W06_Scenario_Bank.json` and `.csv`: synthetic, public-safe scenario bank.
- `W06_Raw_Model_Outputs.jsonl`: unprocessed model responses.
- `W06_Results.csv`: response-level experiment records.
- `W06_Judge_Ratings.csv`: individual and majority judge labels.
- `W06_Analysis.json`: statistical analysis and headline comparisons.
- `W06_Run_Metadata.json`: model, seeds, batch size, runtime, and direct hashes.
- `test_w06_experiment2.py`: design and evidence-chain integrity tests.
- `verify_w06_independent.py`: independent standard-library recomputation.

The scenarios contain no customer data, internal-system details, or
proprietary procedures.
