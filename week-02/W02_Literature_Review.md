# W02 Literature Review: Embodied AI Evaluation, Safety, and Trust

Date: 2026-06-23

## Scope

This review surveys public literature across embodied AI evaluation, deployment safety, and human-robot trust in order to identify specific research gaps that can be operationalized as Week 3 benchmark scenarios and Week 4-6 experiments. The product anchors are Aido Rover for navigation and decision AI and Fari for high-stakes service-robot interaction, with educational service-robot context included in the trust cluster. All claims below are grounded in the public papers cited.

## Cluster A: Foundation Model Evaluation for Embodied AI

### A1. Open X-Embodiment Collaboration et al. (2023), "Open X-Embodiment: Robotic Learning Datasets and RT-X Models"

Citation: Open X-Embodiment Collaboration et al. (2023). Open X-Embodiment: Robotic learning datasets and RT-X models. arXiv.
URL: https://arxiv.org/abs/2310.08864

- Contribution summary: This paper assembles a large cross-institution robot dataset spanning many embodiments, tasks, and skills, then trains RT-X policies to test whether cross-robot transfer can improve downstream performance. It shows that diverse robot experience can produce positive transfer rather than requiring every robot behavior to be learned from scratch. It also establishes a shared data format and evaluation reference point for generalist robot policy research.
- Methodological insight: Cross-embodiment evaluation needs held-out robots, tasks, and environments rather than only in-distribution task success.
- Key limitation: The evaluation is strongest for manipulation policies and does not directly answer outdoor mobile-robot decision making under safety constraints.

### A2. Kim et al. (2024), "OpenVLA: An Open-Source Vision-Language-Action Model"

Citation: Kim et al. (2024). OpenVLA: An open-source vision-language-action model. arXiv.
URL: https://arxiv.org/abs/2406.09246

- Contribution summary: OpenVLA introduces an open 7B-parameter vision-language-action model trained on large-scale robot demonstrations. It shows that a pretrained language and vision backbone can be adapted to robot action and fine-tuned efficiently with LoRA-style methods and quantization. It is especially useful for this internship because it gives a concrete public VLA baseline rather than relying only on closed commercial systems.
- Methodological insight: Efficient fine-tuning and quantized serving should be part of embodied-model evaluation because deployment constraints affect which baselines are realistic.
- Key limitation: The reported tasks are mostly manipulation tasks, leaving mobile patrol, multi-sensor uncertainty, and runtime safety gating underexplored.

### A3. Octo Model Team et al. (2024), "Octo: An Open-Source Generalist Robot Policy"

Citation: Octo Model Team et al. (2024). Octo: An open-source generalist robot policy. arXiv.
URL: https://arxiv.org/abs/2405.12213

- Contribution summary: Octo trains a transformer-based generalist policy on hundreds of thousands of robot trajectories and supports language or goal-image conditioning. It is designed to adapt to new observation and action spaces with limited fine-tuning, which makes it a useful comparison point for platform transfer. Its ablations clarify how architecture, data mixture, and conditioning choices influence generalist robot policies.
- Methodological insight: Benchmark design should separate policy initialization quality from adaptation quality because a generalist model can be useful even when zero-shot performance is weak.
- Key limitation: Octo still focuses on manipulation and does not evaluate whether uncertainty-aware deferral or safety monitoring improves decisions in high-stakes service settings.

### A4. Black et al. (2024), "pi0: A Vision-Language-Action Flow Model for General Robot Control"

Citation: Black et al. (2024). pi0: A vision-language-action flow model for general robot control. arXiv.
URL: https://arxiv.org/abs/2410.24164

- Contribution summary: pi0 proposes a flow-matching VLA architecture for general robot control across multiple robot platforms and dexterous tasks. The paper highlights the data, generalization, and robustness obstacles that remain before robot foundation models become reliable real-world systems. It is relevant to PIC-style research because it treats action generation as a foundation-model problem, not only a classical robotics control problem.
- Methodological insight: Evaluations should track whether action-generation models preserve task performance when language, scene, or embodiment changes.
- Key limitation: The paper does not provide a direct method for confidence calibration, safe fallback, or human-facing explanation during uncertain actions.

