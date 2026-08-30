from __future__ import annotations

import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
W10 = ROOT / "week-10"
W11 = ROOT / "week-11"
W12 = ROOT / "week-12"
FIGURES = W12 / "figures"

TITLE = (
    "Generator Choice Sets the Safety Operating Point: Unsafe Compliance and "
    "Over-Refusal in Language-Model Decisions for Service Robots"
)

DISCUSSION_INSERT_MARKER = "### 5.2 No blanket mitigation (from C2, descriptive)"
CHILD_FACTOR_SHORT_TITLE = "The Child Factor in Child-Robot Interaction"
CHILD_FACTOR_FULL_TITLE = (
    "The Child Factor in Child-Robot Interaction: Discovering the Impact of "
    "Developmental Stage and Individual Characteristics"
)

LANGUAGE_FIXES_SHARED = (
    (
        "Qwen2.5-7B-Instruct had lower failure rates than "
        "Mistral-7B-Instruct-v0.3 by 55.0 percentage points on "
        "plain-caution scenarios",
        "Qwen2.5-7B-Instruct's failure rates were 55.0 percentage points "
        "lower than Mistral-7B-Instruct-v0.3's on plain-caution scenarios",
    ),
    (
        "and 40.1 percentage points on pressured-caution scenarios",
        "and 40.1 percentage points lower on pressured-caution scenarios",
    ),
    (
        "or the lexical safety behavior that audit exposed",
        "or the lexical safety behavior that the audit exposed",
    ),
    (
        "reports unauthorized-action interception and false-rejection rate "
        "together",
        "reports unauthorized-action interception rate and false-rejection "
        "rate together",
    ),
    (
        "lexical success did not replace semantically judged action outcomes",
        "lexical success was not a reliable proxy for semantically judged "
        "action outcomes",
    ),
    (
        "the very salience factor the contrast meant to isolate",
        "the very salience factor the contrast was meant to isolate",
    ),
)

LANGUAGE_FIXES_MARKDOWN = (
    (
        "the plain contrast moves to -25.6 points without changing sign",
        "the plain contrast moves to -25.6 percentage points without "
        "changing sign",
    ),
    (
        "which come from the §3.3 judge panel",
        "which come from the judge panel described in §3.3",
    ),
    (
        "The §3.3 amendment reports",
        "The acceptance amendment of §3.3 reports",
    ),
    (
        "Two design questions separate the benchmarks, and they are why we "
        "built a new bank",
        "Two design questions separate the benchmarks, and they explain why "
        "we built a new bank",
    ),
    (
        "catalogue sensor fusion, real-time decision, and HRI challenges",
        "catalogue sensor fusion, real-time decision making, and HRI "
        "challenges",
    ),
    (
        "switch to a backup policy [12] — precisely the third action "
        "our benchmark does not yet score —",
        "switch to a backup policy [12] — deferral is precisely the "
        "action our benchmark does not yet score —",
    ),
    (
        "not independently human-annotated",
        "not independently human-labeled",
    ),
    (
        "a pre-registered ceiling analysis",
        "a preregistered ceiling analysis",
    ),
    (
        "Under the identical common prompt, the generators show different "
        "trade-offs",
        "Under the identical common prompt, the generators showed different "
        "trade-offs",
    ),
    (
        "All three contrasts exclude zero, and the effects are large by "
        "conventional standards",
        "All three contrasts excluded zero, and the effects were large by "
        "conventional standards",
    ),
    (
        "exact McNemar p < 1e−26",
        "exact McNemar p < 10⁻²⁶",
    ),
    (
        "the direction measured in the pilot study within Mistral under a "
        "different 32-scenario design",
        "the direction measured within Mistral in the pilot study under a "
        "different 32-scenario design",
    ),
    (
        "prompt/template, and judging stack together",
        "prompt/template, and judge stack together",
    ),
    (
        "Where pressure did break through, it was tactic-concentrated:",
        "Where pressure did break through, the failures concentrated in "
        "specific tactics:",
    ),
    (
        "its control over-refusals were platform-uniform (15/80 each)",
        "its control over-refusals were uniform across platforms "
        "(15/80 each)",
    ),
    (
        "seed-to-seed variability is small relative to the reported "
        "contrasts",
        "seed-to-seed variability was small relative to the reported "
        "contrasts",
    ),
    (
        "the tactics that actually broke through",
        "the tactics that broke through",
    ),
    (
        "One candidate explanation — plain items state the governing "
        "prerequisite more saliently —",
        "One candidate explanation — that plain items state the "
        "governing prerequisite more saliently —",
    ),
    (
        "none states it is missing",
        "none states that it is missing",
    ),
    (
        "a registered 2×2 salience-by-pressure factorial",
        "a registered two-by-two salience-by-pressure factorial",
    ),
)

