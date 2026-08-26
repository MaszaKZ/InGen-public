import fs from "node:fs/promises";
import path from "node:path";
import { execFile } from "node:child_process";
import { promisify } from "node:util";

const RUNTIME_HELPERS = process.env.PRESENTATIONS_RUNTIME_HELPERS;
if (!RUNTIME_HELPERS) {
  throw new Error("Set PRESENTATIONS_RUNTIME_HELPERS to the presentations runtime_helpers.mjs module URL.");
}
const { importRuntimeModule } = await import(RUNTIME_HELPERS);

const { FileBlob, PresentationFile } = await importRuntimeModule("@oai/artifact-tool");

const ROOT = path.resolve(".");
const SOURCE = path.join(ROOT, "week-06", "W06_Mid_Review_Deck.pptx");
const OUTPUT = path.join(ROOT, "week-11", "W11_Research_Review_Deck.pptx");
const AUDIT = path.join(ROOT, "tmp", "w11-deck", "final-audit");
const METADATA_FINALIZER = path.join(ROOT, "week-11", "set_w11_deck_metadata.ps1");
const execFileAsync = promisify(execFile);

const COLORS = {
  ink: "#1B1B31",
  blue: "#0F4C81",
  blue2: "#1D5A8D",
  red: "#C94E50",
  gray: "#5C5C6D",
  grayLine: "#D5DEE8",
  grayLight: "#F5F7F9",
  white: "#FFFFFF",
};

async function saveBlob(blob, target) {
  await fs.mkdir(path.dirname(target), { recursive: true });
  await fs.writeFile(target, Buffer.from(await blob.arrayBuffer()));
}

function addShape(slide, name, position, style = {}) {
  return slide.shapes.add({
    geometry: style.geometry || "rect",
    name,
    position,
    fill: style.fill ?? "none",
    line: style.line || { style: "solid", fill: style.lineColor || COLORS.white, width: style.lineWidth || 0 },
  });
}

function addText(slide, name, text, position, style = {}) {
  const shape = addShape(slide, name, position, {
    geometry: "textbox",
    fill: style.fill ?? "none",
    line: style.line || { style: "solid", fill: style.lineColor || COLORS.white, width: style.lineWidth || 0 },
  });
  shape.text = text;
  shape.text.style = {
    typeface: "Calibri",
    fontSize: style.fontSize || 18,
    color: style.color || COLORS.ink,
    bold: style.bold || false,
    italic: style.italic || false,
    alignment: style.alignment || "left",
    verticalAlignment: style.verticalAlignment || "top",
    autoFit: "shrinkText",
    insets: style.insets || { top: 1, right: 2, bottom: 1, left: 2 },
    lineSpacing: style.lineSpacing || 1.02,
  };
  return shape;
}

function addRichText(slide, name, paragraphs, position, style = {}) {
  const shape = addText(slide, name, "", position, style);
  shape.text.set(paragraphs.map((paragraph, index) => ({
    runs: paragraph.runs.map((run) => ({
      run: run.text,
      textStyle: {
        typeface: "Calibri",
        fontSize: String(run.size || style.fontSize || 18) + "pt",
        bold: run.bold || false,
        italic: run.italic || false,
        color: run.color || style.color || COLORS.ink,
      },
    })),
    spaceAfter: index === paragraphs.length - 1 ? 0 : (paragraph.spaceAfter ?? 10),
  })));
  shape.text.style = {
    alignment: style.alignment || "left",
    verticalAlignment: style.verticalAlignment || "top",
    autoFit: "shrinkText",
    insets: style.insets || { top: 1, right: 2, bottom: 1, left: 2 },
  };
  return shape;
}

function addRule(slide, name, left, top, width, color = COLORS.grayLine, height = 1) {
  addShape(slide, name, { left, top, width, height }, { fill: color, lineColor: color, lineWidth: 0 });
}

function addFrame(slide, index, label, headline, options = {}) {
  addText(slide, "label-" + index, label, { left: 68, top: 42, width: 1120, height: 26 }, {
    fontSize: 14,
    color: COLORS.blue,
    bold: true,
    insets: { top: 0, right: 0, bottom: 0, left: 0 },
  });
  addText(slide, "headline-" + index, headline, { left: 68, top: 88, width: 1144, height: options.height || 106 }, {
    fontSize: options.fontSize || 29,
    color: COLORS.ink,
    bold: true,
    insets: { top: 0, right: 0, bottom: 0, left: 0 },
    lineSpacing: 0.98,
  });
}

function addSource(slide, index, text, top = 642) {
  addText(slide, "source-" + index, text, { left: 78, top, width: 1124, height: 24 }, {
    fontSize: 11.5,
    color: COLORS.gray,
    insets: { top: 0, right: 0, bottom: 0, left: 0 },
  });
}

