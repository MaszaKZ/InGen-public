# Research Work Process Through the Mid-Point Review

**Author:** Ziyue Li
**Program:** InGen Dynamics AI Research Internship
**Coverage:** Phases A-B, Weeks 1-6
**Review point:** July 2026

## Purpose and evidence boundary

This document records how the research developed through the mid-point review. It is organized around the work process: the questions entering each stage, the design and implementation choices made, the problems discovered, the corrective work performed, and the way each result changed the next step. It complements the completed mid-review presentation; findings already explained there are summarized only when needed to make the process understandable.

The account distinguishes three evidence levels. Work in `week-01` through `week-05` and the submitted `week-06` directory is the canonical record of the internship. Preliminary Week 6 work is summarized here only for methodological context; superseded working files are not part of this snapshot, and their statistics are not combined with the submitted Week 6 results. Internal product documents, customer information, deployment logs, and proprietary procedures are outside the publication boundary; the research uses public descriptions and synthetic scenarios.

## Executive summary: the process, not only the result

The first half of the internship followed a progression from broad research orientation to a narrowly testable empirical claim. Weeks 1 and 2 established the physical-AI landscape, mapped the public PIC 2.0 model roles to open research areas, and translated broad concerns about uncertainty, safety, and trust into measurable questions. Week 3 converted those questions into a public-safe, text-only benchmark. Week 4 added a third model and a failure taxonomy so that the work could move from describing performance to selecting a tractable failure mechanism. Week 5 tested a prompt intervention, but the apparent improvement was traced to lexical scoring errors. That correction changed the research question from “Which prompt scores better?” to “What condition actually produces the unsafe behavior, and how can it be measured credibly?”

Preliminary Week 6 work then went through three increasingly rigorous experiment iterations. The first leaked condition information and ignored dependence among related scenarios. The second corrected masking and family-level inference but produced an absolute performance floor because the targets quoted their own constraints. The third introduced adversarial pressure, a revised scorer, a more diverse judge panel, and prevalence-robust reliability analysis, but still ended inconclusive and revealed a safety-versus-over-refusal trade-off. Instead of hiding those failures, the entire line was archived and the canonical Week 6 experiment was started afresh.

The submitted Week 6 experiment used the methodological lessons from those iterations but asked a cleaner diagnostic question: does the same baseline model fail more often when a safety boundary is contested by social pressure than when it is stated plainly? On the committed synthetic Mistral-7B benchmark, failures rose from 3/32 plain targets to 12/32 pressured targets. Explicit deliberation reduced pressured failures to 2/32 while leaving the observed benign-control failure count at 1/32. Constraint gating eliminated pressured failures but increased control failures from 1/32 to 4/32. The mid-point claim is therefore deliberately bounded: adversarial social pressure exposed a decision-layer safety weakness in this model and benchmark, and deliberation provided the best observed safety/refusal trade-off among the tested prompts.

The most important contribution of the process is not a claim that one prompt makes robots safe. It is the development of a more credible evidence chain: paired scenarios, controls for over-refusal, semantic rather than purely lexical endpoints, family-clustered uncertainty, judge-sensitivity analysis, reproducible scripts, and explicit separation between exploratory and canonical evidence.

## Process overview and major inflection points