LANGUAGE_FIXES_TEX = (
    (
        "the plain contrast moves to $-25.6$ points without changing sign",
        "the plain contrast moves to $-25.6$ percentage points without "
        "changing sign",
    ),
    (
        "labels assigned by the Section~\\ref{sec:adjudication} judge panel",
        "labels assigned by the judge panel described in "
        "Section~\\ref{sec:adjudication}",
    ),
    (
        "The Section~\\ref{sec:adjudication} amendment reports",
        "The acceptance amendment of Section~\\ref{sec:adjudication} "
        "reports",
    ),
    (
        "rather than improving both errors at once",
        "rather than reducing both error rates at once",
    ),
    (
        "whether any tested prompt intervention improves both errors under "
        "the registered mitigation rule",
        "whether any tested prompt intervention reduces both error rates "
        "under the registered mitigation rule",
    ),
    (
        "may open only during a recorded traction-power isolation and under "
        "the line controller's active work permit",
        "may open only under a recorded traction-power isolation and the "
        "line controller's active work permit",
    ),
    (
        "were smaller than the design can resolve",
        "were smaller than the design could resolve",
    ),
    (
        "Prompt adaptation therefore bought Mistral lower caution failure "
        "at a small refusal cost and moved Qwen favorably on plain caution, "
        "and the gap between the two adapted pipelines kept the direction "
        "of the registered contrast on every outcome.",
        "Prompt adaptation therefore lowered Mistral's caution failure at a "
        "small refusal cost and moved Qwen favorably on plain caution. The "
        "gap between the two adapted pipelines preserved the direction of "
        "the registered contrast on every outcome.",
    ),
)


ADAPTED_BASELINE_MARKDOWN = (
    "Model-adapted prompting moved each generator along the same trade-off rather "
    "than off it (Table T2a). Mistral's adapted baseline more than halved its "
    "pressured-caution failure relative to the common baseline, from 43.1% (69/160) "
    "to 18.8% (30/160) (−24.4pp, family-clustered 95% CI [−35.0, −13.1]), and "
    "reduced plain-caution failure from 88.8% (142/160) to 57.5% (92/160), while "
    "its authorized-control failure rose from 0.0% (0/160) to 6.2% (10/160). "
    "Qwen's adapted baseline moved all three point estimates in the favorable "
    "direction: plain-caution failure fell from 33.8% (54/160) to 20.6% (33/160) "
    "(−13.1pp, CI [−26.9, −1.9]), while the pressured change (3.2%, 5/157, to "
    "2.5%, 4/160; CI [−9.4, +8.3]) and the control change (18.8%, 30/160, to "
    "14.4%, 23/160; CI [−14.4, +3.1]) were smaller than the design could resolve. "
    "Prompt adaptation therefore lowered Mistral's caution failure at a small "
    "refusal cost and moved Qwen favorably on plain caution. The gap between "
    "the two adapted pipelines preserved the direction of the registered contrast on "
    "every outcome (adapted-baseline contrasts from W07_Analysis.json, "
    "`paired_contrasts.adaptation_effects`)."
)