### A5. Dey et al. (2024), "ReVLA: Reverting Visual Domain Limitation of Robotic Foundation Models"

Citation: Dey et al. (2024). ReVLA: Reverting visual domain limitation of robotic foundation models. arXiv.
URL: https://arxiv.org/abs/2409.15250

- Contribution summary: ReVLA studies visual out-of-domain generalization in robotic foundation models and finds that existing models can be brittle when the visual domain shifts. The paper argues that adaptation can degrade pretrained visual features and proposes model-merging-based reversal to recover visual generalization. This directly reinforces a central concern for embodied deployment: models must remain reliable as sensors, lighting, and environments change.
- Methodological insight: A useful embodied benchmark should include visual shift cases, not only task variants in familiar scenes.
- Key limitation: The paper focuses on visual generalization and does not connect the failures to downstream safety decisions, operator trust, or calibrated deferral.

### A6. Dissanayake et al. (2025), "How Good are Foundation Models in Step-by-Step Embodied Reasoning?"

Citation: Dissanayake et al. (2025). How good are foundation models in step-by-step embodied reasoning? arXiv.
URL: https://arxiv.org/abs/2509.15293

- Contribution summary: This paper proposes FoMER, a benchmark for evaluating step-by-step reasoning in embodied decision scenarios. It separates perceptual grounding from action reasoning and includes tasks that require physical constraints, safety awareness, and valid next actions. It is useful for Week 3 because it offers a template for scenario-based evaluation rather than only trajectory success metrics.
- Methodological insight: Benchmark scenarios should score multiple dimensions of behavior, including grounding, safety reasoning, and action validity.
- Key limitation: Natural-language embodied reasoning still abstracts away from real robot control loops, sensor drift, and deployment-time uncertainty.

## Cluster B: Safety, Uncertainty, OOD Behavior, and Distribution Shift

### B1. Tolle et al. (2025), "Towards Safe Robot Foundation Models"

Citation: Tolle et al. (2025). Towards safe robot foundation models. arXiv.
URL: https://arxiv.org/abs/2503.07404

- Contribution summary: This paper argues that robot foundation model research has emphasized generalization while under-addressing deployment safety. It adds an ATACOM-based safety layer to constrain a generalist policy's action space and prevent unsafe state transitions. The work is a strong open counterpart to safety oversight because it treats safety as a runtime constraint rather than an evaluation afterthought.
- Methodological insight: Safety evaluation should test whether a constraint mechanism changes actual action selection under risky states.
- Key limitation: The experiments are narrow relative to diverse mobile service-robot contexts and do not evaluate user trust or calibrated uncertainty communication.

### B2. Tolle et al. (2025), "Towards Safe Robot Foundation Models Using Inductive Biases"

Citation: Tolle et al. (2025). Towards safe robot foundation models using inductive biases. arXiv.
URL: https://arxiv.org/abs/2505.10219

- Contribution summary: This follow-up extends the safety-layer argument by emphasizing geometric inductive biases for safe robot foundation models. It claims that safe behavior should not be expected to emerge only from more demonstrations, because behavior cloning has no formal safety guarantee. The paper is relevant because it makes explicit the tradeoff between learned generalist behavior and engineered safety constraints.
- Methodological insight: A benchmark should include cases where a model's nominal task objective conflicts with an explicit safety constraint.
- Key limitation: It shows formal safety for selected tasks but leaves open how to score broader ethical, operational, or human-facing constraints.

### B3. Guerrier, Fouad, and Beltrame (2024), "Learning Control Barrier Functions and their Application in Reinforcement Learning: A Survey"

Citation: Guerrier, Fouad, and Beltrame. (2024). Learning control barrier functions and their application in reinforcement learning: A survey. arXiv.
URL: https://arxiv.org/abs/2404.16879

