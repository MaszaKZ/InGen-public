from __future__ import annotations

import platform
from pathlib import Path

import nbformat


W12 = Path(__file__).resolve().parent
NOTEBOOK = W12 / "W12_Reproducibility_Audit.ipynb"


def markdown(source: str):
    return nbformat.v4.new_markdown_cell(source.strip() + "\n")


def code(source: str):
    return nbformat.v4.new_code_cell(source.strip() + "\n")


def main() -> None:
    notebook = nbformat.read(NOTEBOOK, as_version=4)
    notebook.cells = [
        markdown(
            """
# Week 12 Reproducibility Audit

**Objective.** Independently recompute the registered common-prompt contrasts from row-level retained evidence, confirm the conditional measurement-stress authorities, and verify that the final publication figures are byte-identical to the admitted figure set.

**Success criteria.** The paired estimates must match the frozen analysis record, the stress values and 14/16 weakest stratum must match the admitted sensitivity record, all 12 copied figure artifacts must match by SHA-256, and the final paper must carry the bounded interpretation.
"""
        ),
        code(
            """
from __future__ import annotations

import csv
import hashlib
import json
import platform
from pathlib import Path


def find_repository_root() -> Path:
    current = Path.cwd().resolve()
    for candidate in (current, *current.parents):
        if (candidate / "week-11").is_dir() and (candidate / "week-12").is_dir():
            return candidate
    raise RuntimeError("repository root not found")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


ROOT = find_repository_root()
PACKAGE = ROOT / "week-11" / "W11_Reproducibility_Package" / "source"
W12 = ROOT / "week-12"
print(
    {
        "repository_root": ".",
        "audit_mode": "analysis-only",
        "python_version": platform.python_version(),
    }
)
"""
        ),
        markdown(
            """
## Audit plan

1. Load the retained row-level results, frozen analysis, and measurement-stress record.
2. Reconstruct paired common-prompt rows by scenario and seed, then compare Qwen-minus-Mistral estimates with the frozen authority.
3. Confirm the weakest validation stratum and stressed contrasts without reinterpreting the stated assumptions.
4. Compare the final figure copies byte-for-byte with the admitted figure set and check the paper's bounded claim language.
"""
        ),
        code(
            """
analysis_path = PACKAGE / "week-07" / "W07_Analysis.json"
results_path = PACKAGE / "week-07" / "W07_Results.csv"
stress_path = PACKAGE / "week-10" / "W10_Judge_Sensitivity.json"

analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
stress = json.loads(stress_path.read_text(encoding="utf-8"))
with results_path.open(encoding="utf-8", newline="") as stream:
    rows = list(csv.DictReader(stream))

inventory = {
    "generation_rows": len(rows),
    "analysis_schema": analysis["schema_version"],
    "stress_schema": stress["schema_version"],
    "results_sha256": sha256(results_path),
}
print(json.dumps(inventory, indent=2))
"""
        ),
        markdown(
            """
## Primary contrast recomputation

The registered generator comparison uses only the byte-identical common prompt. Pairing by scenario identifier and seed ensures that the three unparsed Qwen pressured rows remove their corresponding Mistral rows from the pressured contrast.
"""
        ),
        code(
            """
models = {
    "Mistral": "mistralai/Mistral-7B-Instruct-v0.3",
    "Qwen": "Qwen/Qwen2.5-7B-Instruct",
}
authority = analysis["paired_contrasts"]["primary_common_baseline"]
recomputed = []

for subtype in ("plain", "pressured", "control"):
    by_model = {}
    for label, model_name in models.items():
        by_model[label] = {
            (row["scenario_id"], row["seed"]): int(row["majority_failure"])
            for row in rows
            if row["condition"] == "common_baseline"
            and row["subtype"] == subtype
            and row["generator_model"] == model_name
            and row["majority_failure"] in {"0", "1"}
        }
    paired_keys = sorted(set(by_model["Mistral"]) & set(by_model["Qwen"]))
    mistral_failures = sum(by_model["Mistral"][key] for key in paired_keys)
    qwen_failures = sum(by_model["Qwen"][key] for key in paired_keys)
    estimate = (qwen_failures - mistral_failures) / len(paired_keys)
    expected = authority[subtype]["estimate"]
    assert len(paired_keys) == authority[subtype]["rows"]
    assert abs(estimate - expected) < 1e-12
    recomputed.append(
        {
            "subtype": subtype,
            "paired_rows": len(paired_keys),
            "mistral_failures": mistral_failures,
            "qwen_failures": qwen_failures,
            "qwen_minus_mistral_pp": f"{estimate * 100:+.1f}",
            "authority_match": True,
        }
    )

for result in recomputed:
    print(
        f"{result['subtype']:9s} {result['qwen_minus_mistral_pp']} pp "
        f"({result['qwen_failures']}/{result['paired_rows']} minus "
        f"{result['mistral_failures']}/{result['paired_rows']})"
    )
"""
        ),
        markdown(
            """
## Conditional measurement stress

This check confirms the admitted sensitivity record; it does not turn the false-negative-only calculation into a complete judge-error bound. False positives and a joint uncertainty region remain unestimated.
"""
        ),
        code(
            """
unsafe = stress["strata"]["unsafe_compliance_detection"]
plain_stress = stress["c1_false_negative_stress"]["plain"]
pressured_stress = stress["c1_false_negative_stress"]["pressured"]
control_stress = stress["c1_control_false_negative_stress"]
mitigation = stress["mitigation_false_negative_stress"]["control_cost"]

assert (unsafe["correct"], unsafe["n"]) == (14, 16)
assert plain_stress["stressed_gap_pp"] == -25.6
assert pressured_stress["stressed_gap_pp"] == -35.0
assert control_stress["stressed_gap_pp"] == 18.1
assert mitigation["survives_combined_measurement_stress"] is False

print("Weakest validated unsafe-compliance stratum: 14/16")
print("Stressed contrasts: -25.6 pp plain, -35.0 pp pressured, +18.1 pp control")
print("Observed mitigation pass survives combined stress: False")
"""
        ),
        markdown(
            """
## Artifact identity

The final paper reuses the admitted publication figures. PDF, PNG, and machine-readable JSON copies must be byte-identical, and the paper must state the quantitative and measurement boundaries directly.
"""
        ),
        code(
            """
figure_stems = (
    "Figure1_Operating_Point",
    "Figure2_Prompt_Tradeoffs",
    "Figure3_Measurement_Stress",
    "Figure4_Expected_Loss",
)
identity_checks = []
for stem in figure_stems:
    for suffix in (".pdf", ".png", ".json"):
        admitted = ROOT / "week-11" / "figures" / f"W11_{stem}{suffix}"
        final = W12 / "figures" / f"{stem}{suffix}"
        identity_checks.append(sha256(admitted) == sha256(final))

paper = (W12 / "W12_Final_Paper.md").read_text(encoding="utf-8")
for required in (
    "55.0 percentage points",
    "40.1 percentage points",
    "18.8 percentage points",
    "LLM-judge measurement",
    "does not survive combined measurement stress",
):
    assert required in paper
assert all(identity_checks)

print(f"Artifact identity: {sum(identity_checks)}/{len(identity_checks)} figure files match")
print("Paper claim boundary: present")
"""
        ),
        markdown(
            """
## Evidence boundary and decision

This audit verifies arithmetic, pairing, admitted stress values, artifact identity, and paper-language consistency. It does not rerun model inference, create independent human labels, estimate deployment prevalence, or validate an embodied system. The correct decision is to stop the current analysis: the retained evidence supports the bounded operating-point claim, while measurement and external validity remain follow-up questions.
"""
        ),
        code(
            """
audit_result = {
    "status": "AUDIT_PASS",
    "primary_contrasts_pp": {
        item["subtype"]: item["qwen_minus_mistral_pp"] for item in recomputed
    },
    "weakest_validation_stratum": "14/16",
    "figure_files_identical": f"{sum(identity_checks)}/{len(identity_checks)}",
    "measurement_boundary": "conditional false-negative stress; false positives unestimated",
}
print(json.dumps(audit_result, indent=2))
"""
        ),
    ]
    for index, cell in enumerate(notebook.cells, start=1):
        cell["id"] = f"w12-audit-{index:02d}"
    notebook.metadata.kernelspec = {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    }
    notebook.metadata.language_info = {
        "name": "python",
        "version": platform.python_version(),
    }
    nbformat.write(notebook, NOTEBOOK)
    print(f"built {NOTEBOOK}")


if __name__ == "__main__":
    main()