FIGURE_INSERTS = {
    "### 4.2 Interventions and the registered mitigation rule (descriptive)": """
![Figure 1. Common-prompt operating points jointly expose unsafe compliance and authorized-control refusal.](figures/Figure1_Operating_Point.png)

*Figure 1. Common-prompt operating points. Lower values are better on both axes. Error bars are 95% family-clustered bootstrap intervals; the connected points show that generator choice changes the balance between the two errors rather than yielding a uniform ranking.*

""",
    "### 4.3 Plain caution fails more than pressured caution (exploratory)": """
![Figure 2. Prompt interventions move each generator through a different safety-versus-control-cost space.](figures/Figure2_Prompt_Tradeoffs.png)

*Figure 2. Prompt-intervention trade-offs relative to each generator's adapted baseline. The registered acceptance region requires at least 25% relative reduction in pressured failure and no more than 3.125 percentage points of added authorized-control failure.*

""",
    "### 4.5 Judge-measurement stress analysis (descriptive)": """
![Figure 3. The primary contrast directions survive conditional false-negative stress, but the observed mitigation pass does not.](figures/Figure3_Measurement_Stress.png)

*Figure 3. Conditional measurement-stress results. The analysis assigns additional missed failures to the arm that most weakens each claim and does not estimate false positives or a joint confidence region.*

""",
    DISCUSSION_INSERT_MARKER: """
### 5.2 From rates to setting-specific loss

The two-error representation becomes actionable only after a target setting assigns costs and state frequencies. Let *p*<sub>P</sub>, *p*<sub>A</sub>, and *p*<sub>C</sub> denote failure rates for plain caution, pressured caution, and authorized control. Let *w*<sub>P</sub>, *w*<sub>A</sub>, and *w*<sub>C</sub> denote the corresponding state frequencies, and let *c*<sub>U</sub> and *c*<sub>R</sub> denote the costs of unsafe compliance and authorized refusal. A simple expected loss is

*L* = *c*<sub>U</sub>(*w*<sub>P</sub>*p*<sub>P</sub> + *w*<sub>A</sub>*p*<sub>A</sub>) + *c*<sub>R</sub>*w*<sub>C</sub>*p*<sub>C</sub>,

where the weights sum to one. The benchmark estimates the three failure rates but does not estimate deployment frequencies or costs. For the common prompt, the point-estimate change from Mistral to Qwen is

Δ*L* = -0.550*c*<sub>U</sub>*w*<sub>P</sub> - 0.401*c*<sub>U</sub>*w*<sub>A</sub> + 0.188*c*<sub>R</sub>*w*<sub>C</sub>.

Qwen is preferred at the point estimates when the avoided unsafe-compliance cost exceeds the added refusal cost; Mistral is preferred when authorized refusal is sufficiently frequent or costly. This equation makes explicit why the experiment does not identify a context-free model ranking.

**Table T3 — illustrative point-estimate break-even cost ratios** (equal aggregate exposure to caution and authorized-control states):

| Plain share among caution states | Caution improvement | Break-even *c*<sub>U</sub> / *c*<sub>R</sub> |
| --- | --- | --- |
| 1.00 | 0.550 | 0.342 |
| 0.75 | 0.513 | 0.367 |
| 0.50 | 0.476 | 0.395 |
| 0.25 | 0.438 | 0.429 |
| 0.00 | 0.401 | 0.469 |

Within caution states, the plain-share parameter controls how much of the observed improvement comes from the larger plain-caution contrast. Qwen has lower point-estimate loss above each listed ratio and Mistral below it. These values are illustrative, not deployment recommendations: changing the authorized-control frequency rescales the threshold, and the calculation does not propagate the joint family-bootstrap distribution.

![Figure 4. Expected loss changes with deployment prevalence and the relative cost assigned to unsafe compliance and over-refusal.](figures/Figure4_Expected_Loss.png)

*Figure 4. Decision-theoretic interpretation of the common-prompt operating points. No single generator minimizes expected loss for every prevalence and cost ratio, so model selection requires an explicit deployment loss model.*

All three primary intervals exclude zero, but a confidence interval for the break-even ratio requires the joint bootstrap distribution of all three contrasts and the target weights. Dividing marginal interval endpoints would ignore dependence and could produce misleading thresholds. A deployment-oriented extension should evaluate the loss within every family-bootstrap draw and report the probability that each pipeline has lower loss over a declared grid of costs and state frequencies.

The conditional measurement stress replaces the observed contrasts with -0.256, -0.350, and +0.181. Under equal aggregate caution and control exposure, the stressed point-estimate break-even ratios range from 0.517 for an all-pressured caution mix to 0.707 for an all-plain mix. The region favoring Qwen narrows but does not disappear. These ratios inherit the false-negative-only assumptions and unestimated false-positive boundary of the stress analysis.

The registered mitigation rule uses a constraint rather than a scalar loss: an intervention must achieve a minimum pressured reduction while respecting a maximum refusal increase. That form is suitable when a system has a hard refusal budget. It also prevents a large relative change on a small baseline from automatically compensating for control harm. The Qwen deliberation arm passes the observed constraint and fails the stressed constraint, a more informative disposition than reporting its 100% relative reduction alone.

### 5.3 No blanket mitigation (from C2, descriptive)

""",
}


def strip_internal_markdown_links(text: str) -> str:
    text = re.sub(
        r"!\[[^]]*\]\((?:\.\./week-|W10_)[^)]+\)\s*\n\s*\*Figure[^\n]*\*\s*",
        "",
        text,
    )
    text = re.sub(
        r"\[([^]]+)\]\((?:\.\./week-|W10_)[^)]+\)",
        lambda match: match.group(1).replace("`", ""),
        text,
    )
    return re.sub(
        r"\[([^]]+)\]\((?!https?://|figures/|#)[^)]+\)",
        lambda match: match.group(1).replace("`", ""),
        text,
    )


def normalize_markdown_citations(body: str, references: str) -> tuple[str, str]:
    entries = []
    key_to_number: dict[str, int] = {}
    for line in references.splitlines():
        match = re.match(r"- \[@([^]]+)\]\s+(.+)", line)
        if not match:
            continue
        key, citation = match.groups()
        key_to_number[key] = len(entries) + 1
        entries.append(f"[{len(entries) + 1}] {citation}")

    def replace_citation(match: re.Match[str]) -> str:
        keys = re.findall(r"@([A-Za-z0-9_:-]+)", match.group(0))
        numbers = [str(key_to_number[key]) for key in keys if key in key_to_number]
        return "[" + ", ".join(numbers) + "]" if numbers else match.group(0)

    body = re.sub(r"\[@[^]]+\]", replace_citation, body)
    return body, "\n".join(entries)


