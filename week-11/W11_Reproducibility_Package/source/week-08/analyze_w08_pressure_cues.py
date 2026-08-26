"""Post-outcome exploratory audit of Week 7 plain/pressure pairs.

This script does not run model inference. It reads the committed Week 7
confirmation bank and common-baseline panel results, checks whether the
previously proposed prerequisite-salience contrast is estimable, and writes a
deterministic descriptive audit.
"""

from __future__ import annotations

import csv
import json
import math
import random
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
WEEK7 = ROOT / "week-07"
WEEK8 = ROOT / "week-08"
BANK_PATH = WEEK7 / "W07_Confirmation_Bank.json"
RESULTS_PATH = WEEK7 / "W07_Results.csv"
JSON_PATH = WEEK8 / "W08_Pressure_Cue_Audit.json"
MARKDOWN_PATH = WEEK8 / "W08_Pressure_Cue_Audit.md"

BOOTSTRAP_SEED = 20260726
BOOTSTRAP_DRAWS = 10_000

# A plain item enters the proposed "explicitly missing" stratum only if it
# actually says that an authorization prerequisite is unavailable, absent, or
# unverified. Merely stating the governing rule does not satisfy this coding
# definition.
EXPLICIT_MISSING_PATTERNS = (
    r"\bnot recorded\b",
    r"\bnot on file\b",
    r"\bno (?:active |valid |recorded )?"
    r"(?:record|permit|authorization|approval|clearance|consent)\b",
    r"\bmissing\b",
    r"\babsent\b",
    r"\bunverified\b",
    r"\bunconfirmed\b",
    r"\bnot verified\b",
    r"\bnot confirmed\b",
    r"\bhas not been\b",
    r"\bhasn't been\b",
    r"\bwithout (?:a |an |the )?"
    r"(?:permit|authorization|approval|clearance|consent)\b",
)

MODEL_LABELS = {
    "mistralai/Mistral-7B-Instruct-v0.3": "Mistral-7B-Instruct-v0.3",
    "Qwen/Qwen2.5-7B-Instruct": "Qwen2.5-7B-Instruct",
}

TACTIC_ORDER = (
    "authority_claim",
    "false_clearance",
    "urgency",
    "normalization",
)


def load_bank() -> dict[str, Any]:
    return json.loads(BANK_PATH.read_text(encoding="utf-8"))


def load_results() -> list[dict[str, str]]:
    with RESULTS_PATH.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def explicit_missing(stimulus: str) -> bool:
    return any(re.search(pattern, stimulus, flags=re.IGNORECASE) for pattern in EXPLICIT_MISSING_PATTERNS)


def quantile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def clustered_interval(
    pairs: list[dict[str, Any]],
    rng: random.Random,
) -> tuple[float, float]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for pair in pairs:
        grouped[pair["family"]].append(pair)
    families = sorted(grouped)
    draws: list[float] = []
    for _ in range(BOOTSTRAP_DRAWS):
        sampled = [rng.choice(families) for _ in families]
        differences = [
            pair["difference"]
            for family in sampled
            for pair in grouped[family]
        ]
        draws.append(sum(differences) / len(differences))
    return quantile(draws, 0.025), quantile(draws, 0.975)


def summarize(
    pairs: list[dict[str, Any]],
    *,
    model: str,
    tactic: str,
    rng: random.Random,
) -> dict[str, Any]:
    plain_failures = sum(pair["plain_failure"] for pair in pairs)
    pressured_failures = sum(pair["pressured_failure"] for pair in pairs)
    difference = sum(pair["difference"] for pair in pairs) / len(pairs)
    low, high = clustered_interval(pairs, rng)
    return {
        "model": model,
        "model_label": MODEL_LABELS.get(model, model),
        "tactic": tactic,
        "complete_pairs": len(pairs),
        "families": len({pair["family"] for pair in pairs}),
        "plain_failures": plain_failures,
        "plain_rate": plain_failures / len(pairs),
        "pressured_failures": pressured_failures,
        "pressured_rate": pressured_failures / len(pairs),
        "paired_difference_pressured_minus_plain": difference,
        "family_clustered_bootstrap_95_ci": [low, high],
    }


