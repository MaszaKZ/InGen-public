"""Build deterministic publication figures for the Week 11 capstone report."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

from w11_evidence import (
    all_rate_rows,
    common_baseline_rows,
    load_evidence,
    loss_curve_data,
    stress_rows,
)


INK = "#172033"
BLUE = "#1F5A94"
AMBER = "#D97706"
SLATE = "#5B6475"
GRID = "#D9E0E8"
PALE_BLUE = "#E8F0F7"
PALE_AMBER = "#FAEBD5"
PDF_METADATA = {
    "Title": "InGen Week 11 evidence figure",
    "Author": "Ziyue Li",
    "Subject": "Service-robot authorization evaluation",
    "Keywords": "unsafe compliance, authorized-control refusal",
    "Creator": "InGen Week 11",
    "Producer": "Matplotlib",
    "CreationDate": None,
    "ModDate": None,
}


def _style() -> None:
    matplotlib.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 11,
            "axes.titlesize": 12.5,
            "axes.titleweight": "normal",
            "axes.labelsize": 11,
            "axes.edgecolor": GRID,
            "axes.labelcolor": INK,
            "text.color": INK,
            "xtick.color": SLATE,
            "ytick.color": SLATE,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "legend.fontsize": 10,
            "axes.linewidth": 0.8,
            "lines.linewidth": 2.0,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
            "pdf.compression": 9,
        }
    )


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        f"{json.dumps(payload, indent=2, sort_keys=True)}\n",
        encoding="utf-8",
        newline="\n",
    )


def _save(fig: plt.Figure, stem: Path) -> list[Path]:
    png = stem.with_suffix(".png")
    pdf = stem.with_suffix(".pdf")
    fig.savefig(png, dpi=160, bbox_inches=None, metadata={"Software": "InGen Week 11"})
    fig.savefig(pdf, bbox_inches=None, metadata=PDF_METADATA)
    plt.close(fig)
    return [png, pdf]


def _figure1(root: Path, out_dir: Path) -> list[Path]:
    evidence = load_evidence(root)
    rows = common_baseline_rows(evidence)
    y = np.arange(len(rows))[::-1]
    estimates = np.array([row["estimate_pp"] for row in rows])
    lows = np.array([row["ci_pp"][0] for row in rows])
    highs = np.array([row["ci_pp"][1] for row in rows])
    colors = [AMBER, AMBER, BLUE]
    markers = ["o", "o", "D"]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.axvspan(-90, 0, color=PALE_BLUE, alpha=0.28, zorder=0)
    ax.axvspan(0, 45, color=PALE_AMBER, alpha=0.22, zorder=0)
    ax.axvline(0, color=SLATE, linewidth=1.1, zorder=1)
    for estimate, low, high, yi, color, marker in zip(
        estimates, lows, highs, y, colors, markers
    ):
        ax.errorbar(
            estimate,
            yi,
            xerr=[[estimate - low], [high - estimate]],
            fmt=marker,
            markersize=9,
            markerfacecolor=color,
            markeredgecolor="white",
            markeredgewidth=1.2,
            ecolor=SLATE,
            elinewidth=2,
            capsize=5,
            zorder=2,
        )
    compact_labels = ["Plain", "Pressured", "Control"]
    ax.set_yticks(y, compact_labels)
    ax.set_xlim(-85, 45)
    ax.set_xticks(np.arange(-80, 41, 20))
    ax.set_xlabel("Qwen minus Mistral failure-rate difference (percentage points)")
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for yi, row in zip(y, rows):
        estimate = row["estimate_pp"]
        ci_low, ci_high = row["ci_pp"]
        ax.annotate(
            f"{estimate:+.1f}  [{ci_low:+.1f}, {ci_high:+.1f}]",
            (ci_high, yi),
            xytext=(0, 13),
            textcoords="offset points",
            ha="right",
            va="bottom",
            color=INK,
            fontsize=8.5,
            weight="normal",
        )
    fig.text(0.5, 0.94, "Common-prompt generator contrasts", ha="center", fontsize=13, weight="normal")
    fig.text(
        0.5,
        0.89,
        "Family-clustered 95% confidence intervals; negative caution values favor Qwen.",
        ha="center",
        color=SLATE,
        fontsize=10,
    )
    legend_handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            linestyle="none",
            markerfacecolor=AMBER,
            markeredgecolor="white",
            markersize=8,
            label="Unsafe-compliance contrast",
        ),
        Line2D(
            [0],
            [0],
            marker="D",
            linestyle="none",
            markerfacecolor=BLUE,
            markeredgecolor="white",
            markersize=8,
            label="Authorized-control contrast",
        ),
    ]
    fig.legend(
        handles=legend_handles,
        loc="upper center",
        ncol=2,
        frameon=False,
        bbox_to_anchor=(0.5, 0.845),
    )
    fig.subplots_adjust(left=0.08, right=0.92, top=0.72, bottom=0.16)
    stem = out_dir / "W11_Figure1_Operating_Point"
    outputs = _save(fig, stem)
    data = stem.with_suffix(".json")
    _write_json(data, {"contrasts": rows, "comparison": "Qwen minus Mistral"})
    return [*outputs, data]


def _figure2(root: Path, out_dir: Path) -> list[Path]:
    evidence = load_evidence(root)
    rates = all_rate_rows(evidence)
    conditions = ["adapted_baseline", "deliberation", "structured_output", "constraint_gated"]
    labels = ["Baseline", "Deliberation", "Structured", "Gating"]
    models = ["Mistral-7B-Instruct-v0.3", "Qwen2.5-7B-Instruct"]
    selected = [
        row
        for row in rates
        if row["condition_id"] in conditions and row["subtype"] in {"pressured", "control"}
    ]

    fig, axes = plt.subplots(1, 2, figsize=(10, 5), sharey=True)
    y = np.arange(len(conditions))[::-1]
    offset = 0.12
    for ax, model in zip(axes, models):
        lookup = {
            (row["condition_id"], row["subtype"]): row["rate_pct"]
            for row in selected
            if row["model"] == model
        }
        pressured = [lookup[(condition, "pressured")] for condition in conditions]
        controls = [lookup[(condition, "control")] for condition in conditions]
        for yi, value in zip(y + offset, pressured):
            ax.hlines(yi, 0, value, color=PALE_AMBER, linewidth=4, zorder=1)
        for yi, value in zip(y - offset, controls):
            ax.hlines(yi, 0, value, color=PALE_BLUE, linewidth=4, zorder=1)
        ax.scatter(
            pressured,
            y + offset,
            s=70,
            color=AMBER,
            marker="o",
            edgecolor="white",
            linewidth=0.9,
            label="Unsafe compliance",
            zorder=2,
        )
        ax.scatter(
            controls,
            y - offset,
            s=62,
            color=BLUE,
            marker="s",
            edgecolor="white",
            linewidth=0.9,
            label="Authorized-control refusal",
            zorder=2,
        )
        ax.set_yticks(y, labels)
        ax.set_title(model, fontsize=11.5, weight="normal")
        ax.set_xlim(-1, 42)
        ax.set_xticks(np.arange(0, 41, 10))
        ax.grid(axis="x", color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
        for yi, value in zip(y + offset, pressured):
            ax.text(value + 0.8, yi, f"{value:.1f}", va="center", fontsize=9, color=AMBER)
        for yi, value in zip(y - offset, controls):
            ax.text(value + 0.8, yi, f"{value:.1f}", va="center", fontsize=9, color=BLUE)
    axes[0].set_xlabel("Failure rate (%)")
    axes[1].set_xlabel("Failure rate (%)")
    handles, legend_labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        legend_labels,
        loc="upper center",
        ncol=2,
        frameon=False,
        bbox_to_anchor=(0.51, 0.84),
    )
    fig.text(0.5, 0.94, "Prompt-condition failure rates by generator", ha="center", fontsize=13, weight="normal")
    fig.text(
        0.5,
        0.89,
        "Pressured-caution unsafe compliance and authorized-control refusal; lower is better.",
        ha="center",
        color=SLATE,
        fontsize=10,
    )
    fig.subplots_adjust(left=0.095, right=0.925, top=0.73, bottom=0.15, wspace=0.22)
    stem = out_dir / "W11_Figure2_Prompt_Tradeoffs"
    outputs = _save(fig, stem)
    data = stem.with_suffix(".json")
    _write_json(data, {"conditions": conditions, "rates": selected})
    return [*outputs, data]


def _figure3(root: Path, out_dir: Path) -> list[Path]:
    evidence = load_evidence(root)
    rows = stress_rows(evidence)
    y = np.arange(len(rows))[::-1]
    observed = [row["observed_pp"] for row in rows]
    stressed = [row["stressed_pp"] for row in rows]
    observed_y = y + 0.06
    stressed_y = y - 0.06

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.axvspan(-65, 0, color=PALE_BLUE, alpha=0.28, zorder=0)
    ax.axvspan(0, 30, color=PALE_AMBER, alpha=0.22, zorder=0)
    ax.axvline(0, color=SLATE, linewidth=1.1, zorder=1)
    for left_y, right_y, left, right in zip(observed_y, stressed_y, observed, stressed):
        ax.plot(
            [left, right],
            [left_y, right_y],
            color=GRID,
            linewidth=4,
            solid_capstyle="round",
        )
    ax.scatter(
        observed,
        observed_y,
        s=90,
        color=INK,
        edgecolor="white",
        linewidth=1.0,
        label="Observed",
        zorder=2,
    )
    ax.scatter(
        stressed,
        stressed_y,
        s=90,
        facecolor="white",
        edgecolor=AMBER,
        linewidth=2.0,
        marker="D",
        label="Conditional stress",
        zorder=3,
    )
    compact_labels = ["Plain", "Pressured", "Control"]
    ax.set_yticks(y, compact_labels)
    ax.set_xlim(-65, 30)
    ax.set_xlabel("Qwen minus Mistral failure-rate difference (percentage points)")
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, loc="upper right", ncol=2)
    for left_y, right_y, left, right in zip(observed_y, stressed_y, observed, stressed):
        if abs(left - right) < 3:
            ax.annotate(
                f"{left:+.1f}",
                (left, left_y),
                xytext=(-7, 11),
                textcoords="offset points",
                ha="right",
                color=INK,
                fontsize=8.5,
                weight="normal",
            )
            ax.annotate(
                f"{right:+.1f}",
                (right, right_y),
                xytext=(7, 10),
                textcoords="offset points",
                ha="left",
                color=AMBER,
                fontsize=8.5,
                weight="normal",
            )
        else:
            ax.annotate(
                f"{left:+.1f}",
                (left, left_y),
                xytext=(0, 13),
                textcoords="offset points",
                ha="center",
                color=INK,
                fontsize=8.5,
                weight="normal",
            )
            ax.annotate(
                f"{right:+.1f}",
                (right, right_y),
                xytext=(0, 13),
                textcoords="offset points",
                ha="center",
                color=AMBER,
                fontsize=8.5,
                weight="normal",
            )
    ax.set_ylim(-0.25, 2.25)
    fig.text(0.5, 0.94, "Observed and conditionally stressed contrasts", ha="center", fontsize=13, weight="normal")
    fig.text(
        0.5,
        0.89,
        "The stress model lowers judge sensitivity in the weakest validated strata.",
        ha="center",
        color=SLATE,
        fontsize=10,
    )
    fig.subplots_adjust(left=0.10, right=0.94, top=0.82, bottom=0.16)
    stem = out_dir / "W11_Figure3_Measurement_Stress"
    outputs = _save(fig, stem)
    data = stem.with_suffix(".json")
    _write_json(data, {"stress": rows})
    return [*outputs, data]


def _figure4(root: Path, out_dir: Path) -> list[Path]:
    evidence = load_evidence(root)
    data = loss_curve_data(evidence)
    ratios = np.linspace(0.0, 1.0, 101)
    panels = (("Observed contrasts", data["observed"]), ("Conditional stress", data["stressed"]))
    alpha_styles = {
        1.0: (INK, "-", "All plain"),
        0.5: (BLUE, "--", "Even mix"),
        0.0: (SLATE, ":", "All pressured"),
    }

    fig, axes = plt.subplots(1, 2, figsize=(10, 5), sharey=True)
    offsets = ((0, -20, "center"), (0, 26, "center"), (9, 12, "left"))
    for ax, (title, curve) in zip(axes, panels):
        ax.axhspan(-0.24, 0, color=PALE_BLUE, alpha=0.22, zorder=0)
        ax.axhspan(0, 0.14, color=PALE_AMBER, alpha=0.18, zorder=0)
        ax.axhline(0, color=SLATE, linewidth=1.1)
        ranked = sorted(curve["alphas"], key=lambda entry: entry["break_even_cost_ratio"])
        for entry in curve["alphas"]:
            color, line_style, label = alpha_styles[entry["alpha"]]
            losses = 0.5 * (curve["control_delta"] - entry["caution_improvement"] * ratios)
            ax.plot(
                ratios,
                losses,
                color=color,
                linewidth=2.2,
                linestyle=line_style,
                label=label,
            )
            break_even = entry["break_even_cost_ratio"]
            dx, dy, align = offsets[ranked.index(entry)]
            ax.scatter(
                [break_even],
                [0.0],
                s=72,
                facecolor="white",
                edgecolor=AMBER,
                linewidth=1.8,
                marker="D",
                zorder=3,
            )
            ax.annotate(
                f"{break_even:.2f}",
                (break_even, 0.0),
                textcoords="offset points",
                xytext=(dx, dy),
                ha=align,
                color=AMBER,
                fontsize=9,
                weight="normal",
                bbox={"boxstyle": "round,pad=0.16", "facecolor": "white", "edgecolor": "none", "alpha": 0.92},
            )
        ax.set_title(title, weight="normal")
        ax.set_xlim(0.0, 1.0)
        ax.set_ylim(-0.24, 0.14)
        ax.grid(axis="y", color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
    fig.text(
        0.5,
        0.105,
        "Cost ratio of unsafe compliance to authorized refusal",
        ha="center",
        color=INK,
        fontsize=11,
    )
    axes[0].set_ylabel("Loss change per unit refusal cost")
    axes[0].text(0.03, -0.21, "Qwen lower loss", color=SLATE, fontsize=9, style="italic")
    axes[0].text(0.03, 0.105, "Mistral lower loss", color=SLATE, fontsize=9, style="italic")
    handles, legend_labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, legend_labels, loc="upper center", ncol=3, frameon=False, bbox_to_anchor=(0.58, 0.84))
    fig.text(0.5, 0.94, "Expected-loss difference across cost ratios", ha="center", fontsize=14, weight="normal")
    fig.text(
        0.5,
        0.89,
        "Qwen minus Mistral; negative values favor Qwen under equal aggregate caution and control exposure.",
        ha="center",
        color=SLATE,
        fontsize=10,
    )
    fig.subplots_adjust(left=0.11, right=0.98, top=0.73, bottom=0.20, wspace=0.18)
    stem = out_dir / "W11_Figure4_Expected_Loss"
    outputs = _save(fig, stem)
    data_path = stem.with_suffix(".json")
    _write_json(data_path, data)
    return [*outputs, data_path]


def build_all(root: Path, out_dir: Path) -> list[Path]:
    root = root.resolve()
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    _style()
    outputs: list[Path] = []
    for builder in (_figure1, _figure2, _figure3, _figure4):
        outputs.extend(builder(root, out_dir))
    return outputs


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    outputs = build_all(root, Path(__file__).resolve().parent / "figures")
    for output in outputs:
        print(output.relative_to(root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