def build_markdown() -> None:
    source = (W10 / "W10_Paper_Draft_v2.md").read_text(encoding="utf-8")
    abstract_at = source.index("## Abstract")
    evidence_at = source.index("## Evidence provenance")
    references_at = source.index("## References")
    body = source[abstract_at:evidence_at].strip()
    references = source[references_at + len("## References") :]
    references = references.split("\n---", 1)[0].strip()

    body = strip_internal_markdown_links(body)
    body, references = normalize_markdown_citations(body, references)
    body = body.replace("## 2 Related work", "## 2 Related Work")
    body = body.replace(
        "## 6 Limitations and future work", "## 6 Limitations and Future Work"
    )
    phase_replacements = {
        "from the Week 2 review": "from the preliminary literature review",
        "Our Week 5 audit": "Our earlier lexical-rubric audit",
        "relative to Week 6": "relative to the pilot study",
        "measured in Week 6": "measured in the pilot study",
        "the Week 7 acceptance record": "the panel-acceptance record",
        "Because Weeks 6 and 7 changed": (
            "Because the pilot and confirmation studies changed"
        ),
        "In Week 5": "In the initial study",
        "Week 6 moved to": "The pilot study moved to",
        "and Week 7 added": "and the confirmation study added",
        "Weeks 5–7 changed banks, templates, and judges": (
            "The initial, pilot, and confirmation studies changed banks, templates, and judges"
        ),
    }
    for old, new in phase_replacements.items():
        body = body.replace(old, new)
    remaining_phase = re.search(r"\bWeeks?\s+[0-9]+(?:[–-][0-9]+)?\b", body)
    if remaining_phase:
        raise ValueError(f"unmapped study-phase label: {remaining_phase.group(0)}")
    body = body.replace(
        "What this paper does that the cited work does not",
        "What this paper adds",
    )
    body = body.replace(
        "**Table T2b — registered primary contrasts:**",
        "**Table T2b — registered primary contrasts** (generated from "
        "W07_Analysis.json, `paired_contrasts.primary_common_baseline`):",
    )
    body = body.replace(
        "**Table T2c — registered mitigation-rule disposition** "
        "(vs. within-generator adapted baseline):",
        "**Table T2c — registered mitigation-rule disposition** "
        "(vs. within-generator adapted baseline; generated from "
        "W07_Analysis.json, `mitigation_rule`):",
    )
    body = body.replace(
        "but 19 points worse on authorized-action refusal.",
        "but 19 points worse on authorized-action refusal.\n\n"
        + ADAPTED_BASELINE_MARKDOWN,
    )
    body = re.sub(
        r"\*\*Future work \(proposed\)\.\*\*.*?The reproducibility package.*?\n",
        "**Future work (proposed).** The highest-value extension combines a third generator family, a registered two-by-two salience-by-pressure factorial with tactic and setting counterbalanced within family, blinded human validation of the weakest judge stratum, matched authorized controls, and calibrated deferral as a scored third action.\n",
        body,
        flags=re.DOTALL,
    )
    body = body.replace(
        "Every reported rate is an LLM-judge measurement, not human-annotated ground truth:",
        "Every reported rate is an LLM-judge measurement rather than an independently human-labeled endpoint:",
    )
    body = body.replace("40.1 points", "40.1 percentage points")
    body = body.replace("18.8 points higher", "18.8 percentage points higher")
    body = body.replace("−25.6", "-25.6")
    body = body.replace(
        "Gold labels are AI-assisted and human-verified, not independently human-annotated.",
        "Calibration labels were AI-assisted and human-verified rather than independently human-labeled.",
    )
    body = body.replace("cross-week", "cross-study")
    references = references.replace(CHILD_FACTOR_SHORT_TITLE, CHILD_FACTOR_FULL_TITLE)
    for old, new in LANGUAGE_FIXES_SHARED + LANGUAGE_FIXES_MARKDOWN:
        body = body.replace(old, new)
    for marker, insert in FIGURE_INSERTS.items():
        replacement = insert if marker == DISCUSSION_INSERT_MARKER else insert + marker
        body = body.replace(marker, replacement)
    body = body.replace(
        "### 5.3 The endpoint determines the conclusion",
        "### 5.4 The endpoint determines the conclusion",
    )
    body = body.replace(
        "### 5.4 Implications for platform evaluation",
        "### 5.5 Implications for platform evaluation",
    )
    body = body.replace(
        "### 5.5 The pressure-direction reversal, explored and bounded",
        "### 5.6 The pressure-direction reversal, explored and bounded",
    )
    body = body.replace(
        "a stable model property (§5.5, §6)", "a stable model property (§5.6, §6)"
    )
    body = body.replace(
        "pair variant, and setting (§5.5)", "pair variant, and setting (§5.6)"
    )
    body = body.replace(
        "conclusion is available (§5.5)", "conclusion is available (§5.6)"
    )
    body = body.replace("## 7 Conclusion", REPRODUCIBILITY_MARKDOWN + "## 7 Conclusion")

    paper = (
        f"# {TITLE}\n\n"
        "**Ziyue Li · InGen Dynamics**\n\n"
        f"{body}\n\n"
        "## References\n\n"
        f"{references}\n"
    )
    paper = paper.replace("−", "-")
    paper = re.sub(r"\n{3,}", "\n\n", paper)
    (W12 / "W12_Final_Paper.md").write_text(paper, encoding="utf-8", newline="\n")


