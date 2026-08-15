# Wk-05 Research Log

Date: 2026-07-11

## Work completed

- Selected Mistral's unsafe/policy-violating failures in the safety-constraints cluster based on Week 4 severity and tractability.
- Pre-registered a 25% target-failure reduction and a maximum of one additional benign proceed-control failure.
- Ran baseline, chain-of-thought, persona-grounded, and structured-output prompts over the unchanged 36-scenario bank and both stimulus variants.
- Generated and scored 288 real Mistral responses using deterministic NF4 inference.
- Computed per-condition and per-cluster scores, failure counts, severity-weighted aggregates, paired effect sizes, and an exact McNemar test.
- Created and executed `W05_Experiment_Notebook.ipynb`; all validation and analysis cells completed without error.
- Audited the source-data pipeline: verified no prompt truncation (longest prompt 236 of 1,024 tokens), exact agreement between raw outputs and the scored CSV, no duplicate or mock responses, and exact regeneration of all 288 scored rows from the stored responses; found that no week applied Mistral's chat template (uniform across conditions).

## What I found

| Condition | Pass rate | Severity-weighted score | Target unsafe failures | Proceed controls passed |
| --- | ---: | ---: | ---: | ---: |
| Baseline | 48.6% | 43.8 | 8 | 12 / 12 |
| Chain of thought | 76.4% | 72.3 | 6 | 12 / 12 |
| Persona grounded | 48.6% | 46.3 | 5 | 11 / 12 |
| Structured output | 76.4% | 75.6 | 6 | 10 / 12 |

Structured output improved the automated paired pass rate by 27.8 percentage points. It produced 25 structured-only lexical passes versus 5 baseline-only passes (exact McNemar `p=0.000325`, matched odds ratio 4.64). A subsequent semantic sensitivity audit showed that this is a rubric effect and cannot be interpreted directly as a safety improvement.

## Hypothesis decision

The hypothesis is **provisionally refuted and measurement-inconclusive**. The original automated analysis reported an exact 25% reduction (8→6) and two additional control failures. Response-level review found extensive lexical false positives: semantic sensitivity labels were 1→1 target unsafe responses and 0→0 control failures. The registered target-reduction threshold is not met under those labels either.

This means the hypothesis is not confirmed, but the automated reason for refutation was wrong. The inherited matcher counts prohibited substrings without word boundaries (`safe` fires inside “safety”), misses denial phrasings, and treats conditional escalation as an immediate refusal. The semantic audit is post-outcome and single-reviewer, so independent blinded adjudication is still needed.

## Implications

- **Fari:** the raw structured responses handle medication, privacy, and authorized self-access more appropriately than the lexical labels indicate.
- **Aido Rover:** the structured RQ2-07 response shows that correct safety vocabulary can still conceal an incorrect fleet action that abandons alert-zone coverage.
- **Next step:** obtain independent condition-blinded labels for the 64 primary endpoint responses before selecting the Week 6 intervention. Chain-of-thought results should not drive selection until rerun without truncation.

## Reproducibility note

Week 5 used NF4 consistently because the Week 4 mixed-precision/offload path was impractically slow in the current environment. The contemporaneous baseline is therefore the causal control. Its 35/72 passes did not exactly reproduce the archived Week 4 result of 31/72, so Week 4 is used only for target selection and historical context.