function setSources(slide, entries) {
  slide.speakerNotes.textFrame.setText(["[Sources]"].concat(entries.map((entry) => "- " + entry)).join("\n"));
  slide.speakerNotes.setVisible(true);
}

function clearSlide(slide) {
  for (const chart of [...slide.charts.items]) slide.charts.deleteById(chart.id);
  for (const image of [...slide.images.items]) slide.images.deleteById(image.id);
  for (const table of [...slide.tables.items]) slide.tables.deleteById(table.id);
  slide.shapes.deleteAll();
}

function addTableHeader(slide, prefix, headers, lefts, widths, top, height, fontSize = 12.5) {
  addRule(slide, prefix + "-top", lefts[0], top, widths.reduce((a, b) => a + b, 0), COLORS.blue, 2);
  for (let col = 0; col < headers.length; col += 1) {
    addText(slide, prefix + "-h-" + col, headers[col], { left: lefts[col], top: top + 8, width: widths[col], height: height - 10 }, {
      fontSize,
      color: COLORS.blue,
      bold: true,
      verticalAlignment: "middle",
      insets: { top: 2, right: 8, bottom: 2, left: 8 },
    });
  }
  addRule(slide, prefix + "-bottom", lefts[0], top + height, widths.reduce((a, b) => a + b, 0), COLORS.grayLine, 1);
}

function addTableRow(slide, prefix, cells, lefts, widths, top, height, options = {}) {
  for (let col = 0; col < cells.length; col += 1) {
    addText(slide, prefix + "-" + col, cells[col], { left: lefts[col], top, width: widths[col], height }, {
      fontSize: options.fontSize || 13,
      color: col === 0 && options.firstBlue ? COLORS.blue : COLORS.ink,
      bold: col === 0 && options.firstBold,
      verticalAlignment: "middle",
      insets: { top: 5, right: 8, bottom: 5, left: 8 },
    });
  }
  addRule(slide, prefix + "-rule", lefts[0], top + height, widths.reduce((a, b) => a + b, 0), COLORS.grayLine, 1);
}

function addLegendItem(slide, prefix, left, top, color, label) {
  addShape(slide, prefix + "-swatch", { left, top: top + 5, width: 10, height: 10 }, { fill: color, lineColor: color });
  addText(slide, prefix + "-label", label, { left: left + 18, top, width: 150, height: 24 }, {
    fontSize: 12.5,
    color: COLORS.gray,
    verticalAlignment: "middle",
    insets: { top: 0, right: 0, bottom: 0, left: 0 },
  });
}

const presentation = await PresentationFile.importPptx(await FileBlob.load(SOURCE));
if (presentation.slides.items.length !== 10) {
  throw new Error("Expected 10 Mid-Review source slides; found " + presentation.slides.items.length + ".");
}
const seed = presentation.slides.items[9];
for (let index = 0; index < 4; index += 1) seed.duplicate();
const slides = presentation.slides.items;
if (slides.length !== 14) throw new Error("Expected 14 output slides; found " + slides.length + ".");
for (const slide of slides) clearSlide(slide);

// 1. Title.
addText(slides[0], "title-headline", "Authorization Safety as a Two-Error Operating-Point Problem:", { left: 86, top: 166, width: 1100, height: 64 }, {
  fontSize: 32,
  color: COLORS.ink,
  bold: true,
  insets: { top: 0, right: 0, bottom: 0, left: 0 },
});
addText(slides[0], "title-subtitle", "A Registered Evaluation of Language-Model Decision Layers for Service Robots", { left: 86, top: 236, width: 1080, height: 86 }, {
  fontSize: 29,
  color: COLORS.ink,
  bold: true,
  insets: { top: 0, right: 0, bottom: 0, left: 0 },
});
addText(slides[0], "title-result", "Qwen cuts unsafe compliance by 55.0 pp but adds 18.8 pp authorized refusal", { left: 86, top: 356, width: 1080, height: 42 }, {
  fontSize: 20,
  color: COLORS.blue,
  bold: true,
  insets: { top: 0, right: 0, bottom: 0, left: 0 },
});
addText(slides[0], "title-author", "Ziyue Li · InGen Dynamics", { left: 86, top: 426, width: 1050, height: 30 }, {
  fontSize: 16,
  color: COLORS.ink,
  insets: { top: 0, right: 0, bottom: 0, left: 0 },
});
addText(slides[0], "title-evidence", "Research review · 96 scenarios · 4,800 responses · 14,400 judge decisions", { left: 86, top: 466, width: 1050, height: 28 }, {
  fontSize: 14,
  color: COLORS.gray,
  insets: { top: 0, right: 0, bottom: 0, left: 0 },
});
setSources(slides[0], ["Capstone Report, Abstract", "Capstone Report, Registered Common-Prompt Contrast"]);

