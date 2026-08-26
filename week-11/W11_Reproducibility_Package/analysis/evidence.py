"""Authoritative quantitative evidence used by the Week 11 submission."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


MISTRAL_ID = "mistralai/Mistral-7B-Instruct-v0.3"
QWEN_ID = "Qwen/Qwen2.5-7B-Instruct"
MODEL_LABELS = {
    MISTRAL_ID: "Mistral-7B-Instruct-v0.3",
    QWEN_ID: "Qwen2.5-7B-Instruct",
}
CONDITION_LABELS = {
    "common_baseline": "Common baseline",
    "adapted_baseline": "Adapted baseline",
    "deliberation": "Deliberation",
    "structured_output": "Structured output",
    "constraint_gated": "Constraint gating",
}
SUBTYPE_LABELS = {
    "plain": "Plain caution",
    "pressured": "Pressured caution",
    "control": "Authorized control",
}
FAMILY_LABELS = {
    "rail_platform_gate": "Rail-platform gate",
    "generator_transfer": "Generator transfer",
    "restricted_drone_launch": "Restricted drone launch",
    "archive_case_purge": "Archive-case purge",
    "chemical_bypass_valve": "Chemical bypass valve",
    "biometric_enrollment": "Biometric enrollment",
    "warehouse_exclusion_zone": "Warehouse exclusion zone",
    "evacuation_alarm_silence": "Evacuation-alarm silence",
    "insulin_administration": "Insulin administration",
    "bed_exit_alarm": "Bed-exit alarm",
    "private_suite_entry": "Private-suite entry",
    "telehealth_recording": "Telehealth recording",
    "feeding_tube_flush": "Feeding-tube flush",
    "powered_lift_transfer": "Powered lift transfer",
    "specimen_handoff": "Specimen handoff",
    "resident_reimbursement": "Resident reimbursement",
}


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"required evidence is missing: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"evidence root must be an object: {path}")
    return payload


def load_evidence(root: Path) -> dict[str, dict[str, Any]]:
    """Load the exact upstream evidence admitted by Week 10."""
    root = root.resolve()
    return {
        "week6": _read_json(root / "week-06" / "W06_Analysis.json"),
        "week7": _read_json(root / "week-07" / "W07_Analysis.json"),
        "week7_metadata": _read_json(root / "week-07" / "W07_Run_Metadata.json"),
        "week8": _read_json(root / "week-08" / "W08_Pressure_Cue_Audit.json"),
        "week10": _read_json(root / "week-10" / "W10_Judge_Sensitivity.json"),
    }


def _pp(value: float) -> float:
    return round(100.0 * float(value), 1)


def common_baseline_rows(evidence: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    primary = evidence["week7"]["paired_contrasts"]["primary_common_baseline"]
    rows: list[dict[str, Any]] = []
    for subtype in ("plain", "pressured", "control"):
        item = primary[subtype]
        rows.append(
            {
                "subtype": subtype,
                "label": SUBTYPE_LABELS[subtype],
                "estimate_pp": _pp(item["estimate"]),
                "ci_pp": [_pp(item["ci_low"]), _pp(item["ci_high"])],
                "families": int(item["families"]),
                "rows": int(item["rows"]),
            }
        )
    return rows


def all_rate_rows(evidence: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in evidence["week7"]["rates"]:
        model_id = str(item["model"])
        condition = str(item["condition"])
        subtype = str(item["subtype"])
        rows.append(
            {
                "model_id": model_id,
                "model": MODEL_LABELS[model_id],
                "condition_id": condition,
                "condition": CONDITION_LABELS[condition],
                "subtype": subtype,
                "subtype_label": SUBTYPE_LABELS[subtype],
                "rate_pct": _pp(item["estimate"]),
                "ci_pct": [_pp(item["ci_low"]), _pp(item["ci_high"])],
                "rows": int(item["rows"]),
                "failures": int(round(float(item["estimate"]) * int(item["rows"]))),
            }
        )
    return rows


def mitigation_rows(evidence: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    results = evidence["week7"]["mitigation_rule"]["results"]
    stress_survives = bool(
        evidence["week10"]["mitigation_false_negative_stress"]["control_cost"]
        ["survives_combined_measurement_stress"]
    )
    rows: list[dict[str, Any]] = []
    for model_id in (MISTRAL_ID, QWEN_ID):
        for condition in ("deliberation", "structured_output", "constraint_gated"):
            item = results[model_id][condition]
            observed_pass = bool(item["passes"])
            rows.append(
                {
                    "model_id": model_id,
                    "model": MODEL_LABELS[model_id],
                    "condition_id": condition,
                    "condition": CONDITION_LABELS[condition],
                    "pressured_relative_reduction_pct": _pp(
                        item["pressured_relative_reduction"]
                    ),
                    "control_cost_pp": _pp(item["control_failure_increase"]),
                    "observed_pass": observed_pass,
                    "combined_stress_pass": observed_pass and stress_survives,
                }
            )
    return rows


def stress_rows(evidence: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    w10 = evidence["week10"]
    rows: list[dict[str, Any]] = []
    for endpoint in ("plain", "pressured"):
        item = w10["c1_false_negative_stress"][endpoint]
        rows.append(
            {
                "endpoint": endpoint,
                "label": SUBTYPE_LABELS[endpoint],
                "observed_pp": round(float(item["observed_gap_pp"]), 1),
                "stressed_pp": round(float(item["stressed_gap_pp"]), 1),
                "sign_survives": bool(item["sign_survives_false_negative_stress"]),
            }
        )
    control = w10["c1_control_false_negative_stress"]
    rows.append(
        {
            "endpoint": "control",
            "label": SUBTYPE_LABELS["control"],
            "observed_pp": round(float(control["observed_gap_pp"]), 1),
            "stressed_pp": round(float(control["stressed_gap_pp"]), 1),
            "sign_survives": bool(control["sign_survives_false_negative_stress"]),
        }
    )
    return rows


def week6_diagnostic(evidence: dict[str, dict[str, Any]]) -> dict[str, Any]:
    item = evidence["week6"]["diagnostic_baseline_pressured_vs_plain"]
    return {
        "plain_failures": 3,
        "pressured_failures": 12,
        "rows": 32,
        "difference_pp": _pp(item["difference_b_minus_a"]),
        "ci_pp": [
            _pp(item["family_bootstrap"]["lower_95"]),
            _pp(item["family_bootstrap"]["upper_95"]),
        ],
        "mcnemar_p": round(float(item["exact_two_sided_mcnemar_p"]), 4),
    }


def per_family_common_rows(root: Path) -> list[dict[str, Any]]:
    """Descriptive per-family counts under the common baseline.

    Counts come from the registered panel-majority results record. Rows with
    an unparsed panel endpoint carry an empty outcome and are excluded from
    both numerator and denominator, matching the registered denominator audit.
    """
    path = root.resolve() / "week-07" / "W07_Results.csv"
    if not path.is_file():
        raise FileNotFoundError(f"required evidence is missing: {path}")
    counts: dict[tuple[str, str, str], list[int]] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        for record in csv.DictReader(handle):
            if record["condition"] != "common_baseline":
                continue
            outcome = record["majority_failure"]
            if outcome not in ("0", "1"):
                continue
            key = (record["family"], record["generator_model"], record["subtype"])
            cell = counts.setdefault(key, [0, 0])
            cell[0] += int(outcome)
            cell[1] += 1
    rows: list[dict[str, Any]] = []
    for family_id, family_label in FAMILY_LABELS.items():
        row: dict[str, Any] = {"family_id": family_id, "family": family_label}
        for model_id, model_key in ((MISTRAL_ID, "mistral"), (QWEN_ID, "qwen")):
            for subtype in ("plain", "pressured", "control"):
                failures, evaluable = counts[(family_id, model_id, subtype)]
                row[f"{model_key}_{subtype}"] = {
                    "failures": failures,
                    "rows": evaluable,
                }
        rows.append(row)
    return rows


def loss_curve_data(evidence: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Expected-loss coefficients implied by the registered contrasts.

    Follows the report's illustrative weighting: equal aggregate exposure to
    caution and authorized-control states, with the caution share split by the
    plain fraction alpha. All quantities are point-estimate derivations; no
    new inference is performed.
    """
    observed = {
        row["subtype"]: row["estimate_pp"] / 100.0
        for row in common_baseline_rows(evidence)
    }
    stressed = {
        row["endpoint"]: row["stressed_pp"] / 100.0
        for row in stress_rows(evidence)
    }
    alphas = (1.0, 0.5, 0.0)

    def curve(contrasts: dict[str, float]) -> dict[str, Any]:
        control_delta = contrasts["control"]
        entries = []
        for alpha in alphas:
            caution_improvement = -(
                alpha * contrasts["plain"] + (1.0 - alpha) * contrasts["pressured"]
            )
            entries.append(
                {
                    "alpha": alpha,
                    "caution_improvement": round(caution_improvement, 4),
                    "break_even_cost_ratio": round(
                        control_delta / caution_improvement, 3
                    ),
                }
            )
        return {"control_delta": round(control_delta, 4), "alphas": entries}

    return {
        "weighting": "equal aggregate caution and authorized-control exposure",
        "observed": curve(observed),
        "stressed": curve(stressed),
    }
