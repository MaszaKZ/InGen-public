from __future__ import annotations

import re
import json
import importlib.util
import unittest
import zlib
from pathlib import Path


W12 = Path(__file__).resolve().parent
ROOT = W12.parent


def read(name: str) -> str:
    path = W12 / name
    if not path.is_file():
        raise AssertionError(f"missing Week 12 artifact: {name}")
    return path.read_text(encoding="utf-8")


def prose_words(markdown: str) -> list[str]:
    body = re.sub(r"```.*?```", " ", markdown, flags=re.DOTALL)
    body = re.sub(r"`[^`]+`", " ", body)
    body = re.sub(r"^#{1,6}\s+.*$", " ", body, flags=re.MULTILINE)
    body = re.sub(r"\[[^]]+\]\([^)]+\)", " ", body)
    return re.findall(r"\b[\w'-]+\b", body)


class Week12InventoryTests(unittest.TestCase):
    def test_required_local_artifacts_exist(self) -> None:
        required = (
            "README.md",
            "W12_Final_Paper.md",
            "W12_Final_Paper.tex",
            "W12_Final_Paper.pdf",
            "W12_Retrospective.md",
            "W12_Presentation_Defense_Brief.md",
            "W12_Reproducibility_Audit.ipynb",
            "Wk-12-Final-ResearchLog.md",
            "test_w12.py",
            "verify_w12.py",
        )
        missing = [name for name in required if not (W12 / name).is_file()]
        self.assertEqual(missing, [])