def build_audit() -> dict[str, Any]:
    bank = load_bank()
    scenarios = bank["scenarios"]
    plain = [scenario for scenario in scenarios if scenario["subtype"] == "plain"]
    pressured = [scenario for scenario in scenarios if scenario["subtype"] == "pressured"]
    plain_by_id = {scenario["scenario_id"]: scenario for scenario in plain}

    def code_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "scenario_id": scenario["scenario_id"],
                "family": scenario["family"],
                "pair_variant": scenario["pair_variant"],
                "tactic": scenario.get("tactic"),
                "explicitly_states_missing_prerequisite": explicit_missing(scenario["stimulus"]),
            }
            for scenario in items
        ]

    plain_coding = code_items(plain)
    pressured_coding = code_items(pressured)
    explicit_count = sum(item["explicitly_states_missing_prerequisite"] for item in plain_coding)

    # The same coding is applied to the pressured arm. Salience is the factor the
    # proposed contrast wanted to isolate, so any pressured-side variation in it is
    # a confound that must be disclosed rather than left inside "bundled wording".
    pressured_explicit_count = sum(
        item["explicitly_states_missing_prerequisite"] for item in pressured_coding
    )
    pressured_explicit_by_tactic = {
        tactic: sum(
            item["explicitly_states_missing_prerequisite"]
            for item in pressured_coding
            if item["tactic"] == tactic
        )
        for tactic in TACTIC_ORDER
    }
    pressured_total_by_tactic = {
        tactic: sum(1 for item in pressured_coding if item["tactic"] == tactic)
        for tactic in TACTIC_ORDER
    }
    salience_confounded_tactics = sorted(
        tactic for tactic, count in pressured_explicit_by_tactic.items() if count
    )

    common = [
        row
        for row in load_results()
        if row["condition"] == "common_baseline"
        and row["subtype"] in {"plain", "pressured"}
    ]
    result_index: dict[tuple[str, int, str], dict[str, str]] = {}
    model_seeds: dict[str, set[int]] = defaultdict(set)
    for row in common:
        key = (row["generator_model"], int(row["seed"]), row["scenario_id"])
        if key in result_index:
            raise ValueError(f"Duplicate common-baseline result: {key}")
        result_index[key] = row
        model_seeds[row["generator_model"]].add(int(row["seed"]))

    pairs: list[dict[str, Any]] = []
    missing_pairs: list[dict[str, Any]] = []
    for model in sorted(model_seeds):
        for pressured_scenario in sorted(
            pressured,
            key=lambda item: (item["family"], item["pair_variant"]),
        ):
            plain_id = pressured_scenario["paired_plain_id"]
            plain_scenario = plain_by_id[plain_id]
            for seed in sorted(model_seeds[model]):
                plain_row = result_index.get((model, seed, plain_id))
                pressured_row = result_index.get(
                    (model, seed, pressured_scenario["scenario_id"])
                )
                reasons: list[str] = []
                if plain_row is None:
                    reasons.append("plain row absent")
                elif plain_row["majority_failure"] == "":
                    reasons.append("plain panel endpoint unparsed")
                if pressured_row is None:
                    reasons.append("pressured row absent")
                elif pressured_row["majority_failure"] == "":
                    reasons.append("pressured panel endpoint unparsed")
                if reasons:
                    missing_pairs.append(
                        {
                            "model": model,
                            "model_label": MODEL_LABELS.get(model, model),
                            "seed": seed,
                            "family": pressured_scenario["family"],
                            "pair_variant": pressured_scenario["pair_variant"],
                            "tactic": pressured_scenario["tactic"],
                            "plain_scenario_id": plain_id,
                            "pressured_scenario_id": pressured_scenario["scenario_id"],
                            "reason": "; ".join(reasons),
                        }
                    )
                    continue

                plain_failure = int(plain_row["majority_failure"])
                pressured_failure = int(pressured_row["majority_failure"])
                pairs.append(
                    {
                        "model": model,
                        "seed": seed,
                        "family": pressured_scenario["family"],
                        "pair_variant": pressured_scenario["pair_variant"],
                        "tactic": pressured_scenario["tactic"],
                        "plain_scenario_id": plain_id,
                        "pressured_scenario_id": pressured_scenario["scenario_id"],
                        "plain_failure": plain_failure,
                        "pressured_failure": pressured_failure,
                        "difference": pressured_failure - plain_failure,
                    }
                )

    rng = random.Random(BOOTSTRAP_SEED)
    overall = [
        summarize(
            [pair for pair in pairs if pair["model"] == model],
            model=model,
            tactic="all",
            rng=rng,
        )
        for model in sorted(model_seeds)
    ]
    by_model_and_tactic = []
    for model in sorted(model_seeds):
        for tactic in TACTIC_ORDER:
            selected = [
                pair
                for pair in pairs
                if pair["model"] == model and pair["tactic"] == tactic
            ]
            by_model_and_tactic.append(
                summarize(selected, model=model, tactic=tactic, rng=rng)
            )

    return {
        "schema_version": "w08-pressure-cue-audit-v1",
        "status": "post_outcome_exploratory",
        "generated_from": [
            "week-07/W07_Confirmation_Bank.json",
            "week-07/W07_Results.csv",
        ],
        "feasibility": {
            "proposed_contrast": (
                "Within-pair failure differentials stratified by whether the plain "
                "item explicitly states that the governing prerequisite is missing."
            ),
            "estimable": explicit_count not in {0, len(plain)},
            "plain_items": len(plain),
            "plain_items_explicitly_stating_missing_prerequisite": explicit_count,
            "plain_items_stating_governing_prerequisite_only": len(plain) - explicit_count,
            "coding_definition": (
                "Explicit absence language must say that a prerequisite is missing, "
                "absent, unavailable, unrecorded, unverified, or unconfirmed; stating "
                "the governing rule alone is not explicit absence."
            ),
            "coding": plain_coding,
            "conclusion": (
                "The registered salience contrast is non-estimable because the "
                "proposed stratifier has no variation among plain items."
            ),
            "within_pair_salience_asymmetry": {
                "pressured_items": len(pressured),
                "pressured_items_explicitly_stating_missing_prerequisite": (
                    pressured_explicit_count
                ),
                "pressured_explicit_by_tactic": pressured_explicit_by_tactic,
                "pressured_items_by_tactic": pressured_total_by_tactic,
                "salience_confounded_tactics": salience_confounded_tactics,
                "note": (
                    "Prerequisite salience does not vary among plain items, but it does "
                    "vary across the pair: the pressured wording adds explicit "
                    "missing-prerequisite language in one tactic arm and not the others. "
                    "Differences involving that arm are therefore confounded with the "
                    "very factor the proposed contrast intended to isolate."
                ),
                "coding": pressured_coding,
            },
        },
        "methods": {
            "analysis_population": (
                "Week 7 common-baseline plain/pressured panel endpoints for both "
                "generators."
            ),
            "pair_key": [
                "generator_model",
                "family",
                "pair_variant",
                "seed",
            ],
            "estimand": "mean(pressured_failure - plain_failure) among complete pairs",
            "missing_handling": "complete-case pairs; every exclusion listed",
            "bootstrap": {
                "draws": BOOTSTRAP_DRAWS,
                "seed": BOOTSTRAP_SEED,
                "cluster": "scenario family",
                "interval": "2.5th and 97.5th percentile with linear interpolation",
            },
        },
        "results": {
            "overall_by_model": overall,
            "by_model_and_tactic": by_model_and_tactic,
            "missing_pairs": missing_pairs,
        },
        "interpretation_limits": [
            "This audit was specified after the Week 7 outcomes were known.",
            "Pressure tactics are bundled with prompt wording and systematically assigned to scenario families, pair variants, and settings.",
            "Tactic-stratified differences are descriptive heterogeneity, not causal tactic effects or a priority ranking.",
            "No confirmatory p-values or multiplicity-adjusted claims are made.",
            (
                f"Explicit missing-prerequisite language appears in {pressured_explicit_count} "
                f"of {len(pressured)} pressured items, all in the "
                f"{', '.join(salience_confounded_tactics)} arm, so differences involving that "
                "arm are confounded with prerequisite salience."
            ),
            "Because the proposed stratifier has no variation, this audit cannot test the salience explanation of the Week 7 plain/pressure reversal. That explanation is neither supported nor ruled out here.",
        ],
        "future_experiment_spec": {
            "status": "proposed_not_run",
            "design": "2x2 salience-by-pressure factorial",
            "factors": {
                "prerequisite_salience": [
                    "governing boundary only",
                    "explicit statement that the prerequisite is missing",
                ],
                "pressure": ["none", "pressure cue"],
            },
            "requirements": [
                "Hold the governing boundary constant within each scenario family.",
                "Counterbalance tactic and setting within family rather than assigning them systematically.",
                "Vary salience on both sides of the pair and across every tactic, so that salience is crossed with pressure rather than nested inside one arm.",
                "Retain authorized controls and score unsafe compliance and over-refusal jointly.",
                "Register the primary interaction contrast and family-clustered interval before inference.",
            ],
            "relation_to_existing_bank": (
                "The Week 7 bank already varies prerequisite salience, but only on the "
                "pressured side and only within one tactic arm. That is a partial, "
                "nested manipulation, not a factorial one, and it cannot substitute for "
                "the design above."
            ),
        },
    }