def replace_tex_figures(tex: str) -> str:
    paths = (
        "../week-07/figures/W07_Figure1_Common_Baseline_Cross_Model.png",
        "../week-09/figures/W09_Figure2_Prompt_Safety_and_Control_Cost.png",
        "../week-09/figures/W09_Figure3_Seed_Variability_and_Judge_Agreement.png",
    )
    replacements = (
        "figures/Figure1_Operating_Point.pdf",
        "figures/Figure2_Prompt_Tradeoffs.pdf",
        "figures/Figure3_Measurement_Stress.pdf",
    )
    for old, new in zip(paths, replacements, strict=True):
        tex = tex.replace(old, new)
    return tex


DECISION_THEORY_TEX = r"""
\subsection{From Rates to Setting-Specific Loss}

The two-error representation becomes actionable only after a target setting assigns costs and state frequencies. Let $p_P$, $p_A$, and $p_C$ denote failure rates for plain caution, pressured caution, and authorized control. Let $w_P$, $w_A$, and $w_C$ denote the corresponding state frequencies, and let $c_U$ and $c_R$ denote the costs of unsafe compliance and authorized refusal. A simple expected loss is
\begin{equation}
\mathcal{L}=c_U(w_Pp_P+w_Ap_A)+c_Rw_Cp_C,
\label{eq:loss}
\end{equation}
where the weights sum to one. The benchmark estimates the three failure rates but does not estimate deployment frequencies or costs. For the common prompt, the point-estimate change from Mistral to Qwen is
\begin{equation}
\Delta\mathcal{L}=-0.550c_Uw_P-0.401c_Uw_A+0.188c_Rw_C.
\label{eq:delta}
\end{equation}
Qwen is preferred at the point estimates when the avoided unsafe-compliance cost exceeds the added refusal cost; Mistral is preferred when authorized refusal is sufficiently frequent or costly. Equation~(\ref{eq:delta}) makes explicit why the experiment does not identify a context-free model ranking.

\begin{table}[!t]
\centering
\caption{Illustrative Point-Estimate Break-Even Cost Ratios}
\label{tab:breakeven}
\footnotesize
\begin{tabular}{@{}ccc@{}}
\toprule
\textbf{Plain share} & \textbf{Caution improvement} & \textbf{Break-even $c_U/c_R$} \\
\midrule
1.00 & 0.550 & 0.342 \\
0.75 & 0.513 & 0.367 \\
0.50 & 0.476 & 0.395 \\
0.25 & 0.438 & 0.429 \\
0.00 & 0.401 & 0.469 \\
\bottomrule
\end{tabular}
\end{table}

Within caution states, the plain-share parameter controls how much of the observed improvement comes from the larger plain-caution contrast. Qwen has lower point-estimate loss above each listed ratio and Mistral below it. These values are illustrative rather than deployment recommendations: changing the authorized-control frequency rescales the threshold, and the calculation does not propagate the joint family-bootstrap distribution.

\begin{figure*}[!t]
\centering
\includegraphics[width=0.96\textwidth]{figures/Figure4_Expected_Loss.pdf}
\caption{Expected loss across deployment assumptions for the two common-prompt operating points. The preferred generator changes with the prevalence of caution cases and the relative cost of unsafe compliance versus over-refusal; the figure therefore supports operating-point selection rather than a context-free ranking.}
\label{fig:expected-loss}
\end{figure*}

All three primary intervals exclude zero, but a confidence interval for the break-even ratio requires the joint bootstrap distribution of all three contrasts and the target weights. Dividing marginal interval endpoints would ignore dependence and could produce misleading thresholds. A deployment-oriented extension should evaluate Eq.~(\ref{eq:delta}) within every family-bootstrap draw and report the probability that each pipeline has lower loss over a declared grid of costs and state frequencies.

The conditional measurement stress replaces the observed contrasts with $-0.256$, $-0.350$, and $+0.181$. Under equal aggregate caution and control exposure, the stressed point-estimate break-even ratios range from 0.517 for an all-pressured caution mix to 0.707 for an all-plain mix. The region favoring Qwen narrows but does not disappear. These ratios inherit the false-negative-only assumptions and unestimated false-positive boundary of the stress analysis.

The registered mitigation rule uses a constraint rather than a scalar loss: an intervention must achieve a minimum pressured reduction while respecting a maximum refusal increase. That form is suitable when a system has a hard refusal budget. It also prevents a large relative change on a small baseline from automatically compensating for control harm. The Qwen deliberation arm passes the observed constraint and fails the stressed constraint, a more informative disposition than reporting its 100\% relative reduction alone.

"""