- Contribution summary: This survey reviews how control barrier functions can enforce safe states during reinforcement learning. It explains why safe RL is hard on real robots: safety functions require domain knowledge, and learned barriers must remain valid under changing dynamics. It is useful here because it clarifies what safety mechanisms can guarantee and where they remain brittle.
- Methodological insight: Safety constraints should be evaluated separately from task reward because a high reward can hide near-violation behavior.
- Key limitation: Barrier-function methods usually require mathematically specified state constraints and do not directly encode ambiguous social or service-robot safety norms.

### B4. Lekeufack et al. (2023), "Conformal Decision Theory: Safe Autonomous Decisions from Imperfect Predictions"

Citation: Lekeufack et al. (2023). Conformal decision theory: Safe autonomous decisions from imperfect predictions. arXiv.
URL: https://arxiv.org/abs/2310.05921

- Contribution summary: Conformal Decision Theory extends conformal prediction from uncertainty sets to calibrated decisions with risk guarantees. It is directly relevant to embodied AI because examples include robot planning around humans and choosing between a nominal policy and a safe backup policy. The paper provides a principled way to ask when an imperfect model should act, defer, or switch policy.
- Methodological insight: Week 3 scenarios can score whether a model's decision to act or defer is calibrated to risk, not only whether the final answer is correct.
- Key limitation: The method assumes access to calibration data and a defined loss/risk function, which may be difficult for heterogeneous service-robot interactions.

### B5. Hodge, Paterson, and Habli (2025), "Out-of-Distribution Detection for Safety Assurance of AI and Autonomous Systems"

Citation: Hodge, Paterson, and Habli. (2025). Out-of-distribution detection for safety assurance of AI and autonomous systems. arXiv.
URL: https://arxiv.org/abs/2510.21254

- Contribution summary: This review frames OOD detection as part of safety assurance across the lifecycle of AI-enabled autonomous systems. It explains why autonomous systems face novel and uncertain situations that cannot be fully specified during development. The paper is important because it connects technical OOD methods to the safety-case problem of arguing that a system remains safe in deployment.
- Methodological insight: OOD behavior should be treated as a safety-assurance signal, not just as a machine-learning classification metric.
- Key limitation: The review is broad and does not prescribe a small benchmark protocol for evaluating VLA or service-robot behavior with public models.

## Cluster C: Human-AI Interaction and Trust Calibration in Service Robots

### C1. Rezaei Khavas, Ahmadzadeh, and Robinette (2020), "Modeling Trust in Human-Robot Interaction: A Survey"

Citation: Rezaei Khavas, Ahmadzadeh, and Robinette. (2020). Modeling trust in human-robot interaction: A survey. arXiv.
URL: https://arxiv.org/abs/2011.04796

- Contribution summary: This survey reviews models of trust in human-robot interaction and argues that trust should be calibrated rather than maximized. It explains the risk of misuse when users overtrust robots and disuse when users undertrust them. The paper provides the conceptual basis for treating user trust as a measurable research variable.
- Methodological insight: Service-robot evaluation should distinguish performance, perceived reliability, and calibrated trust instead of treating trust as a generic positive outcome.
- Key limitation: Many trust models are not operationalized into lightweight benchmarks that can be run with public text or multimodal models.

### C2. Perkins, Rezaei Khavas, and Robinette (2021), "Trust Calibration and Trust Respect: A Method for Building Team Cohesion in Human Robot Teams"

Citation: Perkins, Rezaei Khavas, and Robinette. (2021). Trust calibration and trust respect: A method for building team cohesion in human robot teams. arXiv.
URL: https://arxiv.org/abs/2110.06809

- Contribution summary: This paper proposes that robots should calibrate human trust when trust is misaligned with actual performance, but respect trust when mistrust comes from other human factors. It studies trust calibration cues as a mechanism for adjusting human trust in human-robot teams. The distinction is useful for service robots because not every user hesitation should trigger persuasion.
- Methodological insight: A benchmark can score whether a model communicates limits in a way that aligns trust with system capability rather than simply increasing confidence.
- Key limitation: The work does not evaluate modern LLM/VLM-generated explanations or high-stakes care and security contexts.

