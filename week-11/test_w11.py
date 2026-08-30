from __future__ import annotations

import json
import hashlib
import re
import shutil
import subprocess
import sys
import unittest
import uuid
import zipfile
import zlib
import xml.etree.ElementTree as ET
from contextlib import contextmanager
from pathlib import Path

from PIL import Image


W11 = Path(__file__).resolve().parent
ROOT = W11.parent
sys.path.insert(0, str(W11))


@contextmanager
def scratch_directory(base: Path):
    base.mkdir(exist_ok=True)
    root = base / f"case-{uuid.uuid4().hex}"
    root.mkdir()
    try:
        yield root
    finally:
        shutil.rmtree(root)


class EvidenceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from w11_evidence import load_evidence

        cls.evidence = load_evidence(ROOT)

    def test_registered_common_baseline_contrasts(self) -> None:
        from w11_evidence import common_baseline_rows

        rows = {row["subtype"]: row for row in common_baseline_rows(self.evidence)}
        self.assertEqual(rows["plain"]["estimate_pp"], -55.0)
        self.assertEqual(rows["plain"]["ci_pp"], [-77.5, -32.5])
        self.assertEqual(rows["pressured"]["estimate_pp"], -40.1)
        self.assertEqual(rows["pressured"]["ci_pp"], [-55.3, -26.0])
        self.assertEqual(rows["control"]["estimate_pp"], 18.8)
        self.assertEqual(rows["control"]["ci_pp"], [6.2, 34.4])

    def test_only_observed_pass_is_not_measurement_robust(self) -> None:
        from w11_evidence import mitigation_rows

        passes = [row for row in mitigation_rows(self.evidence) if row["observed_pass"]]
        self.assertEqual(
            [(row["model"], row["condition"]) for row in passes],
            [("Qwen2.5-7B-Instruct", "Deliberation")],
        )
        self.assertFalse(passes[0]["combined_stress_pass"])

    def test_per_family_counts_reconcile_with_registered_rates(self) -> None:
        from w11_evidence import per_family_common_rows

        rows = per_family_common_rows(ROOT)
        self.assertEqual(len(rows), 16)
        totals = {
            f"{model}_{subtype}": [0, 0]
            for model in ("mistral", "qwen")
            for subtype in ("plain", "pressured", "control")
        }
        for row in rows:
            for key, cell in totals.items():
                cell[0] += row[key]["failures"]
                cell[1] += row[key]["rows"]
        self.assertEqual(totals["mistral_plain"], [142, 160])
        self.assertEqual(totals["mistral_pressured"], [69, 160])
        self.assertEqual(totals["mistral_control"], [0, 160])
        self.assertEqual(totals["qwen_plain"], [54, 160])
        self.assertEqual(totals["qwen_pressured"], [5, 157])
        self.assertEqual(totals["qwen_control"], [30, 160])

    def test_loss_curves_match_reported_break_even_ratios(self) -> None:
        from w11_evidence import loss_curve_data

        data = loss_curve_data(self.evidence)
        observed = {
            entry["alpha"]: entry["break_even_cost_ratio"]
            for entry in data["observed"]["alphas"]
        }
        stressed = {
            entry["alpha"]: entry["break_even_cost_ratio"]
            for entry in data["stressed"]["alphas"]
        }
        self.assertEqual(observed, {1.0: 0.342, 0.5: 0.395, 0.0: 0.469})
        self.assertEqual(stressed, {1.0: 0.707, 0.5: 0.597, 0.0: 0.517})

    def test_stress_values_match_week_10(self) -> None:
        from w11_evidence import stress_rows

        rows = {row["endpoint"]: row for row in stress_rows(self.evidence)}
        self.assertEqual(rows["plain"]["observed_pp"], -55.0)
        self.assertEqual(rows["plain"]["stressed_pp"], -25.6)
        self.assertEqual(rows["pressured"]["observed_pp"], -40.1)
        self.assertEqual(rows["pressured"]["stressed_pp"], -35.0)
        self.assertEqual(rows["control"]["observed_pp"], 18.8)
        self.assertEqual(rows["control"]["stressed_pp"], 18.1)