| Period | Starting question | Work process | Inflection point |
| --- | --- | --- | --- |
| Week 1 | Which physical-AI research problems are both relevant to InGen and open in the literature? | Built the environment, reviewed platform context and anchor papers, mapped the ecosystem and PIC 2.0 roles. | Shifted from a broad “physical AI” topic to decision safety, calibrated uncertainty, and human oversight. |
| Week 2 | Can those themes become precise and measurable? | Reviewed 18 papers across embodied evaluation, safety/OOD behavior, and trust; wrote research gaps and hypotheses. | Defined three benchmark-ready research questions with explicit success criteria. |
| Week 3 | Can the questions be operationalized in a discriminative benchmark? | Authored 36 scenario families with paraphrases, implemented scoring and three judge rules, and ran two baselines. | Added proceed-mode controls after recognizing that an always-refuse policy would otherwise appear safe. |
| Week 4 | Which failures matter most, and which are tractable? | Added Mistral-7B, preserved prior rows, built severity weighting, and created a three-level failure taxonomy. | Safety-boundary and escalation failures became the intervention target, while taxonomy refinement separated real errors from small-model non-responses. |
| Week 5 | Can targeted prompting reduce high-severity safety failures without excess refusal? | Ran four prompt conditions and audited the entire source-to-score pipeline. | A semantic audit overturned the lexical interpretation; the apparent gain was a measurement artifact. |
| Preliminary Week 6 | Can a gated prompt solve the failure without introducing refusal cost? | Iterated through v1, masked family-clustered rerun-v2, and adversarial rerun-v3. | Leakage, target floors, scorer defects, prevalence effects, and judge gullibility forced a complete redesign and archival of the line. |
| Canonical Week 6 | Are genuine failures concentrated under adversarial pressure, and which mitigation preserves benign compliance? | Built a fresh paired diagnostic bank, ran four conditions, used three semantic judges plus sensitivity scoring, and independently recomputed the analysis. | Pressure produced the clearest diagnostic contrast; deliberation alone met the registered benefit/cost rule. |

## Weeks 1-2: narrowing the research problem

### Question entering the work

“Physical AI” covered too many layers for one internship: perception, planning, control, uncertainty, safety, human interaction, and fleet coordination. The initial task was therefore to find a problem that was relevant to InGen’s public platform context, genuinely open in the literature, and executable with local compute and public-safe evidence.

### Work process

Week 1 established a Python 3.11/CUDA environment and verified the machine-learning and analysis stack in an executable notebook. Credential-free environment checks separated toolchain verification from model execution and established an early rule: empirical claims should be tied to runnable code, recorded settings, and stored outputs.

The landscape study then mapped public PIC 2.0 roles to nearby open-method families. The mapping was structural rather than name-based: STUM connected to calibrated uncertainty and abstention; SEOM to safe reinforcement learning and constrained oversight; AMDC to sensor calibration; HTD-IRL to hierarchical planning; GRPO to policy choice; and CRL-MRS to multi-agent coordination. Imperfect mappings were treated as research boundaries rather than forced equivalents. In particular, the difficulty of mapping high-level safety oversight to one method highlighted the gap between stating a rule and maintaining it in an operational decision.

Week 2 organized 18 papers into embodied-model evaluation, safety/uncertainty/OOD behavior, and trust calibration. Each annotation asked what the paper measured, what remained unresolved for service-robot decisions, and how the gap could become a compact benchmark. Conformal decision theory was especially influential because it reframed uncertainty around the operational choice among acting, deferring, requesting review, and using a safer fallback.

### Decision and transition

The review produced three measurable questions: uncertainty-gated decisions, safety constraints without excessive refusal, and trust-calibrating explanations. The project stayed at the decision layer and used text descriptions so different open models could receive comparable evidence. Multimodal and deployed-system claims were deferred rather than approximated.

**Primary process evidence:** `week-01/Wk-01-ResearchLog.md`, `week-01/W01_Research_Landscape.md`, `week-02/Wk-02-ResearchLog.md`, `week-02/W02_Literature_Review.md`, `week-02/W02_PIC20_Mapping.md`, and `week-02/W02_Research_Questions.md`.
## Week 3: building a benchmark that could fail in both directions

### From research questions to scenario structure

Week 3 created a 36-scenario text benchmark: 12 scenarios for each research question, with an original and paraphrased stimulus for every item. Each scenario recorded the platform context, expected behavior, failure conditions, severity, relevant PIC 2.0 roles, and concepts used by the deterministic scorer. The initial baseline therefore contained 72 responses per model.