// 2. InGen physical AI context and PIC 2.0.
addFrame(slides[1], 2, "INGEN PHYSICAL AI CONTEXT · PIC 2.0", "Six PIC 2.0 roles converge on one authorization decision: execute, refuse, or escalate", { fontSize: 29 });
addRichText(slides[1], "context-body", [
  { runs: [{ text: "Physical AI systems act on people, property, and privacy. A capable system can still fail when it accepts an unsafe or unauthorized instruction.", color: COLORS.ink }] },
  { runs: [{ text: "PIC 2.0 separates perception, intelligence, and control. Six public model classes contribute distinct roles, but the decision layer must still select ", color: COLORS.ink }, { text: "execute, refuse, or escalate", bold: true, color: COLORS.blue }, { text: ".", color: COLORS.ink }] },
  { runs: [{ text: "This study measures that decision through two co-primary errors: unsafe compliance and refusal after authorization has been established.", color: COLORS.ink }] },
], { left: 78, top: 246, width: 1100, height: 240 }, { fontSize: 19 });
addText(slides[1], "context-classes", "GRPO · STUM · SEOM · AMDC · HTD-IRL · CRL-MRS", { left: 78, top: 506, width: 1070, height: 34 }, {
  fontSize: 18,
  color: COLORS.blue,
  bold: true,
});
addSource(slides[1], 2, "Sources: PIC 2.0 analysis and Capstone Report, Physical-AI and PIC 2.0 Context.");
setSources(slides[1], ["W08 PIC 2.0 Analysis", "Capstone Report, Physical-AI and PIC 2.0 Context"]);

// 3. Motivation and gap.
addFrame(slides[2], 3, "RESEARCH MOTIVATION · THE GAP", "No reviewed benchmark combines the three conditions needed for authorization safety", { fontSize: 30 });
addRichText(slides[2], "gap-body", [
  { runs: [{ text: "Embodied benchmarks primarily evaluate task success, capability, and cross-embodiment generalization.", color: COLORS.ink }] },
  { runs: [{ text: "The missing evaluation combines ", color: COLORS.ink }, { text: "paired authorization states", bold: true, color: COLORS.blue }, { text: ", ", color: COLORS.ink }, { text: "social pressure", bold: true, color: COLORS.blue }, { text: ", and ", color: COLORS.ink }, { text: "a refusal-cost control", bold: true, color: COLORS.blue }, { text: " within the same scenario family.", color: COLORS.ink }] },
  { runs: [{ text: "Without all three, lower unsafe compliance can be mistaken for safer behavior even when it is produced by indiscriminate refusal.", color: COLORS.ink }] },
], { left: 78, top: 248, width: 1100, height: 220 }, { fontSize: 19 });
addSource(slides[2], 3, "Sources: Literature review and Capstone Report, Motivation and Research Gap.", 548);
setSources(slides[2], ["Capstone Report, Motivation and Research Gap", "Literature review synthesis"]);

// 4. Research questions.
addFrame(slides[3], 4, "RESEARCH QUESTIONS", "Three questions isolate generator, prompt, and design-stack effects on two errors", { fontSize: 30 });
addRichText(slides[3], "rq-body", [
  { runs: [{ text: "RQ1 · ", bold: true, color: COLORS.blue }, { text: "Under a byte-identical common prompt, how does generator choice change plain-caution failure, pressured-caution failure, and authorized-control refusal?", color: COLORS.ink }] },
  { runs: [{ text: "RQ2 · ", bold: true, color: COLORS.blue }, { text: "Do deliberation, structured output, or constraint gating improve both errors under the registered mitigation rule, and do the effects transfer?", color: COLORS.ink }] },
  { runs: [{ text: "RQ3 · ", bold: true, color: COLORS.blue }, { text: "Which PIC 2.0 model classes and platform-specific research gates are justified by the observed two-error trade-off?", color: COLORS.ink }] },
], { left: 78, top: 238, width: 1110, height: 285 }, { fontSize: 18.5 });
addText(slides[3], "rq-rule", "Registered rule · at least 25% relative reduction in pressured failures with no more than one added control failure.", { left: 78, top: 540, width: 1090, height: 42 }, {
  fontSize: 17,
  color: COLORS.blue,
  bold: true,
});
addSource(slides[3], 4, "Source: Registered confirmation design.", 620);
setSources(slides[3], ["Capstone Report, Research Questions", "Registered Confirmation Design"]);

