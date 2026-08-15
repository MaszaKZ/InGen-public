"""Build the Week 7 fresh holdout set for post-fix panel validation.

The v15 instrument corrections were identified by inspecting reviewed-set
failures, so the reviewed 32-case set can no longer serve as independent
evidence. This holdout draws only responses that never entered the gold set,
mirrors the reviewed split's draft composition, and stays draft-only until an
external reviewer records adjudication. The holdout is evaluated exactly once.
"""
from __future__ import annotations

import hashlib
from collections import Counter, defaultdict
from typing import Any

from build_w07_gold import (
    candidates,
    load_sources,
    normalize,
    order_key,
)
from w07_common import (
    GOLD,
    MODELS,
    ROOT,
    WEEK7,
    read_csv,
    read_json,
    read_jsonl,
    sha256_text,
    write_csv,
)

HOLDOUT_SCHEMA_VERSION = "w07-action-holdout-v5-human-review"
# Rounds 1-4 were each evaluated once and failed; all are preserved as records
# and excluded — by response hash and by scenario ID — from the round-5 draw so
# the new holdout is genuinely disjoint from every prior set. The gates are
# outcome-focused, so no standalone ESCALATE_ONLY stratum is needed. Round 5's
# floor rules were pre-registered before this draw in
# W07_Holdout_v5_Design_Registration.json.
SPENT_HOLDOUTS = (
    WEEK7 / "W07_Judge_Holdout_Set.csv",
    WEEK7 / "W07_Judge_Holdout_v2_Set.csv",
    WEEK7 / "W07_Judge_Holdout_v3_Set.csv",
    WEEK7 / "W07_Judge_Holdout_v4_Set.csv",
)
HOLDOUT = WEEK7 / "W07_Judge_Holdout_v5_Set.csv"
HOLDOUT_TARGETS = {
    ("safe_denial", "WITHHOLD"): 3,
    ("unsafe_compliance", "PROCEED_NOW"): 3,
    ("authorized_correct", "PROCEED_NOW"): 3,
    ("over_verification", "WITHHOLD"): 3,
    ("contract_conflict", "AMBIGUOUS"): 2,
}
HOLDOUT_ROWS = sum(HOLDOUT_TARGETS.values()) * len(MODELS)
SELECTION_ORDER = (
    ("contract_conflict", "AMBIGUOUS"),
    ("over_verification", "WITHHOLD"),
    ("unsafe_compliance", "PROCEED_NOW"),
    ("safe_denial", "WITHHOLD"),
    ("authorized_correct", "PROCEED_NOW"),
)
ARCHIVE_SOURCES = (
    (
        "week-06-explorations/rerun-v2/Raw_Model_Outputs.jsonl",
        "week-06-explorations/rerun-v2/frozen/Scenario_Bank.json",
    ),
    (
        "week-06-explorations/archive-v1/artifacts/W06_Confirmatory_Raw_Model_Outputs.jsonl",
        "week-06-explorations/archive-v1/artifacts/W06_Confirmatory_Scenario_Bank.json",
    ),
    (
        "week-06-explorations/rerun-v3/pilot/Raw_Model_Outputs.jsonl",
        "week-06-explorations/rerun-v3/frozen/Pilot_Scenario_Bank.json",
    ),
    (
        "week-06-explorations/rerun-v3/pilot-iter1/Raw_Model_Outputs.jsonl",
        "week-06-explorations/rerun-v3/frozen/Pilot_Scenario_Bank.json",
    ),
)


DIAGNOSTIC_POOL = WEEK7 / "W07_Holdout_Diagnostic_Raw_Model_Outputs.jsonl"


def load_archive_sources() -> list[dict[str, Any]]:
    """Add archived natural Mistral pools that never fed the exhausted gold set."""
    rows: list[dict[str, Any]] = []
    for outputs_rel, bank_rel in ARCHIVE_SOURCES:
        bank = read_json(ROOT / bank_rel)
        scenarios = bank["scenarios"] if isinstance(bank, dict) else bank
        by_id = {scenario["id"]: scenario for scenario in scenarios}
        for row in read_jsonl(ROOT / outputs_rel):
            scenario = by_id.get(row.get("scenario_id"))
            if scenario is None:
                continue
            rows.append(normalize(row, MODELS["mistral"]["id"], outputs_rel, scenario))
    return rows


def load_diagnostic_sources() -> list[dict[str, Any]]:
    """Add targeted fresh-seed generations for strata the recorded pools exhausted."""
    rows: list[dict[str, Any]] = []
    for row in read_jsonl(DIAGNOSTIC_POOL):
        rows.append(
            normalize(
                row,
                row["generator_model"],
                "week-07/W07_Holdout_Diagnostic_Raw_Model_Outputs.jsonl",
                row,
            )
        )
    return rows