REPRODUCIBILITY_MARKDOWN = """
### 6.1 Reproducibility and auditability

The evidence package separates three questions that are often conflated: whether the published rates can be recomputed from recorded outcomes, whether the generation and judging pipelines can be reconstructed, and whether the judge labels are valid measurements of the requested operation. The first question is addressed by a deterministic analysis layer. It consumes the row-level generation outcomes and judge ratings, recomputes panel-majority decisions, applies the registered exclusions, rebuilds all counts and family-clustered intervals, and compares the result with the frozen analysis record. The same layer regenerates the tables, the four publication figures, the pressure-cue audit, and the conditional measurement-stress calculations. Independent verification separately derives the primary counts and contrasts rather than trusting the report tables.

The second question is addressed through pinned pipeline provenance. The record fixes generator and judge model revisions, prompt bytes, native chat-template use, decoding parameters, seeds, quantization settings, scenario-bank and output hashes, parsing rules, and the bootstrap seed. The byte-identical common prompt is stored independently of model-specific rendering so the registered generator contrast can be distinguished from adapted-prompt comparisons. Raw responses and judge outputs are retained as immutable evidence; generated summaries are rebuildable products rather than authorities. A hash-verifying fetch step allows large raw artifacts to be restored without silently substituting a different snapshot. These controls make accidental drift detectable, but they do not imply bit-for-bit regeneration of model text on every accelerator or software stack.

The third question remains the limiting one. Recomputing the panel's decisions perfectly cannot establish that the panel measured the operational endpoint without error. The calibration and holdout records therefore accompany the outcome table, and the weakest validated strata are carried into the conditional stress analysis. The distinction matters: the primary generator-contrast directions remain stable under the specified false-negative stress, whereas the only observed mitigation pass does not. Judge agreement, deterministic scripts, and matching hashes are evidence of consistency and provenance; none substitutes for blinded human adjudication or an estimate of false positives.

Reproduction can consequently be performed at two levels. An analysis-only run starts from the retained generation and rating records and regenerates every derived quantitative claim without loading the five language models. A full pipeline run additionally recreates generation and judging under the pinned configurations, subject to model availability and hardware-level reproducibility limits. The analysis-only level is the appropriate minimum for checking this paper because it directly tests arithmetic, exclusions, pairing, uncertainty, and claim-to-figure consistency. The full level tests operational reconstructability but is substantially more expensive and can reveal infrastructure drift that does not alter the already recorded experiment.

Several explicit boundaries prevent overinterpretation. The scenario bank is synthetic and has no claim to deployment prevalence. The two generators are specified pipelines, not representatives of every model in their families. The native chat templates remain part of those pipelines even under identical instruction bytes. The family bootstrap quantifies variation across 16 designed families, not across all possible service-robot tasks. The conditional stress model changes false negatives only and does not create a joint uncertainty distribution. Finally, none of the retained artifacts contains sensor streams, actuator behavior, operator outcomes, or field incidents. The reproducibility materials support the numerical claims made here; they do not turn the benchmark into deployment validation.

This layered evidence design is useful beyond the present study. A future three-generator, human-adjudicated experiment can retain the same separation between immutable evidence, deterministic derivation, and measurement validation while adding a held-out scenario set and a scored deferral outcome. Doing so would permit direct comparison with the current operating points without treating changes in models, judges, or scenario distributions as if they were replications of the same estimand.

"""


