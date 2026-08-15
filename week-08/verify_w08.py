"""Deterministic integrity checks for the Week 8 documentation package."""

from __future__ import annotations

import csv
import json
import math
import random
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
WEEK8 = ROOT / "week-08"
ANALYSIS = WEEK8 / "W08_PIC20_Analysis.md"
FRAMEWORK = WEEK8 / "W08_Application_Framework.md"
LOG = WEEK8 / "Wk-08-ResearchLog.md"
HANDOFF = WEEK8 / "W08_Paper_Handoff.md"
REGISTRY = WEEK8 / "W08_Paper_Claim_Registry.json"
AUDIT_JSON = WEEK8 / "W08_Pressure_Cue_Audit.json"
AUDIT_MD = WEEK8 / "W08_Pressure_Cue_Audit.md"
BIBLIOGRAPHY = ROOT / "references.bib"
INDEX = WEEK8 / "README.md"

BOOTSTRAP_SEED = 20260726
BOOTSTRAP_DRAWS = 10_000
TACTIC_ORDER = (
    "authority_claim",
    "false_clearance",
    "urgency",
    "normalization",
)
# Deliberately broader than the analyzer's pattern set, so that this check can catch
# an analyzer that under-counts explicit-absence wording rather than merely agreeing
# with it. Anything this flags but the analyzer misses will surface as a count mismatch.
INDEPENDENT_ABSENCE = re.compile(
    r"\bnot recorded\b|\bnot on file\b|\bmissing\b|\babsent\b|\bunverified\b"
    r"|\bunconfirmed\b|\bnot verified\b|\bnot confirmed\b|\bhas not been\b"
    r"|\bhasn't been\b|\blacks?\b|\blacking\b|\bexpired\b|\bnever\b"
    r"|\bno (?:active |valid |recorded |current )?"
    r"(?:record|permit|authorization|approval|clearance|consent)\b"
    r"|\bwithout (?:a |an |the )?"
    r"(?:permit|authorization|approval|clearance|consent)\b"
    r"|\b(?:does|do|did) not appear\b|\bcould not find\b|\bcouldn't find\b",
    flags=re.IGNORECASE,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def close(actual: float, expected: float, label: str) -> None:
    require(abs(actual - expected) < 1e-12, f"{label}: {actual} != {expected}")


def verify_week4_counts() -> None:
    with (ROOT / "week-04/W04_Failure_Cases.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    scenarios: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        for model_class in row["pic_classes"].split("|"):
            counts[model_class][row["taxonomy_subtype"]] += 1
            scenarios[model_class].add(row["scenario_id"])

    expected = {
        "GRPO": (33, 7, {"degenerate or non-response": 12, "unsafe output": 7, "incomplete or partial action": 6}),
        "STUM": (99, 25, {"degenerate or non-response": 34, "incomplete or partial action": 27, "missed escalation": 10, "hallucination of authorization or certainty": 4, "overconfident uncertainty handling": 1}),
        "SEOM": (69, 15, {"degenerate or non-response": 22, "unsafe output": 18, "incomplete or partial action": 10, "excessive refusal": 2}),
        "AMDC": (34, 9, {"degenerate or non-response": 12, "unsafe output": 5, "missed escalation": 4, "hallucination of authorization or certainty": 2}),
        "HTD-IRL": (62, 14, {"incomplete or partial action": 19, "degenerate or non-response": 18, "acceptable action, weak justification": 4}),
        "CRL-MRS": (7, 2, {"degenerate or non-response": 2, "missed escalation": 2, "incomplete or partial action": 2, "unsafe output": 1}),
    }
    for model_class, (row_count, scenario_count, subtypes) in expected.items():
        require(sum(counts[model_class].values()) == row_count, f"{model_class} row count")
        require(len(scenarios[model_class]) == scenario_count, f"{model_class} scenario count")
        for subtype, value in subtypes.items():
            require(counts[model_class][subtype] == value, f"{model_class} / {subtype}")


def verify_week6_and_week7() -> None:
    w6 = json.loads((ROOT / "week-06/W06_Analysis.json").read_text(encoding="utf-8"))
    tables = w6["condition_tables"]
    require(tables["baseline"]["pressured_targets"]["failures"] == 12, "W6 baseline pressured")
    require(tables["chain_of_thought"]["pressured_targets"]["failures"] == 2, "W6 deliberation pressured")
    require(tables["structured_output"]["pressured_targets"]["failures"] == 14, "W6 structured pressured")
    require(tables["constraint_gated"]["pressured_targets"]["failures"] == 0, "W6 gate pressured")
    require(tables["baseline"]["controls"]["failures"] == 1, "W6 baseline controls")
    require(tables["constraint_gated"]["controls"]["failures"] == 4, "W6 gate controls")

    w7 = json.loads((ROOT / "week-07/W07_Analysis.json").read_text(encoding="utf-8"))
    primary = w7["paired_contrasts"]["primary_common_baseline"]
    close(primary["plain"]["estimate"], -0.55, "W7 plain contrast")
    close(primary["pressured"]["estimate"], -0.4012738853503185, "W7 pressured contrast")
    close(primary["control"]["estimate"], 0.1875, "W7 control contrast")
    mitigation = w7["mitigation_rule"]["results"]
    passing = [
        (model, arm)
        for model, arms in mitigation.items()
        for arm, result in arms.items()
        if result["passes"]
    ]
    require(passing == [("Qwen/Qwen2.5-7B-Instruct", "deliberation")], "W7 mitigation winner")


def verify_platform_strata() -> None:
    with (ROOT / "week-07/W07_Results.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    selected = [
        row for row in rows
        if row["condition"] == "common_baseline" and row["majority_failure"] != ""
    ]
    grouped: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in selected:
        grouped[(row["generator_model"], row["platform"], row["subtype"])].append(row)
    expected = {
        ("Qwen/Qwen2.5-7B-Instruct", "Sentinel Prime AI", "control"): (15, 80),
        ("Qwen/Qwen2.5-7B-Instruct", "Sentinel Prime AI", "pressured"): (5, 78),
        ("Qwen/Qwen2.5-7B-Instruct", "Aido Humanoid", "control"): (15, 80),
        ("Qwen/Qwen2.5-7B-Instruct", "Aido Humanoid", "plain"): (39, 80),
        ("Qwen/Qwen2.5-7B-Instruct", "Aido Humanoid", "pressured"): (0, 79),
        ("mistralai/Mistral-7B-Instruct-v0.3", "Sentinel Prime AI", "control"): (0, 80),
        ("mistralai/Mistral-7B-Instruct-v0.3", "Sentinel Prime AI", "pressured"): (29, 80),
        ("mistralai/Mistral-7B-Instruct-v0.3", "Aido Humanoid", "control"): (0, 80),
        ("mistralai/Mistral-7B-Instruct-v0.3", "Aido Humanoid", "pressured"): (40, 80),
    }
    for key, (failures, total) in expected.items():
        values = grouped[key]
        require(len(values) == total, f"platform denominator {key}")
        require(sum(int(row["majority_failure"]) for row in values) == failures, f"platform failures {key}")

    mistral_sentinel = [
        row for row in selected
        if row["generator_model"] == "mistralai/Mistral-7B-Instruct-v0.3"
        and row["platform"] == "Sentinel Prime AI"
        and row["subtype"] == "pressured"
    ]
    tactic_counts = Counter()
    for row in mistral_sentinel:
        tactic_counts[(row["tactic"], "rows")] += 1
        tactic_counts[(row["tactic"], "failures")] += int(row["majority_failure"])
    for tactic, failures in {"authority_claim": 17, "urgency": 12, "false_clearance": 0, "normalization": 0}.items():
        require(tactic_counts[(tactic, "rows")] == 20, f"Sentinel tactic denominator: {tactic}")
        require(tactic_counts[(tactic, "failures")] == failures, f"Sentinel tactic failures: {tactic}")


def independent_pairs() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    bank = json.loads((ROOT / "week-07/W07_Confirmation_Bank.json").read_text(encoding="utf-8"))
    plain = {
        item["scenario_id"]: item
        for item in bank["scenarios"]
        if item["subtype"] == "plain"
    }
    pressured = [
        item for item in bank["scenarios"] if item["subtype"] == "pressured"
    ]
    require(len(plain) == 32 and len(pressured) == 32, "Week 7 plain/pressure bank size")
    require(
        all(
            INDEPENDENT_ABSENCE.search(item["stimulus"]) is None
            for item in plain.values()
        ),
        "independent zero-variation salience coding",
    )

    with (ROOT / "week-07/W07_Results.csv").open(encoding="utf-8", newline="") as handle:
        rows = [
            row for row in csv.DictReader(handle)
            if row["condition"] == "common_baseline"
            and row["subtype"] in {"plain", "pressured"}
        ]
    index = {
        (row["generator_model"], int(row["seed"]), row["scenario_id"]): row
        for row in rows
    }
    model_seeds: dict[str, set[int]] = defaultdict(set)
    for row in rows:
        model_seeds[row["generator_model"]].add(int(row["seed"]))

    pairs: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    for model in sorted(model_seeds):
        for item in sorted(pressured, key=lambda value: (value["family"], value["pair_variant"])):
            for seed in sorted(model_seeds[model]):
                plain_row = index[(model, seed, item["paired_plain_id"])]
                pressure_row = index[(model, seed, item["scenario_id"])]
                if plain_row["majority_failure"] == "" or pressure_row["majority_failure"] == "":
                    missing.append(
                        {
                            "model": model,
                            "seed": seed,
                            "plain_scenario_id": item["paired_plain_id"],
                            "pressured_scenario_id": item["scenario_id"],
                        }
                    )
                    continue
                plain_failure = int(plain_row["majority_failure"])
                pressure_failure = int(pressure_row["majority_failure"])
                pairs.append(
                    {
                        "model": model,
                        "family": item["family"],
                        "tactic": item["tactic"],
                        "plain_failure": plain_failure,
                        "pressured_failure": pressure_failure,
                        "difference": pressure_failure - plain_failure,
                    }
                )
    return pairs, missing


def independent_salience_coding() -> tuple[set[str], dict[str, int], dict[str, int]]:
    """Recompute the pressured-arm absence coding straight from the Week 7 bank."""
    bank = json.loads((ROOT / "week-07/W07_Confirmation_Bank.json").read_text(encoding="utf-8"))
    pressured = [item for item in bank["scenarios"] if item["subtype"] == "pressured"]
    flagged = {
        item["scenario_id"]
        for item in pressured
        if INDEPENDENT_ABSENCE.search(item["stimulus"])
    }
    by_tactic = {
        tactic: sum(
            1
            for item in pressured
            if item["tactic"] == tactic and item["scenario_id"] in flagged
        )
        for tactic in TACTIC_ORDER
    }
    totals = {
        tactic: sum(1 for item in pressured if item["tactic"] == tactic)
        for tactic in TACTIC_ORDER
    }
    return flagged, by_tactic, totals


def verify_salience_asymmetry(audit: dict[str, Any]) -> None:
    """The pressured arm varies the very factor the proposed contrast wanted to isolate."""
    asymmetry = audit["feasibility"]["within_pair_salience_asymmetry"]
    flagged, by_tactic, totals = independent_salience_coding()

    require(asymmetry["pressured_items"] == 32, "pressured arm size")
    require(
        asymmetry["pressured_items_explicitly_stating_missing_prerequisite"] == len(flagged),
        "pressured explicit-absence count",
    )
    require(asymmetry["pressured_explicit_by_tactic"] == by_tactic, "pressured explicit by tactic")
    require(asymmetry["pressured_items_by_tactic"] == totals, "pressured items by tactic")
    require(
        asymmetry["salience_confounded_tactics"]
        == sorted(tactic for tactic, count in by_tactic.items() if count),
        "salience-confounded tactic list",
    )
    # The asymmetry must be real and one-sided, or the disclosure below is miswritten.
    require(len(flagged) > 0, "pressured arm must carry the absence wording")
    require(
        len(asymmetry["salience_confounded_tactics"]) < len(TACTIC_ORDER),
        "confound must be nested in a strict subset of tactics",
    )
    require(
        {item["scenario_id"] for item in asymmetry["coding"]
         if item["explicitly_states_missing_prerequisite"]} == flagged,
        "pressured coding identities",
    )


def independent_quantile(values: list[float], p: float) -> float:
    values = sorted(values)
    position = (len(values) - 1) * p
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return values[lower]
    fraction = position - lower
    return values[lower] + fraction * (values[upper] - values[lower])


def independent_bootstrap(
    selected: list[dict[str, Any]],
    rng: random.Random,
) -> list[float]:
    clusters: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in selected:
        clusters[row["family"]].append(row)
    families = sorted(clusters)
    draws = []
    for _ in range(BOOTSTRAP_DRAWS):
        sample = [rng.choice(families) for _ in families]
        values = [
            row["difference"]
            for family in sample
            for row in clusters[family]
        ]
        draws.append(sum(values) / len(values))
    return [independent_quantile(draws, 0.025), independent_quantile(draws, 0.975)]


def verify_pressure_audit() -> None:
    audit = json.loads(AUDIT_JSON.read_text(encoding="utf-8"))
    require(audit["schema_version"] == "w08-pressure-cue-audit-v1", "audit schema")
    require(audit["status"] == "post_outcome_exploratory", "audit evidence status")
    feasibility = audit["feasibility"]
    require(feasibility["estimable"] is False, "salience contrast must be non-estimable")
    require(feasibility["plain_items"] == 32, "plain feasibility denominator")
    require(feasibility["plain_items_explicitly_stating_missing_prerequisite"] == 0, "salience zero variation")
    verify_salience_asymmetry(audit)

    pairs, missing = independent_pairs()
    require(len(pairs) == 317, "complete paired audit rows")
    require(len(missing) == 3, "missing paired audit rows")
    recorded_missing = audit["results"]["missing_pairs"]
    require(len(recorded_missing) == 3, "recorded missing pairs")
    expected_missing_ids = {
        (row["model"], row["seed"], row["plain_scenario_id"], row["pressured_scenario_id"])
        for row in missing
    }
    actual_missing_ids = {
        (row["model"], row["seed"], row["plain_scenario_id"], row["pressured_scenario_id"])
        for row in recorded_missing
    }
    require(actual_missing_ids == expected_missing_ids, "missing-pair identities")

    expected_rows: list[tuple[str, str, list[dict[str, Any]]]] = []
    for model in sorted({row["model"] for row in pairs}):
        expected_rows.append((model, "all", [row for row in pairs if row["model"] == model]))
    for model in sorted({row["model"] for row in pairs}):
        for tactic in TACTIC_ORDER:
            expected_rows.append(
                (
                    model,
                    tactic,
                    [
                        row for row in pairs
                        if row["model"] == model and row["tactic"] == tactic
                    ],
                )
            )
    actual_rows = (
        audit["results"]["overall_by_model"]
        + audit["results"]["by_model_and_tactic"]
    )
    require(len(actual_rows) == len(expected_rows), "audit result row count")
    rng = random.Random(BOOTSTRAP_SEED)
    for actual, (model, tactic, selected) in zip(actual_rows, expected_rows):
        require(actual["model"] == model and actual["tactic"] == tactic, f"audit row order {model}/{tactic}")
        n = len(selected)
        plain_failures = sum(row["plain_failure"] for row in selected)
        pressured_failures = sum(row["pressured_failure"] for row in selected)
        difference = sum(row["difference"] for row in selected) / n
        require(actual["complete_pairs"] == n, f"pair count {model}/{tactic}")
        require(actual["plain_failures"] == plain_failures, f"plain failures {model}/{tactic}")
        require(actual["pressured_failures"] == pressured_failures, f"pressured failures {model}/{tactic}")
        close(actual["plain_rate"], plain_failures / n, f"plain rate {model}/{tactic}")
        close(actual["pressured_rate"], pressured_failures / n, f"pressured rate {model}/{tactic}")
        close(actual["paired_difference_pressured_minus_plain"], difference, f"pair difference {model}/{tactic}")
        expected_ci = independent_bootstrap(selected, rng)
        for observed, expected in zip(actual["family_clustered_bootstrap_95_ci"], expected_ci):
            close(observed, expected, f"bootstrap CI {model}/{tactic}")

    report = AUDIT_MD.read_text(encoding="utf-8")
    for phrase in (
        "supplementary Week 8 work",
        "post-outcome exploratory",
        "non-estimable",
        "descriptive heterogeneity only",
        "cannot identify a causal tactic effect",
        "proposed, not run",
        # The salience confound must be disclosed, not left implicit in "bundled wording".
        "Within-pair salience asymmetry",
        "confounded with prerequisite salience",
        "does not support or rule it out",
    ):
        require(phrase.lower() in report.lower(), f"audit boundary phrase: {phrase}")
    require(
        "cannot explain the week 7" not in report.lower(),
        "stale ruled-out phrasing of the salience explanation",
    )


def markdown_links(document: Path) -> list[str]:
    return re.findall(r"\[[^\]]+\]\(([^)]+)\)", document.read_text(encoding="utf-8"))


def verify_local_links(documents: tuple[Path, ...]) -> None:
    for document in documents:
        for target in markdown_links(document):
            if target.startswith(("http://", "https://", "#")):
                continue
            clean_target = target.split("#", 1)[0]
            path = (document.parent / clean_target).resolve()
            require(path.exists(), f"broken local link in {document.name}: {target}")


def prose_word_count(markdown: str) -> int:
    lines = []
    in_code = False
    for line in markdown.splitlines():
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code or line.lstrip().startswith("|"):
            continue
        lines.append(line)
    text = re.sub(r"\[[^\]]+\]\([^)]+\)", " ", "\n".join(lines))
    text = re.sub(r"[#>*_`-]", " ", text)
    return len(re.findall(r"\b[\w’']+(?:-[\w’']+)*\b", text, flags=re.UNICODE))


def section_between(text: str, start: str, next_heading_prefix: str = "## ") -> str:
    position = text.find(start)
    require(position >= 0, f"missing section: {start}")
    remaining = text[position + len(start):]
    match = re.search(rf"(?m)^{re.escape(next_heading_prefix)}", remaining)
    return remaining if match is None else remaining[:match.start()]


def verify_plan_conformance() -> None:
    analysis = ANALYSIS.read_text(encoding="utf-8")
    framework = FRAMEWORK.read_text(encoding="utf-8")
    log = LOG.read_text(encoding="utf-8")

    model_classes = ("GRPO", "STUM", "SEOM", "AMDC", "HTD-IRL", "CRL-MRS")
    for index, model_class in enumerate(model_classes):
        start = f"## {model_class}"
        position = analysis.find(start)
        require(position >= 0, f"missing class section: {model_class}")
        end_positions = [
            analysis.find(f"## {later}", position + len(start))
            for later in model_classes[index + 1:]
        ]
        end_positions = [value for value in end_positions if value >= 0]
        section = analysis[position:min(end_positions) if end_positions else len(analysis)]
        for element in ("Observed risk pattern", "Failure scenario", "Mitigation", "Open question"):
            require(f"**{element}" in section, f"{model_class} missing {element}")

    for platform in ("Sentinel", "Aido Humanoid", "Fari", "Senpai", "Aido Rover"):
        require(framework.count(f"| {platform}") >= 2, f"missing two risk cells: {platform}")
    for intervention in (
        "Generator selection",
        "Deliberation / CoT",
        "Structured output",
        "Constraint gating",
        "Persona grounding",
        "RAG",
        "Fine-tuning / PEFT / LoRA",
    ):
        require(f"| {intervention} |" in framework, f"missing intervention: {intervention}")
    for status in ("Tested", "Inconclusive", "Proposed", "Literature-only"):
        require(status.lower() in (analysis + framework).lower(), f"missing evidence status: {status}")
    for gap in ("partially addressed", "substantially addressed, not closed", "fully open", "New gaps"):
        require(gap.lower() in framework.lower(), f"gap-analysis category: {gap}")
    require("descriptive and confounded" in framework, "confounded cue wording")
    # Phrasing may vary; the disclaimer itself may not disappear.
    require(
        re.search(
            r"(?:do not identify|identify neither)\s+causal tactic effects?"
            r"\s+(?:or|nor)\s+a priority ranking",
            framework,
            flags=re.IGNORECASE,
        )
        is not None,
        "no tactic causal ranking",
    )
    require(
        "confounds that arm" in framework or "confounded with the very factor" in framework
        or "confounds that arm with" in framework,
        "framework must disclose the salience confound",
    )
    require("paired salience analysis (ready for week 9" not in framework.lower(), "stale feasible salience claim")

    summary_heading = "## Weekly summary (300–500 words)"
    summary = section_between(log, summary_heading)
    summary_words = prose_word_count(summary)
    require(300 <= summary_words <= 500, f"weekly summary word count: {summary_words}")
    for heading in (
        "## Detailed chronological audit trail",
        "## Deliverable conformance",
        "## Open items",
        "## Verification record",
        "## Final Week 8 completion entry",
    ):
        require(heading in log, f"research-log section: {heading}")
    for status in ("complete", "complete with limitation", "deferred by plan"):
        require(status in log.lower(), f"conformance status: {status}")
    for artifact in (
        "W08_PIC20_Analysis.md",
        "W08_Application_Framework.md",
        "Wk-08-ResearchLog.md",
        "W08_Paper_Handoff.md",
        "W08_Paper_Claim_Registry.json",
        "W08_Pressure_Cue_Audit.json",
        "references.bib",
        "week-08/README.md",
    ):
        require(artifact in log, f"research log artifact: {artifact}")
    require("PASS: Week 8 verification complete" in log, "latest verifier result in research log")
    require(1200 <= prose_word_count(analysis) <= 1800, "PIC analysis approximate three-page budget")
    require(550 <= prose_word_count(framework) <= 950, "application framework approximate two-page budget")


def bibtex_keys(text: str) -> set[str]:
    return set(re.findall(r"@\w+\s*\{\s*([a-z][a-z0-9_-]*)\s*,", text, flags=re.IGNORECASE))


def verify_paper_handoff() -> None:
    handoff = HANDOFF.read_text(encoding="utf-8")
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    bib = BIBLIOGRAPHY.read_text(encoding="utf-8")
    keys = bibtex_keys(bib)
    require(len(keys) >= 20, "shared bibliography entry count")
    require(bib.count("{") == bib.count("}"), "balanced BibTeX braces")

    week2 = (ROOT / "week-02/W02_Literature_Review.md").read_text(encoding="utf-8")
    arxiv_ids = set(re.findall(r"arxiv\.org/abs/([0-9.]+)", week2, flags=re.IGNORECASE))
    require(len(arxiv_ids) == 18, "Week 2 arXiv source count")
    for arxiv_id in arxiv_ids:
        require(re.search(rf"eprint\s*=\s*\{{{re.escape(arxiv_id)}\}}", bib), f"bibliography missing arXiv {arxiv_id}")

    used_citations = set()
    for group in re.findall(r"\[@([^\]]+)\]", handoff):
        for citation in group.split(";"):
            key = citation.strip().lstrip("@").split(",", 1)[0].strip()
            used_citations.add(key)
    require(used_citations <= keys, f"undefined handoff citekeys: {sorted(used_citations - keys)}")

    require(registry["artifact_role"] == "supplementary_week_8_preparation_for_plan_specified_week_9_paper", "registry role")
    require(registry["replaces_master_deliverable"] is False, "registry replacement boundary")
    permitted = {"confirmatory", "descriptive", "exploratory", "proposed"}
    require(set(registry["permitted_statuses"]) == permitted, "registry status enum")
    claims = {claim["id"]: claim for claim in registry["claims"]}
    require(registry["primary_claim_id"] == "C1", "primary claim ID")
    require(claims["C1"]["status"] == "confirmatory", "C1 status")
    require(claims["C4"]["status"] == "exploratory", "pressure-cue status")
    require(claims["C5"]["status"] == "proposed", "application status")
    require(all(claim["status"] in permitted for claim in claims.values()), "claim status validity")

    limitation_ids = {item["id"] for item in registry["limitations"]}
    figure_ids = {item["id"] for item in registry["figures"]}
    for claim in claims.values():
        require(set(claim["limitation_ids"]) <= limitation_ids, f"claim limitation IDs: {claim['id']}")
        require(set(claim["figure_ids"]) <= figure_ids, f"claim figure IDs: {claim['id']}")
        for evidence_path in claim["evidence_paths"]:
            require((ROOT / evidence_path).exists(), f"claim evidence path: {evidence_path}")
    for figure in registry["figures"]:
        for field in ("png", "svg", "source"):
            require((ROOT / figure[field]).exists(), f"figure {figure['id']} {field}")
        require(set(figure["supports_claim_ids"]) <= set(claims), f"figure claim IDs: {figure['id']}")
    require(set(registry["citation_keys"]) <= keys, "registry citekeys")

    primary = json.loads((ROOT / "week-07/W07_Analysis.json").read_text(encoding="utf-8"))["paired_contrasts"]["primary_common_baseline"]
    require("-0.55" in claims["C1"]["estimand"], "C1 plain exact estimate")
    require("-0.401" in claims["C1"]["estimand"], "C1 pressured exact estimate")
    require("+0.1875" in claims["C1"]["estimand"], "C1 control exact estimate")
    close(primary["plain"]["estimate"], -0.55, "registry source plain")

    for phrase in (
        "supplementary Week 8 preparation",
        "not an addition to, or replacement for",
        "Paper versus capstone boundary",
        "Canonical claim hierarchy",
        "Week 9 paper architecture",
        "Figure and table manifest",
        "Reproducibility preflight",
        "Week 9 readiness checklist",
    ):
        require(phrase.lower() in handoff.lower(), f"handoff section/boundary: {phrase}")
    verify_local_links((ANALYSIS, FRAMEWORK, LOG, HANDOFF, AUDIT_MD, INDEX))


def verify_publication_boundary() -> None:
    public_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ANALYSIS, FRAMEWORK, LOG, HANDOFF, AUDIT_MD, INDEX)
    ).lower()
    for marker in ("internal" + " docs", "plans/", "confidential"):
        require(marker not in public_text, f"publication-boundary marker: {marker}")
    require(
        "ai assistance" in public_text
        or "ai-assisted" in public_text,
        "AI assistance disclosure",
    )


def main() -> None:
    checks = (
        ("Week 4 class-tagged taxonomy counts", verify_week4_counts),
        ("Week 6/7 decisive results", verify_week6_and_week7),
        ("Week 7 platform strata", verify_platform_strata),
        ("exploratory pressure-cue audit", verify_pressure_audit),
        ("internship-plan deliverable conformance", verify_plan_conformance),
        ("paper handoff, claims, figures, citations, and links", verify_paper_handoff),
        ("publication boundary and AI disclosure", verify_publication_boundary),
    )
    for label, check in checks:
        check()
        print(f"PASS: {label}")
    print("PASS: Week 8 verification complete")


if __name__ == "__main__":
    main()
