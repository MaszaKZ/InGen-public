"""Build the rerunnable Week 7 analysis notebook; execute it with nbconvert."""
from __future__ import annotations

from pathlib import Path

import nbformat as nbf

W7 = Path(__file__).resolve().parent
OUT = W7 / "W07_Analysis_Notebook.ipynb"


def main() -> None:
    nb = nbf.v4.new_notebook()
    nb["metadata"] = {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3"}}
    cells = []
    cells.append(nbf.v4.new_markdown_cell("""# Week 7 cross-experiment synthesis and audit companion

This executed notebook is the cross-experiment synthesis for the Week 7
confirmation study and the audit-facing companion to `W07_Research_Note.md`.
It recomputes headline rates with their registered family-clustered intervals,
adds standardized effect sizes and paired exact tests, surfaces every stored
intervention contrast, stratifies results by InGen platform (Sentinel Prime AI
and Aido Humanoid), and juxtaposes the Week 6 within-Mistral experiment with
the Week 7 cross-model results. The 96 scenarios are synthetic; gold labels are
AI-assisted and externally human-verified, not independently human-annotated;
both generators used NF4 inference."""))
    cells.append(nbf.v4.new_code_cell("""from pathlib import Path
import json
import pandas as pd
from IPython.display import display, Image

ROOT = Path.cwd()
if not (ROOT / 'week-07').exists():
    ROOT = ROOT.parent
W7 = ROOT / 'week-07'
results = pd.read_csv(W7 / 'W07_Results.csv')
ratings = pd.read_csv(W7 / 'W07_Judge_Ratings.csv')
analysis = json.loads((W7 / 'W07_Analysis.json').read_text(encoding='utf-8'))
calibration = json.loads((W7 / 'W07_Judge_Calibration.json').read_text(encoding='utf-8'))
metadata = json.loads((W7 / 'W07_Run_Metadata.json').read_text(encoding='utf-8'))
print(f"{len(results):,} generations; {len(ratings):,} judgments; panel={calibration['selected_panel']}")"""))
    cells.append(nbf.v4.new_markdown_cell("## Acceptance and data integrity"))
    cells.append(nbf.v4.new_code_cell("""assert len(results) == 4_800
assert len(ratings) == 14_400
assert results[['generator_model','condition','scenario_id','seed']].drop_duplicates().shape[0] == 4_800
assert ratings[['generator_model','condition','scenario_id','seed','judge_name']].drop_duplicates().shape[0] == 14_400
# Registered rule: panel rows whose votes did not all parse are excluded from
# every statistic and disclosed; the analysis fails above a 1% bound.
unparsed = results[results.parse_success.astype(int) == 0]
assert len(unparsed) <= 48, f'panel-unparsed rows exceed the 1% bound: {len(unparsed)}'
assert analysis['panel_unparsed']['count'] == len(unparsed)
results = results[results.parse_success.astype(int) == 1].copy()
ratings = ratings[ratings.response_id.isin(set(results.response_id))].copy()
assert len(calibration['selected_panel']) == 3
assert all(calibration['candidates'][j]['passes'] for j in calibration['selected_panel'])
print(f"All registered row, key, and judge-gate checks pass; "
      f"{len(unparsed)} panel-unparsed rows disclosed and excluded.")"""))
    cells.append(nbf.v4.new_markdown_cell("""## Headline outcome rates with registered intervals

Every rate carries its stored family-clustered 95% bootstrap interval from
`W07_Analysis.json` (10,000 draws over the 16 complete scenario families)."""))
    cells.append(nbf.v4.new_code_cell("""rates = pd.DataFrame(analysis['rates'])[['model','condition','subtype','estimate','ci_low','ci_high','rows']]
recomputed = (results.groupby(['generator_model','condition','subtype'])
              .majority_failure.mean().rename('recomputed').reset_index())
rates = rates.merge(recomputed, left_on=['model','condition','subtype'],
                    right_on=['generator_model','condition','subtype']).drop(columns='generator_model')
assert (rates.estimate - rates.recomputed).abs().max() < 1e-12
display(rates.drop(columns='recomputed').style.format({'estimate':'{:.1%}','ci_low':'{:.1%}','ci_high':'{:.1%}'}))"""))
    cells.append(nbf.v4.new_markdown_cell("""## Registered paired comparisons

The cross-model endpoint uses only the identical common-baseline text before native chat rendering. Prompt adaptation is estimated within each model. Interventions are compared with that model's adapted baseline."""))
    cells.append(nbf.v4.new_code_cell("""primary = pd.DataFrame(analysis['paired_contrasts']['primary_common_baseline']).T
display(primary[['comparison','estimate','ci_low','ci_high']].style.format({'estimate':'{:+.1%}','ci_low':'{:+.1%}','ci_high':'{:+.1%}'}))
adapt = []
for model, blocks in analysis['paired_contrasts']['adaptation_effects'].items():
    for subtype, row in blocks.items(): adapt.append({'model':model,'subtype':subtype,**row})
display(pd.DataFrame(adapt)[['model','subtype','estimate','ci_low','ci_high']].style.format({'estimate':'{:+.1%}','ci_low':'{:+.1%}','ci_high':'{:+.1%}'}))"""))
    cells.append(nbf.v4.new_markdown_cell("## Mitigation rule, seed stability, and judge agreement"))
    cells.append(nbf.v4.new_code_cell("""mitigation=[]
for model, blocks in analysis['mitigation_rule']['results'].items():
    for condition, row in blocks.items(): mitigation.append({'model':model,'condition':condition,**row})
display(pd.DataFrame(mitigation).style.format({'pressured_relative_reduction':'{:+.1%}','control_failure_increase':'{:+.1%}'}))
print('Judge agreement:', analysis['judge_agreement'])
display(pd.DataFrame(analysis['action_vote_patterns']).sort_values('count', ascending=False).head(20))
display(pd.DataFrame(analysis['judge_action_distribution']))
seed = pd.DataFrame(analysis['seed_stability'])
display(seed[seed.subtype=='pressured'].pivot_table(index=['generator_model','condition'],columns='seed',values='majority_failure').style.format('{:.1%}'))"""))
    cells.append(nbf.v4.new_markdown_cell("""## Standardized effect sizes and paired exact tests (supplementary)

Cohen's h, the risk ratio, and an exact McNemar test on `(scenario_id, seed)`-
paired binary outcomes supplement the registered analysis. The registered
inference remains the family-clustered bootstrap: scenarios cluster within 16
families, so these unclustered p-values overstate precision and are reported
as descriptive corroboration, not as the acceptance criterion."""))
    cells.append(nbf.v4.new_code_cell("""import math
from scipy.stats import binomtest

MISTRAL = [m for m in results.generator_model.unique() if 'istral' in m][0]
QWEN = [m for m in results.generator_model.unique() if 'Qwen' in m][0]

def paired_effects(left, right, label):
    keys = ['scenario_id', 'seed']
    merged = left[keys + ['majority_failure']].merge(
        right[keys + ['majority_failure']], on=keys, suffixes=('_l', '_r'))
    p_l, p_r = merged.majority_failure_l.mean(), merged.majority_failure_r.mean()
    b = int(((merged.majority_failure_l == 0) & (merged.majority_failure_r == 1)).sum())
    c = int(((merged.majority_failure_l == 1) & (merged.majority_failure_r == 0)).sum())
    cohens_h = 2 * math.asin(math.sqrt(p_r)) - 2 * math.asin(math.sqrt(p_l))
    mcnemar_p = binomtest(min(b, c), b + c, 0.5).pvalue if b + c else float('nan')
    return {'comparison': label, 'n_pairs': len(merged), 'rate_left': p_l, 'rate_right': p_r,
            'difference': p_r - p_l, 'cohens_h': cohens_h,
            'risk_ratio': (p_r / p_l) if p_l > 0 else float('inf'),
            'discordant_01': b, 'discordant_10': c, 'mcnemar_exact_p': mcnemar_p}

def block(model, condition, subtype):
    return results[(results.generator_model == model) & (results.condition == condition) & (results.subtype == subtype)]

effects = [paired_effects(block(MISTRAL, 'common_baseline', s), block(QWEN, 'common_baseline', s),
                          f'Qwen vs Mistral, common baseline, {s}') for s in ('plain', 'pressured', 'control')]
for model, name in ((MISTRAL, 'Mistral'), (QWEN, 'Qwen')):
    for s in ('pressured', 'control'):
        effects.append(paired_effects(block(model, 'adapted_baseline', s), block(model, 'deliberation', s),
                                      f'{name}: deliberation vs adapted, {s}'))
display(pd.DataFrame(effects).style.format({'rate_left':'{:.1%}','rate_right':'{:.1%}','difference':'{:+.1%}',
                                            'cohens_h':'{:+.2f}','risk_ratio':'{:.2f}','mcnemar_exact_p':'{:.2e}'}))"""))
    cells.append(nbf.v4.new_markdown_cell("""## All stored intervention contrasts

The 18 `interventions_vs_adapted` contrasts (each intervention minus that
model's adapted baseline) with their registered family-clustered intervals —
previously computed in `W07_Analysis.json` but not surfaced in any report."""))
    cells.append(nbf.v4.new_code_cell("""intervention_rows = []
for model, conditions in analysis['paired_contrasts']['interventions_vs_adapted'].items():
    for condition, blocks in conditions.items():
        for subtype, row in blocks.items():
            intervention_rows.append({'model': model.split('/')[0], 'condition': condition,
                                      'subtype': subtype, 'estimate': row['estimate'],
                                      'ci_low': row['ci_low'], 'ci_high': row['ci_high']})
display(pd.DataFrame(intervention_rows).style.format({'estimate':'{:+.1%}','ci_low':'{:+.1%}','ci_high':'{:+.1%}'}))"""))
    cells.append(nbf.v4.new_markdown_cell("""## Platform-stratified results (Sentinel Prime AI vs Aido Humanoid)

The bank assigns 48 scenarios (8 families) to each platform, and `platform`
is a first-class column of the results, so platform stratification requires
no join. Tactic rates come from the stored `pressure_tactic_breakdown`."""))
    cells.append(nbf.v4.new_code_cell("""platform_rates = (results[results.condition == 'common_baseline']
                  .groupby(['platform', 'generator_model', 'subtype'])
                  .majority_failure.agg(['mean', 'sum', 'count']).reset_index())
display(platform_rates.style.format({'mean':'{:.1%}'}))
tactics = pd.DataFrame([r for r in analysis['pressure_tactic_breakdown'] if r['condition'] == 'common_baseline'])
display(tactics[['generator_model','tactic','sum','count','mean']].style.format({'mean':'{:.1%}'}))"""))
    cells.append(nbf.v4.new_markdown_cell("""## Cross-experiment synthesis with Week 6

Week 6 (within Mistral, its own 32-scenario bank, plain prompt stack) found
pressure increased unsafe compliance (3/32 plain vs 12/32 pressured) and
chain-of-thought deliberation was the only registered-rule-passing mitigation
(12/32 to 2/32). The cells below place those numbers beside the Week 7
cross-model results on the new 96-scenario bank."""))
    cells.append(nbf.v4.new_code_cell("""w6 = json.loads((ROOT / 'week-06' / 'W06_Analysis.json').read_text(encoding='utf-8'))
w6_rows = []
for condition, table in w6['condition_tables'].items():
    w6_rows.append({'experiment': 'Week 6 (Mistral, W6 bank)', 'condition': condition,
                    **{k: f"{v['failures']}/{v['n']}" for k, v in table.items()}})
display(pd.DataFrame(w6_rows))
w6d = w6['diagnostic_baseline_pressured_vs_plain']
print(f"Week 6 pressure effect within Mistral: +{w6d['difference_b_minus_a']:.1%} "
      f"(exact McNemar p={w6d['exact_two_sided_mcnemar_p']:.4f}, "
      f"family CI [{w6d['family_bootstrap']['lower_95']:+.1%}, {w6d['family_bootstrap']['upper_95']:+.1%}])")
w7_mistral = (results[results.generator_model == MISTRAL]
              .groupby(['condition', 'subtype']).majority_failure.mean().unstack())
print('\\nWeek 7 Mistral panel-majority failure rates by condition:')
display(w7_mistral.style.format('{:.1%}'))"""))
    cells.append(nbf.v4.new_markdown_cell("""**Transfer conclusion.** The Week 6 deliberation effect does not transfer
additively to the Week 7 stack: on the new bank, Mistral's pressured failures
under deliberation (19.4%) are indistinguishable from its adapted baseline
(18.8%), and the pressured-failure suppression relative to the common baseline
(43.1%) comes from the adapters and structured arms rather than deliberation.
The direction of the pressure effect also reverses on the new bank — both
generators fail plain caution scenarios more often than pressured ones — which
bounds the Week 6 pressure finding to its bank construction and is examined in
the research note and self-critique."""))
    cells.append(nbf.v4.new_markdown_cell("## Reader-facing figures"))
    cells.append(nbf.v4.new_code_cell("""for name in ['W07_Figure1_Common_Baseline_Cross_Model.png','W07_Figure2_Prompt_Safety_and_Control_Cost.png','W07_Figure3_Seed_Variability_and_Judge_Agreement.png']:
    display(Image(filename=str(W7 / 'figures' / name)))"""))
    cells.append(nbf.v4.new_markdown_cell("""## Scope and interpretation

The design supports pipeline-level conclusions for these two pinned, quantized instruction models on synthetic text scenarios. Model-specific prompts make adapted cross-model differences descriptive rather than causal architectural effects. Scenario-family bootstrap intervals address clustered scenario sampling; five fixed decoding seeds expose observed sampling variability but do not exhaust possible decoding behavior."""))
    nb["cells"] = cells
    OUT.write_text(nbf.writes(nb), encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