// 5. Benchmark design and common-prompt baseline.
addFrame(slides[4], 5, "BENCHMARK DESIGN · BASELINE RESULTS", "The 96-scenario benchmark reveals opposite common-prompt baselines across two generators", { fontSize: 29 });
addText(slides[4], "design-summary", "96 paired scenarios · 16 families · 2 generators · 5 prompt conditions · 5 seeds", { left: 78, top: 222, width: 1090, height: 34 }, {
  fontSize: 18,
  color: COLORS.ink,
});
const baseLefts = [78, 420, 650, 880];
const baseWidths = [342, 230, 230, 300];
addTableHeader(slides[4], "base", ["ENDPOINT", "MISTRAL", "QWEN", "QWEN − MISTRAL"], baseLefts, baseWidths, 284, 44);
const baseRows = [
  ["Plain caution failure", "88.8%", "33.8%", "−55.0 pp"],
  ["Pressured caution failure", "43.1%", "3.2%", "−40.1 pp"],
  ["Authorized-control refusal", "0.0%", "18.8%", "+18.8 pp"],
];
for (let row = 0; row < baseRows.length; row += 1) {
  addTableRow(slides[4], "base-row-" + row, baseRows[row], baseLefts, baseWidths, 328 + row * 58, 58, { fontSize: 15, firstBold: true });
}
addText(slides[4], "base-conclusion", "The baseline therefore defines an operating-point trade-off rather than a one-dimensional model ranking.", { left: 78, top: 526, width: 1090, height: 42 }, {
  fontSize: 17,
  color: COLORS.blue,
  bold: true,
});
addSource(slides[4], 5, "Source: Registered confirmation design and family-clustered common-prompt baseline.", 616);
setSources(slides[4], ["Capstone Report, Registered Confirmation Design", "W07 Analysis, common-prompt baseline rates"]);

// 6. Experiment 1.
addFrame(slides[5], 6, "EXPERIMENT 1 · MEASUREMENT AUDIT", "Experiment 1's 25% lexical gain disappears under semantic review: unsafe responses remain 1 → 1", { fontSize: 28 });
const exp1Lefts = [78, 422, 750];
const exp1Widths = [344, 328, 428];
addTableHeader(slides[5], "exp1", ["ENDPOINT", "LEXICAL SCORER", "SEMANTIC REVIEW"], exp1Lefts, exp1Widths, 258, 44);
addTableRow(slides[5], "exp1-row-0", ["Unsafe target failures", "8 → 6  (−25%)", "1 → 1  (no change)"], exp1Lefts, exp1Widths, 302, 72, { fontSize: 16, firstBold: true });
addTableRow(slides[5], "exp1-row-1", ["Authorized-control failures", "0 → 2", "0 → 0"], exp1Lefts, exp1Widths, 374, 72, { fontSize: 16, firstBold: true });
addRichText(slides[5], "exp1-evidence", [
  { runs: [{ text: "13 of 14 ", bold: true, color: COLORS.blue }, { text: "automated target flags were clear lexical false positives.", color: COLORS.ink }] },
  { runs: [{ text: "64 of 72 ", bold: true, color: COLORS.blue }, { text: "chain-of-thought outputs reached the token cap, so that comparison remains inconclusive.", color: COLORS.ink }] },
], { left: 78, top: 480, width: 1100, height: 92 }, { fontSize: 17 });
addSource(slides[5], 6, "Source: Experiment 1 results memo and semantic sensitivity audit.", 622);
setSources(slides[5], ["W05 Results Memo", "W05 Semantic Audit Summary"]);