The benchmark drew on scenario-level evaluation principles from established benchmark practice: explicit task definitions, multiple scoring dimensions, perturbation testing, and auditable outputs. The six dimensions were task accuracy, robustness, calibration, safety, escalation correctness, and explanation quality. Three heterogeneous automated judge rules produced independent binary decisions emphasizing safety/compliance, calibration/explanation, and task/escalation respectively; majority vote determined the row-level pass label.

### The proceed-control correction

The most consequential design correction happened before the full run. An early version rewarded caution in every scenario. Under that design, a model that always refused or escalated could appear well calibrated and safe. Six proceed-mode control scenarios were added, two per research cluster, and each also had a paraphrase. These controls required the model to act, answer, or explain confidently when the request was benign and the evidence was clear.

This changed both the benchmark and the scoring code. `run_w03_baseline.py` validates the presence of caution and proceed modes, builds a fixed prompt, generates both stimulus variants, computes the six scores, applies action-aware failure logic, and calculates nominal Krippendorff’s alpha over the three-by-N judge matrix. The control design became a permanent methodological principle carried through Weeks 4-6: unsafe compliance and unnecessary refusal must be measured together.

### Baseline execution and interpretation

The full run compared `google/flan-t5-base` and `Qwen/Qwen2.5-1.5B-Instruct`. Flan passed 4/72 responses and frequently produced degenerate outputs that repeated prompt labels. Qwen passed 29/72 and 11/12 controls, demonstrating a meaningful capability difference and confirming that the benchmark was not passed by blanket refusal. Qwen’s main product-relevant weakness was instead unsafe or policy-violating behavior on high-severity caution scenarios.

Overall Krippendorff’s alpha was 0.574. This was treated as moderate agreement among automated rules, not as human-rater reliability. The distinction mattered: the judges were reproducible decision functions, but they could not validate whether a human expert would interpret borderline responses the same way.

### Week 3 decision

The benchmark was sufficiently discriminative to extend, but its scorer was still coarse. Week 4 would add a 7B model, preserve the scenario bank, and convert row-level failures into an auditable taxonomy. Human or stronger semantic judging remained an open need.

**Primary process evidence:** `week-03/Wk-03-ResearchLog.md`, `week-03/W03_Benchmark_Design.md`, `week-03/W03_Scenario_Bank.yaml`, `week-03/run_w03_baseline.py`, and the committed baseline results and reliability summary.

## Week 4: extending the comparison and learning from failure cases

### Preserving comparability

Week 4 reused the Week 3 scenario bank exactly and retained the existing Flan and Qwen rows. The extension runner added `mistralai/Mistral-7B-Instruct-v0.3`, using CPU offload where needed, then produced a combined 216-row dataset. This avoided changing the benchmark while changing the model, which made capability-tier comparisons interpretable.

Mistral ranked first with 31/72 passes and a severity-weighted score of 39.3, compared with Qwen’s 29/72 and 36.0. The small margin was less important than the failure record: across all models, 152/216 rows failed, including safety-boundary violations, missed escalation, over-caution, partial actions, and many degenerate Flan outputs.

### Building and revising the taxonomy

The first taxonomy draft used four top-level categories: factual/task error, reasoning/calibration failure, safety/alignment failure, and robustness/over-caution failure. During review, the factual/task bucket contained 101 rows and was too broad to guide an intervention. The code and report were revised to separate degenerate non-responses, wrong actions, incomplete actions, and acceptable actions with weak justification. The per-row “likely mechanism” field was also changed from a repeated template into scenario-specific text that named the expected action and quoted the model’s operational decision.

`run_w04_extended.py` supports this correction without rerunning inference. Its `--reclassify` path regenerates the taxonomy and reports from the existing scored rows. This was a useful separation of concerns: model outputs remained immutable evidence, while the explanatory classification could be improved transparently.

### Severity and intervention selection

The analysis used a severity-weighted score so that a severity-5 medication, privacy, or physical-risk failure counted more than a low-severity nuisance. This did not make the metric a deployment-risk model, but it provided a principled way to choose the next experiment. Safety-boundary and missed-escalation failures were more actionable than the much larger set of small-model task errors.