### C3. Sanneman and Shah (2020), "Trust Considerations for Explainable Robots: A Human Factors Perspective"

Citation: Sanneman and Shah. (2020). Trust considerations for explainable robots: A human factors perspective. arXiv.
URL: https://arxiv.org/abs/2005.05940

- Contribution summary: This paper connects explainable robot systems to human factors research on trust. It argues that robot explanations should be evaluated for trust calibration, specificity, and the bases of trust rather than only for interpretability. It is relevant because user-facing explanations may be part of safe deferral, escalation, or review workflows.
- Methodological insight: Explanation quality should be scored by whether it supports appropriate reliance in a specific task context.
- Key limitation: The paper is conceptual and does not supply a ready-made scenario set for embodied foundation model evaluation.

### C4. Wald, Puthuveetil, and Erickson (2024), "Do Mistakes Matter? Comparing Trust Responses of Different Age Groups to Errors Made by Physically Assistive Robots"

Citation: Wald, Puthuveetil, and Erickson. (2024). Do mistakes matter? Comparing trust responses of different age groups to errors made by physically assistive robots. arXiv.
URL: https://arxiv.org/abs/2408.13153

- Contribution summary: This study examines how younger and older adults respond to mistakes by physically assistive robots in sensitive tasks. It finds that trust responses depend on both user age and task type, and that older adults may evaluate robots using factors beyond immediate task performance. This paper is directly relevant to service robots in eldercare because it warns against assuming a single trust response model.
- Methodological insight: High-stakes HRI benchmarks should vary user context and task sensitivity because trust effects are not uniform.
- Key limitation: The study focuses on physical assistance tasks and does not test LLM/VLM decision explanations or uncertainty disclosure.

### C5. Mazzola et al. (2025), "Toward an Interaction-Centered Approach to Robot Trustworthiness"

Citation: Mazzola et al. (2025). Toward an interaction-centered approach to robot trustworthiness. arXiv.
URL: https://arxiv.org/abs/2508.13976

- Contribution summary: This position paper argues that robot trustworthiness should be studied through interaction, mutual understanding, human awareness, and transparency. It emphasizes that overtrust and misplaced trust are safety and ethics risks. The paper helps translate technical uncertainty into user-facing behavior, because a robot must communicate what it knows and intends.
- Methodological insight: Trustworthiness evaluation should include both robot transparency and the user's ability to retain control.
- Key limitation: The framework is not yet an empirical benchmark and does not specify measurable thresholds for acceptable trust calibration.

### C6. Lisondra, Benhabib, and Nejat (2025), "Embodied AI with Foundation Models for Mobile Service Robots: A Systematic Review"

Citation: Lisondra, Benhabib, and Nejat. (2025). Embodied AI with foundation models for mobile service robots: A systematic review. arXiv.
URL: https://arxiv.org/abs/2505.20503

- Contribution summary: This systematic review surveys foundation models in mobile service robotics and identifies challenges in sensor fusion, real-time decisions, task generalization, and human-robot interaction. It bridges the foundation-model literature with service-robot deployment contexts such as domestic assistance and healthcare. The paper is important because it makes clear that mobile service robots require more than a single language or vision model.
- Methodological insight: Evaluation should combine model behavior, sensor/scene uncertainty, and human interaction outcomes because service robots fail across those boundaries.
- Key limitation: The review identifies open challenges but does not reduce them to a compact benchmark that can be executed during a 12-week internship.

### C7. Rudenko et al. (2024), "The Child Factor in Child-Robot Interaction: Discovering the Impact of Developmental Stage and Individual Characteristics"

Citation: Rudenko, Rudenko, Lilienthal, Arras, and Bruno. (2024). The child factor in child-robot interaction: Discovering the impact of developmental stage and individual characteristics. arXiv.
URL: https://arxiv.org/abs/2404.13432