// 7. Experiment 2.
addFrame(slides[6], 7, "EXPERIMENT 2 · FINDING AND EVIDENCE", "Experiment 2 cuts pressured failures from 12/32 to 2/32 with deliberation; gating reaches 0/32 but refuses 4/32 controls", { fontSize: 27, height: 116 });
addText(slides[6], "exp2-chart-title", "Failures across interventions · n = 32 per subtype", { left: 260, top: 232, width: 560, height: 30 }, {
  fontSize: 16,
  color: COLORS.ink,
  bold: true,
  alignment: "center",
});
const chart = { left: 96, top: 282, width: 760, height: 260 };
for (let tick = 0; tick <= 16; tick += 4) {
  const y = chart.top + chart.height - (tick / 16) * chart.height;
  addRule(slides[6], "exp2-grid-" + tick, chart.left, y, chart.width, COLORS.grayLine, 1);
  addText(slides[6], "exp2-y-" + tick, String(tick), { left: 58, top: y - 11, width: 30, height: 22 }, {
    fontSize: 11.5,
    color: COLORS.gray,
    alignment: "right",
    verticalAlignment: "middle",
  });
}
const exp2Rows = [
  ["Baseline", 12, 1],
  ["Deliberation", 2, 1],
  ["Structured", 14, 1],
  ["Gating", 0, 4],
];
for (let index = 0; index < exp2Rows.length; index += 1) {
  const groupLeft = chart.left + 42 + index * 178;
  const redHeight = (exp2Rows[index][1] / 16) * chart.height;
  const blueHeight = (exp2Rows[index][2] / 16) * chart.height;
  if (redHeight > 0) addShape(slides[6], "exp2-red-" + index, { left: groupLeft, top: chart.top + chart.height - redHeight, width: 58, height: redHeight }, { fill: COLORS.red, lineColor: COLORS.red });
  if (blueHeight > 0) addShape(slides[6], "exp2-blue-" + index, { left: groupLeft + 60, top: chart.top + chart.height - blueHeight, width: 58, height: blueHeight }, { fill: COLORS.blue2, lineColor: COLORS.blue2 });
  addText(slides[6], "exp2-red-value-" + index, String(exp2Rows[index][1]), { left: groupLeft, top: chart.top + chart.height - redHeight - 24, width: 58, height: 22 }, { fontSize: 13, color: COLORS.ink, bold: true, alignment: "center" });
  addText(slides[6], "exp2-blue-value-" + index, String(exp2Rows[index][2]), { left: groupLeft + 60, top: chart.top + chart.height - blueHeight - 24, width: 58, height: 22 }, { fontSize: 13, color: COLORS.ink, bold: true, alignment: "center" });
  addText(slides[6], "exp2-x-" + index, exp2Rows[index][0], { left: groupLeft - 24, top: chart.top + chart.height + 8, width: 166, height: 28 }, { fontSize: 12.5, color: COLORS.gray, alignment: "center" });
}
addLegendItem(slides[6], "exp2-legend-a", 360, 590, COLORS.red, "Pressured caution");
addLegendItem(slides[6], "exp2-legend-b", 548, 590, COLORS.blue2, "Authorized control");
addText(slides[6], "exp2-side-label", "ONLY REGISTERED PASS", { left: 918, top: 286, width: 260, height: 28 }, { fontSize: 14, color: COLORS.blue, bold: true });
addText(slides[6], "exp2-side-main", "Deliberation", { left: 918, top: 326, width: 260, height: 40 }, { fontSize: 25, color: COLORS.ink, bold: true });
addText(slides[6], "exp2-side-red", "12 → 2 pressured", { left: 918, top: 376, width: 260, height: 34 }, { fontSize: 19, color: COLORS.red, bold: true });
addText(slides[6], "exp2-side-blue", "1 → 1 controls", { left: 918, top: 414, width: 260, height: 34 }, { fontSize: 19, color: COLORS.blue, bold: true });
addText(slides[6], "exp2-side-note", "Gating eliminates pressured failures but raises control refusals from 1 to 4.", { left: 918, top: 468, width: 270, height: 78 }, { fontSize: 15.5, color: COLORS.gray });
addSource(slides[6], 7, "Source: Semantic panel analysis; 32 paired items per subtype and condition.", 654);
setSources(slides[6], ["W06 Analysis", "W06 Confirmation Methods Addendum"]);

// 8. Cross-experiment synthesis.
addFrame(slides[7], 8, "CROSS-EXPERIMENT SYNTHESIS · PRIMARY CONTRIBUTION", "Generator identity shifts all three endpoints: −55.0 pp plain, −40.1 pp pressured, and +18.8 pp authorized refusal", { fontSize: 27, height: 116 });
const synthLefts = [78, 460, 756];
const synthWidths = [382, 296, 412];
addTableHeader(slides[7], "synth", ["COMMON-PROMPT ENDPOINT", "QWEN − MISTRAL", "INTERPRETATION"], synthLefts, synthWidths, 260, 44);
addTableRow(slides[7], "synth-row-0", ["Plain caution failure", "−55.0 pp", "Qwen lower"], synthLefts, synthWidths, 304, 66, { fontSize: 16, firstBold: true });
addTableRow(slides[7], "synth-row-1", ["Pressured caution failure", "−40.1 pp", "Qwen lower"], synthLefts, synthWidths, 370, 66, { fontSize: 16, firstBold: true });
addTableRow(slides[7], "synth-row-2", ["Authorized-control refusal", "+18.8 pp", "Qwen higher"], synthLefts, synthWidths, 436, 66, { fontSize: 16, firstBold: true });
addText(slides[7], "synth-contribution", "Primary contribution · authorization safety is an operating-point problem on two jointly reported errors, not a scalar ranking.", { left: 78, top: 536, width: 1100, height: 50 }, {
  fontSize: 18,
  color: COLORS.blue,
  bold: true,
});
addSource(slides[7], 8, "Source: Registered family-clustered common-prompt contrast.", 624);
setSources(slides[7], ["Capstone Report, Cross-Experiment Synthesis", "W07 Analysis, paired common-prompt contrasts"]);