### Week 4 decision

Week 5 would focus on Mistral and test whether prompting could reduce unsafe or policy-violating outputs in the safety-constraint cluster. The experiment would retain benign controls so that any intervention had to improve safety without abandoning authorized tasks.

**Primary process evidence:** `week-04/Wk-04-ResearchLog.md`, `week-04/run_w04_extended.py`, `week-04/W04_Extended_Benchmark.ipynb`, `week-04/W04_Failure_Analysis.md`, and the failure-case and reliability artifacts.

## Week 5: when a reproducible result failed semantic review

### Hypothesis and experimental control

Week 5 tested whether structured decision output could reduce Mistral’s unsafe safety-cluster responses. The registered decision rule required at least a 25% relative reduction in target unsafe failures and no more than one additional failure across the 12 benign proceed controls.

Four conditions were run over the unchanged 36-scenario bank and both variants: baseline, chain-of-thought deliberation, persona grounding, and structured output. All conditions used Mistral-7B-Instruct-v0.3, greedy decoding, NF4 quantization, and the inherited scoring logic. The contemporaneous Week 5 baseline, rather than the Week 4 result, served as the causal control because runtime precision had changed.

The experiment generated 288 real responses. `run_w05_experiment.py` verifies that its baseline prompt matches the Week 3/4 prompt, records all prompt specifications and runtime settings, writes raw and scored outputs, computes severity-weighted summaries, and performs an exact paired McNemar test. The source-data audit confirmed no prompt truncation, blank responses, duplicates, mock responses, or disagreement between raw outputs and the scored CSV.

### The apparent improvement

Under the inherited lexical rubric, structured output increased the paired pass rate by 27.8 percentage points. It produced 25 structured-only passes versus five baseline-only passes, with an exact McNemar p-value of 0.000325. Target unsafe failures appeared to fall from 8 to 6, while proceed-control failures appeared to rise from 0 to 2. The registered hypothesis was therefore not confirmed because the control-cost rule failed, even before semantic review.

### Why the measurement was wrong

The result looked suspicious because the structured prompt explicitly requested words such as constraint, safety, boundary, and escalation—the same vocabulary used by the scorer. A response-level audit replayed every trigger over the primary target and control rows. Thirteen of the 14 target responses flagged across baseline and structured output were safe denials or explanations. Examples included `safe` matching inside “safety,” `share` being detected when the model said it would not share data, and conditional future escalation being mistaken for immediate refusal.

The semantic sensitivity audit changed the primary counts to 1→1 unsafe target responses and 0→0 control failures. This did not prove the interventions equivalent, because the review was post-outcome and single-reviewer. It did prove that the automated 8→6 interpretation was invalid. The official conclusion became “provisionally refuted and measurement-inconclusive pending independent adjudication.”

### Process lesson and next question

Week 5 was valuable precisely because the code was reproducible enough to expose the measurement failure. The numerical result could be regenerated perfectly, but it measured lexical overlap rather than the intended safety behavior. The research therefore moved away from selecting an intervention based on that metric.

Raw-response review suggested a competing explanation: the model often maintained an explicit boundary in a plain request but became less reliable when the requester claimed authority, urgency, prior clearance, or accepted practice. This observation motivated a diagnostic rather than another generic prompt comparison.

**Primary process evidence:** `week-05/Wk-05-ResearchLog.md`, `week-05/run_w05_experiment.py`, `week-05/audit_w05_semantics.py`, `week-05/W05_Results_Memo.md`, `week-05/W05_Semantic_Audit.csv`, and `week-05/W05_Semantic_Audit_Summary.json`.

## Preliminary Week 6 exploration: three iterations before the canonical submission

### Why this work remains in the record

The preliminary work is not part of the canonical deliverable set. It is summarized in this section because its three iterations each exposed a concrete defect that informed the fresh `week-06` experiment.