class FinalPaperContractTests(unittest.TestCase):
    def test_markdown_has_workshop_structure_and_authoritative_results(self) -> None:
        paper = read("W12_Final_Paper.md")
        for heading in (
            "## Abstract",
            "## 1 Introduction",
            "## 2 Related Work",
            "## 3 Methods",
            "## 4 Results",
            "## 5 Discussion",
            "## 6 Limitations and Future Work",
            "## 7 Conclusion",
            "## References",
        ):
            self.assertIn(heading, paper)
        for result in (
            "55.0 percentage points",
            "40.1 percentage points",
            "18.8 percentage points",
            "14,400 judgments",
            "4,800 generations",
            "14/16",
            "-25.6",
        ):
            self.assertIn(result, paper)
        self.assertIn("LLM-judge measurement", paper)
        self.assertIn("does not survive combined measurement stress", paper)

    def test_paper_has_no_process_or_unsupported_release_claims(self) -> None:
        paper = read("W12_Final_Paper.md").casefold()
        for phrase in (
            "draft status",
            "week 10",
            "week 11",
            "week 12",
            "../week-",
            "c:\\users",
            "human-annotated ground truth",
            "public release completed",
        ):
            self.assertNotIn(phrase, paper)

    def test_generated_sources_have_clean_prose_and_traceable_evidence(self) -> None:
        markdown = read("W12_Final_Paper.md")
        latex = read("W12_Final_Paper.tex")
        malformed = (
            "our an earlier",
            "the an earlier",
            "from the an earlier",
            "executed the archived",
            "receipt the archived",
            "archived analysis record, the archived analysis record",
        )
        for source in (markdown, latex):
            folded = source.casefold()
            for phrase in malformed:
                self.assertNotIn(phrase, folded)
            self.assertNotIn("\n\n\n", source)
        for artifact in ("W07_Analysis.json", "W10_Judge_Sensitivity.json"):
            self.assertIn(artifact, markdown)
        self.assertRegex(markdown, r"Table T2b[^\n]*W07_Analysis\.json")
        self.assertRegex(markdown, r"Table T2c[^\n]*W07_Analysis\.json")

    def test_markdown_and_latex_are_synchronized(self) -> None:
        markdown = read("W12_Final_Paper.md")
        latex = read("W12_Final_Paper.tex")
        markdown_title = re.search(r"^#\s+(.+)$", markdown, flags=re.MULTILINE)
        latex_title = re.search(r"\\title\{([^}]+)\}", latex)
        self.assertIsNotNone(markdown_title)
        self.assertIsNotNone(latex_title)
        self.assertEqual(markdown_title.group(1), latex_title.group(1))

        for stem in (
            "Figure1_Operating_Point",
            "Figure2_Prompt_Tradeoffs",
            "Figure3_Measurement_Stress",
            "Figure4_Expected_Loss",
        ):
            self.assertIn(stem, markdown)
            self.assertIn(stem, latex)

        adapted_claim = (
            "Model-adapted prompting moved each generator along the same trade-off"
        )
        self.assertIn(adapted_claim, markdown)
        self.assertIn(adapted_claim, latex)

        table_rules = re.findall(r"^\|\s*:?-{3,}", markdown, flags=re.MULTILINE)
        self.assertGreaterEqual(len(table_rules), 3)
        self.assertGreaterEqual(latex.count("\\begin{table"), 3)
        references = re.findall(r"^\[\d+\]\s+", markdown, flags=re.MULTILINE)
        bibitems = re.findall(r"^\\bibitem\{", latex, flags=re.MULTILINE)
        self.assertEqual(len(references), 22)
        self.assertEqual(len(bibitems), 22)

        markdown_subsections = re.findall(
            r"^###\s+\d+\.\d+\s+(.+)$", markdown, flags=re.MULTILINE
        )
        latex_subsections = re.findall(r"^\\subsection\{([^}]+)\}", latex, flags=re.MULTILINE)

        def normalize_heading(heading: str) -> str:
            heading = re.sub(r"\s+\([^)]*\)$", "", heading)
            heading = heading.casefold().replace("--", "-")
            return re.sub(r"^the\s+", "", heading)

        expected_subsections = [
            "robot foundation models and their evaluations",
            "runtime safety mechanisms",
            "calibrated decisions and trust",
            "what this paper adds",
            "scenario bank",
            "generators and prompt conditions",
            "outcome adjudication and panel acceptance",
            "registered analysis",
            "cross-generator trade-off",
            "interventions and the registered mitigation rule",
            "plain caution fails more than pressured caution",
            "measurement quality",
            "judge-measurement stress analysis",
            "operating points, not rankings",
            "from rates to setting-specific loss",
            "no blanket mitigation",
            "endpoint determines the conclusion",
            "implications for platform evaluation",
            "pressure-direction reversal, explored and bounded",
            "reproducibility and auditability",
        ]
        self.assertEqual(
            [normalize_heading(heading) for heading in markdown_subsections],
            expected_subsections,
        )
        self.assertEqual(
            [normalize_heading(heading) for heading in latex_subsections],
            expected_subsections,
        )

    def test_bibliography_uses_complete_child_factor_title(self) -> None:
        full_title = (
            "The Child Factor in Child-Robot Interaction: Discovering the Impact "
            "of Developmental Stage and Individual Characteristics"
        )
        self.assertIn(full_title, read("W12_Final_Paper.md"))
        self.assertIn(full_title.casefold(), read("W12_Final_Paper.tex").casefold())

    def test_primary_contrast_units_are_explicit_in_both_sources(self) -> None:
        required = (
            "55.0 percentage points",
            "40.1 percentage points",
            "18.8 percentage points higher",
        )
        for source in (read("W12_Final_Paper.md"), read("W12_Final_Paper.tex")):
            for phrase in required:
                self.assertIn(phrase, source)

    def test_markdown_local_links_resolve(self) -> None:
        markdown = read("W12_Final_Paper.md")
        local_links = re.findall(r"!?\[[^]]*\]\((?!https?://|#)([^)]+)\)", markdown)
        self.assertTrue(local_links)
        missing = [link for link in local_links if not (W12 / link).resolve().is_file()]
        self.assertEqual(missing, [])

    def test_pdf_is_ten_to_twelve_pages(self) -> None:
        pdf = W12 / "W12_Final_Paper.pdf"
        self.assertTrue(pdf.is_file(), pdf)
        data = pdf.read_bytes()
        segments = [data]
        for match in re.finditer(rb"stream\r?\n", data):
            start = match.end()
            end = data.find(b"endstream", start)
            if end == -1:
                continue
            try:
                segments.append(zlib.decompress(data[start:end].rstrip(b"\r\n")))
            except zlib.error:
                continue
        corpus = b"".join(segments)
        pages = len(re.findall(rb"/Type\s*/Page\b", corpus))
        self.assertGreaterEqual(pages, 10)
        self.assertLessEqual(pages, 12)

    def test_section_cross_references_resolve(self) -> None:
        markdown = read("W12_Final_Paper.md")
        headings = set(
            re.findall(r"^#{2,3}\s+(\d+(?:\.\d+)?)\s+", markdown, flags=re.MULTILINE)
        )
        references = re.findall(r"§(\d+(?:\.\d+)?)", markdown)
        self.assertTrue(references)
        unresolved = sorted(set(references) - headings)
        self.assertEqual(unresolved, [])


