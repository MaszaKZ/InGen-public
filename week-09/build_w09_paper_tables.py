"""Build the Week 9 paper tables directly from committed Week 7 analysis JSON.

The Week 8 paper handoff requires that paper tables T1 and T2 be generated from
`week-07/W07_Analysis.json`, never transcribed from prose. This script emits the
exact Markdown table rows embedded in `W09_Paper_Draft_v1.md`;
`verify_w09.py` independently recomputes the same rows and requires that the
draft contain them verbatim.

Usage (from the repository root):
    .\\.conda-w01\\python.exe week-09\\build_w09_paper_tables.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ANALYSIS = ROOT / "week-07" / "W07_Analysis.json"
METADATA = ROOT / "week-07" / "W07_Run_Metadata.json"
OUTPUT = Path(__file__).resolve().parent / "W09_Paper_Tables.md"

MODEL_LABELS = {
    "mistralai/Mistral-7B-Instruct-v0.3": "Mistral-7B-Instruct-v0.3",
    "Qwen/Qwen2.5-7B-Instruct": "Qwen2.5-7B-Instruct",
}
CONDITION_LABELS = {
    "common_baseline": "Common baseline",
    "adapted_baseline": "Adapted baseline",
    "deliberation": "Deliberation",
    "structured_output": "Structured output",
    "constraint_gated": "Constraint gated",
}
SUBTYPE_LABELS = {
    "plain": "Plain caution",
    "pressured": "Pressured caution",
    "control": "Authorized control",
}


def pct(x: float) -> str:
    return f"{100.0 * x:.1f}"


def rate_cell(entry: dict) -> str:
    count = round(entry["estimate"] * entry["rows"])
    return (
        f"{pct(entry['estimate'])}% ({count}/{entry['rows']}) "
        f"[{pct(entry['ci_low'])}, {pct(entry['ci_high'])}]"
    )


def signed_pp(x: float) -> str:
    return f"{100.0 * x:+.1f}"


def contrast_cell(entry: dict) -> str:
    return (
        f"{signed_pp(entry['estimate'])}pp "
        f"[{signed_pp(entry['ci_low'])}, {signed_pp(entry['ci_high'])}] "
        f"(n={entry['rows']})"
    )


def build_t1(metadata: dict) -> list[str]:
    generators = ", ".join(
        f"{MODEL_LABELS[g['id']]} (rev `{g['revision'][:12]}`)"
        for g in metadata["generators"]
    )
    judges = ", ".join(
        f"{j['id']} (rev `{j['revision'][:12]}`)" for j in metadata["judges"]
    )
    decoding = metadata["decoding"]
    analysis = metadata["analysis"]
    seeds = ", ".join(str(s) for s in metadata["seeds"])
    rows = [
        "| Design component | Registered value |",
        "| --- | --- |",
        "| Scenario bank | 96 scenarios in 16 families of 6; 32 plain caution / 32 pressured caution / 32 authorized control |",
        f"| Generators | {generators} |",
        f"| Prompt conditions | {len(metadata['conditions'])} arms: common baseline (registered cross-model endpoint), adapted baseline, deliberation, structured output, constraint gated |",
        f"| Seeds | {seeds} |",
        f"| Generations / judgments | {metadata['row_counts']['generations']:,} / {metadata['row_counts']['judgments']:,} |",
        f"| Decoding | temperature {decoding['temperature']}, top-p {decoding['top_p']}, max {decoding['max_new_tokens']} new tokens; NF4 double-quantized, float16 compute |",
        f"| Judge panel | {judges} |",
        f"| Primary estimands | Panel-majority failure rates; scenario-and-seed-paired Qwen−Mistral contrasts at the common baseline |",
        f"| Uncertainty | {analysis['bootstrap_draws']:,} bootstrap draws over complete scenario families (seed {analysis['bootstrap_seed']}) |",
        "| Mitigation rule | ≥25% relative pressured-failure reduction at ≤3.125pp added authorized-control failure |",
    ]
    return rows


def build_t2_rates(analysis: dict) -> list[str]:
    header = [
        "| Generator | Condition | Plain caution | Pressured caution | Authorized control |",
        "| --- | --- | --- | --- | --- |",
    ]
    by_key: dict[tuple[str, str], dict[str, dict]] = {}
    for entry in analysis["rates"]:
        by_key.setdefault((entry["model"], entry["condition"]), {})[
            entry["subtype"]
        ] = entry
    rows = []
    for model in MODEL_LABELS:
        for condition in CONDITION_LABELS:
            cells = by_key[(model, condition)]
            rows.append(
                f"| {MODEL_LABELS[model]} | {CONDITION_LABELS[condition]} | "
                f"{rate_cell(cells['plain'])} | {rate_cell(cells['pressured'])} | "
                f"{rate_cell(cells['control'])} |"
            )
    return header + rows


def build_t2_contrasts(analysis: dict) -> list[str]:
    primary = analysis["paired_contrasts"]["primary_common_baseline"]
    header = [
        "| Registered contrast (Qwen − Mistral, common baseline) | Estimate [family-clustered 95% CI] |",
        "| --- | --- |",
    ]
    rows = [
        f"| {SUBTYPE_LABELS[subtype]} | {contrast_cell(primary[subtype])} |"
        for subtype in ("plain", "pressured", "control")
    ]
    return header + rows


def build_t2_rule(analysis: dict) -> list[str]:
    rule = analysis["mitigation_rule"]["results"]
    header = [
        "| Generator | Intervention | Relative pressured reduction | Control-failure change | Passes rule |",
        "| --- | --- | --- | --- | --- |",
    ]
    rows = []
    for model in MODEL_LABELS:
        for intervention in ("deliberation", "structured_output", "constraint_gated"):
            r = rule[model][intervention]
            rows.append(
                f"| {MODEL_LABELS[model]} | {CONDITION_LABELS[intervention]} | "
                f"{100.0 * r['pressured_relative_reduction']:+.1f}% | "
                f"{signed_pp(r['control_failure_increase'])}pp | "
                f"{'**Yes**' if r['passes'] else 'No'} |"
            )
    return header + rows


def build_all() -> str:
    analysis = json.loads(ANALYSIS.read_text(encoding="utf-8"))
    metadata = json.loads(METADATA.read_text(encoding="utf-8"))
    sections = [
        "<!-- Generated by build_w09_paper_tables.py from week-07/W07_Analysis.json",
        "     and week-07/W07_Run_Metadata.json. Do not edit the table rows by hand;",
        "     verify_w09.py requires the paper draft to contain them verbatim. -->",
        "",
        "## T1 — Registered design summary",
        "",
        *build_t1(metadata),
        "",
        "## T2a — Panel-majority failure rates (all arms)",
        "",
        *build_t2_rates(analysis),
        "",
        "## T2b — Registered primary contrasts",
        "",
        *build_t2_contrasts(analysis),
        "",
        "## T2c — Registered mitigation-rule disposition",
        "",
        *build_t2_rule(analysis),
        "",
    ]
    return "\n".join(sections)


def main() -> None:
    OUTPUT.write_text(build_all(), encoding="utf-8", newline="\n")
    print(f"wrote {OUTPUT}")


if __name__ == "__main__":
    main()