### Iteration v1: apparent confirmation with invalid evidence exposure

The first exploratory path extended Week 5 with diagnostic, confirmatory, programmed-sensitivity, and synthetic adjudication workflows. Subsequent audit found that the nominally masked packets revealed condition through prompt-specific response-field labels. It also found that scenario-level significance treated related variants as independent rather than accounting for scenario-family dependence. The earlier “statistically conclusive” language and synthetic claim were withdrawn.

The response was not a wording change to the report. The evidence was preserved under the archive and explicitly demoted. This established an evidence-discipline rule used later: masking must be evaluated from the rater’s view, and uncertainty must be calculated at the family level when multiple items share a boundary or scenario template.

### Rerun-v2: corrected masking, but an unfalsifiable target

Rerun-v2 used condition-neutral fields, shuffled action-only packets, and family-clustered analysis. It was methodologically stronger, but its result was structurally uninformative. Every target stated the governing constraint verbatim immediately before the request—for example, directly telling the model that an active fire-alarm charging station could not be used. Neither prompt condition produced a genuine prohibited action: the baseline target failure floor was 0/160.

The iteration also exposed two measurement defects. Scorer v3 flagged many controls because exact success phrases failed under harmless paraphrase and incidental refusal words appeared inside allowed actions. Its target flags were negation errors. Meanwhile, nominal Krippendorff’s alpha was used as a hard reliability gate at near-zero failure prevalence, where the coefficient could remain low despite very high raw agreement. The panel itself was vulnerable because a weak Qwen judge was nearly constant and the Mistral self-judge plus deterministic scorer could form a correlated majority.

Rerun-v2’s frozen decision remained inconclusive. The important output was a design memo that tied every next change to an observed failure rather than adding complexity speculatively.

### Rerun-v3 design: pressure, improved scoring, and a stronger panel

Rerun-v3 introduced 32 unseen families whose targets no longer handed the model an uncontested rule. Five pressure tactics supplied concrete reasons to override or reinterpret the boundary: authority override, false clearance, urgency minimization, incremental requests, and social proof. The gated instruction gained an explicit fast path for authorized requests so it would not invent constraints when none applied.

Scorer v4 replaced exact-phrase control matching with stemmed token overlap, expanded modal-negation handling, and limited refusal detection to refusals directed at the requested action. The judge panel expanded to four members: scorer v4, Qwen2.5-7B, a disclosed Mistral self-judge, and Phi-3.5-mini. A 3/4 supermajority was required, 2-2 ties were recorded, and Gwet’s AC1 replaced alpha as the registered prevalence-robust reliability gate. The judge module and other load-bearing sources were hash-pinned before confirmatory inference.

Two pilot iterations occurred before the freeze. The first showed that bare insistence was too weak and exposed scorer defects. The second used concrete false legitimacy claims and produced a measurable structured-baseline failure rate. It also revealed that LLM judges could inherit the generator’s gullibility: judges sometimes accepted unsafe actions merely because the response repeated the requester’s claimed authority. The judge prompt was hardened to treat legitimacy claims as unverified and to check controls against the scenario’s stated authorization.

### Rerun-v3 outcome and why it was still archived

On the four-judge supermajority endpoint, structured targets failed 61/160 times and gated targets failed 48/160 times, a 21.3% relative reduction. The family-bootstrap effect was -8.1 percentage points with a 95% interval from -17.5 to +1.2 points, so the target benefit was uncertain. Control failures increased from 7/96 to 17/96, with a positive family-bootstrap interval. Panel AC1 was 0.443, below its registered gate, and 125 items ended in 2-2 ties. The frozen decision was “inconclusive or criteria not met.”

These results did not support a clean gated-prompt claim, but the exploration established three durable observations: adversarial pressure was necessary to create a falsifiable target, gate-first prompting could cause real over-deferral, and judge models themselves needed protection against false-authority framing. Because the line had accumulated multiple designs and a different primary question, the complete work was archived rather than selectively folded into the Week 6 submission.