REPRODUCIBILITY_TEX = r"""
\subsection{Reproducibility and Auditability}

The evidence package separates three questions that are often conflated: whether the published rates can be recomputed from recorded outcomes, whether the generation and judging pipelines can be reconstructed, and whether the judge labels are valid measurements of the requested operation. The first question is addressed by a deterministic analysis layer. It consumes the row-level generation outcomes and judge ratings, recomputes panel-majority decisions, applies the registered exclusions, rebuilds all counts and family-clustered intervals, and compares the result with the frozen analysis record. The same layer regenerates the tables, the four publication figures, the pressure-cue audit, and the conditional measurement-stress calculations. Independent verification separately derives the primary counts and contrasts rather than trusting the report tables.

The second question is addressed through pinned pipeline provenance. The record fixes generator and judge model revisions, prompt bytes, native chat-template use, decoding parameters, seeds, quantization settings, scenario-bank and output hashes, parsing rules, and the bootstrap seed. The byte-identical common prompt is stored independently of model-specific rendering so the registered generator contrast can be distinguished from adapted-prompt comparisons. Raw responses and judge outputs are retained as immutable evidence; generated summaries are rebuildable products rather than authorities. A hash-verifying fetch step allows large raw artifacts to be restored without silently substituting a different snapshot. These controls make accidental drift detectable, but they do not imply bit-for-bit regeneration of model text on every accelerator or software stack.

The third question remains the limiting one. Recomputing the panel's decisions perfectly cannot establish that the panel measured the operational endpoint without error. The calibration and holdout records therefore accompany the outcome table, and the weakest validated strata are carried into the conditional stress analysis. The distinction matters: the primary generator-contrast directions remain stable under the specified false-negative stress, whereas the only observed mitigation pass does not. Judge agreement, deterministic scripts, and matching hashes are evidence of consistency and provenance; none substitutes for blinded human adjudication or an estimate of false positives.

Reproduction can consequently be performed at two levels. An analysis-only run starts from the retained generation and rating records and regenerates every derived quantitative claim without loading the five language models. A full pipeline run additionally recreates generation and judging under the pinned configurations, subject to model availability and hardware-level reproducibility limits. The analysis-only level is the appropriate minimum for checking this paper because it directly tests arithmetic, exclusions, pairing, uncertainty, and claim-to-figure consistency. The full level tests operational reconstructability but is substantially more expensive and can reveal infrastructure drift that does not alter the already recorded experiment.

Several explicit boundaries prevent overinterpretation. The scenario bank is synthetic and has no claim to deployment prevalence. The two generators are specified pipelines rather than representatives of every model in their families. Native chat templates remain part of those pipelines even under identical instruction bytes. The family bootstrap quantifies variation across 16 designed families, not across all possible service-robot tasks. The conditional stress model changes false negatives only and does not create a joint uncertainty distribution. Finally, none of the retained artifacts contains sensor streams, actuator behavior, operator outcomes, or field incidents. The reproducibility materials support the numerical claims made here; they do not turn the benchmark into deployment validation.

This layered evidence design is useful beyond the present study. A future three-generator, human-adjudicated experiment can retain the same separation between immutable evidence, deterministic derivation, and measurement validation while adding a held-out scenario set and a scored deferral outcome. Doing so would permit direct comparison with the current operating points without treating changes in models, judges, or scenario distributions as replications of the same estimand.

"""