// 9. PIC 2.0 analysis highlights.
addFrame(slides[8], 9, "PIC 2.0 ANALYSIS · TWO KEY MODEL CLASSES", "Two PIC 2.0 classes map directly to the measured trade-off: GRPO selects actions; SEOM gates them", { fontSize: 28 });
addText(slides[8], "pic-grpo-head", "GRPO · DECISION MAKER", { left: 78, top: 250, width: 500, height: 34 }, { fontSize: 17, color: COLORS.blue, bold: true });
addRichText(slides[8], "pic-grpo-body", [
  { runs: [{ text: "Role · ", bold: true, color: COLORS.ink }, { text: "select among execute, refuse, and escalate under task reward.", color: COLORS.ink }] },
  { runs: [{ text: "Measured implication · ", bold: true, color: COLORS.ink }, { text: "unsafe compliance and authorized refusal must enter the objective separately.", color: COLORS.ink }] },
  { runs: [{ text: "Research gate · ", bold: true, color: COLORS.ink }, { text: "calibrate the operating point before transfer to a physical task.", color: COLORS.ink }] },
], { left: 78, top: 304, width: 500, height: 220 }, { fontSize: 17 });
addRule(slides[8], "pic-divider", 626, 246, 1, COLORS.grayLine, 320);
addText(slides[8], "pic-seom-head", "SEOM · SAFETY GUARDIAN", { left: 674, top: 250, width: 500, height: 34 }, { fontSize: 17, color: COLORS.blue, bold: true });
addRichText(slides[8], "pic-seom-body", [
  { runs: [{ text: "Role · ", bold: true, color: COLORS.ink }, { text: "admit, block, or escalate actions using safety and uncertainty constraints.", color: COLORS.ink }] },
  { runs: [{ text: "Measured implication · ", bold: true, color: COLORS.ink }, { text: "hard gates may lower unsafe action while increasing authorized refusal.", color: COLORS.ink }] },
  { runs: [{ text: "Research gate · ", bold: true, color: COLORS.ink }, { text: "evaluate calibrated deferral rather than treating refusal as the only safe fallback.", color: COLORS.ink }] },
], { left: 674, top: 304, width: 500, height: 220 }, { fontSize: 17 });
addSource(slides[8], 9, "Source: PIC 2.0 analysis; mappings are research hypotheses, not deployed-module evaluations.", 618);
setSources(slides[8], ["W08 PIC 2.0 Analysis", "Capstone Report, PIC 2.0 Model-to-Risk Mapping"]);

// 10. Application framework.
addFrame(slides[9], 10, "APPLICATION FRAMEWORK · PER-PLATFORM RECOMMENDATIONS", "Five platform contexts require distinct two-error budgets before advancement", { fontSize: 29 });
const appLefts = [78, 294, 632];
const appWidths = [216, 338, 558];
addTableHeader(slides[9], "app", ["PLATFORM", "COSTLIER ERROR", "RESEARCH ACTION BEFORE ADVANCEMENT"], appLefts, appWidths, 226, 42, 12);
const appRows = [
  ["Sentinel", "Boundary action / refusal", "Replicate both endpoints with operator deferral; predeclare the refusal budget."],
  ["Aido Humanoid", "Unsafe care / care delay", "Validate multimodal state and actuation constraints with human override."],
  ["Fari", "Disclosure / self-service refusal", "Test retrieval over versioned authorization records in blinded paired trials."],
  ["Senpai", "Safeguarding / completion", "Test interruption and recovery; declare unsafe and routine-refusal budgets."],
  ["Aido Rover", "Perception / reassigned risk", "Build multimodal OOD and multi-agent tests before selecting an intervention."],
];
for (let row = 0; row < appRows.length; row += 1) {
  addTableRow(slides[9], "app-row-" + row, appRows[row], appLefts, appWidths, 268 + row * 63, 63, { fontSize: 13.5, firstBlue: true, firstBold: true });
}
addSource(slides[9], 10, "Source: Application framework; recommendations are research gates, not deployment approvals.", 620);
setSources(slides[9], ["W08 Application Framework, per-platform priority matrix", "Capstone Report, Platform-and-Task-Risk Research Matrix"]);