- Contribution summary: This paper integrates robot-centered and child-centered perspectives on child-robot interaction and argues that developmental stage and individual characteristics are decisive factors for sustainable, long-term engagement in educational settings. It reviews child-robot interaction outcomes through child-psychology theory and proposes experiment designs that account for how differently children of different ages and dispositions respond to the same robot behavior. It is directly relevant to Senpai-style educational service robots because it shows that a single trust or interaction model cannot be assumed across a young, heterogeneous user population.
- Methodological insight: Educational-robot evaluation should stratify scenarios by user developmental stage and individual characteristics rather than assuming a uniform user, because the same explanation or correction can land very differently across learners.
- Key limitation: The work is oriented toward interaction design and child psychology and does not provide a runnable benchmark for evaluating modern language- or vision-model explanations under uncertainty.

## Research Gap Analysis

### Gap 1: Calibrated embodied deferral under uncertainty

Gap statement: Public embodied AI benchmarks do not yet provide a compact way to test whether a foundation model knows when to act, defer, ask for review, or switch to a safer fallback under sensor, visual, or context shift.

Evidence: OpenVLA (Kim et al., 2024) and Octo (Octo Model Team et al., 2024) demonstrate that generalist robot policies can be trained and adapted, but their evaluations emphasize task success and adaptation more than calibrated deferral. ReVLA (Dey et al., 2024) shows visual OOD brittleness, and Conformal Decision Theory (Lekeufack et al., 2023) provides a decision-calibration framework, but these threads are not combined into a small benchmark for mobile service-robot scenarios.

Method that could address it: Build a Week 3 scenario bank with normal, ambiguous, degraded, and adversarial scene descriptions; score models on action validity, uncertainty acknowledgement, deferral correctness, and unsafe overconfidence.

### Gap 2: Safety constraints for foundation-policy decisions under edge cases

Gap statement: Current work shows safety layers and barrier functions can constrain selected robot policies, but there is limited public evidence on how explicit safety constraints affect foundation-model decisions in diverse, high-level service-robot edge cases.

Evidence: Towards Safe Robot Foundation Models (Tolle et al., 2025) and its inductive-bias follow-up (Tolle et al., 2025) show that safety should not be expected to emerge from demonstrations alone. The control-barrier-function survey (Guerrier, Fouad, and Beltrame, 2024) explains how formal safe-state constraints can work, but these methods map less directly to high-level constraints involving human proximity, privacy, escalation, and operator review.

Method that could address it: Create paired benchmark scenarios with and without explicit safety rules, then compare whether models choose safer actions while preserving task progress. Measure safety violation rate, task-completion preservation, and explanation quality.

### Gap 3: Trust calibration from model explanations in high-stakes service robots

Gap statement: HRI literature shows that trust should be calibrated, but there is little evidence on whether modern language or multimodal models can generate explanations that help users rely appropriately on service robots after uncertain or mistaken decisions.

Evidence: Trust modeling surveys (Rezaei Khavas, Ahmadzadeh, and Robinette, 2020) and trust calibration work (Perkins, Rezaei Khavas, and Robinette, 2021) establish that overtrust and undertrust both harm human-robot teaming. Across the two anchor user populations, assistive-robot error studies in eldercare (Wald, Puthuveetil, and Erickson, 2024) and developmental-stage findings in educational child-robot interaction (Rudenko et al., 2024) both show that trust responses vary sharply by user and task. Explainable-robot work (Sanneman and Shah, 2020) describes trust-specific explanation goals, but these lines do not yet produce an evaluation set for model-generated robot explanations across these heterogeneous service-robot users.

Method that could address it: Design service-robot dialogue and alert scenarios where the model must disclose uncertainty, explain limits, and recommend escalation. Score each response for calibrated reliance, specificity, honesty about uncertainty, and avoidance of inappropriate reassurance.

## Candidate Research Questions for Week 3

1. Can a public foundation model reliably choose defer/review actions in embodied scenarios where scene or sensor information is ambiguous?
2. Do explicit safety constraints reduce unsafe model decisions without causing excessive refusal or task abandonment?
3. Can model-generated explanations calibrate user trust after uncertain or mistaken service-robot behavior?