def build_latex() -> None:
    tex = (W10 / "W10_Paper_Draft_v2_IEEE.tex").read_text(encoding="utf-8")
    tex = re.sub(r"pdftitle=\{[^\n]+\}", f"pdftitle={{{TITLE}}}", tex)
    tex = re.sub(r"\\title\{.*?\}\s*\n\n\\author", f"\\\\title{{{TITLE}}}\n\n\\\\author", tex, flags=re.DOTALL)
    tex = replace_tex_figures(tex)
    tex = tex.replace(
        "\\caption{Common-baseline failure rates by generator and scenario type. Failure denotes immediate execution in caution scenarios and refusal in authorized-control scenarios. Bars contain 160 scenario--seed rows per cell, except Qwen pressured caution ($n=157$ after three unparsed panel endpoints). Error bars are family-clustered 95\\% bootstrap confidence intervals; lower is better.}",
        "\\caption{Common-prompt Qwen-minus-Mistral failure-rate contrasts. Negative caution values favor Qwen; positive authorized-control values favor Mistral. Error bars are family-clustered 95\\% bootstrap confidence intervals.}",
    )
    tex = tex.replace(
        "\\caption{Measurement stability. (a) Per-seed pressured-failure rates by generator and prompt condition. (b) Exact judge-agreement rates for the operational endpoint; the vertical axis starts at 0.90. The panel was accepted under the disclosed amendment of Section~\\ref{sec:adjudication}; agreement is not evidence of accuracy on the weakest stratum.}",
        "\\caption{Observed and conditionally stressed common-prompt contrasts. The stress model lowers sensitivity in the weakest validated strata. All three directions survive, but the model does not estimate false positives or a joint uncertainty region.}",
    )
    tex = tex.replace(
        "\\subsection{No Blanket Mitigation}",
        DECISION_THEORY_TEX + "\\subsection{No Blanket Mitigation}",
    )
    tex = re.sub(
        r"\\section\*\{Evidence Provenance\}.*?(?=\\begin\{thebibliography\})",
        "",
        tex,
        flags=re.DOTALL,
    )
    tex = re.sub(
        r"\\par\\smallskip\s*\\noindent\\textbf\{AI-assistance disclosure\.\}.*?(?=\\end\{document\})",
        "",
        tex,
        flags=re.DOTALL,
    )
    phase_replacements = {
        "Our Week 5 audit": "Our earlier lexical-rubric audit",
        "In Week 5": "In the initial study",
        "Week 6 moved to": "The pilot study moved to",
        "and Week 7 added": "and the confirmation study added",
        "Weeks 5--7 changed banks, templates, and judges": (
            "The initial, pilot, and confirmation studies changed banks, templates, and judges"
        ),
    }
    for old, new in phase_replacements.items():
        tex = tex.replace(old, new)
    remaining_phase = re.search(r"\bWeeks?\s+[0-9]+(?:--[0-9]+)?\b", tex)
    if remaining_phase:
        raise ValueError(f"unmapped study-phase label: {remaining_phase.group(0)}")
    tex = tex.replace(
        "human-annotated ground truth",
        "an independently human-labeled endpoint",
    )
    tex = tex.replace("40.1 points", "40.1 percentage points")
    tex = tex.replace("18.8 points higher", "18.8 percentage points higher")
    tex = tex.replace("not independently human-annotated", "not independently human-labeled")
    tex = tex.replace(
        "\\subsection{What This Paper Does That the Cited Work Does Not}",
        "\\subsection{What This Paper Adds}",
    )
    tex = tex.replace("cross-week", "cross-study")
    tex = tex.replace(
        "To our knowledge, no public study combines",
        "To our knowledge from the preliminary literature review, "
        "no public study combines",
    )
    tex = tex.replace(
        "failed 48.8\\% of common-baseline rows, 39/80",
        "failed 48.8\\% of plain care-boundary rows at the common baseline, 39/80",
    )
    tex = tex.replace(
        "Two generators cannot support a universal method ranking. These results "
        "show only that the tested deliberation and gating prompts did not "
        "transfer uniformly between the two tested generator stacks. Any broader "
        "claim should be tested separately on each generator while measuring both "
        "error types.",
        "The tested deliberation and gating prompts therefore did not transfer "
        "uniformly between the two tested generator stacks.",
    )
    tex = tex.replace(
        "These are proposed research and evaluation priorities for decision "
        "pipelines, not deployment approvals; no deployed robot, sensor stack, "
        "or proprietary module was tested. Future platform evaluation",
        "Future platform evaluation",
    )
    tex = tex.replace(
        "the combined measurement stress reported in "
        "\\path{W10_Judge_Sensitivity.json}",
        "the combined measurement stress reported in the archived "
        "sensitivity record",
    )
    tex = tex.replace(
        "The calculation and machine-readable result are in "
        "\\path{analyze_w10_judge_sensitivity.py} and "
        "\\path{W10_Judge_Sensitivity.json}.",
        "The calculation and its machine-readable result are retained in the "
        "archived sensitivity analysis.",
    )
    tex = tex.replace(
        "row-listed in \\path{W07_Analysis.json} and",
        "row-listed in the archived analysis record and",
    )
    for old, new in LANGUAGE_FIXES_SHARED + LANGUAGE_FIXES_TEX:
        tex = tex.replace(old, new)
    tex = re.sub(
        r"\\textbf\{(?:External validity|Measurement|Missingness|"
        r"Resolution and robustness|Cross-experiment comparability|"
        r"Exploratory cue analysis)\.\}\s*",
        "",
        tex,
    )
    tex = tex.replace(
        "Gold labels are AI-assisted and human-verified, not independently human-annotated.",
        "Calibration labels were AI-assisted and human-verified rather than independently human-labeled.",
    )
    tex = tex.replace(
        "The child factor in child-robot interaction",
        CHILD_FACTOR_FULL_TITLE,
    )
    tex = re.sub(
        r"\\textbf\{Future work \(proposed\)\.\}.*?\\section\{Conclusion\}",
        lambda _: (
            "The highest-value extension of this study combines a third generator family, a registered two-by-two salience-by-pressure factorial with tactic and setting counterbalanced within family, blinded human validation of the weakest judge stratum, matched authorized controls, and calibrated deferral as a scored third action.\n"
            + REPRODUCIBILITY_TEX
            + "\\section{Conclusion}"
        ),
        tex,
        flags=re.DOTALL,
    )
    tex = re.sub(r"\n{3,}", "\n\n", tex)
    (W12 / "W12_Final_Paper.tex").write_text(tex, encoding="utf-8", newline="\n")


def copy_figures() -> None:
    FIGURES.mkdir(exist_ok=True)
    for number, stem in enumerate(
        (
            "Figure1_Operating_Point",
            "Figure2_Prompt_Tradeoffs",
            "Figure3_Measurement_Stress",
            "Figure4_Expected_Loss",
        ),
        start=1,
    ):
        del number
        for suffix in (".pdf", ".png", ".json"):
            shutil.copy2(
                W11 / "figures" / f"W11_{stem}{suffix}",
                FIGURES / f"{stem}{suffix}",
            )


def main() -> None:
    copy_figures()
    build_markdown()
    build_latex()
    print("built Week 12 paper sources and copied four publication figures")


if __name__ == "__main__":
    main()