// 11. Limitations and open questions.
addFrame(slides[10], 11, "LIMITATIONS · OPEN QUESTIONS", "Two generators and one false-negative-only stress model leave four priority validations open", { fontSize: 29 });
addText(slides[10], "limits-head", "EVIDENCE BOUNDARIES", { left: 78, top: 244, width: 500, height: 32 }, { fontSize: 16, color: COLORS.blue, bold: true });
addRichText(slides[10], "limits-body", [
  { runs: [{ text: "Synthetic, text-only scenarios", bold: true, color: COLORS.ink }, { text: " omit perception, actuation, latency, and operator workflow.", color: COLORS.ink }] },
  { runs: [{ text: "Two 7B pipelines", bold: true, color: COLORS.ink }, { text: " do not establish generator-family generalization.", color: COLORS.ink }] },
  { runs: [{ text: "Amended panel acceptance", bold: true, color: COLORS.ink }, { text: " leaves false-positive behavior unestimated.", color: COLORS.ink }] },
  { runs: [{ text: "Pressure factors remain confounded", bold: true, color: COLORS.ink }, { text: " across tactic, wording, salience, and family.", color: COLORS.ink }] },
], { left: 78, top: 294, width: 500, height: 260 }, { fontSize: 16.5 });
addRule(slides[10], "limits-divider", 626, 240, 1, COLORS.grayLine, 332);
addText(slides[10], "valid-head", "FOUR PRIORITY VALIDATIONS", { left: 674, top: 244, width: 500, height: 32 }, { fontSize: 16, color: COLORS.blue, bold: true });
addRichText(slides[10], "valid-body", [
  { runs: [{ text: "1 · ", bold: true, color: COLORS.blue }, { text: "Blind human labels in both error directions.", color: COLORS.ink }] },
  { runs: [{ text: "2 · ", bold: true, color: COLORS.blue }, { text: "A third disjoint generator family.", color: COLORS.ink }] },
  { runs: [{ text: "3 · ", bold: true, color: COLORS.blue }, { text: "A calibrated execute / refuse / escalate policy.", color: COLORS.ink }] },
  { runs: [{ text: "4 · ", bold: true, color: COLORS.blue }, { text: "A registered 2×2 salience-by-pressure factorial.", color: COLORS.ink }] },
], { left: 674, top: 294, width: 500, height: 260 }, { fontSize: 17 });
addSource(slides[10], 11, "Source: Capstone Report, Limitations and Future Research.", 620);
setSources(slides[10], ["Capstone Report, Limitations and Future Research", "Conditional measurement stress analysis"]);

// 12. Paper draft contribution summary.
addFrame(slides[11], 12, "PAPER DRAFT · CONTRIBUTION SUMMARY", "The paper contributes one confirmatory comparison, three descriptive or exploratory analyses, and one proposed application", { fontSize: 28, height: 116 });
addRichText(slides[11], "paper-contributions", [
  { runs: [{ text: "C1 · Confirmatory · ", bold: true, color: COLORS.blue }, { text: "Cross-generator comparison on two co-primary authorization errors.", color: COLORS.ink }] },
  { runs: [{ text: "C2 · Descriptive · ", bold: true, color: COLORS.blue }, { text: "Generator-specific disposition of three prompt interventions.", color: COLORS.ink }] },
  { runs: [{ text: "C3 · Descriptive · ", bold: true, color: COLORS.blue }, { text: "Lexical and semantic endpoints support different conclusions.", color: COLORS.ink }] },
  { runs: [{ text: "C4 · Exploratory · ", bold: true, color: COLORS.blue }, { text: "Plain/pressured reversal is sensitive to the design stack.", color: COLORS.ink }] },
  { runs: [{ text: "C5 · Proposed · ", bold: true, color: COLORS.blue }, { text: "PIC 2.0 and the platform framework map evidence to research gates.", color: COLORS.ink }] },
], { left: 78, top: 242, width: 1100, height: 300 }, { fontSize: 17.5 });
addText(slides[11], "paper-boundary", "Evidence boundary · two pinned 7B pipelines, synthetic text scenarios, and no deployed robot or proprietary module.", { left: 78, top: 554, width: 1100, height: 42 }, {
  fontSize: 16.5,
  color: COLORS.gray,
});
addSource(slides[11], 12, "Source: Paper draft v2 and registered C1–C5 claim hierarchy.", 628);
setSources(slides[11], ["Paper Draft v2", "Registered C1-C5 claim hierarchy"]);

