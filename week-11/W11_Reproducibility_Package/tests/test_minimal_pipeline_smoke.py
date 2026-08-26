from __future__ import annotations

import json
import importlib.util
import os
import subprocess
import sys
import unittest
import uuid
from pathlib import Path
from unittest import mock


PACKAGE = Path(__file__).resolve().parent.parent
RUNNER = PACKAGE / "run_minimal_pipeline_smoke.py"
SCRATCH = PACKAGE / ".test-tmp"
SCRATCH.mkdir(exist_ok=True)


def load_runner():
    spec = importlib.util.spec_from_file_location("minimal_pipeline_smoke", RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {RUNNER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RUNNER_MODULE = load_runner()


class MinimalPipelineSmokeContractTests(unittest.TestCase):
    def test_plan_only_reports_the_fixed_minimal_scope(self) -> None:
        case = SCRATCH / f"plan-{uuid.uuid4().hex}"
        cache = case / "shared-cache" / "hub"
        output = case / "output"
        completed = subprocess.run(
            [
                sys.executable,
                str(RUNNER),
                "--plan-only",
                "--cache-dir",
                str(cache),
                "--output-dir",
                str(output),
            ],
            cwd=PACKAGE,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        plan = json.loads(completed.stdout)
        self.assertEqual(plan["verification_level"], "minimal_full_pipeline_smoke")
        self.assertEqual(plan["condition"], "common_baseline")
        self.assertEqual(plan["scenario_count"], 1)
        self.assertEqual(plan["generators"], ["mistral", "qwen"])
        self.assertEqual(
            plan["judges"], ["granite8b", "phi4_14b", "falcon3_10b"]
        )
        self.assertEqual(plan["expected_rows"], {
            "generations": 2,
            "judgments": 6,
            "panels": 2,
        })
        self.assertEqual(plan["generation_max_new_tokens"], 64)
        self.assertEqual(Path(plan["cache_dir"]), cache.resolve())
        self.assertEqual(Path(plan["output_dir"]), output.resolve())
        self.assertFalse(output.exists())

    def test_cache_configuration_enforces_offline_shared_cache_use(self) -> None:
        cache = (SCRATCH / "shared-cache" / "hub").resolve()
        with mock.patch.dict(os.environ, {}, clear=True):
            RUNNER_MODULE.configure_offline_cache(cache)
            self.assertEqual(os.environ["HF_HOME"], str(cache.parent))
            self.assertEqual(os.environ["HF_HUB_CACHE"], str(cache))
            self.assertEqual(os.environ["HUGGINGFACE_HUB_CACHE"], str(cache))
            self.assertEqual(os.environ["HF_HUB_OFFLINE"], "1")
            self.assertEqual(os.environ["TRANSFORMERS_OFFLINE"], "1")

    def test_validation_requires_the_complete_two_six_two_product(self) -> None:
        models = {
            "mistral": (
                "mistralai/Mistral-7B-Instruct-v0.3",
                "a" * 40,
            ),
            "qwen": ("Qwen/Qwen2.5-7B-Instruct", "b" * 40),
        }
        judges = {
            "granite8b": ("ibm-granite/granite-3.3-8b-instruct", "c" * 40),
            "phi4_14b": ("microsoft/phi-4", "d" * 40),
            "falcon3_10b": ("tiiuae/Falcon3-10B-Instruct", "e" * 40),
        }
        generations = [
            {
                "response_id": f"response-{name}",
                "generator_model": model_id,
                "generator_revision": revision,
                "condition": "common_baseline",
                "scenario_id": "PF-01",
                "seed": 20260731,
                "response": "Decision action: WITHHOLD\nRationale: Boundary not met.",
            }
            for name, (model_id, revision) in models.items()
        ]
        judgments = [
            {
                "response_id": generation["response_id"],
                "judge_name": judge_name,
                "judge_model": model_id,
                "judge_revision": revision,
                "parse_success": 1,
            }
            for generation in generations
            for judge_name, (model_id, revision) in judges.items()
        ]
        panels = [
            {"response_id": row["response_id"], "parse_success": 1}
            for row in generations
        ]

        counts = RUNNER_MODULE.validate_pipeline_rows(
            generations,
            judgments,
            panels,
            expected_generators={value for value in models.values()},
            expected_judges={
                name: value for name, value in judges.items()
            },
        )
        self.assertEqual(counts, {"generations": 2, "judgments": 6, "panels": 2})

        judgments[-1]["parse_success"] = 0
        with self.assertRaisesRegex(AssertionError, "parsed judgments"):
            RUNNER_MODULE.validate_pipeline_rows(
                generations,
                judgments,
                panels,
                expected_generators={value for value in models.values()},
                expected_judges={name: value for name, value in judges.items()},
            )

    def test_orchestration_runs_generation_then_each_judge_then_panel(self) -> None:
        events: list[str] = []
        generations = [
            {"response_id": "response-mistral"},
            {"response_id": "response-qwen"},
        ]

        def generate_stage():
            events.append("generation")
            return generations, {"seconds": 1.0}

        def judge_stage(name, source):
            self.assertIs(source, generations)
            events.append(name)
            return [
                {"response_id": row["response_id"], "judge_name": name}
                for row in source
            ], {"seconds": 2.0}

        def aggregate_stage(source, ratings):
            self.assertIs(source, generations)
            self.assertEqual(len(ratings), 6)
            events.append("panel")
            return [
                {"response_id": row["response_id"], "parse_success": 1}
                for row in source
            ]

        rows, ratings, panels, metadata = RUNNER_MODULE.orchestrate_minimal_pipeline(
            generate_stage, judge_stage, aggregate_stage
        )
        self.assertIs(rows, generations)
        self.assertEqual(len(ratings), 6)
        self.assertEqual(len(panels), 2)
        self.assertEqual(
            events,
            ["generation", "granite8b", "phi4_14b", "falcon3_10b", "panel"],
        )
        self.assertEqual(set(metadata["judges"]), set(RUNNER_MODULE.JUDGES))

    def test_existing_output_directory_is_rejected(self) -> None:
        output = SCRATCH / f"existing-{uuid.uuid4().hex}"
        output.mkdir()
        try:
            with self.assertRaisesRegex(FileExistsError, "output directory already exists"):
                RUNNER_MODULE.prepare_output_directory(output)
        finally:
            output.rmdir()

    def test_generation_summary_discloses_token_cap_rows(self) -> None:
        summary = RUNNER_MODULE.summarize_generation_rows(
            [
                {
                    "response": "Complete response.",
                    "generated_token_count": 64,
                    "hit_max_new_tokens": True,
                },
                {
                    "response": "Another complete response.",
                    "generated_token_count": 62,
                    "hit_max_new_tokens": False,
                },
            ]
        )
        self.assertEqual(summary["nonblank_rows"], 2)
        self.assertEqual(summary["rows_at_token_cap"], 1)
        self.assertEqual(summary["generated_token_counts"], [64, 62])


if __name__ == "__main__":
    unittest.main(verbosity=2)