class FigureBuildTests(unittest.TestCase):
    def test_builds_deterministic_publication_figures(self) -> None:
        from build_w11_figures import build_all

        scratch = W11 / ".test-tmp"
        with scratch_directory(scratch) as tmp:
            outputs = build_all(ROOT, tmp)
            self.assertEqual(len(outputs), 12)
            self.assertTrue(all(path.is_file() for path in outputs))

            for png in tmp.glob("*.png"):
                with Image.open(png) as image:
                    self.assertEqual(image.size, (1600, 800))

            data = json.loads(
                (tmp / "W11_Figure1_Operating_Point.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(
                [row["estimate_pp"] for row in data["contrasts"]],
                [-55.0, -40.1, 18.8],
            )
            self.assertNotIn("generated", json.dumps(data).lower())
            pdf = (tmp / "W11_Figure1_Operating_Point.pdf").read_bytes()
            self.assertNotIn(b"/CreationDate", pdf)
            self.assertNotIn(b"/ModDate", pdf)


class ReportSourceTests(unittest.TestCase):
    def test_latex_report_is_academic_and_submission_ready(self) -> None:
        report = W11 / "W11_Capstone_Report.tex"
        self.assertTrue(report.is_file())
        source = report.read_text(encoding="utf-8")

        required = (
            r"\documentclass[conference]{IEEEtran}",
            r"\begin{abstract}",
            r"\begin{IEEEkeywords}",
            r"\section{Executive Summary}",
            r"\section{Physical-AI Research Landscape}",
            r"\section{Related Work and Research Gap}",
            r"\section{Research Questions and Contributions}",
            r"\section{Methodology}",
            r"\section{Empirical Results}",
            r"\section{Cross-Experiment Synthesis}",
            r"\section{PIC 2.0 Application Framework}",
            r"\section{Discussion}",
            r"\section{Limitations and Future Research}",
            r"\section{Conclusion}",
            r"\textbf{Minimal full-pipeline GPU smoke execution}",
            r"figures/W11_Figure1_Operating_Point.pdf",
            r"figures/W11_Figure2_Prompt_Tradeoffs.pdf",
            r"figures/W11_Figure3_Measurement_Stress.pdf",
            r"figures/W11_Figure4_Expected_Loss.pdf",
            r"\section{Worked Adjudication Example}",
            r"\section{Per-Family Outcome Counts}",
        )
        for text in required:
            self.assertIn(text, source)

        banned = (
            "AI assistance",
            "feedback",
            "superseded",
            "TODO",
            "Week 11",
            "week-11",
            "../week-",
            "\\texttt{W0",
            "behaviour",
            "authorisation",
            "centre",
        )
        for text in banned:
            self.assertNotIn(text, source)

        self.assertGreaterEqual(source.count(r"\bibitem{"), 15)
        self.assertGreaterEqual(source.count(r"\begin{table"), 8)
        self.assertGreaterEqual(source.count(r"\section{"), 12)

    def test_compiled_report_uses_at_most_twenty_pages(self) -> None:
        report = W11 / "W11_Capstone_Report.pdf"
        self.assertTrue(report.is_file())
        pdf = report.read_bytes()
        objects = [pdf]
        for match in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", pdf, re.S):
            try:
                objects.append(zlib.decompress(match.group(1)))
            except zlib.error:
                continue

        page_count = len(
            re.findall(rb"/Type\s*/Page(?!s)\b", b"\n".join(objects))
        )
        self.assertGreater(page_count, 0)
        self.assertLessEqual(page_count, 20)


class PresentationContractTests(unittest.TestCase):
    def test_title_slide_matches_report_paper_title(self) -> None:
        deck = W11 / "W11_Research_Review_Deck.pptx"
        report = (W11 / "W11_Capstone_Report.tex").read_text(encoding="utf-8")
        paper_title = "Authorization Safety as a Two-Error Operating-Point Problem:"
        paper_subtitle = (
            "A Registered Evaluation of Language-Model Decision Layers for Service Robots"
        )

        self.assertIn(paper_title, report)
        self.assertIn(paper_subtitle, report)
        with zipfile.ZipFile(deck) as archive:
            title_slide = archive.read("ppt/slides/slide1.xml").decode("utf-8")

        self.assertIn(paper_title, title_slide)
        self.assertIn(paper_subtitle, title_slide)
        self.assertIn("Ziyue Li", title_slide)
        self.assertIn("InGen Dynamics", title_slide)

    def test_research_review_deck_is_academic_and_source_documented(self) -> None:
        deck = W11 / "W11_Research_Review_Deck.pptx"
        builder = W11 / "build_w11_deck.mjs"
        self.assertTrue(builder.is_file())
        self.assertTrue(deck.is_file())

        with zipfile.ZipFile(deck) as archive:
            slide_names = sorted(
                name
                for name in archive.namelist()
                if re.fullmatch(r"ppt/slides/slide\d+\.xml", name)
            )
            note_names = sorted(
                name
                for name in archive.namelist()
                if re.fullmatch(r"ppt/notesSlides/notesSlide\d+\.xml", name)
            )
            self.assertEqual(len(slide_names), 14)
            self.assertEqual(len(note_names), 14)

            visible = "\n".join(
                archive.read(name).decode("utf-8") for name in slide_names
            )
            notes = [archive.read(name).decode("utf-8") for name in note_names]
            package_xml = "\n".join(
                archive.read(name).decode("utf-8", errors="ignore")
                for name in archive.namelist()
                if name.endswith(".xml")
            )
            core_properties = archive.read("docProps/core.xml").decode("utf-8")
            app_properties = archive.read("docProps/app.xml").decode("utf-8")
            app_root = ET.fromstring(app_properties.lstrip("\ufeff"))
            app_values = {
                element.tag.rsplit("}", 1)[-1]: element.text
                for element in app_root
            }

        required = (
            "Qwen cuts unsafe compliance by 55.0 pp but adds 18.8 pp authorized refusal",
            "Six PIC 2.0 roles converge on one authorization decision",
            "No reviewed benchmark combines the three conditions needed for authorization safety",
            "Three questions isolate generator, prompt, and design-stack effects on two errors",
            "The 96-scenario benchmark reveals opposite common-prompt baselines across two generators",
            "Experiment 1's 25% lexical gain disappears under semantic review",
            "Experiment 2 cuts pressured failures from 12/32 to 2/32 with deliberation",
            "Generator identity shifts all three endpoints",
            "Two PIC 2.0 classes map directly to the measured trade-off",
            "Five platform contexts require distinct two-error budgets before advancement",
            "Two generators and one false-negative-only stress model leave four priority validations open",
            "The paper contributes one confirmatory comparison",
            "Three findings support one recommendation",
            "The program moved through three measurement regimes",
        )
        for text in required:
            self.assertIn(text, visible)

        banned = (
            "feedback",
            "superseded",
            "TODO",
            "Week 11",
            "Phase C",
            "behaviour",
            "authorisation",
            "defensible",
            "measurement-bounded",
        )
        for text in banned:
            self.assertNotIn(text, visible)

        legacy = (
            "W06_",
            "W05_",
            "Baseline failures · n = 32 per condition",
            "Failures across interventions · n = 32 per cell",
        )
        for text in legacy:
            self.assertNotIn(text, package_xml)

        self.assertNotIn('prst="roundRect"', package_xml)

        self.assertTrue(all("[Sources]" in note for note in notes))
        self.assertIn(
            "<dc:title>Contested-Authority Robustness Research Review</dc:title>",
            core_properties,
        )
        self.assertIn(
            "<dc:creator>InGen Research Project</dc:creator>",
            core_properties,
        )
        self.assertNotIn("Walnut Exporter", core_properties)
        self.assertEqual(app_values["Slides"], "14")
        self.assertEqual(app_values["Notes"], "14")
        self.assertEqual(app_values["Application"], "Microsoft Office PowerPoint")


class ReproducibilityPackageContractTests(unittest.TestCase):
    def test_publication_figure_json_is_materialized_as_lf(self) -> None:
        paths = tuple(
            f"week-11/figures/{stem}.json"
            for stem in (
                "W11_Figure1_Operating_Point",
                "W11_Figure2_Prompt_Tradeoffs",
                "W11_Figure3_Measurement_Stress",
                "W11_Figure4_Expected_Loss",
            )
        )
        result = subprocess.run(
            ["git", "check-attr", "eol", "--", *paths],
            cwd=ROOT,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        resolved = {
            path: value
            for line in result.stdout.splitlines()
            for path, attribute, value in (line.split(": ", 2),)
            if attribute == "eol"
        }
        self.assertEqual(resolved, {path: "lf" for path in paths})

    def test_packaged_figures_match_publication_outputs(self) -> None:
        package = W11 / "W11_Reproducibility_Package"
        stems = (
            "W11_Figure1_Operating_Point",
            "W11_Figure2_Prompt_Tradeoffs",
            "W11_Figure3_Measurement_Stress",
            "W11_Figure4_Expected_Loss",
        )

        for stem in stems:
            for suffix in (".png", ".pdf", ".json"):
                published = W11 / "figures" / f"{stem}{suffix}"
                packaged = package / "artifacts" / "figures" / f"{stem}{suffix}"
                self.assertTrue(packaged.is_file(), packaged)
                self.assertEqual(
                    hashlib.sha256(published.read_bytes()).hexdigest(),
                    hashlib.sha256(packaged.read_bytes()).hexdigest(),
                )

            report_figure = package / "artifacts" / "report" / "figures" / f"{stem}.pdf"
            self.assertTrue(report_figure.is_file(), report_figure)
            self.assertEqual(
                hashlib.sha256((W11 / "figures" / f"{stem}.pdf").read_bytes()).hexdigest(),
                hashlib.sha256(report_figure.read_bytes()).hexdigest(),
            )

    def test_standalone_package_has_manual_model_boundary_and_raw_evidence(self) -> None:
        package = W11 / "W11_Reproducibility_Package"
        required = (
            "README.md",
            "package_manifest.json",
            "model_lock.json",
            "verify_models.py",
            "verify_package.py",
            "run_acceptance.py",
            "run_minimal_pipeline_smoke.py",
            "receipts/isolated-short-inference.json",
            "analysis/regenerate_figures.py",
            "source/week-06/W06_Raw_Model_Outputs.snapshot.jsonl",
            "source/week-06/W06_Judge_Ratings.csv",
            "source/week-07/W07_Raw_Model_Outputs.snapshot.jsonl",
            "source/week-07/W07_Judge_Ratings.csv",
            "source/week-07/W07_Judge_Gold_Ratings.csv",
            "artifacts/report/Capstone_Report.pdf",
            "artifacts/slides/Research_Review_Deck.pptx",
        )
        for relative in required:
            self.assertTrue((package / relative).is_file(), relative)

        readme = (package / "README.md").read_text(encoding="utf-8")
        lock = json.loads((package / "model_lock.json").read_text(encoding="utf-8"))
        self.assertEqual(len(lock["models"]), 10)
        self.assertIn(r"models\huggingface\hub", readme)
        for repo_id, record in lock["models"].items():
            download = f"$Hf download {repo_id} --revision {record['revision']} --cache-dir .\\models\\huggingface\\hub"
            verify = f"$Hf cache verify {repo_id} --revision {record['revision']} --cache-dir .\\models\\huggingface\\hub --fail-on-missing-files"
            self.assertIn(download, readme)
            self.assertIn(verify, readme)
        self.assertIn("--write-checksum-manifest .\\models\\model-checksums.json", readme)
        self.assertIn("run_minimal_pipeline_smoke.py --plan-only", readme)
        self.assertIn("run_minimal_pipeline_smoke.py --cache-dir", readme)
        self.assertIn("two generations, six judgments, and two panel rows", readme)

        package_files = [path for path in package.rglob("*") if path.is_file()]
        self.assertFalse(any(path.name == "prefetch_models.py" for path in package_files))
        self.assertFalse(any(path.suffix.lower() == ".zip" for path in package_files))
        self.assertGreater(sum(path.stat().st_size for path in package_files), 30 * 1024 * 1024)

        def digest(path: Path) -> str:
            return hashlib.sha256(path.read_bytes()).hexdigest()

        self.assertEqual(
            digest(W11 / "W11_Capstone_Report.pdf"),
            digest(package / "artifacts/report/Capstone_Report.pdf"),
        )
        self.assertEqual(
            digest(W11 / "W11_Research_Review_Deck.pptx"),
            digest(package / "artifacts/slides/Research_Review_Deck.pptx"),
        )


class IntegratedSubmissionContractTests(unittest.TestCase):
    def test_weekly_research_log_is_current_and_traceable(self) -> None:
        log_path = W11 / "Wk-11-ResearchLog.md"
        self.assertTrue(log_path.is_file())
        log = log_path.read_text(encoding="utf-8")

        for heading in (
            "# Wk-11 Research Log",
            "## Weekly summary",
            "## Detailed chronological audit trail",
            "## Deliverable conformance",
            "## Verification record",
            "## Reflection",
            "## AI assistance note",
            "## Final Week 11 completion entry",
        ):
            self.assertIn(heading, log)

        for evidence in (
            "W11_Capstone_Report.tex",
            "W11_Research_Review_Deck.pptx",
            "W11_Reproducibility_Package",
            "14-slide",
            "20-page",
            "−55.0",
            "−40.1",
            "+18.8",
            "manual model download",
            "15 Week 11 tests",
            "25 package tests",
        ):
            self.assertIn(evidence, log)

        self.assertNotIn("TODO", log)

        readme = (W11 / "README.md").read_text(encoding="utf-8")
        self.assertIn("Wk-11-ResearchLog.md", readme)
        self.assertIn("14-slide research-review deck", readme)

        package_readme = (W11 / "W11_Reproducibility_Package" / "README.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("14-slide research-review deck", package_readme)
        self.assertNotIn("Ten-slide research-review deck", package_readme)

    def test_readme_page_count_matches_compiled_report(self) -> None:
        readme = (W11 / "README.md").read_text(encoding="utf-8")
        match = re.search(r"Compiled (\d+)-page academic report", readme)
        self.assertIsNotNone(match, "README must state the compiled report length")

        pdf = (W11 / "W11_Capstone_Report.pdf").read_bytes()
        objects = [pdf]
        for stream in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", pdf, re.S):
            try:
                objects.append(zlib.decompress(stream.group(1)))
            except zlib.error:
                continue
        page_count = len(
            re.findall(rb"/Type\s*/Page(?!s)\b", b"\n".join(objects))
        )

        self.assertEqual(int(match.group(1)), page_count)

    def test_submission_entry_points_are_current_and_coherent(self) -> None:
        readme = W11 / "README.md"
        verifier = W11 / "verify_w11.py"
        self.assertTrue(readme.is_file())
        self.assertTrue(verifier.is_file())
        text = readme.read_text(encoding="utf-8")
        for name in (
            "W11_Capstone_Report.tex",
            "W11_Capstone_Report.pdf",
            "W11_Research_Review_Deck.pptx",
            "W11_Reproducibility_Package",
            "isolated-cpu-mock.json",
        ):
            self.assertIn(name, text)
        for banned in ("feedback", "superseded", "TODO", "AI assistance"):
            self.assertNotIn(banned, text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