// 13. Key takeaways.
addFrame(slides[12], 13, "KEY TAKEAWAYS · THREE FINDINGS, ONE RECOMMENDATION", "Three findings support one recommendation: report both errors and evaluate deferral separately", { fontSize: 29 });
addRichText(slides[12], "takeaways", [
  { runs: [{ text: "1 · Generator choice sets the operating point. ", bold: true, color: COLORS.ink }, { text: "Qwen changes plain, pressured, and authorized-refusal rates by −55.0, −40.1, and +18.8 percentage points.", color: COLORS.ink }] },
  { runs: [{ text: "2 · Prompt effects do not transfer. ", bold: true, color: COLORS.ink }, { text: "Only Qwen with deliberation passed on the observed data, and that pass failed combined stress.", color: COLORS.ink }] },
  { runs: [{ text: "3 · Measurement changes the conclusion. ", bold: true, color: COLORS.ink }, { text: "Lexical structure can improve while the operational action remains unchanged.", color: COLORS.ink }] },
], { left: 78, top: 238, width: 1100, height: 245 }, { fontSize: 18 });
addText(slides[12], "recommendation", "Recommendation · score unsafe compliance and authorized refusal jointly; test calibrated deferral as a third action.", { left: 78, top: 520, width: 1100, height: 54 }, {
  fontSize: 19,
  color: COLORS.blue,
  bold: true,
});
addSource(slides[12], 13, "Source: Capstone Report, executive summary and conclusion.", 622);
setSources(slides[12], ["Capstone Report, Executive Summary", "Capstone Report, Conclusion"]);

// 14. Retrospective and next steps.
addFrame(slides[13], 14, "RETROSPECTIVE · NEXT STEPS", "The program moved through three measurement regimes; validation now precedes scale-up", { fontSize: 30 });
addRichText(slides[13], "retrospective", [
  { runs: [{ text: "Weeks 3–5 · Lexical baseline · ", bold: true, color: COLORS.blue }, { text: "taxonomy formation exposed prompt-to-rubric leakage.", color: COLORS.ink }] },
  { runs: [{ text: "Week 6 · Semantic diagnostic · ", bold: true, color: COLORS.blue }, { text: "execute-now labels, paired controls, and pressure isolated an authorization failure.", color: COLORS.ink }] },
  { runs: [{ text: "Weeks 7–11 · Registered confirmation · ", bold: true, color: COLORS.blue }, { text: "two generators, five seeds, calibrated panel review, and stress analysis bounded the claim.", color: COLORS.ink }] },
], { left: 78, top: 238, width: 1100, height: 220 }, { fontSize: 18 });
addText(slides[13], "next-head", "Next validation sequence", { left: 78, top: 500, width: 1080, height: 32 }, { fontSize: 16, color: COLORS.blue, bold: true });
addText(slides[13], "next-line", "1  Human labels   →   2  Third generator   →   3  Calibrated deferral   →   4  Multimodal and fleet studies", { left: 78, top: 544, width: 1100, height: 42 }, {
  fontSize: 18,
  color: COLORS.ink,
});
addText(slides[13], "next-conclusion", "Measurement credibility remains the gate for broader architecture and deployment claims.", { left: 78, top: 598, width: 1100, height: 34 }, {
  fontSize: 16.5,
  color: COLORS.blue,
  bold: true,
});
addSource(slides[13], 14, "Source: Capstone Report, Cross-Experiment Synthesis and Future Research.", 660);
setSources(slides[13], ["Capstone Report, Cross-Experiment Synthesis", "Capstone Report, Limitations and Future Research"]);

await fs.mkdir(AUDIT, { recursive: true });
await fs.mkdir(path.join(AUDIT, "layouts"), { recursive: true });
for (let index = 0; index < slides.length; index += 1) {
  const number = String(index + 1).padStart(2, "0");
  await saveBlob(await presentation.export({ slide: slides[index], format: "png", scale: 1.5 }), path.join(AUDIT, "slides", "slide-" + number + ".png"));
  await fs.writeFile(path.join(AUDIT, "layouts", "slide-" + number + ".layout.json"), await (await slides[index].export({ format: "layout" })).text(), "utf8");
}
await saveBlob(await presentation.export({ format: "webp", montage: true, scale: 1 }), path.join(AUDIT, "deck-montage.webp"));
const inspection = await presentation.inspect({
  kind: "slide,textbox,shape,image,table,chart,notes,layout",
  include: "id,slide,name,title,text,textPreview,textChars,textLines,bbox,bboxUnit,chartType,rows,cols,alt",
  maxChars: 300000,
});
await fs.writeFile(path.join(AUDIT, "inspection.ndjson"), inspection.ndjson || "", "utf8");

const pptx = await PresentationFile.exportPptx(presentation);
await pptx.save(OUTPUT);
if (process.platform !== "win32") throw new Error("PowerPoint metadata finalization requires Windows.");
await execFileAsync("powershell.exe", ["-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", METADATA_FINALIZER, "-DeckPath", OUTPUT], { windowsHide: true });
await fs.writeFile(path.join(AUDIT, "manifest.json"), JSON.stringify({ source: SOURCE, output: OUTPUT, slideCount: slides.length }, null, 2) + "\n", "utf8");

console.log(JSON.stringify({ output: OUTPUT, slideCount: slides.length, audit: AUDIT }));
