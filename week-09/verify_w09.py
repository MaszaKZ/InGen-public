"""Independent verification of the Week 9 deliverables.

Checks, from committed sources only:
  1. Paper tables T1/T2a/T2b/T2c match an independent re-derivation from
     `week-07/W07_Analysis.json` and `week-07/W07_Run_Metadata.json`.
  2. The abstract respects the 150-200 word budget and carries all three
     registered contrasts, the synthetic/text-only boundary, and the
     amendment limitation.
  3. Every quantitative prose value is recomputed from its committed artifact
     (Week 6 analysis, Week 7 analysis/results, Week 8 audit) or checked for
     consistency with its source document (research-note effect sizes).
  4. Citations resolve against `references.bib`; local links resolve on disk.
  5. Required structure, claim-status labels, and disclosure language are
     present; forbidden overclaim phrasings are absent.
  6. The self-critique answers all four plan questions and names a specific
     paper; the research log carries the plan-required reflection and the
     reproducibility findings; meeting-feedback conformance (2026-08-03) holds.

Usage (from the repository root):
    .\\.conda-w01\\python.exe week-09\\verify_w09.py
"""

from __future__ import annotations

import csv
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
W9 = ROOT / "week-09"
DRAFT = W9 / "W09_Paper_Draft_v1.md"
CRITIQUE = W9 / "W09_Self_Critique.md"
TABLES_MD = W9 / "W09_Paper_Tables.md"
LOG = W9 / "Wk-09-ResearchLog.md"
README9 = W9 / "README.md"
FEEDBACK = W9 / "W09_Meeting_Feedback.md"
ROOT_README = ROOT / "README.md"
BIB = ROOT / "references.bib"

W7_ANALYSIS = ROOT / "week-07" / "W07_Analysis.json"
W7_METADATA = ROOT / "week-07" / "W07_Run_Metadata.json"
W7_RESULTS = ROOT / "week-07" / "W07_Results.csv"
W7_NOTE = ROOT / "week-07" / "W07_Research_Note.md"
W6_ANALYSIS = ROOT / "week-06" / "W06_Analysis.json"
W8_AUDIT = ROOT / "week-08" / "W08_Pressure_Cue_Audit.json"
W5_MEMO = ROOT / "week-05" / "W05_Results_Memo.md"

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
MINUS = "−"

failures: list[str] = []


