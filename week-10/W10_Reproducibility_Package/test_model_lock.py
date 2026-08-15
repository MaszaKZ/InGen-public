"""Contract tests for the immutable reproduction model lock."""
from __future__ import annotations

import re
import unittest

from reproduction_model_lock import LOCK_PATH, load_model_lock, revision_for


EXPECTED = {
    "google/flan-t5-base": "7bcac572ce56db69c1ea7c8af255c5d7c9672fc2",
    "Qwen/Qwen2.5-1.5B-Instruct": "989aa7980e4cf806f80c7fef2b1adb7bc71aa306",
    "Qwen/Qwen2.5-3B-Instruct": "aa8e72537993ba99e69dfaafa59ed015b17504d1",
    "mistralai/Mistral-7B-Instruct-v0.3": "c170c708c41dac9275d15a8fff4eca08d52bab71",
    "Qwen/Qwen2.5-7B-Instruct": "a09a35458c702b33eeacc393d103063234e8bc28",
    "microsoft/Phi-3.5-mini-instruct": "2fe192450127e6a83f7441aef6e3ca586c338b77",
    "ibm-granite/granite-3.3-8b-instruct": "51dd4bc2ade4059a6bd87649d68aa11e4fb2529b",
    "microsoft/phi-4": "2db69c1c3e91a05d2c64a3185acfbaf36f744e25",
    "tiiuae/Falcon3-10B-Instruct": "8799bc6aec0152757221dc6b272d824642db6202",
    "tiiuae/Falcon3-7B-Instruct": "1e57a0ecd176c7c139f289c60a74e57f887c3dfb",
}


class ModelLockContractTests(unittest.TestCase):
    def test_lock_contains_exact_immutable_revisions(self) -> None:
        lock = load_model_lock()
        self.assertEqual(set(lock), set(EXPECTED))
        for repo_id, expected_revision in EXPECTED.items():
            self.assertRegex(lock[repo_id]["revision"], r"[0-9a-f]{40}")
            self.assertTrue(lock[repo_id]["roles"])
            self.assertTrue(lock[repo_id]["consumers"])
            self.assertEqual(revision_for(repo_id), expected_revision)

    def test_manifest_declares_the_registered_schema_and_lock_date(self) -> None:
        import json

        payload = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema_version"], "ingen-model-lock-v1")
        self.assertEqual(payload["locked_on"], "2026-08-14")

    def test_unknown_model_is_named_in_lookup_error(self) -> None:
        unknown = "example/not-locked"
        with self.assertRaisesRegex(KeyError, re.escape(unknown)):
            revision_for(unknown)


if __name__ == "__main__":
    unittest.main()