def _excluded_keys() -> tuple[set[tuple[str, str]], set[str]]:
    """Responses and scenarios used by the gold set or any spent holdout."""
    prior = list(read_csv(GOLD))
    for spent in SPENT_HOLDOUTS:
        prior += read_csv(spent)
    responses = {(row["generator_model"], row["response_sha256"]) for row in prior}
    scenarios = {row["scenario_id"] for row in prior}
    return responses, scenarios


# Contract-conflict ("declares proceed, body verifies") responses only occur on
# a handful of scenarios, all consumed by the gold set and the first holdout.
# For that one stratum the round-2 draw reuses scenarios but still requires
# fresh responses (distinct response hashes); every other stratum stays fully
# disjoint from the gold set and first holdout by both response hash and
# scenario ID. This relaxation is disclosed in the documentation.
SCENARIO_REUSE_STRATA = {"contract_conflict"}
# Contract-conflict responses are scarce for Qwen even at higher sampling
# temperature, so the stratum is best-effort: take what fresh responses exist
# (up to the target per generator) and require a minimum total for the
# ambiguity gate to be exercised.
BEST_EFFORT_STRATA = {"contract_conflict"}
CONTRACT_CONFLICT_MIN = 2


def select_holdout(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    used_responses, used_scenario_ids = _excluded_keys()
    buckets: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if (row["generator_model"], row["response_sha256"]) in used_responses:
            continue
        buckets[(row["generator_model"], row["case_type"], row["gold_action"])].append(row)

    selected: list[dict[str, Any]] = []
    for model in (MODELS["mistral"]["id"], MODELS["qwen"]["id"]):
        used_scenarios: set[str] = set()
        for case_type, action in SELECTION_ORDER:
            target = HOLDOUT_TARGETS[(case_type, action)]
            allow_prior_scenario = case_type in SCENARIO_REUSE_STRATA
            pool = sorted(
                buckets[(model, case_type, action)],
                key=lambda row: order_key(row, f"holdout-v2-{case_type}-{action}"),
            )
            chosen: list[dict[str, Any]] = []
            # First pass: distinct scenarios not seen in prior sets or this holdout.
            for row in pool:
                if not allow_prior_scenario and row["scenario_id"] in used_scenario_ids:
                    continue
                if row["scenario_sha256"] in used_scenarios:
                    continue
                chosen.append(row)
                used_scenarios.add(row["scenario_sha256"])
                if len(chosen) == target:
                    break
            # Fallback: distinct responses regardless of scenario. For strata
            # that must stay scenario-disjoint this still forbids prior scenarios.
            if len(chosen) < target:
                chosen_hashes = {row["response_sha256"] for row in chosen}
                for row in pool:
                    if not allow_prior_scenario and row["scenario_id"] in used_scenario_ids:
                        continue
                    if row["response_sha256"] in chosen_hashes:
                        continue
                    chosen.append(row)
                    chosen_hashes.add(row["response_sha256"])
                    if len(chosen) == target:
                        break
            if len(chosen) != target and case_type not in BEST_EFFORT_STRATA:
                raise RuntimeError(
                    f"insufficient candidates for {model}/{case_type}/{action}: "
                    f"need {target}, found {len(chosen)}; targeted fresh-seed generation is required"
                )
            selected.extend(chosen)
    ambiguity = sum(1 for row in selected if row["case_type"] == "contract_conflict")
    if ambiguity < CONTRACT_CONFLICT_MIN:
        raise RuntimeError(
            f"contract-conflict stratum has {ambiguity} rows; the ambiguity gate "
            f"needs at least {CONTRACT_CONFLICT_MIN}; more fresh conflicts are required"
        )
    return selected


def to_holdout(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for row in rows:
        gold_id = sha256_text(
            f"{HOLDOUT_SCHEMA_VERSION}|{row['generator_model']}|{row['source_artifact']}|"
            f"{row['condition']}|{row['scenario_id']}|{row['source_seed']}|{row['response_sha256']}"
        )[:20]
        output.append({
            "gold_id": gold_id,
            "gold_schema_version": HOLDOUT_SCHEMA_VERSION,
            "split": "holdout",
            "generator_model": row["generator_model"],
            "condition": row["condition"],
            "scenario_id": row["scenario_id"],
            "family": row["family"],
            "mode": row["mode"],
            "subtype": row["subtype"],
            "tactic": row["tactic"],
            "scenario": row["scenario"],
            "response": row["response"],
            "gold_action": row["gold_action"],
            "gold_evidence": row["gold_evidence"],
            "case_type": row["case_type"],
            "stress_case": 0,
            "annotation_method": "AI-assisted full-response operational-action rubric",
            "review_status": "pending",
            "reviewed_action": "",
            "review_note": "",
            "reviewer_role": "",
            "reviewed_utc": "",
            "source_artifact": row["source_artifact"],
            "source_response_id": row["source_response_id"],
            "source_seed": row["source_seed"],
            "response_sha256": row["response_sha256"],
        })
    for model in (MODELS["mistral"]["id"], MODELS["qwen"]["id"]):
        for case_type in (
            "safe_denial",
            "unsafe_compliance",
            "authorized_correct",
            "over_verification",
            "contract_conflict",
        ):
            choices = [
                row
                for row in output
                if row["generator_model"] == model and row["case_type"] == case_type
            ]
            if not choices:
                continue
            selected = min(
                choices,
                key=lambda row: hashlib.sha256(
                    f"holdout-stress-v2|{row['gold_id']}".encode()
                ).hexdigest(),
            )
            selected["stress_case"] = 1
    output.sort(key=lambda row: (row["generator_model"], row["case_type"], row["gold_id"]))
    return output


def validate_holdout(rows: list[dict[str, Any]]) -> None:
    if len({row["gold_id"] for row in rows}) != len(rows):
        raise AssertionError("holdout gold_id values are not unique")
    if len({(row["generator_model"], row["response_sha256"]) for row in rows}) != len(rows):
        raise AssertionError("holdout responses are not unique within generator")
    used_responses, used_scenario_ids = _excluded_keys()
    response_overlap = {
        (row["generator_model"], row["response_sha256"]) for row in rows
    } & used_responses
    if response_overlap:
        raise AssertionError(
            f"holdout responses overlap the gold set or spent holdout: {response_overlap}"
        )
    # Every stratum except the disclosed contract-conflict reuse must be
    # scenario-disjoint from the prior sets.
    disjoint_scenarios = {
        row["scenario_id"]
        for row in rows
        if row["case_type"] not in SCENARIO_REUSE_STRATA
    }
    scenario_overlap = disjoint_scenarios & used_scenario_ids
    if scenario_overlap:
        raise AssertionError(
            f"holdout scenarios overlap the gold set or spent holdout: {scenario_overlap}"
        )
    # Strict strata meet their per-generator targets; the contract-conflict
    # stratum is best-effort but must clear the ambiguity minimum.
    for model in (MODELS["mistral"]["id"], MODELS["qwen"]["id"]):
        subset = [row for row in rows if row["generator_model"] == model]
        actual = Counter((row["case_type"], row["gold_action"]) for row in subset)
        for key, target in HOLDOUT_TARGETS.items():
            if key[0] in BEST_EFFORT_STRATA:
                continue
            if actual.get(key, 0) != target:
                raise AssertionError(
                    f"holdout composition is incorrect for {model} {key}: {actual.get(key, 0)}"
                )
    ambiguity = sum(1 for row in rows if row["case_type"] == "contract_conflict")
    if ambiguity < CONTRACT_CONFLICT_MIN:
        raise AssertionError(f"holdout has only {ambiguity} contract-conflict rows")
    # One stress row per non-empty generator/case-type stratum.
    present_strata = {
        (row["generator_model"], row["case_type"]) for row in rows
    }
    if sum(int(row["stress_case"]) for row in rows) != len(present_strata):
        raise AssertionError("holdout stress rows must be one per present stratum")
    reviewed = [row for row in rows if row["review_status"] != "pending"]
    for row in reviewed:
        if row["review_status"] not in {"confirmed", "corrected"}:
            raise AssertionError(f"invalid holdout review state: {row['gold_id']}")


def main() -> None:
    existing = read_csv(HOLDOUT)
    if existing and any(
        row["review_status"] in {"confirmed", "corrected"} for row in existing
    ):
        validate_holdout(existing)
        print("validated committed externally reviewed holdout; review fields are preserved")
        return
    output = to_holdout(
        select_holdout(
            candidates(
                load_sources() + load_archive_sources() + load_diagnostic_sources()
            )
        )
    )
    validate_holdout(output)
    write_csv(HOLDOUT, output)
    reused = {}
    for model in (MODELS["mistral"]["id"], MODELS["qwen"]["id"]):
        for case_type in {row["case_type"] for row in output}:
            stratum = [
                row for row in output
                if row["generator_model"] == model and row["case_type"] == case_type
            ]
            scenarios = {row["scenario_id"] for row in stratum}
            if len(scenarios) != len(stratum):
                reused[f"{model.split('/')[0]}/{case_type}"] = {
                    "responses": len(stratum),
                    "distinct_scenarios": len(scenarios),
                }
    print(
        "holdout rows",
        len(output),
        "actions",
        Counter(row["gold_action"] for row in output),
        "case types",
        Counter(row["case_type"] for row in output),
    )
    if reused:
        print(
            "scenario-distinctness relaxed (distinct responses, repeated scenario) "
            "for scarce strata:",
            reused,
        )


if __name__ == "__main__":
    main()
