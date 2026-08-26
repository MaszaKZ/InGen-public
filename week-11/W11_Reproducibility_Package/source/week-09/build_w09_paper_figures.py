"""Publication variants of Figures 2 and 3 for the Week 9 IEEE manuscript.

Reads only committed Week 7 analysis outputs (no recomputation): every plotted
value comes from week-07/W07_Analysis.json. The Week 7 figure script and its
figures are left untouched; these variants add (a)/(b) panel labels, move the
outcome palette off the model colors, zoom the judge-agreement axis, and use
print-scale fonts.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

WEEK9 = Path(__file__).resolve().parent
ANALYSIS = WEEK9.parent / "week-07" / "W07_Analysis.json"
FIGURES = WEEK9 / "figures"

MODELS = ("mistralai/Mistral-7B-Instruct-v0.3", "Qwen/Qwen2.5-7B-Instruct")
MODEL_LABEL = {MODELS[0]: "Mistral 7B", MODELS[1]: "Qwen 2.5 7B"}
CONDITIONS = ("common_baseline", "adapted_baseline", "deliberation", "structured_output", "constraint_gated")
COND_LABEL = {
    "common_baseline": "Common", "adapted_baseline": "Adapted", "deliberation": "Deliberation",
    "structured_output": "Structured", "constraint_gated": "Constraint gating",
}
# Blue/orange stay reserved for the models (Figures 1 and 3a); the outcome
# palette uses hues that appear in no other figure.
COLORS = {"Mistral 7B": "#4778A8", "Qwen 2.5 7B": "#D07A35", "safety": "#2A9D8F", "control": "#7B5EA7"}
JUDGE_PAIRS = ("falcon3_10b|granite8b", "falcon3_10b|phi4_14b", "granite8b|phi4_14b")


def annotate(ax, x: float, y: float, text: str, cap: float, fontsize: int = 10) -> None:
    ax.text(x, min(cap, y), text, ha="center", va="bottom", fontsize=fontsize, color="#222222")


def save(fig, name: str) -> None:
    FIGURES.mkdir(exist_ok=True)
    fig.savefig(FIGURES / f"{name}.png", dpi=200, bbox_inches="tight", facecolor="white")
    fig.savefig(FIGURES / f"{name}.svg", bbox_inches="tight", facecolor="white", metadata={"Date": None})
    plt.close(fig)


def main() -> None:
    analysis = json.loads(ANALYSIS.read_text(encoding="utf-8"))
    rate_lookup = {(r["model"], r["condition"], r["subtype"]): r for r in analysis["rates"]}
    seed_rates: dict[tuple[str, str], list[float]] = {}
    for row in analysis["seed_stability"]:
        if row["subtype"] == "pressured":
            seed_rates.setdefault((row["generator_model"], row["condition"]), []).append(row["majority_failure"])
    for model in MODELS:
        for condition in CONDITIONS:
            if len(seed_rates[(model, condition)]) != 5:
                raise AssertionError(f"expected 5 seed rates for {model}/{condition}")

    plt.rcParams.update({"font.size": 12, "svg.hashsalt": "w09", "axes.spines.top": False, "axes.spines.right": False})

    # Figure 2: intervention safety and control cost, split by generator.
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), sharey=True)
    for panel, (ax, model) in zip("ab", zip(axes, MODELS)):
        x = np.arange(len(CONDITIONS))
        width = .34
        for offset, subtype, color, label in ((-width/2, "pressured", COLORS["safety"], "Pressured failure"),
                                              (width/2, "control", COLORS["control"], "Control refusal")):
            blocks = [rate_lookup[(model, condition, subtype)] for condition in CONDITIONS]
            vals = [b["estimate"] for b in blocks]
            errs = [[v - b["ci_low"] for v, b in zip(vals, blocks)], [b["ci_high"] - v for v, b in zip(vals, blocks)]]
            ax.bar(x + offset, vals, width, color=color, label=label, zorder=2)
            ax.errorbar(x + offset, vals, yerr=errs, fmt="none", ecolor="#5F6368", capsize=3, lw=1.1, zorder=3)
            for xx, v, b in zip(x + offset, vals, blocks):
                annotate(ax, xx, max(v, b["ci_high"]) + 0.035, f"{v:.0%}", cap=1.10)
        ax.set(xticks=x, xticklabels=[COND_LABEL[c] for c in CONDITIONS], ylim=(0, 1.15),
               title=f"({panel}) {MODEL_LABEL[model]}")
        ax.tick_params(axis="x", rotation=24)
        ax.grid(axis="y", color="#E5E7EB", linewidth=.8, zorder=0)
    axes[0].set_ylabel("Panel-majority failure rate")
    axes[0].legend(frameon=False, loc="upper left")
    fig.suptitle("Prompt-condition safety and authorized-control cost", y=1.01, fontsize=15)
    fig.tight_layout()
    save(fig, "W09_Figure2_Prompt_Safety_and_Control_Cost")

    # Figure 3: seed variability (a) and judge agreement on a zoomed axis (b).
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    x = np.arange(len(CONDITIONS))
    for offset, model in zip((-.1, .1), MODELS):
        label = MODEL_LABEL[model]
        per_seed = [seed_rates[(model, condition)] for condition in CONDITIONS]
        for xi, vals in enumerate(per_seed):
            axes[0].scatter(np.repeat(xi + offset, len(vals)), vals, color=COLORS[label], s=22, alpha=.55, zorder=2)
        means = np.array([np.mean(v) for v in per_seed])
        lows = means - np.array([np.min(v) for v in per_seed])
        highs = np.array([np.max(v) for v in per_seed]) - means
        axes[0].errorbar(x + offset, means, yerr=[lows, highs], fmt="o-", color=COLORS[label],
                         ecolor="#5F6368", capsize=4, label=label, zorder=3)
        for xx, mean, vals in zip(x + offset, means, per_seed):
            annotate(axes[0], xx, max(mean, np.max(vals)) + 0.035, f"{mean:.0%}", cap=1.10)
    axes[0].set(xticks=x, xticklabels=[COND_LABEL[c] for c in CONDITIONS], ylim=(0, 1.15),
                ylabel="Pressured failure rate", title="(a) Five-seed variability")
    axes[0].tick_params(axis="x", rotation=24)
    axes[0].grid(axis="y", color="#E5E7EB")
    axes[0].legend(frameon=False)

    agreement = analysis["judge_agreement"]
    labels = [f"{a}\nvs {b}" for a, b in (p.split("|") for p in JUDGE_PAIRS)] + ["All three\nunanimous"]
    vals = [agreement["pair_exact_agreement"][p] for p in JUDGE_PAIRS] + [agreement["unanimous_action"]]
    bars = axes[1].bar(np.arange(len(vals)), vals, color="#6F7D8C", width=.62, zorder=2)
    for bar, value in zip(bars, vals):
        axes[1].text(bar.get_x() + bar.get_width()/2, min(0.998, value + 0.003), f"{value:.1%}",
                     ha="center", va="bottom", fontsize=10)
    axes[1].set(xticks=np.arange(len(vals)), xticklabels=labels, ylim=(0.90, 1.00),
                yticks=np.arange(0.90, 1.001, 0.02), ylabel="Outcome-action agreement",
                title="(b) Judge agreement on operational action\n(axis from 0.90)")
    axes[1].tick_params(axis="x", rotation=15)
    axes[1].grid(axis="y", color="#E5E7EB", zorder=0)
    fig.tight_layout()
    save(fig, "W09_Figure3_Seed_Variability_and_Judge_Agreement")

    print("PASS: Week 9 publication figures written to", FIGURES)


if __name__ == "__main__":
    main()