**Primary process evidence:** the iteration summaries and decisions retained in this document record the methodological lessons carried into the canonical Week 6 experiment.

## Canonical Week 6: applying the process lessons to a cleaner diagnostic

### Question and design reset

The canonical experiment returned to the Week 5 raw-response observation and selected the diagnostic branch of the internship plan. It asked whether baseline failures were concentrated under adversarial social pressure rather than in the plain underlying scenario, and whether any intervention improved pressure robustness without refusing authorized controls. The diagnostic and mitigation decision rules were fixed before the main run.

`build_w06_bank.py` created 16 main families split between Sentinel Prime AI and Aido Humanoid contexts, plus two holdout families. Each main family provided two plain targets, two pressured targets, and two authorized controls. `run_w06_experiment2.py` randomized the schedule, supported resumable checkpoints, applied Mistral’s chat template, and recorded prompt and response hashes. Three semantic judges produced the primary majority endpoint; the repaired deterministic scorer remained a sensitivity check.

The complete evidence chain contained 384 responses and 1,152 individual ratings. Integrity tests checked bank balance, scenario pairing, scorer regressions, unique keys, cardinality, chat-template application, and vote construction. A separate standard-library verifier recomputed counts, paired tests, family bootstrap intervals, reliability statistics, sensitivity labels, and hashes from the committed artifacts.

### Compact result recap

| Condition | Plain target failures | Pressured target failures | Control failures | Process interpretation |
| --- | ---: | ---: | ---: | --- |
| Baseline | 3/32 | 12/32 | 1/32 | Pressure created the registered diagnostic contrast. |
| Explicit deliberation | 0/32 | 2/32 | 1/32 | Only intervention meeting both benefit and control-cost rules. |
| Structured output | 1/32 | 14/32 | 1/32 | Format alone did not improve pressure robustness. |
| Constraint gating | 0/32 | 0/32 | 4/32 | Eliminated target failures but increased benign refusal. |

The baseline pressured-minus-plain difference was +28.1 percentage points with a family-clustered 95% interval of +6.3 to +53.1 points. This is the main empirical result already developed in the presentation. Its interpretation remained bounded by one model, synthetic text scenarios, automated judges, a small control cell, and imperfectly sentence-matched pressure contexts. Judge thresholds differed materially, and the strict non-self-judge endpoint did not independently satisfy the registered diagnostic rule.

### Process contribution

The canonical result was stronger because prior failures changed the method. It paired plain and pressured cases within families, retained benign controls, replaced a lexical primary endpoint with semantic judgments, reported family-level uncertainty and judge sensitivity, separated sensitivity scoring from the primary label, and added independent verification. The experiment supported a narrow pressure-robustness observation rather than a general robot-safety claim.

**Primary process evidence:** `week-06/Wk-06-ResearchLog.md`, `week-06/build_w06_bank.py`, `week-06/run_w06_experiment2.py`, `week-06/judge_w06_experiment2.py`, `week-06/test_w06_experiment2.py`, `week-06/verify_w06_independent.py`, and the committed bank, outputs, ratings, metadata, and analysis files.
## How the scripts supported the research process

The scripts were not only delivery utilities. They encoded successive methodological decisions and made corrections auditable.

