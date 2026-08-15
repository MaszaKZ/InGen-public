"""Contract tests for locked Hugging Face model acquisition."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import call, patch

from reproduction_model_lock import load_model_lock


MODULE_PATH = Path(__file__).with_name("prefetch_models.py")
SPEC = importlib.util.spec_from_file_location("prefetch_models", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules["prefetch_models"] = MODULE
SPEC.loader.exec_module(MODULE)


class PrefetchTests(unittest.TestCase):
    @patch.object(MODULE, "snapshot_download")
    def test_prefetches_every_locked_model_at_its_revision_and_requested_cache(self, download):
        cache_dir = Path("cache-location")
        locked_models = load_model_lock()
        download.side_effect = lambda **kwargs: f"snapshot://{kwargs['repo_id']}"

        resolved = MODULE.prefetch(cache_dir)

        self.assertEqual(
            resolved,
            {repo_id: f"snapshot://{repo_id}" for repo_id in locked_models},
        )
        self.assertCountEqual(
            download.call_args_list,
            [
                call(
                    repo_id=repo_id,
                    revision=str(spec["revision"]),
                    cache_dir=str(cache_dir),
                )
                for repo_id, spec in locked_models.items()
            ],
        )

    @patch.object(MODULE, "snapshot_download", return_value="snapshot://selected")
    def test_prefetch_limits_acquisition_to_the_selected_locked_models(self, download):
        selected = {"microsoft/phi-4", "google/flan-t5-base"}

        resolved = MODULE.prefetch(Path("cache-location"), selected=selected)

        self.assertEqual(set(resolved), selected)
        self.assertEqual(download.call_count, 2)
        self.assertEqual({item.kwargs["repo_id"] for item in download.call_args_list}, selected)


if __name__ == "__main__":
    unittest.main()