class PublicDerivativeContractTests(unittest.TestCase):
    """Submission-style gates for the public LaTeX derivative.

    The internal Markdown keeps the full apparatus (status labels, artifact
    filenames, run-in bolds); the public .tex must be prose throughout, carry
    no claim-status vocabulary or internal filenames, and state scope caveats
    once, in Limitations.
    """

    def setUp(self) -> None:
        self.latex = read("W12_Final_Paper.tex")

    def test_no_internal_artifact_filenames(self) -> None:
        leaks = re.findall(r"\\path\{[^}]*\}|\bW\d{2}_\w+", self.latex)
        self.assertEqual(leaks, [])

    def test_no_run_in_bold_paragraph_labels(self) -> None:
        self.assertEqual(re.findall(r"\\textbf\{[^{}]*\.\}", self.latex), [])

    def test_no_claim_status_labels(self) -> None:
        folded = self.latex.casefold()
        for label in (
            "(proposed)",
            "(confirmatory)",
            "(descriptive)",
            "(exploratory)",
        ):
            self.assertNotIn(label, folded)

    def test_novelty_claim_is_bounded_to_the_literature_review(self) -> None:
        self.assertIn(
            "To our knowledge from the preliminary literature review", self.latex
        )
        self.assertNotIn("To our knowledge, no public study", self.latex)

    def test_care_boundary_rate_names_its_stratum(self) -> None:
        self.assertIn(
            r"48.8\% of plain care-boundary rows at the common baseline", self.latex
        )
        self.assertNotIn(r"48.8\% of common-baseline rows", self.latex)

    def test_scope_caveats_live_only_in_limitations(self) -> None:
        for duplicated_caveat in (
            "not deployment approvals",
            "Any broader claim should be tested separately",
        ):
            self.assertNotIn(duplicated_caveat, self.latex)


class RetrospectiveContractTests(unittest.TestCase):
    def test_retrospective_answers_the_three_required_questions(self) -> None:
        retrospective = read("W12_Retrospective.md")
        for heading in (
            "## Most Important Finding and Why It Was Surprising",
            "## Weakest Part of the Paper and What Would Strengthen It",
            "## Six-Month Follow-Up Experiment",
        ):
            self.assertIn(heading, retrospective)
        count = len(prose_words(retrospective))
        self.assertGreaterEqual(count, 450)
        self.assertLessEqual(count, 700)
        for phrase in (
            "defer",
            "blinded human adjudication",
            "three generators",
            "matched authorized controls",
            "platform contexts",
            "preregistered",
            "family-clustered",
            "held-out test set",
        ):
            self.assertIn(phrase, retrospective.casefold())


class PresentationContractTests(unittest.TestCase):
    def test_defense_brief_covers_timing_and_review_questions(self) -> None:
        brief = read("W12_Presentation_Defense_Brief.md")
        self.assertIn("30-minute presentation", brief)
        self.assertIn("20-minute research Q&A", brief)
        self.assertIn("14-slide", brief)
        for topic in (
            "Research-question selection",
            "Scenario-bank design",
            "Intervention choice",
            "Novelty",
            "Judge validity",
            "External validity",
            "Operating point rather than a model ranking",
        ):
            self.assertIn(topic, brief)


class DocumentationContractTests(unittest.TestCase):
    def test_final_log_has_required_content_and_word_budget(self) -> None:
        log = read("Wk-12-Final-ResearchLog.md")
        for heading in (
            "## What I Read",
            "## What I Built",
            "## What I Found",
            "## What Remains Open",
            "## Verification Record",
            "## AI Assistance Note",
        ):
            self.assertIn(heading, log)
        count = len(prose_words(log))
        self.assertGreaterEqual(count, 300)
        self.assertLessEqual(count, 500)

    def test_readmes_describe_current_week_11_and_week_12_artifacts(self) -> None:
        week_readme = read("README.md")
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("W12_Final_Paper.md", week_readme)
        self.assertIn("verify_w12.py", week_readme)
        self.assertIn("`week-12/`", root_readme)
        self.assertIn("### Week 12", root_readme)
        for current in (
            "20-page IEEEtran report",
            "14-slide research-review deck",
            "four publication figures",
            "standalone reproducibility package",
        ):
            self.assertIn(current, root_readme)
        for obsolete in (
            "W11_Capstone_Report.md",
            "W11_Capstone_Report.docx",
            "build_w11_report_docx.py",
            "build_w11_deck_pptx.py",
            "W11_Feedback.md",
        ):
            self.assertNotIn(obsolete, root_readme)