def pct(value: float) -> str:
    return f"{100 * value:.1f}%"


def signed_pp(value: float) -> str:
    return f"{100 * value:+.1f}pp"


def render_markdown(audit: dict[str, Any]) -> str:
    feasibility = audit["feasibility"]
    asymmetry = feasibility["within_pair_salience_asymmetry"]
    confounded = ", ".join(f"`{tactic}`" for tactic in asymmetry["salience_confounded_tactics"])
    total_complete = sum(
        row["complete_pairs"] for row in audit["results"]["overall_by_model"]
    )
    lines = [
        "# W08 Exploratory Pressure-Cue Audit",
        "",
        "Date: 2026-07-26",
        "",
        "> **Status: supplementary Week 8 work; post-outcome exploratory.** "
        "This audit prepares the plan-specified Week 9 paper and does not replace "
        "any Week 8 master deliverable.",
        "",
        "## Feasibility result",
        "",
        f"The proposed salience contrast is **non-estimable**. All "
        f"{feasibility['plain_items']} plain caution items state the governing "
        "prerequisite; none states that it is missing. The stratifier therefore has "
        "no variation. This is a design-feasibility finding, not evidence for or "
        "against the salience explanation.",
        "",
        "### Within-pair salience asymmetry",
        "",
        "Salience is not held constant across the pair. Applying the same coding to "
        "the pressured arm flags "
        f"{asymmetry['pressured_items_explicitly_stating_missing_prerequisite']} of "
        f"{asymmetry['pressured_items']} items, all in the {confounded} arm, which "
        "names the absent prerequisite outright.",
        "",
        "| Tactic | Pressured items | Explicitly state the prerequisite is missing |",
        "| --- | ---: | ---: |",
    ]
    for tactic, total in asymmetry["pressured_items_by_tactic"].items():
        lines.append(
            f"| `{tactic}` | {total} | "
            f"{asymmetry['pressured_explicit_by_tactic'][tactic]} |"
        )
    lines.extend(
        [
            "",
            f"Differences involving the {confounded} arm are therefore confounded with "
            "prerequisite salience — the factor the proposed contrast set out to "
            "isolate. Because salience is nested inside one arm rather than crossed "
            "with pressure, this audit cannot test the salience explanation of the "
            "Week 7 reversal, and does not support or rule it out.",
            "",
            "## Replacement descriptive audit",
            "",
        ]
    )
    lines.extend([
        "Common-baseline plain and pressured outcomes were paired by generator, "
        "scenario family, pair variant, and seed. The estimand is pressured minus "
        "plain panel failure among complete pairs. Intervals use 10,000 "
        "deterministic family-cluster bootstrap draws (seed 20260726). Negative "
        "values mean fewer failures under the pressured wording.",
        "",
        "| Generator | Tactic | Complete pairs | Plain failures | Pressured failures | Difference | Family-clustered 95% CI |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ])
    for row in audit["results"]["overall_by_model"]:
        low, high = row["family_clustered_bootstrap_95_ci"]
        lines.append(
            f"| {row['model_label']} | All cues | {row['complete_pairs']} | "
            f"{row['plain_failures']}/{row['complete_pairs']} "
            f"({pct(row['plain_rate'])}) | "
            f"{row['pressured_failures']}/{row['complete_pairs']} "
            f"({pct(row['pressured_rate'])}) | "
            f"{signed_pp(row['paired_difference_pressured_minus_plain'])} | "
            f"[{signed_pp(low)}, {signed_pp(high)}] |"
        )
    for row in audit["results"]["by_model_and_tactic"]:
        low, high = row["family_clustered_bootstrap_95_ci"]
        lines.append(
            f"| {row['model_label']} | `{row['tactic']}` | "
            f"{row['complete_pairs']} | "
            f"{row['plain_failures']}/{row['complete_pairs']} "
            f"({pct(row['plain_rate'])}) | "
            f"{row['pressured_failures']}/{row['complete_pairs']} "
            f"({pct(row['pressured_rate'])}) | "
            f"{signed_pp(row['paired_difference_pressured_minus_plain'])} | "
            f"[{signed_pp(low)}, {signed_pp(high)}] |"
        )

    lines.extend(
        [
            "",
            "### Incomplete pairs",
            "",
            f"{len(audit['results']['missing_pairs'])} of "
            f"{len(audit['results']['missing_pairs']) + total_complete} candidate pairs "
            "are incomplete. Every exclusion is listed below.",
            "",
            "| Generator | Seed | Family / variant | Tactic | Pair | Reason |",
            "| --- | ---: | --- | --- | --- | --- |",
        ]
    )
    for item in audit["results"]["missing_pairs"]:
        lines.append(
            f"| {item['model_label']} | {item['seed']} | "
            f"`{item['family']}` / {item['pair_variant']} | "
            f"`{item['tactic']}` | `{item['plain_scenario_id']}` → "
            f"`{item['pressured_scenario_id']}` | {item['reason']} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            "The tactic rows are **descriptive heterogeneity only**. Tactics are "
            "bundled with wording and systematically assigned to families, pair "
            "variants, and morning/evening settings, and the "
            f"{confounded} arm carries the added salience confound described above. "
            "They cannot identify a causal tactic effect or support a tactic-priority "
            "ranking. This audit was specified after outcomes were observed, reports "
            "no confirmatory p-values, and makes no multiplicity claim.",
            "",
            "## Future estimable experiment (proposed, not run)",
            "",
            "Use a registered 2×2 factorial: governing-boundary-only versus explicit "
            "missing-prerequisite wording, crossed with no-pressure versus pressure. "
            "Hold the boundary constant within family, counterbalance tactic and "
            "setting within family, retain authorized controls, and pre-register the "
            "salience-by-pressure interaction with family-clustered uncertainty. "
            "Unsafe compliance and authorized-control refusal remain joint endpoints. "
            "The existing bank does not substitute for this design: it varies salience "
            "on the pressured side only, and only within one tactic arm.",
            "",
            "## Reproduction",
            "",
            "From the repository root:",
            "",
            "```powershell",
            ".\\.conda-w01\\python.exe week-08\\analyze_w08_pressure_cues.py",
            "```",
            "",
            "Inputs: [`W07_Confirmation_Bank.json`](../week-07/W07_Confirmation_Bank.json) "
            "and [`W07_Results.csv`](../week-07/W07_Results.csv). Machine-readable "
            "output: [`W08_Pressure_Cue_Audit.json`](W08_Pressure_Cue_Audit.json).",
            "",
            "AI assistance was used to implement the deterministic audit and draft "
            "this report. All reported values are regenerated from the committed "
            "Week 7 sources and independently checked by `verify_w08.py`.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    audit = build_audit()
    JSON_PATH.write_text(
        json.dumps(audit, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    MARKDOWN_PATH.write_text(render_markdown(audit), encoding="utf-8")
    print(f"Wrote {JSON_PATH.relative_to(ROOT)}")
    print(f"Wrote {MARKDOWN_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
