"""Independent stdlib verification of the W06 Experiment 2 reported results.

Mirrors the rerun-v3 convention (verify_*_independent.py): recomputes every
reported statistic from W06_Judge_Ratings.csv with self-contained stdlib
implementations (no pandas, no imports from the pipeline except the scorer
for label-reproduction) and compares against W06_Analysis.json, then checks
the structural integrity of the evidence chain. Exit code 0 only if every
comparison passes.

Also prints the endpoint-robustness (judge-ablation) table: the primary
diagnostic and the chain-of-thought contrast under each single-judge,
unanimous, no-self-judge, and deterministic-scorer endpoint definition.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

WEEK = Path(__file__).resolve().parent
CONDITIONS = ("baseline", "chain_of_thought", "structured_output", "constraint_gated")
FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"[{'OK ' if ok else 'FAIL'}] {name}" + (f" :: {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def close(a: float | None, b: float | None) -> bool:
    if a is None or b is None:
        return a is None and b is None
    return math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-12)


# ---------------------------------------------------------------- fresh statistics

def krippendorff_alpha(units: list[list[int]]) -> float | None:
    coincidence: Counter = Counter()
    for unit in units:
        m = len(unit)
        if m < 2:
            continue
        for i in range(m):
            for j in range(m):
                if i != j:
                    coincidence[(unit[i], unit[j])] += 1.0 / (m - 1)
    categories = sorted({c for pair in coincidence for c in pair})
    marginals = {c: sum(coincidence[(c, k)] for k in categories) for c in categories}
    total = sum(marginals.values())
    if total <= 1:
        return None
    observed = sum(v for (a, b), v in coincidence.items() if a != b)
    expected = sum(marginals[a] * marginals[b] for a in categories for b in categories if a != b) / (total - 1)
    return None if expected == 0 else 1 - observed / expected


def gwets_ac1(units: list[list[int]]) -> float | None:
    units = [u for u in units if len(u) >= 2]
    if not units:
        return None
    pa = sum((sum(u) * (sum(u) - 1) + (len(u) - sum(u)) * (len(u) - sum(u) - 1)) / (len(u) * (len(u) - 1)) for u in units) / len(units)
    pi = sum(sum(u) / len(u) for u in units) / len(units)
    pe = 2 * pi * (1 - pi)
    return None if pe >= 1 else (pa - pe) / (1 - pe)


def percent_agreement(units: list[list[int]]) -> float | None:
    units = [u for u in units if len(u) >= 2]
    if not units:
        return None
    return sum((sum(u) * (sum(u) - 1) + (len(u) - sum(u)) * (len(u) - sum(u) - 1)) / (len(u) * (len(u) - 1)) for u in units) / len(units)


def exact_mcnemar(only_a: int, only_b: int) -> float:
    n = only_a + only_b
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(math.comb(n, k) for k in range(min(only_a, only_b) + 1)) / 2 ** n)


def family_bootstrap_ci(effects: dict[str, float], seed: int = 20260717, iterations: int = 10_000) -> tuple[float, float]:
    families = sorted(effects)
    rng = random.Random(seed)
    draws = sorted(
        sum(effects[f] for f in (rng.choice(families) for _ in families)) / len(families)
        for _ in range(iterations)
    )
    low = int(0.025 * iterations) - 1
    return draws[low], draws[iterations - low - 1]


# ---------------------------------------------------------------- verification

def main() -> None:
    rated = list(csv.DictReader((WEEK / "W06_Judge_Ratings.csv").open(newline="", encoding="utf-8")))
    raw = [json.loads(line) for line in (WEEK / "W06_Raw_Model_Outputs.jsonl").read_text(encoding="utf-8").splitlines() if line]
    results = list(csv.DictReader((WEEK / "W06_Results.csv").open(newline="", encoding="utf-8")))
    bank = json.loads((WEEK / "W06_Scenario_Bank.json").read_text(encoding="utf-8"))["scenarios"]
    reported = json.loads((WEEK / "W06_Analysis.json").read_text(encoding="utf-8"))
    metadata = json.loads((WEEK / "W06_Run_Metadata.json").read_text(encoding="utf-8"))

    # --- structural integrity -------------------------------------------------
    for key, name in (("bank_sha256", "W06_Scenario_Bank.json"),
                      ("raw_outputs_sha256", "W06_Raw_Model_Outputs.jsonl"),
                      ("results_sha256", "W06_Results.csv")):
        actual = hashlib.sha256((WEEK / name).read_bytes()).hexdigest()
        check(f"metadata hash {key}", actual == metadata["hashes"][key])
    check("counts 384/384/384", len(rated) == len(raw) == len(results) == 384)
    check("bank 96 main + 12 holdout", sum(not s["holdout"] for s in bank) == 96 and sum(bool(s["holdout"]) for s in bank) == 12)

    raw_by_key = {(r["condition"], r["scenario_id"]): r for r in raw}
    bank_by_id = {s["scenario_id"]: s for s in bank}
    check("rated keys == raw keys", {(r["condition"], r["scenario_id"]) for r in rated} == set(raw_by_key))
    check("stimuli consistent bank<->raw<->rated",
          all(r["stimulus"] == bank_by_id[r["scenario_id"]]["stimulus"] for r in raw)
          and all(r["stimulus"] == raw_by_key[(r["condition"], r["scenario_id"])]["stimulus"] for r in rated))
    check("per-row response sha256",
          all(hashlib.sha256(r["response"].encode("utf-8")).hexdigest() == r["response_sha256"] for r in raw))
    check("majority/vote columns consistent",
          all(int(r["failure_votes"]) == int(r["qwen_label"]) + int(r["phi_label"]) + int(r["mistral_self_label"])
              and int(r["majority_failure"]) == int(int(r["failure_votes"]) >= 2) for r in rated))
    check("scorer labels identical raw<->results<->ratings",
          all(str(raw_by_key[(r["condition"], r["scenario_id"])]["scorer_sensitivity_label"]) == r["scorer_sensitivity_label"]
              for r in results)
          and all(str(raw_by_key[(r["condition"], r["scenario_id"])]["scorer_sensitivity_label"]) == r["scorer_sensitivity_label"]
                  for r in rated))
    try:
        import scorer_w06
        check("scorer module reproduces stored labels",
              all(scorer_w06.sensitivity_label(bank_by_id[r["scenario_id"]], r["response"]) == int(r["scorer_sensitivity_label"])
                  for r in raw))
    except ImportError:
        check("scorer module reproduces stored labels", False, "scorer_w06 not importable")

    # --- recompute condition tables -------------------------------------------
    def majority(r: dict[str, str]) -> int:
        return int(r["majority_failure"])

    for condition in CONDITIONS:
        for subtype, key in (("plain", "plain_targets"), ("pressured", "pressured_targets"), ("control", "controls")):
            rows = [r for r in rated if r["condition"] == condition and r["subtype"] == subtype]
            failures = sum(majority(r) for r in rows)
            rep = reported["condition_tables"][condition][key]
            check(f"table {condition}/{subtype} = {failures}/{len(rows)}",
                  rep["n"] == len(rows) and rep["failures"] == failures)

    # --- diagnostic contrast ---------------------------------------------------
    meta = {r["scenario_id"]: r for r in rated}
    by_key = {(r["condition"], r["scenario_id"]): majority(r) for r in rated}
    scenario_ids = sorted({r["scenario_id"] for r in rated})
    plain_ids = [s for s in scenario_ids if meta[s]["subtype"] == "plain"]

    def contrast(pairs: list[tuple[int, int]]) -> dict[str, float]:
        a_only = sum(1 for a, b in pairs if a == 1 and b == 0)
        b_only = sum(1 for a, b in pairs if a == 0 and b == 1)
        return {
            "a": sum(a for a, _ in pairs), "b": sum(b for _, b in pairs),
            "diff": (sum(b for _, b in pairs) - sum(a for a, _ in pairs)) / len(pairs),
            "p": exact_mcnemar(a_only, b_only),
            "or": (b_only + 0.5) / (a_only + 0.5),
        }

    pairs = [(by_key[("baseline", p)], by_key[("baseline", p.replace("-P", "-A"))]) for p in plain_ids]
    fam: dict[str, list[int]] = defaultdict(list)
    for p in plain_ids:
        fam[meta[p]["family"]].append(by_key[("baseline", p.replace("-P", "-A"))] - by_key[("baseline", p)])
    effects = {f: sum(v) / len(v) for f, v in fam.items()}
    got = contrast(pairs)
    rep = reported["diagnostic_baseline_pressured_vs_plain"]
    lo, hi = family_bootstrap_ci(effects)
    check("diagnostic contrast",
          rep["a_failures"] == got["a"] and rep["b_failures"] == got["b"]
          and close(rep["difference_b_minus_a"], got["diff"])
          and close(rep["exact_two_sided_mcnemar_p"], got["p"])
          and close(rep["matched_odds_ratio_haldane"], got["or"]),
          f"plain {got['a']}/32 pressured {got['b']}/32 diff {got['diff']:+.5f} p {got['p']:.6g}")
    check("diagnostic family effects + bootstrap CI",
          all(close(effects[f], rep["family_bootstrap"]["family_effects"][f]) for f in effects)
          and set(effects) == set(rep["family_bootstrap"]["family_effects"])
          and close(lo, rep["family_bootstrap"]["lower_95"]) and close(hi, rep["family_bootstrap"]["upper_95"]),
          f"CI [{lo}, {hi}]")

    # --- interventions ---------------------------------------------------------
    for condition in CONDITIONS[1:]:
        for subtype in ("pressured", "plain", "control"):
            ids = [s for s in scenario_ids if meta[s]["subtype"] == subtype]
            got = contrast([(by_key[("baseline", s)], by_key[(condition, s)]) for s in ids])
            rep = reported["interventions_vs_baseline"][condition][subtype]
            fam2: dict[str, list[int]] = defaultdict(list)
            for s in ids:
                fam2[meta[s]["family"]].append(by_key[(condition, s)] - by_key[("baseline", s)])
            lo, hi = family_bootstrap_ci({f: sum(v) / len(v) for f, v in fam2.items()})
            check(f"intervention {condition}/{subtype} {got['a']}->{got['b']}",
                  rep["a_failures"] == got["a"] and rep["b_failures"] == got["b"]
                  and close(rep["exact_two_sided_mcnemar_p"], got["p"])
                  and close(rep["matched_odds_ratio_haldane"], got["or"])
                  and close(lo, rep["family_bootstrap"]["lower_95"]) and close(hi, rep["family_bootstrap"]["upper_95"]))

    # --- tactic table ----------------------------------------------------------
    for tactic, block in reported["pressured_targets_by_tactic"].items():
        for condition in CONDITIONS:
            rows = [r for r in rated if r["condition"] == condition and r["subtype"] == "pressured" and r["tactic"] == tactic]
            check(f"tactic {tactic}/{condition}",
                  block[condition]["n"] == len(rows) and block[condition]["failures"] == sum(majority(r) for r in rows))

    # --- reliability -----------------------------------------------------------
    def units_of(rows: list[dict[str, str]]) -> list[list[int]]:
        return [[int(r["qwen_label"]), int(r["phi_label"]), int(r["mistral_self_label"])] for r in rows]

    for scope, rows in (("overall", rated),
                        ("targets", [r for r in rated if r["mode"] == "caution"]),
                        ("controls", [r for r in rated if r["mode"] == "proceed"])):
        units = units_of(rows)
        rep = reported["reliability"][scope]
        counts = {"qwen": sum(u[0] for u in units), "phi": sum(u[1] for u in units), "mistral_self": sum(u[2] for u in units)}
        check(f"reliability {scope}",
              close(krippendorff_alpha(units), rep["krippendorff_alpha_nominal"])
              and close(gwets_ac1(units), rep["gwets_ac1"])
              and close(percent_agreement(units), rep["percent_agreement"])
              and sum(len(set(u)) == 1 for u in units) == rep["unanimous_items"]
              and counts == rep["judge_failure_counts"],
              f"alpha {krippendorff_alpha(units):.4f} AC1 {gwets_ac1(units):.4f} flags {counts}")

    disagreements = sum(1 for r in rated if int(r["scorer_sensitivity_label"]) != majority(r))
    check("scorer disagreement",
          disagreements == reported["scorer_sensitivity_disagreements_with_majority"]
          and close(disagreements / len(rated), reported["scorer_sensitivity_disagreement_rate"]),
          f"{disagreements}/384")

    # --- endpoint robustness (judge ablations), informational -------------------
    endpoints = {
        "majority(2/3)": majority,
        "qwen only": lambda r: int(r["qwen_label"]),
        "phi only": lambda r: int(r["phi_label"]),
        "mistral_self only": lambda r: int(r["mistral_self_label"]),
        "unanimous 3/3": lambda r: int(int(r["failure_votes"]) == 3),
        "no self-judge (qwen&phi)": lambda r: int(int(r["qwen_label"]) + int(r["phi_label"]) == 2),
        "deterministic scorer": lambda r: int(r["scorer_sensitivity_label"]),
    }
    pressured_ids = [s for s in scenario_ids if meta[s]["subtype"] == "pressured"]
    control_ids = [s for s in scenario_ids if meta[s]["subtype"] == "control"]
    print("\nEndpoint robustness -- diagnostic (baseline plain vs pressured) and CoT vs baseline:")
    print(f"{'endpoint':26s} {'plain':>7s} {'press.':>7s} {'diff':>8s} {'p':>8s}   {'CoT press.':>11s} {'CoT ctrl':>9s}")
    for name, fn in endpoints.items():
        by = {(r["condition"], r["scenario_id"]): fn(r) for r in rated}
        d = contrast([(by[("baseline", p)], by[("baseline", p.replace("-P", "-A"))]) for p in plain_ids])
        c = contrast([(by[("baseline", s)], by[("chain_of_thought", s)]) for s in pressured_ids])
        k = contrast([(by[("baseline", s)], by[("chain_of_thought", s)]) for s in control_ids])
        print(f"{name:26s} {d['a']:>4d}/32 {d['b']:>4d}/32 {d['diff']:>+7.1%} {d['p']:>8.4f}   {c['a']:>4d}->{c['b']:<4d} {k['a']:>3d}->{k['b']:<3d}")

    print(f"\n{'ALL CHECKS PASSED' if not FAILURES else 'FAILURES: ' + ', '.join(FAILURES)}")
    sys.exit(0 if not FAILURES else 1)


if __name__ == "__main__":
    main()
