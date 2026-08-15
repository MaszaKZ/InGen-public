"""Independent verification of the Week 10 deliverables.

Checks, from committed sources only:
  1. Paper draft v2 embeds tables T1/T2a/T2b/T2c matching an independent
     re-derivation from `week-07/W07_Analysis.json` and
     `week-07/W07_Run_Metadata.json`.
  2. The v2 abstract respects the 150-200 word budget, carries all three
     registered contrasts, the boundary terms, and the blunter
     judge-dependence statement with the conditional stress value.
  3. Every quantitative prose value carried over from v1 still recomputes
     from its committed artifact (Week 6 analysis, Week 8 audit, Week 7
     analysis/results/note).
  4. The conditional judge-measurement stress analysis is recomputed end-to-end from the
     amendment, analysis JSON, and results CSV, and matches
     `W10_Judge_Sensitivity.json` and every value the draft quotes from it.
  5. The FoMER engagement is present with its bank-grounded example and the
     paired-controls argument.
  6. Citations resolve against `references.bib`; local links in every
     Week 10 document resolve on disk (fetch-first in a fresh clone).
  7. Required structure, claim-status labels, and disclosure language are
     present in v2; forbidden overclaim phrasings are absent.
  8. The reproducibility package is internally consistent: manifest hashes
     match the on-disk raw evidence and the run-metadata pins, externalized
     paths are untracked and ignored, requirements are exactly pinned, and
     the package README covers every canonical script.
  9. The capstone outline carries all eleven planned sections in order plus
     the two drafted sections with the literature separation statement.
 10. The research log records the required reflection, budgets, and
     verification record.
11. The Week 10 READMEs, feedback note, and clean-environment test record
     are present with their required content.

Usage (from the repository root):
    python week-10/verify_w10.py
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
W10 = ROOT / "week-10"
DRAFT = W10 / "W10_Paper_Draft_v2.md"
CAPSTONE = W10 / "W10_Capstone_Outline.md"
SENSITIVITY = W10 / "W10_Judge_Sensitivity.json"
LOG = W10 / "Wk-10-ResearchLog.md"
README10 = W10 / "README.md"
FEEDBACK = W10 / "W10_Feedback.md"
PACKAGE = W10 / "W10_Reproducibility_Package"
MANIFEST = PACKAGE / "data_manifest.json"
TEST_RECORD = PACKAGE / "W10_CleanEnv_Test_Transcript.md"
ROOT_README = ROOT / "README.md"
BIB = ROOT / "references.bib"

W7_ANALYSIS = ROOT / "week-07" / "W07_Analysis.json"
W7_METADATA = ROOT / "week-07" / "W07_Run_Metadata.json"
W7_RESULTS = ROOT / "week-07" / "W07_Results.csv"
W7_NOTE = ROOT / "week-07" / "W07_Research_Note.md"
W7_AMENDMENT = ROOT / "week-07" / "W07_Panel_Acceptance_Amendment.json"
W7_BANK = ROOT / "week-07" / "W07_Confirmation_Bank.json"
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
QWEN = "Qwen/Qwen2.5-7B-Instruct"
MISTRAL = "mistralai/Mistral-7B-Instruct-v0.3"

EXTERNALIZED = [
    "week-03/W03_Raw_Model_Outputs.jsonl",
    "week-04/W04_Raw_Model_Outputs.jsonl",
    "week-05/W05_Raw_Model_Outputs.jsonl",
    "week-06/W06_Raw_Model_Outputs.jsonl",
    "week-06/W06_Judge_Ratings.csv",
    "week-07/W07_Preflight_Raw_Model_Outputs.jsonl",
    "week-07/W07_Raw_Model_Outputs.jsonl",
    "week-07/W07_Holdout_Diagnostic_Raw_Model_Outputs.jsonl",
    "week-07/W07_Judge_Ratings.csv",
    "week-07/W07_Judge_Gold_Ratings.csv",
]

ARCHIVE_SUFFIXES = (".7z", ".zip", ".tar", ".tar.gz", ".tgz")


def parse_git_ls_files_output(output: str) -> list[str]:
    return [path for path in output.split("\0") if path]


def forbidden_tracked_artifacts(paths: list[str]) -> list[str]:
    offenders: list[str] = []
    for original in paths:
        path = original.replace("\\", "/")
        lower = path.lower()
        name = lower.rsplit("/", 1)[-1]
        is_raw_output = name.endswith("raw_model_outputs.jsonl")
        is_archive = any(lower.endswith(suffix) for suffix in ARCHIVE_SUFFIXES)
        if is_raw_output or is_archive:
            offenders.append(path)
    return sorted(set(offenders))

CANONICAL_SCRIPTS = [
    "run_w03_baseline.py",
    "run_w04_extended.py",
    "run_w05_experiment.py", "audit_w05_semantics.py", "build_w05_notebook.py",
    "build_w06_bank.py", "run_w06_experiment2.py", "judge_w06_experiment2.py",
    "scorer_w06.py", "test_w06_experiment2.py", "verify_w06_independent.py",
    "w07_common.py", "w07_prompts.py", "w07_judge_measurement.py",
    "build_w07_confirmation_bank.py", "run_w07_replication.py",
    "audit_w07_preflight.py", "build_w07_gold.py", "build_w07_holdout.py",
    "generate_w07_holdout_pool.py", "judge_w07_holdout.py",
    "judge_w07_replication.py", "analyze_w07.py", "analyze_w07_panel_ceiling.py",
    "build_w07_notebook.py", "write_w07_report.py", "test_w07_replication.py",
    "verify_w07_independent.py",
    "analyze_w08_pressure_cues.py", "verify_w08.py",
    "build_w09_paper_tables.py", "build_w09_paper_figures.py", "verify_w09.py",
    "analyze_w10_judge_sensitivity.py", "verify_w10.py",
    "fetch_data.py", "regenerate_all.py",
]

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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def parsed_result_rows() -> list[dict[str, str]]:
    with open(W7_RESULTS, encoding="utf-8", newline="") as fh:
        return [r for r in csv.DictReader(fh) if r["majority_failure"] in ("0", "1")]


# --------------------------------------------------------------------------
# 1. Generated tables embedded in draft v2
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
    for label, rows in (
        ("T1", expected_t1_rows(metadata)),
        ("T2a", expected_t2a_rows(analysis)),
        ("T2b", expected_t2b_rows(analysis)),
        ("T2c", expected_t2c_rows(analysis)),
    ):
        for row in rows:
            require(row in draft, f"{label} row missing from draft v2: {row}")
    passing = [
        (m, i)
        for m, arms in analysis["mitigation_rule"]["results"].items()
        for i, r in arms.items()
        if r["passes"]
    ]
    require(
        passing == [(QWEN, "deliberation")],
        f"unexpected mitigation-rule passes: {passing}",
    )
    require(
        draft.count("**Yes**") == 1,
        "draft v2 must mark exactly one rule pass as **Yes**",
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
        ci = f"[{upp(e['ci_low'])}, {upp(e['ci_high'])}]"
        require(magnitude in abstract, f"abstract missing {subtype} estimate {magnitude}")
        require(ci in abstract, f"abstract missing {subtype} CI {ci}")
    for term in ("synthetic", "text-only", "amendment"):
        require(term in abstract, f"abstract missing required boundary term '{term}'")

    # Self-critique point (a): the blunter judge-dependence statement, with
    # the conditional stress value quoted from the committed sensitivity JSON.
    require("not human-annotated ground truth" in abstract,
            "abstract missing the blunt judge-dependence statement")
    sens = json.loads(read(SENSITIVITY))
    stressed = sens["c1_false_negative_stress"]["plain"]["stressed_gap_pp"]
    require(f"{MINUS}{abs(stressed):.1f} points" in abstract,
            f"abstract missing conditional stress value {stressed}")


# --------------------------------------------------------------------------
# 3. Week 6 and Week 8 prose values
# --------------------------------------------------------------------------

def verify_week6_week8_values() -> None:
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
    require("8 of 32 pressured items" in draft, "draft missing pressured salience count")
    require("non-estimable" in draft, "draft missing non-estimable statement")


# --------------------------------------------------------------------------
# 4. Week 7 prose values and strata
# --------------------------------------------------------------------------

def verify_week7_prose_values() -> None:
    draft = read(DRAFT)
    note = read(W7_NOTE)
    analysis = json.loads(read(W7_ANALYSIS))

    rates = {
        (e["model"], e["condition"], e["subtype"]): e for e in analysis["rates"]
    }
    q, m = QWEN, MISTRAL
    require(
        f"{pct(rates[(q, 'adapted_baseline', 'pressured')]['estimate'])}% "
        f"→ {pct(rates[(q, 'deliberation', 'pressured')]['estimate'])}%" in draft,
        "Qwen deliberation margin missing or mismatched",
    )
    require(
        f"{pct(rates[(m, 'adapted_baseline', 'pressured')]['estimate'])}% "
        f"→ {pct(rates[(m, 'constraint_gated', 'pressured')]['estimate'])}%" in draft,
        "Mistral gate worsening missing or mismatched",
    )
    require("(160/160)" in draft, "Mistral gated plain 160/160 missing")

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

    unparsed = analysis["panel_unparsed"]
    require(unparsed["count"] == 3, "unparsed count changed")
    require(f"{unparsed['count']} of 4,800" in draft, "unparsed count missing from draft")
    require(f"{unparsed['rate']:.2%}" in draft, "unparsed rate missing from draft")

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

    all_rows = parsed_result_rows()
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
    require("72/80 and 70/80" in draft, "Mistral plain strata missing from draft")
    require("W07_Results.csv" in draft, "platform strata must cite W07_Results.csv")

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
    qm_ctrl = discordant(outcomes(q, "common_baseline", "control"), outcomes(m, "common_baseline", "control"))
    require(qm_ctrl == (0, 30), f"control discordant pairs changed: {qm_ctrl}")
    q_delib = discordant(outcomes(q, "adapted_baseline", "pressured"), outcomes(q, "deliberation", "pressured"))
    require(q_delib == (0, 4), f"Qwen deliberation discordant pairs changed: {q_delib}")
    require("4 discordant pairs" in draft, "draft missing 4-discordant-pair statement")
    require(f"p = {2.0 * 0.5 ** sum(q_delib):g}" in draft,
            "Qwen deliberation McNemar p missing or mismatched")

    lo, hi = clopper_pearson(80, 83)
    require(f"[{lo:.3f}, {hi:.3f}]" in draft,
            f"draft missing exact holdout CP interval [{lo:.3f}, {hi:.3f}]")
    require("rounds the upper bound to 0.993" in draft,
            "draft missing the acceptance-record rounding disclosure")
    s_lo, _ = clopper_pearson(14, 16)
    for token in ("80/83", "14/16", f"{s_lo:.3f}"):
        require(token in draft, f"draft missing panel statistic '{token}'")
    require("64 of 72" in draft, "draft missing W5 token-cap fact")
    require("64 of 72 chain-of-thought responses reached the 160-token cap" in read(W5_MEMO),
            "W05 memo no longer states the 64-of-72 token-cap fact")


# --------------------------------------------------------------------------
# 5. Judge-measurement stress analysis, recomputed end-to-end
# --------------------------------------------------------------------------

def verify_sensitivity() -> None:
    sens = json.loads(read(SENSITIVITY))
    draft = read(DRAFT)
    require(sens["schema_version"] == "w10-judge-sensitivity-v2",
            "sensitivity JSON schema changed")

    # Input hashes recorded in the JSON must match the committed artifacts.
    for entry in sens["inputs"]:
        actual = sha256_file(ROOT / entry["path"])
        require(actual == entry["sha256"],
                f"sensitivity input {entry['path']} hash drifted")

    amendment = json.loads(read(W7_AMENDMENT))
    pooled = amendment["claim"]["pooled_fresh_evidence_rounds_3_to_5"]
    stratum = pooled["unsafe_compliance_detection"]
    control_stratum = pooled["over_verification_detection"]
    require((stratum["correct"], stratum["n"]) == (14, 16), "unsafe amendment stratum changed")
    require((control_stratum["correct"], control_stratum["n"]) == (18, 18),
            "control amendment stratum changed")
    cp_lo, cp_hi = clopper_pearson(14, 16)
    require([round(cp_lo, 4), round(cp_hi, 4)] == stratum["cp95"],
            "amendment CP95 no longer matches exact recomputation")
    control_lo, control_hi = clopper_pearson(18, 18)
    require([round(control_lo, 4), round(control_hi, 4)] == control_stratum["cp95"],
            "control amendment CP95 no longer matches exact recomputation")
    unsafe_sensitivity_floor = min(stratum["cp95"][0], cp_lo)
    control_sensitivity_floor = min(control_stratum["cp95"][0], control_lo)
    require(sens["strata"]["unsafe_compliance_detection"]["sensitivity_floor"] == unsafe_sensitivity_floor,
            "unsafe sensitivity floor mismatch")
    require(sens["strata"]["over_verification_detection"]["sensitivity_floor"] == control_sensitivity_floor,
            "control sensitivity floor mismatch")

    def max_true_failures(observed: int, rows: int, sensitivity: float, alpha: float = 0.05) -> int:
        candidates = [
            true_failures
            for true_failures in range(observed, rows + 1)
            if _binom_cdf(observed, true_failures, sensitivity) >= alpha
        ]
        return max(candidates)

    # Paired counts recomputed from the results CSV.
    all_rows = parsed_result_rows()

    def paired_counts(subtype: str) -> tuple[int, int, int]:
        outcomes: dict[str, dict[tuple[str, str], int]] = {QWEN: {}, MISTRAL: {}}
        for r in all_rows:
            if r["condition"] == "common_baseline" and r["subtype"] == subtype and r["generator_model"] in outcomes:
                outcomes[r["generator_model"]][(r["scenario_id"], r["seed"])] = int(r["majority_failure"])
        keys = outcomes[QWEN].keys() & outcomes[MISTRAL].keys()
        return (sum(outcomes[QWEN][k] for k in keys),
                sum(outcomes[MISTRAL][k] for k in keys), len(keys))

    for subtype in ("plain", "pressured"):
        k_q, k_m, n_pairs = paired_counts(subtype)
        b = sens["c1_false_negative_stress"][subtype]
        require(b["qwen_observed"]["failures"] == k_q and b["qwen_observed"]["pairs"] == n_pairs,
                f"{subtype} Qwen paired counts mismatch")
        require(b["mistral_observed"]["failures"] == k_m,
                f"{subtype} Mistral paired counts mismatch")
        max_q = max_true_failures(k_q, n_pairs, unsafe_sensitivity_floor)
        require(b["qwen_max_true_failures"] == max_q,
                f"{subtype} conditional true-failure limit mismatch")
        require(b["observed_gap_pp"] == round(100 * (k_q - k_m) / n_pairs, 1),
                f"{subtype} observed gap mismatch")
        require(b["stressed_gap_pp"] == round(100 * (max_q - k_m) / n_pairs, 1),
                f"{subtype} stressed gap mismatch")
        require(b["sign_survives_false_negative_stress"] is (max_q - k_m < 0),
                f"{subtype} sign-survival flag mismatch")

    analysis = json.loads(read(W7_ANALYSIS))
    mitigation = sens["mitigation_false_negative_stress"]
    zc = mitigation["pressured_zero_cell"]
    max_concealed = max_true_failures(0, 160, unsafe_sensitivity_floor)
    require(zc["max_concealed_failures"] == max_concealed, "concealment count mismatch")
    require(zc["observed"] == {"failures": 0, "rows": 160}, "zero-cell observed changed")
    require(zc["adapted_baseline"] == {"failures": 4, "rows": 160}, "adapted cell changed")
    worst = (zc["adapted_baseline"]["failures"] - max_concealed) / zc["adapted_baseline"]["failures"]
    require(zc["stressed_relative_reduction"] == worst, "stressed reduction mismatch")
    require(zc["registered_minimum"] == analysis["mitigation_rule"]["thresholds"]["pressured_relative_reduction_min"],
            "registered minimum mismatch")
    require(zc["meets_registered_minimum"] is (worst >= zc["registered_minimum"]),
            "meets-registered-minimum flag mismatch")

    control = mitigation["control_cost"]
    require(control["adapted_baseline"] == {"failures": 23, "rows": 160},
            "adapted control count changed")
    require(control["deliberation"] == {"failures": 25, "rows": 160},
            "deliberation control count changed")
    max_deliberation = max_true_failures(25, 160, control_sensitivity_floor)
    stressed_cost = round(100 * (max_deliberation - 23) / 160, 1)
    require(control["deliberation_max_true_failures"] == max_deliberation,
            "deliberation control true-failure limit mismatch")
    require(control["stressed_control_cost_pp"] == stressed_cost,
            "stressed control cost mismatch")
    require(control["registered_ceiling_pp"] == 3.125,
            "registered control ceiling mismatch")
    require(control["observed_data_pass"] is True,
            "registered observed-data disposition changed")
    require(control["survives_combined_measurement_stress"] is False,
            "mitigation must fail the combined measurement stress")

    c1_control = sens["c1_control_false_negative_stress"]
    require(c1_control["mistral_max_true_failures"] == max_true_failures(0, 160, control_sensitivity_floor),
            "C1 control zero-cell limit mismatch")
    require(c1_control["stressed_gap_pp"] == 18.1,
            "C1 control stressed gap mismatch")

    # Every value the draft quotes from the stress analysis.
    plain = sens["c1_false_negative_stress"]["plain"]
    pressured = sens["c1_false_negative_stress"]["pressured"]
    for token, msg in (
        (f"to {MINUS}{abs(plain['stressed_gap_pp']):.1f}pp", "plain stressed gap"),
        (f"to {MINUS}{abs(pressured['stressed_gap_pp']):.1f}pp", "pressured stressed gap"),
        (f"+{control['stressed_control_cost_pp']:.1f}pp", "stressed mitigation control cost"),
        (f"+{c1_control['stressed_gap_pp']:.1f}pp", "C1 control stressed gap"),
        (f"up to {max_concealed} undetected failures", "concealment count"),
        (f"({worst:.0%}) sits exactly at the registered minimum", "stressed reduction statement"),
        ("18/18", "over-verification stratum"),
        ("does not survive the combined measurement stress", "mitigation robustness conclusion"),
        ("false positives are not estimated", "unestimated false-positive disclosure"),
        ("### 4.5 Judge-measurement stress analysis (descriptive)", "sensitivity subsection header"),
    ):
        require(token in draft, f"draft missing sensitivity value: {msg} ('{token}')")


# --------------------------------------------------------------------------
# 6. FoMER engagement
# --------------------------------------------------------------------------

def verify_fomer() -> None:
    draft = read(DRAFT)
    require("2509.15293" in draft, "FoMER arXiv id missing from draft v2")
    require("dissanayake2025fomer" in draft, "FoMER citation missing from draft v2")
    require("does not expose over-refusal as a dedicated paired endpoint" in draft,
            "bounded FoMER over-refusal comparison missing")
    require("blanket refusal can still lose final-answer or action-validity credit" in draft,
            "FoMER action-validity qualification missing")
    require("reports unauthorized-action interception and false-rejection rate together" in draft,
            "runtime-governance false-rejection comparison missing")
    require("applying both scoring schemes to a shared scenario set remains future work" in draft,
            "shared-scenario future-work statement missing")
    require("W7R-F01-P1" in draft, "bank-grounded scenario example missing")
    bank = json.loads(read(W7_BANK))
    scenarios = bank["scenarios"] if isinstance(bank, dict) and "scenarios" in bank else bank
    if isinstance(scenarios, dict):
        scenarios = list(scenarios.values())
    example = [s for s in scenarios if s.get("scenario_id") == "W7R-F01-P1"]
    require(len(example) == 1, "example scenario W7R-F01-P1 not found in the bank")
    if example:
        require(example[0]["subtype"] == "plain" and example[0]["expected_action"] == "WITHHOLD",
                "example scenario no longer a plain WITHHOLD item")
        require("traction-power isolation" in example[0]["stimulus"],
                "example scenario stimulus no longer matches the draft's description")
    require("W05_Results_Memo.md" in draft.split("## 3 Methods")[0],
            "FoMER engagement must link the Week 5 lexical-vs-semantic audit")


# --------------------------------------------------------------------------
# 7. Citations and links
# --------------------------------------------------------------------------

def verify_citations_and_links() -> None:
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
    require("dissanayake2025fomer" in cited, "FoMER must be cited in v2")
    listed = set(re.findall(r"^- \[@([^\]]+)\]", draft, re.M))
    require(listed == bib_keys, f"references section does not list exactly the bib keys; diff: {sorted(listed ^ bib_keys)}")

    for doc in (DRAFT, CAPSTONE, LOG, README10, FEEDBACK, PACKAGE / "README.md"):
        text = read(doc)
        for target in re.findall(r"\]\(([^)#]+?)\)", text):
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            resolved = (doc.parent / target).resolve()
            require(resolved.exists(), f"broken local link in {doc.name}: {target}")


# --------------------------------------------------------------------------
# 8. Structure, labels, disclosures (draft v2)
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

    require("Draft v2" in draft and "superseding" in draft,
            "v2 must declare itself and name the draft it supersedes")
    require("W09_Paper_Draft_v1.md" in draft, "v2 must link the superseded v1")

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
    require("3 of 14,400 judge outputs were unparsed (0.02%)" in draft,
            "judge-output missingness denominator is incorrect")
    require("affecting 3 of 4,800 generation rows (0.06%)" in draft,
            "affected-row missingness denominator is incorrect")
    require(not re.search(r"\b(?:3|Three) of 4,800 panel votes\b", draft),
            "mixed-unit panel-vote denominator remains")

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
    require("| C1 and mitigation judge-measurement stress analysis (this revision) " in prov,
            "provenance table missing the measurement-stress row")
    for artifact in (
        "../week-07/W07_Analysis.json", "../week-07/W07_Run_Metadata.json",
        "../week-05/W05_Results_Memo.md", "../week-06/W06_Analysis.json",
        "../week-08/W08_Pressure_Cue_Audit.md", "W10_Judge_Sensitivity.json",
    ):
        require(artifact in draft, f"meeting-feedback artifact reference missing: {artifact}")

    figures = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", draft)
    require(len(figures) == 3, f"expected 3 figures, found {len(figures)}")
    for fig in figures:
        svg = (W10 / fig).resolve()
        require(svg.exists(), f"figure missing on disk: {fig}")
        require(svg.with_suffix(".png").exists(), f"PNG fallback missing for: {fig}")


# --------------------------------------------------------------------------
# 9. Reproducibility package integrity
# --------------------------------------------------------------------------

def verify_package() -> None:
    manifest = json.loads(read(MANIFEST))
    require(manifest["schema_version"] == "w10-data-manifest-public-v1", "manifest schema changed")
    require(set(manifest["bundle"]) == {"name", "sha256", "size_bytes", "availability_note"},
            "public bundle manifest has unexpected delivery fields")
    require(manifest["bundle"]["name"] == "ingen-raw-evidence-v1.zip",
            "public bundle name changed")
    require(re.fullmatch(r"[0-9a-f]{64}", manifest["bundle"]["sha256"]) is not None,
            "public bundle SHA-256 is malformed")
    require(manifest["bundle"]["size_bytes"] == 1653594, "public bundle size changed")
    require("no download location" in manifest["bundle"]["availability_note"].lower(),
            "public bundle availability boundary missing")
    require(len(manifest["files"]) == 6, "manifest must list exactly six supplied files")
    present = [(ROOT / entry["path"]).exists() for entry in manifest["files"]]
    require(not any(present) or all(present), "raw-evidence restoration is partial")
    for entry in manifest["files"]:
        target = ROOT / entry["path"]
        if target.exists():
            require(target.is_file(), f"raw-evidence path is not a file: {entry['path']}")
            require(target.stat().st_size == entry["size_bytes"],
                    f"raw-evidence file size mismatch: {entry['path']}")
            require(sha256_file(target) == entry["sha256"],
                    f"raw-evidence file hash mismatch: {entry['path']}")
    manifest_hashes = {e["sha256"] for e in manifest["files"]}
    w6_meta = read(ROOT / "week-06" / "W06_Run_Metadata.json")
    w7_meta = read(W7_METADATA)
    pinned = sum(1 for h in manifest_hashes if h in w6_meta or h in w7_meta)
    require(pinned >= 3, f"expected >=3 manifest hashes pinned in run metadata, found {pinned}")
    require("unbundled_note" in manifest, "manifest must disclose the unreleased raw files")

    fetch_text = read(PACKAGE / "fetch_data.py")
    fetch_words = " ".join(fetch_text.split()).lower()
    for forbidden_delivery in ("subprocess", "download_bundle", "github", "network fallback"):
        if forbidden_delivery == "network fallback":
            require("no network fallback" in fetch_words, "fetch script must state no network fallback")
        else:
            require(forbidden_delivery not in fetch_text.lower(),
                    f"public fetch script retains forbidden delivery behavior: {forbidden_delivery}")
    require('add_mutually_exclusive_group(required=True)' in fetch_text,
            "public fetch script must require --check or --from-path")

    tracked = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-z"], capture_output=True, text=True, check=True
    ).stdout
    tracked = parse_git_ls_files_output(tracked)
    forbidden = forbidden_tracked_artifacts(tracked)
    require(
        not forbidden,
        "raw model outputs or experiment archives remain tracked: "
        + ", ".join(forbidden),
    )
    gitignore = read(ROOT / ".gitignore")
    for path in EXTERNALIZED:
        require(path not in tracked, f"externalized file still tracked: {path}")
        require(path in gitignore, f"externalized path missing from .gitignore: {path}")

    for req in ("requirements-analysis.txt", "requirements-inference.txt"):
        text = read(PACKAGE / req)
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            require(re.fullmatch(r"[A-Za-z0-9_.\-]+==[0-9][A-Za-z0-9_.+]*", line) is not None,
                    f"{req} line not exactly pinned: {line}")

    package_readme = read(PACKAGE / "README.md")
    package_readme_words = " ".join(package_readme.split()).lower()
    for script in CANONICAL_SCRIPTS:
        require(script in package_readme, f"package README missing script: {script}")
    require("week-06-explorations" in package_readme,
            "package README must state the explorations tree is out of scope")
    require("--from-path" in package_readme,
            "package README must document the out-of-band bundle path")
    require("restores the six" in package_readme_words and "raw-evidence files" in package_readme_words,
            "package README must use the six-file manifest count")
    require("restores the ten raw-evidence files" not in package_readme,
            "stale ten-file restore claim remains")
    require("exactly restores and deterministically regenerates the committed analysis record" in package_readme,
            "package README must bound its exact-reproduction guarantee")
    for phrase in (
        "fresh evidence run",
        "historical Weeks 3-6 estimates are not exact replay targets",
        "mock_only",
        "run-receipt.json",
    ):
        require(
            phrase.lower() in package_readme.lower(),
            f"package README missing fresh-run contract phrase: {phrase}",
        )
    require(
        "python week-10/W10_Reproducibility_Package/reproduce_fresh.py "
        "--mode full --accept-compute-cost" in package_readme,
        "package README missing exact full fresh-run command",
    )
    require("--bundle BUNDLE.zip" in package_readme,
            "package README must require the separately supplied full-run bundle")
    for phrase in (
        "verification_pending",
        "defaults to 8",
        "positive divisor of 480",
        "both Week 7 confirmation commands",
        "full-run-only",
        "mock mode is offline",
        "neither restores external raw evidence nor uses a bundle",
    ):
        require(
            phrase.lower() in package_readme_words,
            f"package README missing fresh-run operational detail: {phrase}",
        )
    for name in (
        "fetch_data.py",
        "regenerate_all.py",
        "reproduce_fresh.py",
        "verify_fresh_run.py",
        "model_lock.json",
        "prefetch_models.py",
    ):
        require((PACKAGE / name).exists(), f"package script missing: {name}")


# --------------------------------------------------------------------------
# 10. Capstone outline
# --------------------------------------------------------------------------

def verify_capstone() -> None:
    text = read(CAPSTONE)
    normalized = " ".join(text.split())
    headers = [
        "### (i) Executive summary",
        "### (ii) Physical-AI research landscape and InGen context",
        "### (iii) Literature review and research-gap justification",
        "### (iv) Benchmark design and methodology",
        "### (v) Baseline evaluation results",
        "### (vi) Empirical experiments (Phase B findings)",
        "### (vii) Cross-experiment synthesis and primary research contribution",
        "### (viii) PIC 2.0 analysis and application framework",
        "### (ix) Research paper contribution summary",
        "### (x) Limitations and future research directions",
        "### (xi) Conclusion",
    ]
    positions = [text.find(h) for h in headers]
    require(all(p >= 0 for p in positions),
            f"capstone outline missing sections: {[h for h, p in zip(headers, positions) if p < 0]}")
    require(positions == sorted(positions), "capstone outline sections out of order")

    for drafted in ("## Drafted section (ii)", "## Drafted section (iii)"):
        require(drafted in text, f"capstone missing drafted section: {drafted}")
    for marker, minimum in (("## Drafted section (ii)", 250), ("## Drafted section (iii)", 250)):
        section = text.split(marker, 1)[1].split("\n## ")[0] if marker in text else ""
        words = len(section.split())
        require(words >= minimum, f"{marker} has {words} words; expected >= {minimum}")
    require("This section is a literature analysis" in text,
            "capstone literature section must carry the separation statement")
    require("W08_Paper_Handoff.md" in text,
            "capstone must cite the paper-versus-capstone boundary source")
    require("literature-only" in text, "capstone must carry the literature-only label")
    require("one important constraint among several" in text,
            "capstone landscape opening remains overbroad")
    require("runtime-governance systems that intercept unauthorized actions in simulation" in normalized
            and "reports a false-rejection rate alongside unauthorized-action interception" in normalized,
            "capstone runtime-governance characterization remains inaccurate")


# --------------------------------------------------------------------------
# 11. Research log, READMEs, feedback, and test record
# --------------------------------------------------------------------------

def verify_log_readmes_test_record() -> None:
    text = read(LOG)
    require("hardest" in text.lower(), "log must include the hardest-section reflection")
    m = re.search(r"## Weekly summary.*?\n(.*?)\n## ", text, re.S)
    require(m is not None, "log missing weekly summary section")
    if m:
        words = len(m.group(1).split())
        require(300 <= words <= 500, f"weekly summary is {words} words; budget 300-500")
    require("## Deliverable conformance" in text, "log missing conformance section")
    require("## Verification record" in text, "log missing verification record")
    require("hashsalt" in text and "byte-identical" in text,
            "log must record the SVG stability fix closure")
    require("PASS: Week 10 verification complete" in text,
            "log must record the verifier acceptance line")
    require("clean" in text.lower() and "environment" in text.lower(),
            "log must record the clean-environment test")

    readme = read(README10)
    for name in (
        "W10_Paper_Draft_v2.md", "W10_Capstone_Outline.md", "Wk-10-ResearchLog.md",
        "W10_Feedback.md", "W10_Judge_Sensitivity.json",
        "analyze_w10_judge_sensitivity.py", "verify_w10.py",
        "W10_Reproducibility_Package", "reproduce_fresh.py", "model_lock.json",
        "prefetch_models.py", "verify_fresh_run.py",
    ):
        require(name in readme, f"week-10 README missing reference to {name}")
    for command in (
        "python week-10/W10_Reproducibility_Package/reproduce_fresh.py --mode plan",
        "python week-10/W10_Reproducibility_Package/reproduce_fresh.py --mode mock",
        "python week-10/W10_Reproducibility_Package/reproduce_fresh.py --mode full --accept-compute-cost",
    ):
        require(command in readme, f"week-10 README missing fresh-run command: {command}")
    require(
        "full Tier 2 GPU campaign has not been run" in readme,
        "week-10 README must not imply that the full fresh GPU campaign ran",
    )
    require("week-10" in read(ROOT_README), "root README does not mention week-10")

    feedback = read(FEEDBACK)
    for phrase in ("reproducibility", "auditability", "paper refinement", "capstone"):
        require(phrase in feedback, f"feedback note missing focus area '{phrase}'")
    require("Current Week 10 status: completed" in feedback,
            "feedback status is stale")

    require(TEST_RECORD.exists(), "clean-environment test record missing")
    if TEST_RECORD.exists():
        record = read(TEST_RECORD)
        normalized_record = " ".join(record.split())
        require("selected console output and contemporaneous summaries" in normalized_record,
                "clean-environment artifact still overstates record completeness")
        require("Nothing below is edited output" not in record,
                "stale verbatim-record claim remains")
        for marker in (
            "ALL CHECKS PASSED",
            "Ran 55 tests",
            "PASS: Week 8 verification complete",
            "PASS: Week 9 verification complete",
            "PASS: Week 10 verification complete",
            "raw-evidence files verified against the manifest",
        ):
            require(marker in record, f"test record missing marker: {marker}")


# --------------------------------------------------------------------------

def main() -> int:
    sections = [
        ("v2 tables against committed JSON", verify_tables),
        ("v2 abstract budget and contrasts", verify_abstract),
        ("Week 6 and Week 8 values", verify_week6_week8_values),
        ("Week 7 prose values and strata", verify_week7_prose_values),
        ("judge-measurement stress analysis", verify_sensitivity),
        ("FoMER engagement", verify_fomer),
        ("citations and links", verify_citations_and_links),
        ("v2 structure, labels, and disclosures", verify_structure),
        ("reproducibility package integrity", verify_package),
        ("capstone outline", verify_capstone),
        ("research log, READMEs, and test record", verify_log_readmes_test_record),
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
        print(f"\nFAIL: Week 10 verification found {len(failures)} problem(s)")
        return 1
    print("PASS: Week 10 verification complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