class ReleaseBoundaryTests(unittest.TestCase):
    def test_local_docs_do_not_claim_public_release_or_tag(self) -> None:
        paths = (
            W12 / "README.md",
            W12 / "Wk-12-Final-ResearchLog.md",
            ROOT / "README.md",
        )
        for path in paths:
            self.assertTrue(path.is_file(), path)
            contents = path.read_text(encoding="utf-8").casefold()
            self.assertNotIn("public snapshot promoted", contents)
            self.assertNotIn("v1.0 tag created", contents)


class NotebookContractTests(unittest.TestCase):
    def test_reproducibility_notebook_is_executed_and_conclusive(self) -> None:
        path = W12 / "W12_Reproducibility_Audit.ipynb"
        self.assertTrue(path.is_file(), path)
        notebook = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(notebook.get("nbformat"), 4)
        code_cells = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]
        self.assertGreaterEqual(len(code_cells), 5)
        self.assertTrue(all(cell.get("execution_count") is not None for cell in code_cells))
        errors = [
            output
            for cell in code_cells
            for output in cell.get("outputs", [])
            if output.get("output_type") == "error"
        ]
        self.assertEqual(errors, [])
        source = "\n".join(
            "".join(cell.get("source", [])) for cell in notebook["cells"]
        )
        for phrase in (
            "Primary contrast recomputation",
            "Conditional measurement stress",
            "Artifact identity",
            "Evidence boundary",
        ):
            self.assertIn(phrase, source)
        rendered_outputs = json.dumps(
            [output for cell in code_cells for output in cell.get("outputs", [])],
            ensure_ascii=False,
        )
        for phrase in ("AUDIT_PASS", "-55.0", "-40.1", "+18.8", "14/16"):
            self.assertIn(phrase, rendered_outputs)

        runtime_match = re.search(
            r"['\"]python_version['\"]:\s*['\"]([^'\"]+)", rendered_outputs
        )
        self.assertIsNotNone(runtime_match)
        self.assertEqual(
            notebook["metadata"]["language_info"]["version"],
            runtime_match.group(1),
        )


class VerifierContractTests(unittest.TestCase):
    def test_integrated_verifier_covers_current_and_admitted_evidence(self) -> None:
        verifier = read("verify_w12.py")
        for phrase in (
            "week-12/test_w12.py",
            "week-11/verify_w11.py",
            "W12 VERIFICATION PASSED",
            "subprocess.run",
        ):
            self.assertIn(phrase, verifier)
        self.assertNotIn("http://", verifier)
        self.assertNotIn("https://", verifier)

    def test_verifier_exposes_pdf_and_four_notebook_gates(self) -> None:
        path = W12 / "verify_w12.py"
        spec = importlib.util.spec_from_file_location("verify_w12", path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        package = ROOT / "week-11" / "W11_Reproducibility_Package"
        notebooks = module.notebook_paths(package)
        relative = [path.relative_to(package).as_posix() for path in notebooks]
        self.assertEqual(
            relative,
            [
                "source/week-04/W04_Extended_Benchmark.ipynb",
                "source/week-05/W05_Experiment_Notebook.ipynb",
                "source/week-06/W06_Experiment2_Notebook.ipynb",
                "source/week-07/W07_Analysis_Notebook.ipynb",
            ],
        )
        self.assertTrue(callable(module.run_notebook))
        pdf_result = module.verify_pdf(W12 / "W12_Final_Paper.pdf")
        self.assertGreaterEqual(pdf_result["pages"], 10)
        self.assertLessEqual(pdf_result["pages"], 12)


if __name__ == "__main__":
    unittest.main(verbosity=2)
