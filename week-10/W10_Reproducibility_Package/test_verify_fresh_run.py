"""Synthetic-artifact tests for the fresh Tier 2 evidence verifier."""

from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
import zlib


PACKAGE = Path(__file__).resolve().parent
MODULE_PATH = PACKAGE / "verify_fresh_run.py"
SPEC = importlib.util.spec_from_file_location("verify_fresh_run", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _png_chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n"
    + _png_chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0))
    + _png_chunk(b"IDAT", zlib.compress(b"\x00\x00\x00\x00\xff"))
    + _png_chunk(b"IEND", b"")
)


class FreshRunVerifierTests(unittest.TestCase):
    """Exercise the verifier against a complete, isolated synthetic run tree."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(dir=PACKAGE.parents[1] / "tmp")
        self.root = Path(self.temporary.name)
        self.receipt_path = self.root / "run-receipt.json"
        self.lock = {
            "generator/a": {"revision": "a" * 40},
            "generator/b": {"revision": "b" * 40},
            "judge/a": {"revision": "c" * 40},
            "judge/b": {"revision": "d" * 40},
            "judge/c": {"revision": "e" * 40},
            "judge/d": {"revision": "f" * 40},
        }
        self._write_json("week-10/W10_Reproducibility_Package/model_lock.json", {
            "schema_version": "ingen-model-lock-v1", "models": self.lock,
        })
        self._write_complete_artifacts()
        self._write_receipt()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _path(self, relative: str) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def _write_json(self, relative: str, payload: object) -> None:
        self._path(relative).write_text(json.dumps(payload), encoding="utf-8")

    def _write_jsonl(self, relative: str, count: int, *, row: dict[str, object] | None = None) -> None:
        path = self._path(relative)
        with path.open("w", encoding="utf-8") as handle:
            for index in range(count):
                record = {
                    key: value.format(index=index) if isinstance(value, str) else value
                    for key, value in (row or {}).items()
                }
                handle.write(json.dumps({"index": index, **record}) + "\n")

    def _mutate_jsonl_row(
        self,
        relative: str,
        index: int,
        *,
        updates: dict[str, object] | None = None,
        remove: tuple[str, ...] = (),
    ) -> None:
        path = self.root / relative
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        for field in remove:
            rows[index].pop(field, None)
        rows[index].update(updates or {})
        path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")

    def _write_csv(self, relative: str, count: int, *, fields: tuple[str, ...], row: dict[str, str]) -> None:
        with self._path(relative).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for index in range(count):
                writer.writerow({
                    "index": index,
                    **{key: value.format(index=index) for key, value in row.items()},
                })

    def _write_w07_ratings(self) -> None:
        fields = (
            "index", "response_id", "generator_model", "condition", "scenario_id", "seed",
            "judge_model", "judge_revision", "raw_judgment",
        )
        judges = ("judge/a", "judge/b", "judge/c")
        with self._path("week-07/W07_Judge_Ratings.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for index in range(14400):
                response_index = index // 3
                judge = judges[index % 3]
                generator = ("generator/a", "generator/b")[response_index % 2]
                writer.writerow({
                    "index": index, "response_id": f"response-{response_index}",
                    "generator_model": generator, "condition": "baseline",
                    "scenario_id": f"w07-{response_index}", "seed": response_index,
                    "judge_model": judge, "judge_revision": self.lock[judge]["revision"],
                    "raw_judgment": f"judgment-{index}",
                })

    def _write_w07_raw(self) -> None:
        with self._path("week-07/W07_Raw_Model_Outputs.jsonl").open("w", encoding="utf-8") as handle:
            for index in range(4800):
                generator = ("generator/a", "generator/b")[index % 2]
                handle.write(json.dumps({
                    "index": index, "response_id": f"response-{index}",
                    "generator_model": generator, "generator_revision": self.lock[generator]["revision"],
                    "condition": "baseline", "scenario_id": f"w07-{index}", "seed": index,
                    "response": f"response-{index}",
                }) + "\n")

    def _write_w07_results(self) -> None:
        fields = ("index", "response_id", "generator_model", "generator_revision", "condition", "scenario_id", "seed", "parse_success", "panel_action", "majority_failure")
        with self._path("week-07/W07_Results.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for index in range(4800):
                generator = ("generator/a", "generator/b")[index % 2]
                writer.writerow({
                    "index": index, "response_id": f"response-{index}",
                    "generator_model": generator, "generator_revision": self.lock[generator]["revision"],
                    "condition": "baseline", "scenario_id": f"w07-{index}", "seed": index,
                    "parse_success": "1", "panel_action": "WITHHOLD", "majority_failure": "0",
                })

    def _replace_csv_row(self, relative: str, index: int, updates: dict[str, str]) -> None:
        path = self.root / relative
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            fields = tuple(reader.fieldnames or ())
            rows = list(reader)
        rows[index].update(updates)
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    def _set_unparsed_week7_results(self, count: int) -> None:
        path = self.root / "week-07/W07_Results.csv"
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            fields = tuple(reader.fieldnames or ())
            rows = list(reader)
        for row in rows[:count]:
            row.update({"parse_success": "0", "panel_action": "", "majority_failure": ""})
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    def _write_complete_artifacts(self) -> None:
        for relative, count, row in (
            ("week-03/W03_Raw_Model_Outputs.jsonl", 144, {"model_key": "generator-a", "model_id": "generator/a", "model_revision": self.lock["generator/a"]["revision"], "scenario_id": "w03-{index}", "variant": "original", "response": "response-{index}"}),
            ("week-04/W04_Raw_Model_Outputs.jsonl", 216, {"model_key": "generator-a", "model_id": "generator/a", "model_revision": self.lock["generator/a"]["revision"], "scenario_id": "w04-{index}", "variant": "original", "response": "response-{index}"}),
            ("week-05/W05_Raw_Model_Outputs.jsonl", 288, {"condition": "baseline", "prompt_version": "w05-v1", "model_key": "mistral", "model_id": "generator/a", "model_revision": self.lock["generator/a"]["revision"], "scenario_id": "w05-{index}", "variant": "original", "response": "response-{index}"}),
            ("week-06/W06_Raw_Model_Outputs.jsonl", 384, {"schedule_index": "{index}", "condition": "baseline", "model_revision": self.lock["generator/a"]["revision"], "scenario_id": "w06-{index}", "response": "response-{index}"}),
        ):
            self._write_jsonl(relative, count, row=row)
        self._write_csv("week-06/W06_Judge_Ratings.csv", 384, fields=("index", "condition", "scenario_id", "qwen_label", "qwen_confidence", "qwen_rationale", "phi_label", "phi_confidence", "phi_rationale", "mistral_self_label", "mistral_self_confidence", "mistral_self_rationale"), row={"condition": "baseline", "scenario_id": "w06-{index}", "qwen_label": "0", "qwen_confidence": "high", "qwen_rationale": "qwen-{index}", "phi_label": "0", "phi_confidence": "high", "phi_rationale": "phi-{index}", "mistral_self_label": "0", "mistral_self_confidence": "high", "mistral_self_rationale": "mistral-{index}"})
        self._write_w07_ratings()
        self._write_w07_raw()
        self._write_w07_results()
        self._write_json("week-04/W04_Run_Metadata.json", {
            "selected_model": "generator/a", "selected_model_revision": self.lock["generator/a"]["revision"],
        })
        self._write_json("week-05/W05_Run_Metadata.json", {
            "model_key": "mistral", "model_id": "generator/a", "model_revision": self.lock["generator/a"]["revision"],
        })
        self._write_json("week-06/W06_Run_Metadata.json", {
            "model_id": "generator/a", "model_revision": self.lock["generator/a"]["revision"],
        })
        self._write_json("week-06/W06_Analysis.json", {
            "judges": ["judge/a", "judge/b", "judge/c"],
            "judge_revisions": {
                "first": self.lock["judge/a"]["revision"],
                "second": self.lock["judge/b"]["revision"],
                "third": self.lock["judge/c"]["revision"],
            },
        })
        self._write_json("week-07/W07_Run_Metadata.json", {
            "generators": [
                {"id": "generator/a", "revision": self.lock["generator/a"]["revision"]},
                {"id": "generator/b", "revision": self.lock["generator/b"]["revision"]},
            ],
            "judges": [
                {"id": "judge/a", "revision": self.lock["judge/a"]["revision"]},
                {"id": "judge/b", "revision": self.lock["judge/b"]["revision"]},
                {"id": "judge/c", "revision": self.lock["judge/c"]["revision"]},
            ],
        })
        self._write_jsonl("week-07/W07_Preflight_Raw_Model_Outputs.jsonl", 1)
        self._write_csv("week-07/W07_Judge_Gold_Ratings.csv", 1, fields=("index",), row={})
        for stem in (
            "W07_Figure1_Common_Baseline_Cross_Model",
            "W07_Figure2_Prompt_Safety_and_Control_Cost",
            "W07_Figure3_Seed_Variability_and_Judge_Agreement",
        ):
            self._path(f"week-07/figures/{stem}.png").write_bytes(PNG_BYTES)
            self._path(f"week-07/figures/{stem}.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"/>', encoding="utf-8")
        self._write_json("week-07/W07_Analysis_Notebook.ipynb", {
            "cells": [
                {"cell_type": "code", "execution_count": index, "outputs": [{"output_type": "stream", "text": "ok"}]}
                for index in range(1, 11)
            ],
        })
        for relative, payload in (
            ("week-08/W08_Pressure_Cue_Audit.json", {"schema_version": "w08-pressure-cue-audit-v1", "status": "post_outcome_exploratory"}),
            ("week-08/W08_Pressure_Cue_Audit.md", "# Week 8 audit\n\nThis fresh analysis records substantive findings."),
            ("week-09/W09_Paper_Tables.md", "# Week 9 tables\n\n| Evidence | Value |\n| --- | --- |\n| Rows | 4800 |"),
            ("week-10/W10_Judge_Sensitivity.json", {"schema_version": "w10-judge-sensitivity-v2", "inputs": [{"path": "week-07/W07_Results.csv"}]}),
        ):
            if isinstance(payload, str):
                self._path(relative).write_text(payload, encoding="utf-8")
            else:
                self._write_json(relative, payload)
        for stem in ("W09_Figure2_Prompt_Safety_and_Control_Cost", "W09_Figure3_Seed_Variability_and_Judge_Agreement"):
            self._path(f"week-09/figures/{stem}.png").write_bytes(PNG_BYTES)
            self._path(f"week-09/figures/{stem}.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"/>', encoding="utf-8")

    def _write_receipt(self, *, incomplete: str | None = None) -> None:
        stages = []
        for name in MODULE.FULL_STAGE_NAMES_BEFORE_VERIFY:
            stages.append({"name": name, "status": "passed", "returncode": 0})
        if incomplete is not None:
            stages = [entry for entry in stages if entry["name"] != incomplete]
        self.receipt_path.write_text(json.dumps({
            "source_commit": "f" * 40,
            "mode": "full",
            "status": "incomplete",
            "verification_pending": True,
            "stages": stages,
        }), encoding="utf-8")

    def test_complete_tree_writes_complete_verification_and_receipt(self) -> None:
        # Mutation caught: a verifier that only inspects receipt state could complete without fresh evidence.
        result = MODULE.verify(self.root, self.receipt_path)

        evidence = json.loads((self.root / "fresh-verification.json").read_text(encoding="utf-8"))
        receipt = json.loads(self.receipt_path.read_text(encoding="utf-8"))
        self.assertEqual(result["status"], "complete")
        self.assertEqual(evidence["schema_version"], "ingen-fresh-verification-v1")
        self.assertEqual(evidence["checked_counts"], MODULE.EXPECTED_COUNTS)
        self.assertEqual(evidence["checked_row_counts"]["week06_judge_ratings"], 384)
        self.assertEqual(len(evidence["artifact_sha256"]), len(MODULE.REQUIRED_ARTIFACTS))
        self.assertEqual(receipt["status"], "complete")
        self.assertFalse(receipt["verification_pending"])

    def test_missing_required_artifact_keeps_receipt_incomplete(self) -> None:
        # Mutation caught: absent derived evidence must not leave a complete run receipt behind.
        (self.root / "week-10/W10_Judge_Sensitivity.json").unlink()

        with self.assertRaisesRegex(MODULE.VerificationError, "W10_Judge_Sensitivity"):
            MODULE.verify(self.root, self.receipt_path)

        receipt = json.loads(self.receipt_path.read_text(encoding="utf-8"))
        self.assertEqual(receipt["status"], "incomplete")
        self.assertTrue(receipt["verification_pending"])
        self.assertFalse((self.root / "fresh-verification.json").exists())

    def test_wrong_planned_count_is_rejected(self) -> None:
        # Mutation caught: accepting a partial Week 7 generation would misrepresent inference evidence.
        self._write_jsonl("week-07/W07_Raw_Model_Outputs.jsonl", 4799)

        with self.assertRaisesRegex(MODULE.VerificationError, "week07_raw_generations"):
            MODULE.verify(self.root, self.receipt_path)

    def test_missing_model_revision_is_rejected(self) -> None:
        # Mutation caught: model identities without immutable revisions cannot support a fresh run claim.
        self._write_json("week-05/W05_Run_Metadata.json", {"model_id": "generator/a"})

        with self.assertRaisesRegex(MODULE.VerificationError, "model revision"):
            MODULE.verify(self.root, self.receipt_path)

    def test_schema_less_generation_rows_are_rejected_even_when_metadata_is_valid(self) -> None:
        # Mutation caught: another artifact's metadata must not authenticate schema-less Week 3 rows.
        self._write_jsonl("week-03/W03_Raw_Model_Outputs.jsonl", 144)

        with self.assertRaisesRegex(MODULE.VerificationError, "week03_raw_generations.*model"):
            MODULE.verify(self.root, self.receipt_path)

    def test_week5_row_model_key_must_match_metadata(self) -> None:
        # Mutation caught: a swapped per-row model identity invalidates Week 5 even if its metadata is locked.
        self._write_jsonl("week-05/W05_Raw_Model_Outputs.jsonl", 288, row={
            "condition": "baseline", "prompt_version": "w05-v1", "model_key": "swapped",
            "model_id": "generator/a", "model_revision": self.lock["generator/a"]["revision"],
            "scenario_id": "w05-{index}", "variant": "original", "response": "response-{index}",
        })

        with self.assertRaisesRegex(MODULE.VerificationError, "week05_raw_generations.*model_key"):
            MODULE.verify(self.root, self.receipt_path)

    def test_week5_row_requires_model_id(self) -> None:
        # Mutation caught: one anonymous raw row cannot inherit model identity from run metadata.
        self._mutate_jsonl_row(
            "week-05/W05_Raw_Model_Outputs.jsonl", 137, remove=("model_id",),
        )

        with self.assertRaisesRegex(MODULE.VerificationError, "week05_raw_generations.*model_id"):
            MODULE.verify(self.root, self.receipt_path)

    def test_week5_row_requires_model_revision(self) -> None:
        # Mutation caught: one mutable raw row cannot inherit the locked revision from run metadata.
        self._mutate_jsonl_row(
            "week-05/W05_Raw_Model_Outputs.jsonl", 137, remove=("model_revision",),
        )

        with self.assertRaisesRegex(MODULE.VerificationError, "week05_raw_generations.*model_revision"):
            MODULE.verify(self.root, self.receipt_path)

    def test_week5_row_model_pair_must_match_the_lock(self) -> None:
        # Mutation caught: a row cannot pair the registered model ID with another model's revision.
        self._mutate_jsonl_row(
            "week-05/W05_Raw_Model_Outputs.jsonl",
            137,
            updates={"model_revision": self.lock["generator/b"]["revision"]},
        )

        with self.assertRaisesRegex(MODULE.VerificationError, "week05_raw_generations row 138"):
            MODULE.verify(self.root, self.receipt_path)

    def test_week5_row_locked_pair_must_match_model_key_metadata(self) -> None:
        # Mutation caught: a lock-valid alternate model pair cannot be swapped into one row under the run's model_key.
        self._mutate_jsonl_row(
            "week-05/W05_Raw_Model_Outputs.jsonl",
            137,
            updates={
                "model_id": "generator/b",
                "model_revision": self.lock["generator/b"]["revision"],
            },
        )

        with self.assertRaisesRegex(MODULE.VerificationError, "week05_raw_generations.*model_id"):
            MODULE.verify(self.root, self.receipt_path)

    def test_week6_raw_revision_must_match_run_metadata(self) -> None:
        # Mutation caught: a swapped raw-generation revision cannot be rescued by valid run metadata.
        self._write_jsonl("week-06/W06_Raw_Model_Outputs.jsonl", 384, row={
            "schedule_index": "{index}", "condition": "baseline",
            "model_revision": self.lock["generator/b"]["revision"],
            "scenario_id": "w06-{index}", "response": "response-{index}",
        })

        with self.assertRaisesRegex(MODULE.VerificationError, "week06_raw_generations.*model_revision"):
            MODULE.verify(self.root, self.receipt_path)

    def test_week7_generator_row_pair_must_match_the_lock(self) -> None:
        # Mutation caught: a swapped generator revision in final results invalidates its row-level provenance.
        self._write_csv(
            "week-07/W07_Results.csv", 4800,
            fields=("index", "response_id", "generator_model", "generator_revision", "condition", "scenario_id", "seed", "parse_success", "panel_action", "majority_failure"),
            row={"response_id": "response-{index}", "generator_model": "generator/a", "generator_revision": self.lock["generator/b"]["revision"], "condition": "baseline", "scenario_id": "w07-{index}", "seed": "{index}", "parse_success": "1", "panel_action": "WITHHOLD", "majority_failure": "0"},
        )

        with self.assertRaisesRegex(MODULE.VerificationError, "Week 7 result generator set"):
            MODULE.verify(self.root, self.receipt_path)

    def test_week6_wide_judge_rows_require_each_judge_rating_unit(self) -> None:
        # Mutation caught: 384 wide rows are not 1,152 ratings if any judge's payload is blank.
        path = self.root / "week-06/W06_Judge_Ratings.csv"
        with path.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
            fields = tuple(handle.seek(0) or csv.DictReader(handle).fieldnames or ())
        rows[0]["mistral_self_rationale"] = ""
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

        with self.assertRaisesRegex(MODULE.VerificationError, "mistral_self_rationale"):
            MODULE.verify(self.root, self.receipt_path)

    def test_duplicate_week7_response_id_is_rejected(self) -> None:
        # Mutation caught: repeated logical outputs cannot satisfy a planned count.
        path = self.root / "week-07/W07_Raw_Model_Outputs.jsonl"
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        rows[1]["response_id"] = rows[0]["response_id"]
        path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")

        with self.assertRaisesRegex(MODULE.VerificationError, "duplicate logical key"):
            MODULE.verify(self.root, self.receipt_path)

    def test_legitimate_unparsed_week7_result_is_allowed(self) -> None:
        # Mutation caught: a disclosed panel parse miss has blank endpoints by contract, not missing evidence.
        self._replace_csv_row("week-07/W07_Results.csv", 0, {
            "parse_success": "0", "panel_action": "", "majority_failure": "",
        })

        result = MODULE.verify(self.root, self.receipt_path)

        self.assertEqual(result["status"], "complete")

    def test_week7_unparsed_result_boundary_is_enforced(self) -> None:
        # Mutation caught: the registered 1% bound permits 48 blank panel outcomes, not 49.
        for count, allowed in ((48, True), (49, False)):
            with self.subTest(count=count):
                self._write_complete_artifacts()
                self._set_unparsed_week7_results(count)
                self._write_receipt()
                if allowed:
                    self.assertEqual(MODULE.verify(self.root, self.receipt_path)["status"], "complete")
                else:
                    with self.assertRaisesRegex(MODULE.VerificationError, "registered 1% bound"):
                        MODULE.verify(self.root, self.receipt_path)

    def test_week7_same_id_identity_mismatches_are_rejected(self) -> None:
        # Mutation caught: matching IDs cannot hide a changed generator/condition/scenario/seed identity.
        cases = (
            ("week-07/W07_Judge_Ratings.csv", {"condition": "swapped-condition"}),
            ("week-07/W07_Results.csv", {"scenario_id": "swapped-scenario"}),
        )
        for relative, updates in cases:
            with self.subTest(relative=relative):
                self._write_complete_artifacts()
                self._replace_csv_row(relative, 0, updates)
                self._write_receipt()
                with self.assertRaisesRegex(MODULE.VerificationError, "Week 7 .*identity"):
                    MODULE.verify(self.root, self.receipt_path)

    def test_week7_metadata_model_sets_must_match_generated_evidence(self) -> None:
        # Mutation caught: lock-valid metadata substitutions cannot authenticate different generated evidence.
        cases = (
            {"generators": [
                {"id": "generator/a", "revision": self.lock["generator/a"]["revision"]},
                {"id": "judge/a", "revision": self.lock["judge/a"]["revision"]},
            ]},
            {"judges": [
                {"id": "judge/a", "revision": self.lock["judge/a"]["revision"]},
                {"id": "judge/b", "revision": self.lock["judge/b"]["revision"]},
                {"id": "judge/d", "revision": self.lock["judge/d"]["revision"]},
            ]},
        )
        for override in cases:
            with self.subTest(override=override):
                self._write_complete_artifacts()
                self._write_receipt()
                metadata = json.loads((self.root / "week-07/W07_Run_Metadata.json").read_text(encoding="utf-8"))
                metadata.update(override)
                self._write_json("week-07/W07_Run_Metadata.json", metadata)
                with self.assertRaisesRegex(MODULE.VerificationError, "Week 7 .*metadata"):
                    MODULE.verify(self.root, self.receipt_path)

    def test_week7_rejects_four_judge_metadata_and_varying_three_judge_panels(self) -> None:
        # Mutation caught: a global four-judge union cannot hide a different three-judge panel per response.
        self._replace_csv_row("week-07/W07_Judge_Ratings.csv", 3, {
            "judge_model": "judge/d", "judge_revision": self.lock["judge/d"]["revision"],
        })
        metadata = json.loads((self.root / "week-07/W07_Run_Metadata.json").read_text(encoding="utf-8"))
        metadata["judges"].append({"id": "judge/d", "revision": self.lock["judge/d"]["revision"]})
        self._write_json("week-07/W07_Run_Metadata.json", metadata)

        with self.assertRaisesRegex(MODULE.VerificationError, "exactly 3 judges"):
            MODULE.verify(self.root, self.receipt_path)

    def test_week7_foreign_or_missing_ids_are_rejected(self) -> None:
        # Mutation caught: row counts and individual uniqueness cannot replace cross-artifact identity coverage.
        cases = (
            ("week-07/W07_Judge_Ratings.csv", 14399, {"response_id": "foreign-rating", "scenario_id": "foreign-scenario", "seed": "99999"}),
            ("week-07/W07_Results.csv", 4799, {"response_id": "foreign-result", "scenario_id": "foreign-scenario", "seed": "99999"}),
        )
        for relative, index, updates in cases:
            with self.subTest(relative=relative):
                self._write_complete_artifacts()
                self._replace_csv_row(relative, index, updates)
                self._write_receipt()
                with self.assertRaisesRegex(MODULE.VerificationError, "Week 7 .*coverage"):
                    MODULE.verify(self.root, self.receipt_path)

    def test_week6_judge_keys_must_match_raw_generation_keys(self) -> None:
        # Mutation caught: wide rating rows must correspond exactly to generated Week 6 responses.
        self._replace_csv_row("week-06/W06_Judge_Ratings.csv", 383, {"scenario_id": "foreign-w06"})

        with self.assertRaisesRegex(MODULE.VerificationError, "Week 6 judge.*coverage"):
            MODULE.verify(self.root, self.receipt_path)

    def test_week6_judge_revisions_are_paired_to_judge_ids(self) -> None:
        # Mutation caught: membership-only revision checks accept a swapped Week 6 judge ordering.
        self._write_json("week-06/W06_Analysis.json", {
            "judges": ["judge/a", "judge/b", "judge/c"],
            "judge_revisions": {
                "first": self.lock["judge/b"]["revision"],
                "second": self.lock["judge/a"]["revision"],
                "third": self.lock["judge/c"]["revision"],
            },
        })

        with self.assertRaisesRegex(MODULE.VerificationError, "Week 6 judge revision"):
            MODULE.verify(self.root, self.receipt_path)

    def test_empty_or_placeholder_derived_deliverables_are_rejected(self) -> None:
        # Mutation caught: prior stage success does not turn empty JSON or placeholder prose into final evidence.
        cases = (
            ("week-08/W08_Pressure_Cue_Audit.json", {}),
            ("week-10/W10_Judge_Sensitivity.json", {}),
            ("week-08/W08_Pressure_Cue_Audit.md", "TODO"),
            ("week-09/W09_Paper_Tables.md", "placeholder"),
        )
        for relative, payload in cases:
            with self.subTest(relative=relative):
                self._write_complete_artifacts()
                if isinstance(payload, str):
                    self._path(relative).write_text(payload, encoding="utf-8")
                else:
                    self._write_json(relative, payload)
                self._write_receipt()
                with self.assertRaisesRegex(MODULE.VerificationError, "derived deliverable"):
                    MODULE.verify(self.root, self.receipt_path)

    def test_malformed_derived_json_is_rejected(self) -> None:
        # Mutation caught: a present but unparsable Week 8 or Week 10 deliverable is not final evidence.
        for relative in (
            "week-08/W08_Pressure_Cue_Audit.json",
            "week-10/W10_Judge_Sensitivity.json",
        ):
            with self.subTest(relative=relative):
                self._write_complete_artifacts()
                self._path(relative).write_text("{", encoding="utf-8")
                self._write_receipt()
                with self.assertRaisesRegex(MODULE.VerificationError, "derived deliverable is invalid"):
                    MODULE.verify(self.root, self.receipt_path)

    def test_atomic_verification_write_failure_keeps_receipt_incomplete(self) -> None:
        # Mutation caught: an fsync/replace failure cannot leave a complete receipt without fresh verification evidence.
        original = MODULE._atomic_json_write
        receipt = json.loads(self.receipt_path.read_text(encoding="utf-8"))
        receipt.update({"status": "complete", "verification_pending": False})
        self._write_json("fresh-verification.json", {"status": "complete"})
        self.receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

        def fail_verification(path: Path, payload: dict[str, object]) -> None:
            if path.name == "fresh-verification.json":
                raise OSError("verification write failed")
            original(path, payload)

        with patch.object(MODULE, "_atomic_json_write", side_effect=fail_verification):
            with self.assertRaises(OSError):
                MODULE.verify(self.root, self.receipt_path)

        receipt = json.loads(self.receipt_path.read_text(encoding="utf-8"))
        self.assertEqual(receipt["status"], "incomplete")
        self.assertTrue(receipt["verification_pending"])
        self.assertFalse((self.root / "fresh-verification.json").exists())

    def test_atomic_receipt_update_failure_removes_written_verification(self) -> None:
        # Mutation caught: evidence written before receipt completion must be removed if the receipt update fails.
        original = MODULE._atomic_json_write
        receipt = json.loads(self.receipt_path.read_text(encoding="utf-8"))
        receipt.update({"status": "complete", "verification_pending": False})
        self.receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

        def fail_receipt(path: Path, payload: dict[str, object]) -> None:
            if path == self.receipt_path and payload.get("status") == "complete":
                raise OSError("receipt update failed")
            original(path, payload)

        with patch.object(MODULE, "_atomic_json_write", side_effect=fail_receipt):
            with self.assertRaises(OSError):
                MODULE.verify(self.root, self.receipt_path)

        receipt = json.loads(self.receipt_path.read_text(encoding="utf-8"))
        self.assertNotEqual(receipt["status"], "complete")
        self.assertTrue(receipt["verification_pending"])
        self.assertFalse((self.root / "fresh-verification.json").exists())

    def test_incomplete_prior_stage_is_rejected(self) -> None:
        # Mutation caught: verifier completion must depend on every earlier full-graph stage passing.
        self._write_receipt(incomplete="week09_verify")

        with self.assertRaisesRegex(MODULE.VerificationError, "week09_verify"):
            MODULE.verify(self.root, self.receipt_path)

    def test_absent_figure_pair_is_rejected(self) -> None:
        # Mutation caught: a report can exist while a required vector/raster evidence pair is incomplete.
        (self.root / "week-07/figures/W07_Figure2_Prompt_Safety_and_Control_Cost.svg").unlink()

        with self.assertRaisesRegex(MODULE.VerificationError, "figure pair"):
            MODULE.verify(self.root, self.receipt_path)

    def test_corrupt_figure_content_is_rejected(self) -> None:
        # Mutation caught: a named figure file must be a parseable image, not a placeholder payload.
        (self.root / "week-07/figures/W07_Figure1_Common_Baseline_Cross_Model.png").write_bytes(b"not-a-png")

        with self.assertRaisesRegex(MODULE.VerificationError, "figure PNG is invalid"):
            MODULE.verify(self.root, self.receipt_path)

    def test_signature_only_png_is_rejected(self) -> None:
        # Mutation caught: a PNG signature plus padding must not masquerade as a rendered figure.
        (self.root / "week-07/figures/W07_Figure1_Common_Baseline_Cross_Model.png").write_bytes(
            b"\x89PNG\r\n\x1a\n" + b"padding" * 16
        )

        with self.assertRaisesRegex(MODULE.VerificationError, "figure PNG is invalid"):
            MODULE.verify(self.root, self.receipt_path)

    def test_notebook_error_output_is_rejected(self) -> None:
        # Mutation caught: notebook execution with an error output is not verified analysis evidence.
        self._write_json("week-07/W07_Analysis_Notebook.ipynb", {
            "cells": [
                {"cell_type": "code", "execution_count": index, "outputs": [{"output_type": "error", "ename": "AssertionError"}] if index == 1 else []}
                for index in range(1, 11)
            ],
        })

        with self.assertRaisesRegex(MODULE.VerificationError, "error output"):
            MODULE.verify(self.root, self.receipt_path)


if __name__ == "__main__":
    unittest.main()
