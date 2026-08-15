# W01 Research Landscape: Physical AI and PIC 2.0

Date: 2026-06-13

## Scope and Sources

This brief anchors Week 1 of the AI Research Intern program: physical AI landscape, InGen's Origami AI / PIC 2.0 framework, open-literature counterparts for the six PIC 2.0 model classes, and candidate research themes for Weeks 4-9.

Primary InGen source: the public Origami AI page, https://www.ingendynamics.com/origami-paper.html, the reference for all PIC 2.0 model names and roles used in this brief. It defines PIC 2.0 as a six-model on-device cognitive pipeline (AMDC -> STUM -> HTD-IRL -> GRPO -> SEOM -> CRL-MRS), positioned as a VLA backbone augmented with calibrated uncertainty (STUM), constitutional safety (SEOM), and fleet coordination (CRL-MRS); the per-cycle decision path (AMDC -> STUM -> HTD-IRL -> GRPO -> SEOM) runs edge-only in roughly 12.5 ms. The local internship plan sets the Week 1 scope and the Aido Rover product anchor, and the technical mappings below draw on public papers.

## Anchor References

1. Kim et al. (2024), "OpenVLA: An Open-Source Vision-Language-Action Model"
   URL: https://arxiv.org/abs/2406.09246
   Annotation: OpenVLA is the best VLA anchor because it is open, 7B-parameter scale, trained on 970k robot demonstrations, and explicitly studies efficient fine-tuning with LoRA and quantization. It shows the current physical AI pattern: start with internet-scale visual-language priors, add action representation, and fine-tune on robot data.

2. Tolle et al. (2025), "Towards Safe Robot Foundation Models"
   URL: https://arxiv.org/abs/2503.07404
   Annotation: This is the strongest safety anchor because it treats safety as a deployment requirement for generalist robot policies. Its ATACOM-based safety layer constrains action space transitions, which is directly relevant to SEOM-style safety oversight.

3. Ji et al. (2023/2025), "AI Alignment: A Comprehensive Survey"
   URL: https://arxiv.org/abs/2310.19852
   Annotation: The survey provides the deployed-systems alignment frame: robustness, interpretability, controllability, and ethicality. That frame is useful because physical AI failures include unsafe action, poor calibration, hidden objective mismatch, and weak human oversight.

4. InGen Dynamics (2026), "Origami AI - Physical Intelligence Platform"
   URL: https://www.ingendynamics.com/origami-paper.html
   Annotation: The public Origami page defines PIC 2.0's six model roles and reports public platform claims: a six-model pipeline, edge execution, safety-critical on-device functions, and deployment metrics across Fari/Aido eldercare, Senpai education, Carry & Go logistics, Sentinel Prime AI security, and humanoid manufacturing.

5. Khanda et al. (2025), "Extending Group Relative Policy Optimization to Continuous Control"
   URL: https://arxiv.org/abs/2507.19555
   Annotation: This is the GRPO bridge for robotics because it adapts group-relative policy optimization from discrete/token settings toward continuous robotic control through trajectory clustering, state-aware advantages, and regularized updates.

6. Sohn et al. (2025), "SNOW: Spatio-Temporal Scene Understanding with World Knowledge for Open-World Embodied Reasoning"
   URL: https://arxiv.org/abs/2512.16461
   Annotation: This satisfies the Week 1 scene-understanding requirement and complements STUM by showing how temporal, geometric, and semantic state can become a queryable 4D scene graph for embodied reasoning.

7. Palan et al. (2019), "Learning Reward Functions by Integrating Human Demonstrations and Preferences"
   URL: https://arxiv.org/abs/1906.08928
   Annotation: DemPref is a strong HTD-IRL-adjacent anchor because it combines demonstrations with preference queries to infer rewards more efficiently than either demonstrations or preferences alone.

8. Goeckner et al. (2024), "Graph Neural Network-based Multi-agent Reinforcement Learning for Resilient Distributed Coordination of Multi-Robot Systems"
   URL: https://arxiv.org/abs/2403.13093
   Annotation: MAGEC is the clearest CRL-MRS counterpart because it combines GNN communication with multi-agent PPO for distributed multi-robot coordination under attrition, partial observability, and communication disturbance.

Supporting technical references used for the mappings:

- Lekeufack et al. (2023), "Conformal Decision Theory: Safe Autonomous Decisions from Imperfect Predictions" — https://arxiv.org/abs/2310.05921 (supports STUM mapping)
- Guerrier et al. (2024), "Learning Control Barrier Functions and their Application in Reinforcement Learning: A Survey" — https://arxiv.org/abs/2404.16879 (supports SEOM mapping)
- Mishra and Saripalli (2022), "Extrinsic Calibration of LiDAR, IMU and Camera" — https://arxiv.org/abs/2205.08701 (supports AMDC mapping)
- Chen et al. (2023), "Multi-task Hierarchical Adversarial Inverse Reinforcement Learning" — https://arxiv.org/abs/2305.12633 (supports HTD-IRL mapping)
- Ecosystem VLA / foundation-policy context: pi0 (https://arxiv.org/abs/2410.24164); GR00T N1 (https://arxiv.org/abs/2503.14734); Gemini Robotics (https://arxiv.org/abs/2503.20020).

## Physical AI Ecosystem Map

The physical AI ecosystem has five layers:

- Hardware: humanoids, mobile manipulators, warehouse robots, security robots, eldercare robots, education robots, rovers, drones, and sensor-rich edge devices.
- Data: teleoperation traces, simulation rollouts, human demonstrations, human preference labels, human video, egocentric video, synthetic data, and deployment telemetry.
- Foundation policies: VLA models, diffusion/flow action models, goal-conditioned RL, GRPO-style policy optimization, imitation learning, hierarchical IRL, and world-model/model-predictive control.
- Embodied state and safety: 3D/4D scene representations, calibrated uncertainty, sensor calibration, safety constraints, control barrier functions, runtime monitors, human override, and audit trails.
- Fleet operations: multi-robot task allocation, communication-aware coordination, failure recovery, cross-robot calibration sharing, and deployment observability.

Key players and platforms:

- Google DeepMind: RT-2 and Gemini Robotics demonstrate how large VLMs can be grounded into robot action and embodied reasoning.
- Stanford/Berkeley/Open X-Embodiment ecosystem: OpenVLA, Octo, and open robot datasets provide reproducible baselines for VLA research.
- Physical Intelligence: pi0/pi0.5 emphasizes flow-matching action generation and cross-embodiment manipulation.
- NVIDIA: Isaac, Cosmos, and GR00T N1 combine simulation, synthetic data, humanoid policies, and deployment tooling.
- Figure AI and humanoid companies: dual-system VLA control splits high-level reasoning from fast whole-body action.
- Academic robotics: safe RL, conformal decision theory, sensor calibration, hierarchical IRL, and GNN-MARL supply the methods that map most cleanly to PIC 2.0's six modules.

The ecosystem trend is modular integration. A production physical AI system is not just a VLA. It needs action generation, uncertainty estimation, sensor calibration, safety constraints, task decomposition, fleet coordination, evaluation, and human oversight. The research bottleneck is no longer only "can the model act?" but "can the system act safely, know when it is uncertain, adapt to sensors and environment, and coordinate with other agents?"

## InGen Product Portfolio: AI Research Angles

| Platform | Public / plan positioning | Week 1 AI research angle |
| --- | --- | --- |
| Origami AI / PIC 2.0 | Public physical intelligence platform with six-model cognitive pipeline. | Foundation-model systems analysis: how GRPO, STUM, SEOM, AMDC, HTD-IRL, and CRL-MRS compose into one physical AI stack. |
| Aido Rover | Outdoor patrol/navigation and decision AI anchor in the internship plan; public Origami page also discusses rover coverage in CRL-MRS context. | Rover autonomy requires AMDC sensor calibration, STUM uncertainty gating, SEOM safety constraints, HTD-IRL task decomposition, and CRL-MRS fleet coordination. |
| Fari / Aido eldercare | Public page lists eldercare medication reminders, fall detection, companionship, and 97.3% task completion. | High-stakes human interaction: empathy calibration, privacy-sensitive responses, human override, and stronger SEOM safety weighting for vulnerable users. |
| Senpai education | Public page lists K-12 education, teaching policy, SEND adaptation, and safeguarding detection. | Pedagogical behavior: adaptive content selection, correction accuracy, safeguarding, uncertainty-aware escalation, and evaluation of age-sensitive failures. |
| Sentinel Prime AI | Public page lists security anomaly detection, sensor fusion, and false-alert reduction. | Robust detection under distribution shift: STUM confidence gating, AMDC sensor drift correction, adversarial robustness, and false-negative risk analysis. |
| Carry & Go logistics | Public page lists autonomous delivery and CRL-MRS fleet efficiency gains. | Fleet coordination: CRL-MRS task allocation, congestion avoidance, communication disturbance, and calibration sharing across robot units. |
| Humanoid manufacturing | Public page lists manipulation/locomotion as in development with latency still in progress. | High-dimensional control: GRPO policy optimization, AMDC calibration, SEOM constraints, and latency-sensitive control-loop evaluation. |

## PIC 2.0 Open-Literature Mapping

| PIC 2.0 model | Closest open-literature counterpart | Structural similarity | Key architectural difference | Boundary research question |
| --- | --- | --- | --- | --- |
| GRPO - Group Relative Policy Optimisation (Decision Maker) | Continuous-control GRPO plus constrained/goal-conditioned RL | Both optimize policies by comparing candidate trajectories or actions under reward and constraint signals. | Public GRPO work is still emerging for continuous robot control; Origami adds constitutional/safety terms directly into policy learning. | Can group-relative advantage estimation stay stable when safety penalties dominate sparse task rewards? |
| STUM - Spatiotemporal Uncertainty Model (Confidence Meter) | Conformal prediction / conformal decision theory | Both use calibrated uncertainty to decide when to act, defer, ask a human, or trigger fallback. | Open conformal methods usually calibrate predictors or decisions; Origami frames STUM as a real-time spatial-plus-temporal confidence module inside the robot loop. | How should conformal guarantees degrade under non-exchangeable robot deployment data, stale observations, and sensor drift? |
| SEOM - Self-Supervised Ethical Oversight Mechanism (Safety Guardian) | Safe RL, control barrier functions, constrained policy optimization, differentiable safety costs | Both try to make unsafe behavior unreachable or heavily penalized during learning rather than merely filtered after action selection. | CBF/safe-RL methods usually encode mathematical state constraints; Origami frames safety as domain-specific ethical rules embedded as penalty gradients. | Can high-level ethical or domain rules be made differentiable without hiding brittle hand-coded reward hacks? |
| AMDC - Adaptive Multi-Domain Calibration (Sensor Calibrator) | Online multi-sensor calibration and adaptive sensor-fusion estimation | Both maintain reliable perception by correcting sensor drift, extrinsic mismatch, environmental noise, and calibration uncertainty. | Open calibration work often treats calibration as a perception subsystem; Origami positions AMDC as a 100 Hz shared calibration engine feeding the whole cognitive pipeline. | Which calibration failures most strongly propagate into policy failures, and can they be detected early enough for safe fallback? |
| HTD-IRL - Hierarchical Task Decomposition via IRL (Task Planner) | Hierarchical IRL / multi-task hierarchical adversarial IRL | Both infer reusable task structure, rewards, or sub-skills from demonstrations for long-horizon goals. | Many open methods learn hierarchy offline; Origami frames HTD-IRL as an online task planner that replans when uncertainty is too high. | Can task decomposition remain interpretable and correct when demonstrations are sparse, inconsistent, or user-specific? |
| CRL-MRS - Cooperative Reinforcement Learning for Multi-Robot Systems (Team Coordinator) | GNN-based MARL for resilient multi-robot coordination, e.g., MAGEC | Both coordinate multiple robots under partial observability, communication constraints, shared objectives, and possible agent loss. | MAGEC is a research MARL policy in simulation; Origami frames CRL-MRS as deployment fleet coordination with calibration sharing and fast onboarding. | How can a fleet learn cooperative policies without brittle conventions that fail under robot loss, network delay, or heterogeneous hardware? |

The hardest mapping is SEOM. "Self-supervised ethical oversight" overlaps safe RL, CBFs, constrained optimization, constitutional AI, and runtime shielding, but none is a perfect open-literature equivalent. The distinctive Origami claim is training-time safety through differentiable penalty gradients. The research boundary is whether high-level safety or ethical rules can be encoded precisely enough to improve behavior without becoming opaque reward engineering.

## Candidate Research Themes for Weeks 4-9

1. Safety-constrained GRPO/VLA adaptation for rover-scale control
   Gap: VLA models show generalization and safe-RL papers show constraint mechanisms, but there is little public evidence on how GRPO-style post-training behaves when SEOM-style differentiable safety penalties dominate sparse physical rewards.

2. Calibrated uncertainty gates for physical AI decisions
   Gap: conformal prediction can provide statistical confidence bounds, but deployed robots face non-stationary sensor streams, stale observations, and calibration drift. The tractable Week 4-9 question is when a robot should act, slow down, ask a human, or replan based on STUM-like uncertainty.

3. Human demonstration to fleet behavior transfer
   Gap: IRL/preference learning can infer individual rewards and MARL can coordinate fleets, but the bridge from human demonstrations to cooperative multi-robot conventions remains underdeveloped. The tractable question is whether HTD-IRL can produce shared subtask structure that CRL-MRS agents can use without overfitting to one operator or deployment layout.

## Week 1 Self-Check

- Six PIC 2.0 counterparts are structural, not name-only: GRPO -> continuous constrained policy optimization; STUM -> conformal uncertainty and decision calibration; SEOM -> safe RL / CBF / constrained policy learning; AMDC -> online sensor calibration and adaptive fusion; HTD-IRL -> hierarchical IRL; CRL-MRS -> GNN-MARL multi-robot coordination.
- The three candidate themes identify gaps rather than broad topics: safety-constrained post-training, calibrated uncertainty gates under deployment shift, and demo-to-fleet transfer.
- `W01_env_check.ipynb` runs end-to-end in the local Python 3.11 CUDA environment and verifies PyTorch/CUDA, HuggingFace, PEFT, LangChain, W&B, NumPy, pandas, and SciPy.

## Problems and feedbacks

- Need more details for PIC-Literature mapping, not just giving names.
- Need to identify research gaps, not just listing topics.