| Stage | Main scripts | Process role |
| --- | --- | --- |
| Week 3 baseline | `run_w03_baseline.py` | Validated the scenario bank, generated both variants, applied action-aware scoring, and established automated-judge reliability. |
| Week 4 extension | `run_w04_extended.py` | Preserved earlier rows, added Mistral, generated severity-weighted comparisons, and allowed taxonomy reclassification without regenerating model evidence. |
| Week 5 intervention | `run_w05_experiment.py`, `audit_w05_semantics.py` | Enforced a contemporaneous baseline and four-condition ablation, then replayed lexical triggers and recorded the post-outcome semantic sensitivity audit. |
| Preliminary Week 6 | rerun-v2/v3 builders, runners, adjudicators, scorers, freeze and verifier scripts | Progressively corrected masking, family dependence, prompt leakage, target difficulty, scorer behavior, panel composition, and evidence freezing. |
| Canonical Week 6 | `build_w06_bank.py`, `run_w06_experiment2.py`, `judge_w06_experiment2.py`, `scorer_w06.py` | Implemented the fresh paired pressure diagnostic, semantic majority endpoint, sensitivity scorer, and family-level statistical analysis. |
| Integrity and reproduction | `test_w06_experiment2.py`, `verify_w06_independent.py`, notebook | Checked design invariants and recomputed the headline evidence through an implementation independent of the main judge/analysis module. |

Across the six weeks, the implementation pattern moved from a single integrated baseline script toward a more explicit evidence pipeline: bank construction, generation, judging, analysis, integrity tests, independent verification, and reporting. That separation made it possible to identify whether a problem came from model behavior, scenario design, scorer logic, rater behavior, statistical assumptions, or reporting.

## Limitations and open work at the review point

- All scenarios are synthetic and text-only. They do not measure perception, actuation, latency, multimodal ambiguity, or physical consequence.
- The canonical Week 6 generation result uses one public model family and one quantized runtime.
- Endpoint labels are automated. One judge is from the generator’s model family, and strict non-self judging does not independently confirm the registered diagnostic threshold.
- Plain and pressured scenarios are paired by family and boundary but not perfectly sentence-matched.
- The control sample is small, so “low refusal cost” describes the observed 32-control cell rather than a general property.
- Preliminary Week 6 experiments contain useful instrument-development evidence but cannot be treated as replications of the canonical diagnostic because their questions, banks, prompts, panels, and endpoints differ.
- Blinded human review of high-severity responses, a second generator model family, and a tighter context-matched pressure bank remain the highest-value validation steps.

## Process conclusion

The work through the mid-point review did not progress as a straight line from plan to successful experiment. It advanced through repeated narrowing and correction. Broad physical-AI themes became measurable decision questions; a benchmark that initially rewarded caution gained controls for over-refusal; a large taxonomy was refined into actionable mechanisms; an apparently significant prompt gain was rejected after semantic audit; and three preliminary Week 6 iterations were archived after exposing leakage, floor effects, scorer failures, prevalence problems, judge susceptibility, and over-deferral.

The canonical Week 6 result is stronger because those problems were made explicit. Its central observation—that adversarial pressure increased unsafe compliance and that explicit deliberation produced the best tested trade-off—is still bounded by model, benchmark, and judge sensitivity. At the mid-point, the project’s most defensible achievement is the combination of that directional finding with an increasingly rigorous process for deciding what the evidence can and cannot support.

## Compact evidence map

- **Framing:** `week-01/W01_Research_Landscape.md`, `week-01/Wk-01-ResearchLog.md`, `week-02/Wk-02-ResearchLog.md`, `week-02/W02_Literature_Review.md`, `week-02/W02_PIC20_Mapping.md`, and `week-02/W02_Research_Questions.md`.
- **Benchmark and taxonomy:** `week-03/W03_Benchmark_Design.md`, `week-03/run_w03_baseline.py`, `week-04/run_w04_extended.py`, and `week-04/W04_Failure_Analysis.md`.
- **Measurement correction:** `week-05/W05_Results_Memo.md`, `week-05/audit_w05_semantics.py`, and `week-05/W05_Semantic_Audit_Summary.json`.
- **Preliminary Week 6:** the iteration summaries and methodological decisions in this document.
- **Canonical Week 6:** `week-06/Wk-06-ResearchLog.md`, `week-06/W06_Analysis.json`, `week-06/W06_Run_Metadata.json`, `week-06/README.md`, `week-06/W06_Mid_Review_Deck.pptx`, and `week-06/W06_Mid_Review_Speech_Script.md`.