def require(condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def pct(x: float) -> str:
    return f"{100.0 * x:.1f}"


def spp(x: float) -> str:
    return f"{100.0 * x:+.1f}"


def upp(x: float) -> str:
    """Signed value with the Unicode minus used in prose."""
    return spp(x).replace("-", MINUS)


def _binom_cdf(k: int, n: int, p: float) -> float:
    return sum(math.comb(n, i) * p**i * (1.0 - p) ** (n - i) for i in range(k + 1))


def clopper_pearson(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """Exact Clopper-Pearson interval by bisection on the binomial CDF."""
    if k == 0:
        lower = 0.0
    else:
        a, b = 0.0, 1.0
        for _ in range(80):
            mid = (a + b) / 2
            if 1.0 - _binom_cdf(k - 1, n, mid) < alpha / 2:
                a = mid
            else:
                b = mid
        lower = (a + b) / 2
    if k == n:
        upper = 1.0
    else:
        a, b = 0.0, 1.0
        for _ in range(80):
            mid = (a + b) / 2
            if _binom_cdf(k, n, mid) > alpha / 2:
                a = mid
            else:
                b = mid
        upper = (a + b) / 2
    return lower, upper


def cohen_h(p1: float, p2: float) -> float:
    return 2.0 * math.asin(math.sqrt(p1)) - 2.0 * math.asin(math.sqrt(p2))


# --------------------------------------------------------------------------
# 1. Generated tables
# --------------------------------------------------------------------------

def expected_t1_rows(metadata: dict) -> list[str]:
    generators = ", ".join(
        f"{MODEL_LABELS[g['id']]} (rev `{g['revision'][:12]}`)"
        for g in metadata["generators"]
    )
    judges = ", ".join(
        f"{j['id']} (rev `{j['revision'][:12]}`)" for j in metadata["judges"]
    )
    dec = metadata["decoding"]
    ana = metadata["analysis"]
    return [
        f"| Generators | {generators} |",
        f"| Seeds | {', '.join(str(s) for s in metadata['seeds'])} |",
        f"| Generations / judgments | {metadata['row_counts']['generations']:,} / {metadata['row_counts']['judgments']:,} |",
        f"| Decoding | temperature {dec['temperature']}, top-p {dec['top_p']}, max {dec['max_new_tokens']} new tokens; NF4 double-quantized, float16 compute |",
        f"| Judge panel | {judges} |",
        f"| Uncertainty | {ana['bootstrap_draws']:,} bootstrap draws over complete scenario families (seed {ana['bootstrap_seed']}) |",
    ]


def expected_t2a_rows(analysis: dict) -> list[str]:
    cells: dict[tuple[str, str], dict[str, dict]] = {}
    for entry in analysis["rates"]:
        cells.setdefault((entry["model"], entry["condition"]), {})[
            entry["subtype"]
        ] = entry

    def cell(e: dict) -> str:
        count = round(e["estimate"] * e["rows"])
        return (
            f"{pct(e['estimate'])}% ({count}/{e['rows']}) "
            f"[{pct(e['ci_low'])}, {pct(e['ci_high'])}]"
        )

    rows = []
    for model in MODEL_LABELS:
        for condition in CONDITION_LABELS:
            c = cells[(model, condition)]
            rows.append(
                f"| {MODEL_LABELS[model]} | {CONDITION_LABELS[condition]} | "
                f"{cell(c['plain'])} | {cell(c['pressured'])} | {cell(c['control'])} |"
            )
    return rows


def expected_t2b_rows(analysis: dict) -> list[str]:
    primary = analysis["paired_contrasts"]["primary_common_baseline"]
    rows = []
    for subtype in ("plain", "pressured", "control"):
        e = primary[subtype]
        rows.append(
            f"| {SUBTYPE_LABELS[subtype]} | {spp(e['estimate'])}pp "
            f"[{spp(e['ci_low'])}, {spp(e['ci_high'])}] (n={e['rows']}) |"
        )
    return rows


def expected_t2c_rows(analysis: dict) -> list[str]:
    rule = analysis["mitigation_rule"]["results"]
    rows = []
    for model in MODEL_LABELS:
        for intervention in ("deliberation", "structured_output", "constraint_gated"):
            r = rule[model][intervention]
            rows.append(
                f"| {MODEL_LABELS[model]} | {CONDITION_LABELS[intervention]} | "
                f"{100.0 * r['pressured_relative_reduction']:+.1f}% | "
                f"{spp(r['control_failure_increase'])}pp | "
                f"{'**Yes**' if r['passes'] else 'No'} |"
            )
    return rows


def verify_tables() -> None:
    analysis = json.loads(read(W7_ANALYSIS))
    metadata = json.loads(read(W7_METADATA))
    draft = read(DRAFT)
    tables_md = read(TABLES_MD)
    for label, rows in (
        ("T1", expected_t1_rows(metadata)),
        ("T2a", expected_t2a_rows(analysis)),
        ("T2b", expected_t2b_rows(analysis)),
        ("T2c", expected_t2c_rows(analysis)),
    ):
        for row in rows:
            require(row in draft, f"{label} row missing from draft: {row}")
            require(row in tables_md, f"{label} row missing from W09_Paper_Tables.md: {row}")
    passing = [
        (m, i)
        for m, arms in analysis["mitigation_rule"]["results"].items()
        for i, r in arms.items()
        if r["passes"]
    ]
    require(
        passing == [("Qwen/Qwen2.5-7B-Instruct", "deliberation")],
        f"unexpected mitigation-rule passes: {passing}",
    )
    require(
        draft.count("**Yes**") == 1,
        "draft must mark exactly one rule pass as **Yes**",
    )


# --------------------------------------------------------------------------
# 2. Abstract
# --------------------------------------------------------------------------

def verify_abstract() -> None:
    draft = read(DRAFT)
    m = re.search(r"## Abstract\n(.*?)\n## 1 ", draft, re.S)
    require(m is not None, "abstract section not found")
    if not m:
        return
    abstract = m.group(1)
    words = len(abstract.split())
    require(150 <= words <= 200, f"abstract has {words} words; budget is 150-200")

    analysis = json.loads(read(W7_ANALYSIS))
    primary = analysis["paired_contrasts"]["primary_common_baseline"]
    for subtype in ("plain", "pressured", "control"):
        e = primary[subtype]
        magnitude = f"{abs(100.0 * e['estimate']):.1f}"
        ci = f"[{upp(e['ci_low'])}, {upp(e['ci_high'])}]".replace("+", "+")
        require(magnitude in abstract, f"abstract missing {subtype} estimate {magnitude}")
        require(ci in abstract, f"abstract missing {subtype} CI {ci}")
    for term in ("synthetic", "text-only", "amendment"):
        require(term in abstract, f"abstract missing required boundary term '{term}'")


# --------------------------------------------------------------------------
# 3. Prose values recomputed from artifacts
# --------------------------------------------------------------------------

def verify_week6_values() -> None:
    draft = read(DRAFT)
    diag = json.loads(read(W6_ANALYSIS))["diagnostic_baseline_pressured_vs_plain"]
    require(f"{diag['a_failures']}/32 plain" in draft, "W6 plain count mismatch")
    require(f"{diag['b_failures']}/32 pressured" in draft, "W6 pressured count mismatch")
    require(upp(diag["difference_b_minus_a"]) + "pp" in draft, "W6 difference mismatch")
    require(
        f"p = {diag['exact_two_sided_mcnemar_p']:.4f}" in draft,
        "W6 McNemar p mismatch",
    )
    boot = diag["family_bootstrap"]
    ci = f"[{upp(boot['lower_95'])}, {upp(boot['upper_95'])}]"
    require(ci in draft, f"W6 bootstrap CI mismatch: expected {ci}")


def verify_week8_audit_values() -> None:
    draft = read(DRAFT)
    audit = json.loads(read(W8_AUDIT))
    overall = {
        row["model_label"]: row
        for row in audit["results"]["overall_by_model"]
        if row["tactic"] == "all"
    }
    total_pairs = sum(r["complete_pairs"] for r in overall.values())
    require(f"{total_pairs} of 320" in draft, f"audit pair total {total_pairs} missing")
    for label, row in overall.items():
        diff = upp(row["paired_difference_pressured_minus_plain"]) + "pp"
        lo, hi = row["family_clustered_bootstrap_95_ci"]
        ci = f"[{upp(lo)}, {upp(hi)}]"
        require(diff in draft, f"audit difference for {label} missing: {diff}")
        require(ci in draft, f"audit CI for {label} missing: {ci}")
    feas = audit["feasibility"]
    require(feas["estimable"] is False, "audit feasibility flag changed")
    require(
        feas["plain_items_explicitly_stating_missing_prerequisite"] == 0,
        "plain salience coding changed",
    )
    asym = feas["within_pair_salience_asymmetry"]
    flagged = json.dumps(asym)
    require("8" in flagged and "false_clearance" in flagged, "pressured salience coding changed")
    require("8 of 32 pressured items" in draft, "draft missing pressured salience count")
    require("non-estimable" in draft, "draft missing non-estimable statement")


def verify_week7_prose_values() -> None:
    draft = read(DRAFT)
    note = read(W7_NOTE)
    analysis = json.loads(read(W7_ANALYSIS))

    # Rates quoted in prose (recomputed from the rates table).
    rates = {
        (e["model"], e["condition"], e["subtype"]): e for e in analysis["rates"]
    }
    q = "Qwen/Qwen2.5-7B-Instruct"
    m = "mistralai/Mistral-7B-Instruct-v0.3"
    require(
        f"{pct(rates[(q, 'adapted_baseline', 'pressured')]['estimate'])}% "
        f"→ {pct(rates[(q, 'deliberation', 'pressured')]['estimate'])}%" in draft,
        "Qwen deliberation margin (2.5% -> 0.0%) missing or mismatched",
    )
    require(
        f"{pct(rates[(m, 'adapted_baseline', 'pressured')]['estimate'])}% "
        f"→ {pct(rates[(m, 'constraint_gated', 'pressured')]['estimate'])}%" in draft,
        "Mistral gate worsening (18.8% -> 36.2%) missing or mismatched",
    )
    require("(160/160)" in draft, "Mistral gated plain 160/160 missing")

    # Judge agreement, recomputed.
    agree = analysis["judge_agreement"]
    require(
        f"{100.0 * agree['unanimous_action']:.1f}%" in draft,
        "unanimity percentage mismatch",
    )
    require(
        f"= {agree['fleiss_kappa_nominal']:.3f}" in draft,
        "Fleiss kappa mismatch",
    )
    pair = sorted(agree["pair_exact_agreement"].values())
    require(
        f"{pair[0]:.3f}–{pair[-1]:.3f}" in draft,
        "pairwise agreement range mismatch",
    )

    # Unparsed rows.
    unparsed = analysis["panel_unparsed"]
    require(unparsed["count"] == 3, "unparsed count changed")
    require(f"{unparsed['count']} of 4,800" in draft, "unparsed count missing from draft")
    require(f"{unparsed['rate']:.2%}" in draft, "unparsed rate missing from draft")

    # Tactic concentrations at the common baseline, recomputed.
    tactics = {
        (t["generator_model"], t["tactic"]): t
        for t in analysis["pressure_tactic_breakdown"]
        if t["condition"] == "common_baseline"
    }
    require(
        f"urgency ({tactics[(m, 'urgency')]['sum']}/{tactics[(m, 'urgency')]['count']})" in draft,
        "Mistral urgency tactic count mismatch",
    )
    require(
        f"authority claims ({tactics[(m, 'authority_claim')]['sum']}/{tactics[(m, 'authority_claim')]['count']})" in draft,
        "Mistral authority tactic count mismatch",
    )
    require(
        f"normalization ({tactics[(q, 'normalization')]['sum']}/{tactics[(q, 'normalization')]['count']})" in draft,
        "Qwen normalization tactic count mismatch",
    )

    # Platform strata, recomputed from the committed results CSV.
    with open(W7_RESULTS, encoding="utf-8", newline="") as fh:
        all_rows = [
            r for r in csv.DictReader(fh) if r["majority_failure"] in ("0", "1")
        ]
    rows = [r for r in all_rows if r["condition"] == "common_baseline"]
    strata: dict[tuple[str, str, str], list[int]] = {}
    for r in rows:
        key = (r["generator_model"], r["subtype"], r["platform"])
        strata.setdefault(key, []).append(int(r["majority_failure"]))
    def fail_n(model: str, subtype: str, platform: str) -> str:
        vals = strata[(model, subtype, platform)]
        return f"{sum(vals)}/{len(vals)}"
    care, sec = "Aido Humanoid", "Sentinel Prime AI"
    require(fail_n(q, "plain", care) == "39/80" and "39/80" in draft, "Qwen plain care stratum mismatch")
    require(fail_n(q, "plain", sec) == "15/80" and "15/80" in draft, "Qwen plain security stratum mismatch")
    require(fail_n(q, "pressured", care) == "0/79" and "0/79" in draft, "Qwen pressured care stratum mismatch")
    require(fail_n(q, "pressured", sec) == "5/78" and "5/78" in draft, "Qwen pressured security stratum mismatch")
    require(fail_n(m, "pressured", care) == "40/80" and "40/80 = 50.0%" in draft, "Mistral pressured care stratum mismatch")
    require(fail_n(m, "pressured", sec) == "29/80" and "29/80 = 36.3%" in draft, "Mistral pressured security stratum mismatch")
    mistral_plain = sorted((fail_n(m, "plain", care), fail_n(m, "plain", sec)))
    require(mistral_plain == ["70/80", "72/80"], f"Mistral plain strata changed: {mistral_plain}")
    require("72/80 and 70/80" in draft, "Mistral plain strata missing from draft")

    # The strata paragraph and the §5.4 reuse must cite their source artifact
    # (2026-08-03 meeting feedback: strata are not tabulated in W07_Analysis.json).
    strata_para = next(
        (p for p in draft.split("\n\n") if p.startswith("Platform stratification")), ""
    )
    require("W07_Results.csv" in strata_para,
            "platform-strata paragraph must cite W07_Results.csv")
    care_vals = strata[(q, "plain", care)]
    require(
        f"{100.0 * sum(care_vals) / len(care_vals):.1f}% of plain care-boundary rows "
        f"at the common baseline — {sum(care_vals)}/{len(care_vals)}" in draft,
        "§5.4 care-boundary rate must carry its recomputed denominator",
    )
    require(draft.count("pressure_tactic_breakdown") >= 2,
            "§5.4 tactic counts must cite pressure_tactic_breakdown")

    # Supplementary effect sizes, recomputed from the registered rates. The
    # notebook computes h on full 160-row arm denominators (unparsed rows
    # counted as non-failures); the draft must disclose that convention and
    # give the registered-denominator value alongside it.
    e = {
        (mm, ss): rates[(mm, "common_baseline", ss)]
        for mm in (q, m)
        for ss in ("plain", "pressured", "control")
    }
    h_plain = abs(cohen_h(e[(q, "plain")]["estimate"], e[(m, "plain")]["estimate"]))
    h_control = abs(cohen_h(e[(q, "control")]["estimate"], e[(m, "control")]["estimate"]))
    q_press_fail = round(e[(q, "pressured")]["estimate"] * e[(q, "pressured")]["rows"])
    h_press_notebook = abs(cohen_h(q_press_fail / 160.0, e[(m, "pressured")]["estimate"]))
    h_press_registered = abs(
        cohen_h(e[(q, "pressured")]["estimate"], e[(m, "pressured")]["estimate"])
    )
    rr_plain = e[(q, "plain")]["estimate"] / e[(m, "plain")]["estimate"]
    rr_press = e[(q, "pressured")]["estimate"] / e[(m, "pressured")]["estimate"]
    for token in (
        f"h = {h_plain:.2f}",
        f"h = {h_press_notebook:.2f}",
        f"h = {h_control:.2f}",
        "88 of 160",
        f"risk ratio {rr_plain:.2f}",
        f"risk ratio {rr_press:.2f}",
    ):
        require(token in draft, f"draft missing supplementary statistic '{token}'")
        require(token in note, f"research note lacks supplementary statistic '{token}' quoted in draft")
    require(round(h_press_notebook, 2) != round(h_press_registered, 2),
            "denominator conventions now agree at 2 dp; drop the §4.1 h disclosure")
    require(f"h = {h_press_registered:.2f}" in draft,
            "draft missing registered-denominator pressured h disclosure")
    require("full 160-row arm denominators" in draft,
            "draft missing notebook denominator-convention disclosure")
    h_delib = cohen_h(
        rates[(m, "deliberation", "pressured")]["estimate"],
        rates[(m, "adapted_baseline", "pressured")]["estimate"],
    )
    require(f"h = {h_delib:+.2f}" in draft, "Mistral deliberation h mismatch")

    # Discordant-pair statements, recomputed by pairing committed outcomes.
    def outcomes(model: str, condition: str, subtype: str) -> dict[tuple[str, str], int]:
        return {
            (r["scenario_id"], r["seed"]): int(r["majority_failure"])
            for r in all_rows
            if r["generator_model"] == model
            and r["condition"] == condition
            and r["subtype"] == subtype
        }

    def discordant(a: dict, b: dict) -> tuple[int, int]:
        keys = a.keys() & b.keys()
        n01 = sum(1 for k in keys if a[k] == 0 and b[k] == 1)
        n10 = sum(1 for k in keys if a[k] == 1 and b[k] == 0)
        return n01, n10

    qm_plain = discordant(outcomes(q, "common_baseline", "plain"), outcomes(m, "common_baseline", "plain"))
    require(qm_plain == (88, 0), f"plain discordant pairs changed: {qm_plain}")
    require(2.0 * 0.5 ** sum(qm_plain) < 1e-26, "plain McNemar bound no longer holds")
    qm_ctrl = discordant(outcomes(q, "common_baseline", "control"), outcomes(m, "common_baseline", "control"))
    require(qm_ctrl == (0, 30), f"control discordant pairs changed: {qm_ctrl}")
    require("all 30 discordant pairs against Qwen" in draft,
            "draft missing control discordance statement")
    q_delib = discordant(outcomes(q, "adapted_baseline", "pressured"), outcomes(q, "deliberation", "pressured"))
    require(q_delib == (0, 4), f"Qwen deliberation discordant pairs changed: {q_delib}")
    require("4 discordant pairs" in draft, "draft missing 4-discordant-pair statement")
    require(f"p = {2.0 * 0.5 ** sum(q_delib):g}" in draft,
            "Qwen deliberation McNemar p missing or mismatched")

    # Panel acceptance record: CP bounds recomputed exactly; the Week 7
    # record's rounding of the pooled-holdout upper bound is disclosed.
    lo, hi = clopper_pearson(80, 83)
    require(f"[{lo:.3f}, {hi:.3f}]" in draft,
            f"draft missing exact holdout CP interval [{lo:.3f}, {hi:.3f}]")
    require("rounds the upper bound to 0.993" in draft,
            "draft missing the acceptance-record rounding disclosure")
    require("[0.898, 0.993]" in note,
            "W07 note no longer records [0.898, 0.993]; update the draft disclosure")
    s_lo, _ = clopper_pearson(14, 16)
    for token in ("80/83", "14/16", f"{s_lo:.3f}"):
        require(token in draft, f"draft missing panel statistic '{token}'")
        require(token in note, f"research note lacks panel statistic '{token}' quoted in draft")

    # Week 5 token-cap fact, checked against its source memo.
    require("64 of 72" in draft, "draft missing W5 token-cap fact")
    require("64 of 72 chain-of-thought responses reached the 160-token cap" in read(W5_MEMO),
            "W05 memo no longer states the 64-of-72 token-cap fact")


# --------------------------------------------------------------------------
# 4. Citations and links
# --------------------------------------------------------------------------

def verify_citations() -> None:
    bib_keys = set(re.findall(r"@misc\{([^,]+),", read(BIB)))
    draft = read(DRAFT)
    cited = set()
    for group in re.findall(r"\[(@[^\]]+)\]", draft):
        for token in group.split(";"):
            token = token.strip()
            if token.startswith("@"):
                cited.add(token[1:])
    unknown = cited - bib_keys
    require(not unknown, f"citations not in references.bib: {sorted(unknown)}")
    core = {
        "openx2023rtx", "kim2024openvla", "octo2024policy", "tolle2025safe",
        "tolle2025inductive", "lekeufack2023conformal", "rezaeikhavas2020trust",
        "sanneman2020trust", "zhang2026healthorsc", "qin2026runtime",
    }
    require(core <= cited, f"handoff core citations missing: {sorted(core - cited)}")
    arxiv_keys = {k for k in bib_keys if not k.startswith("ingen")}
    require(len(arxiv_keys) == 20, f"expected 20 arXiv bib entries, found {len(arxiv_keys)}")
    listed = set(re.findall(r"^- \[@([^\]]+)\]", draft, re.M))
    require(listed == bib_keys, f"references section does not list exactly the bib keys; diff: {sorted(listed ^ bib_keys)}")


def verify_links() -> None:
    for doc in (DRAFT, CRITIQUE, LOG, README9, FEEDBACK):
        text = read(doc)
        for target in re.findall(r"\]\(([^)#]+?)\)", text):
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            resolved = (doc.parent / target).resolve()
            require(resolved.exists(), f"broken local link in {doc.name}: {target}")


# --------------------------------------------------------------------------
# 5. Structure, labels, disclosures
# --------------------------------------------------------------------------

def verify_structure() -> None:
    draft = read(DRAFT)
    headers = [
        "## Abstract", "## 1 Introduction", "## 2 Related work", "## 3 Methods",
        "## 4 Results", "## 5 Discussion", "## 6 Limitations and future work",
        "## 7 Conclusion", "## Evidence provenance", "## References",
    ]
    positions = [draft.find(h) for h in headers]
    require(all(p >= 0 for p in positions), f"missing section headers: {[h for h, p in zip(headers, positions) if p < 0]}")
    require(positions == sorted(positions), "section headers out of order")

    amendment = draft.find("W07_Panel_Acceptance_Amendment.json")
    results_at = draft.find("## 4 Results")
    require(0 <= amendment < results_at, "amendment must be described before Results")

    require("This section is a literature analysis" in draft,
            "related work must open with the literature/program separation statement")

    for label in ("(confirmatory)", "(descriptive)", "(proposed)", "exploratory"):
        require(label in draft, f"claim-status label '{label}' missing")
    require(
        "### 4.3 Plain caution fails more than pressured caution (exploratory)" in draft,
        "C4/§4.3 must be labeled exploratory",
    )
    require(
        "**(Exploratory)** Both generators failed" in draft,
        "C4 summary in the introduction must be labeled exploratory",
    )
    require(
        "design-stack sensitivity, not a causal bank effect" in draft,
        "cross-week reversal must preserve its non-causal design-stack scope",
    )
    require(
        "did not transfer uniformly between the two tested generator stacks" in draft,
        "mitigation portability claim must remain scoped to the tested stacks",
    )
    require("**Contribution (confirmatory).**" in draft, "explicit contribution statement missing")
    require("not deployment approvals" in draft, "deployment-approval disclaimer missing")
    require("neither supported nor ruled out" in draft, "salience both-ways statement missing")

    for pattern, msg in (
        (r"salience explanation (was|is|has been) ruled out", "stale salience wording"),
        (r"cannot explain the reversal", "stale 'cannot explain' wording"),
        (r"validates? (the )?PIC", "PIC validation overclaim"),
        (r"deployment[- ]ready|production[- ]ready", "deployment-readiness overclaim"),
        (r"bank-sensitive|property of bank construction", "causal bank-attribution overclaim"),
        (r"not a portable mitigation", "universal prompt-portability overclaim"),
        (r"\bproves\b", "'proves' overclaim"),
    ):
        require(not re.search(pattern, draft, re.I), f"forbidden phrasing present: {msg}")

    body = re.search(r"## Abstract(.*?)## Evidence provenance", draft, re.S).group(1)
    prose_lines = [
        l for l in body.splitlines()
        if not l.strip().startswith(("|", "!", ">", "#", "-", "*Figure"))
    ]
    words = len(" ".join(prose_lines).split())
    require(2900 <= words <= 4300, f"main-text prose is {words} words; expected 2900-4300 (~8-10 pages with tables/figures)")

    prov = draft[draft.find("## Evidence provenance"):]
    for claim in ("C1", "C2", "C3", "C4", "C5"):
        require(f"| {claim} " in prov, f"provenance table missing row for {claim}")
    for artifact in (
        "../week-07/W07_Analysis.json", "../week-07/W07_Run_Metadata.json",
        "../week-05/W05_Results_Memo.md", "../week-06/W06_Analysis.json",
        "../week-08/W08_Pressure_Cue_Audit.md",
    ):
        require(artifact in draft, f"meeting-feedback artifact reference missing: {artifact}")

    figures = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", draft)
    require(len(figures) == 3, f"expected 3 figures, found {len(figures)}")
    for fig in figures:
        svg = (W9 / fig).resolve()
        require(svg.exists(), f"figure missing on disk: {fig}")
        require(svg.with_suffix(".png").exists(), f"PNG fallback missing for: {fig}")


# --------------------------------------------------------------------------
# 6. Self-critique, research log, READMEs, meeting feedback
# --------------------------------------------------------------------------

def verify_self_critique() -> None:
    text = read(CRITIQUE)
    for part in ("## (a)", "## (b)", "## (c)", "## (d)"):
        require(part in text, f"self-critique missing section {part}")
    require("2509.15293" in text and "FoMER" in text,
            "self-critique must name a specific paper (FoMER, arXiv:2509.15293)")
    require("4 discordant" in text, "self-critique must quantify the questioned result")
    require("14/16" in text, "self-critique must carry the weakest-stratum figure")


def verify_log() -> None:
    text = read(LOG)
    require("hardest" in text.lower(), "log must include the hardest-section reflection")
    m = re.search(r"## Weekly summary.*?\n(.*?)\n## ", text, re.S)
    require(m is not None, "log missing weekly summary section")
    if m:
        words = len(m.group(1).split())
        require(300 <= words <= 500, f"weekly summary is {words} words; budget 300-500")
    require("## Deliverable conformance" in text, "log missing conformance section")
    require("## Verification record" in text, "log missing verification record")
    require("dc:date" in text and "hashsalt" in text,
            "log must document the SVG nondeterminism finding and its fix")
    require("PASS: Week 9 verification complete" in text,
            "log must record the verifier acceptance line")


def verify_readmes_and_feedback() -> None:
    readme = read(README9)
    for name in (
        "W09_Paper_Draft_v1.md", "W09_Self_Critique.md", "Wk-09-ResearchLog.md",
        "W09_Meeting_Feedback.md", "build_w09_paper_tables.py", "verify_w09.py",
    ):
        require(name in readme, f"week-09 README missing reference to {name}")
    require("week-09" in read(ROOT_README), "root README does not mention week-09")
    feedback = read(FEEDBACK)
    require(
        "Status: implemented in the Week 9 draft" in feedback,
        "meeting-feedback status must record Week 9 implementation",
    )
    for phrase in ("quantitative", "source artifacts", "literature"):
        require(phrase in feedback, f"meeting-feedback note missing directive keyword '{phrase}'")


# --------------------------------------------------------------------------

def main() -> int:
    sections = [
        ("generated tables against committed JSON", verify_tables),
        ("abstract budget and contrasts", verify_abstract),
        ("Week 6 values", verify_week6_values),
        ("Week 8 audit values", verify_week8_audit_values),
        ("Week 7 prose values and strata", verify_week7_prose_values),
        ("citations and bibliography", verify_citations),
        ("local links", verify_links),
        ("structure, labels, and disclosures", verify_structure),
        ("self-critique", verify_self_critique),
        ("research log", verify_log),
        ("READMEs and meeting feedback", verify_readmes_and_feedback),
    ]
    for name, fn in sections:
        before = len(failures)
        try:
            fn()
        except Exception as exc:  # verification must never pass on a crash
            failures.append(f"{name}: exception {type(exc).__name__}: {exc}")
        print(("PASS" if len(failures) == before else "FAIL") + f": {name}")
    if failures:
        print()
        for f in failures:
            print(f"  - {f}")
        print(f"\nFAIL: Week 9 verification found {len(failures)} problem(s)")
        return 1
    print("PASS: Week 9 verification complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
