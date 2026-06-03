from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from mnemosyne.ui import APP_HTML
from mnemosyne.ui_css import APP_CSS as APP_STYLES
from mnemosyne.problem_authoring import AUTHORING_PROMPT
from mnemosyne.ui_html import (
    CATALOG_VIEW,
    CREATE_AGENT_VIEW,
    MANAGE_VIEW,
    PRACTICE_CODE_VIEW,
    TOPBAR_AND_PRACTICE_FRAME,
)

CHECKS_RUN = 0
FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    global CHECKS_RUN
    CHECKS_RUN += 1
    if condition:
        print(f"PASS {CHECKS_RUN:03d} {name}")
        return
    message = f"FAIL {CHECKS_RUN:03d} {name}"
    if detail:
        message += f": {detail}"
    print(message)
    FAILURES.append(message)


def contains_all(text: str, needles: list[str]) -> bool:
    return all(needle in text for needle in needles)


def between(text: str, start_marker: str, end_marker: str) -> str:
    try:
        start = text.index(start_marker)
        end = text.index(end_marker, start)
    except ValueError:
        return ""
    return text[start:end]


def main() -> int:
    direct_upload_state_at = APP_HTML.find("directJsonUploadedDraft = {content: text")
    direct_upload_clear_after_state = APP_HTML.find("clearDirectJsonAttachmentPicker(input)", direct_upload_state_at)
    manage_mode_branch = between(APP_HTML, "if (mode === 'manage')", "if (mode === 'llm')")
    load_problem_body = between(APP_HTML, "async function loadProblem(problemId)", "function renderMeta(problem)")
    catalog_manage_body = between(APP_HTML, "async function openCatalogProblemManager(problemId", "function setCatalogSearch(value)")

    check("design palette uses warm paper background", "#fcf9f4" in APP_STYLES)
    check("design typography includes Stitch fonts", contains_all(APP_HTML, ["Geist", "JetBrains Mono", "Literata"]))
    check("design uses Material Symbols", "Material Symbols Outlined" in APP_HTML)
    check("Markdown math renderer accepts inline and display math", contains_all(APP_HTML, ["pendingMathTypeset", "oneLineDisplayMath", "math-inline", "math-block"]))
    check("design applies Stitch density pass", "Stitch density pass" in APP_STYLES)
    check("core toolbar actions use icons", contains_all(APP_HTML, ["play_arrow", "send", "publish", "data_object", "check_circle"]))

    check("Practice has four learning tabs", contains_all(TOPBAR_AND_PRACTICE_FRAME, ["learningProblemTab", "learningTheoryTab", "learningExampleTab", "learningSolutionTab"]))
    check("Practice has Stitch code editor shell", contains_all(PRACTICE_CODE_VIEW, ["solution.py", "practice-editor-card", "code-editor"]))
    check("Practice has testcase/result console", contains_all(PRACTICE_CODE_VIEW, ["practiceTestsPane", "practiceResultPane", "practiceErrorPane", "Test Case", "Test Result", "Error"]))
    check("Practice does not duplicate Test Result title", "console-window-title" not in PRACTICE_CODE_VIEW)
    check("Practice has vertical resize and scroll affordance", contains_all(APP_HTML, ["practiceVerticalSplitter", "initPracticeVerticalSplitter", "--practice-console-height"]))
    check("Splitters use quiet hover-only dark handles", contains_all(APP_STYLES, ["--splitter-size: 10px", "--splitter-line: #31302d", "transparent 0 4px", "Color-only semantic pass"]))
    check("Semantic feedback colors avoid bright red green", contains_all(APP_STYLES, ["--feedback-ok-bg: #fcf9f4", "--feedback-error-bg: #31302d", "--feedback-warning-bg: #f7dfc2"]) and "#ecfdf5" not in APP_STYLES[-5000:] and "#fff1f2" not in APP_STYLES[-5000:])
    check("Practice result pane shows runtime errors", contains_all(APP_HTML, ["runtimeDetailEntries", "renderPracticeErrorPanel", "practiceErrorPane", "sanitizeLocalPaths"]))
    check("Practice result pane scrolls independently", "#practiceResultPane" in APP_STYLES and "#practiceErrorPane" in APP_STYLES and "overflow: auto !important" in APP_STYLES)
    check("Manage output hides local paths", "path: ${result.path}" not in APP_HTML and "sanitizeLocalPaths" in APP_HTML)

    check("Problem List uses catalog table", contains_all(CATALOG_VIEW, ["Problem Catalog", "catalog-search", "tagFilters"]) and "catalog-table" in APP_HTML)
    check("Problem List exposes row actions", contains_all(APP_HTML, ["openCatalogProblem", "openCatalogProblemManager", "deleteCatalogProblem"]))

    check("Manage uses two-pane workspace", contains_all(MANAGE_VIEW, ["manage-workspace", "manage-editor-pane", "manage-right-pane"]))
    check("Manage edits five-part learning unit", contains_all(MANAGE_VIEW, ["managerStatement", "managerTheory", "managerExamples", "managerSolutionExplanation", "managerReferenceSolution"]))
    check("Manage can start a new problem draft", contains_all(MANAGE_VIEW, ["managerCreateDraftButton", "Create"]) and contains_all(APP_HTML, ["startManagerCreateDraft", "blankManagerProblemDraft", "managerIsNewDraft"]))
    check("Manage create prompts for draft title without layout changes", contains_all(APP_HTML, ["promptManagerDraftTitle", "Problem title", "managerDirty = titleWasEdited"]) and "managerTitleInput" not in MANAGE_VIEW)
    check("Manage state is independent from Practice selection", "loadManagerWorkspace()" in manage_mode_branch and "currentProblem" not in manage_mode_branch and "selectManagerProblem(problemId)" not in load_problem_body and "loadProblem(problemId)" not in catalog_manage_body)
    check("Manage create preserves original editor layout", "managerProblemIdInput" not in MANAGE_VIEW and "managerTitleInput" not in MANAGE_VIEW and "managerFunctionNameInput" not in MANAGE_VIEW and "managerStarterCode" not in MANAGE_VIEW)
    check("Manage create loads a verifier-ready template", contains_all(APP_HTML, ["# Sum Values", "## Input / Output", "return sum(nums)", "solution_explanation", "visible_tests", "Return 0 when nums is empty."]))
    check("Manage exposes complexity editing", contains_all(MANAGE_VIEW, ["managerComplexityTime", "managerComplexitySpace", "managerComplexityPreview"]))
    check("Manage previews reference solution code", contains_all(MANAGE_VIEW, ["managerReferenceSolutionPreview", "reference_solution.py"]) and "syncManagerSolutionPreview" in APP_HTML)
    check("Manage Solution edit exposes reference code editor", contains_all(MANAGE_VIEW, ["solution-code-shell", "managerReferenceSolution"]) and ".manage-workspace:not(.manager-preview-mode) .solution-code-shell" in APP_STYLES)
    check("Manage Solution edit has visible caret and focus rail", contains_all(APP_STYLES, ["caret-color: #1f1a16", ".solution-code-shell .manager-reference-editor:focus", "inset 3px 0 0 #1f1a16"]))
    check("Manage matches Stitch right-rail order", MANAGE_VIEW.find("manage-right-header") < MANAGE_VIEW.find("Tags &amp; Labels") < MANAGE_VIEW.find("Test Cases") < MANAGE_VIEW.find("Verifier Feedback"))
    check("Manage removed old visible rail cards", "reference-pane" not in MANAGE_VIEW and "manager-topbar" not in MANAGE_VIEW)
    check("Manage uses text-only verifier feedback", contains_all(MANAGE_VIEW, ["Verifier Feedback", "managerOutput", "verifier-output"]) and "managerVerifierLayers" not in APP_HTML and "Verifier Layers" not in MANAGE_VIEW and "Math Check" not in MANAGE_VIEW)
    check("Manage exposes test case editor", contains_all(MANAGE_VIEW, ["managerTestList", "managerInputFields", "managerGeneratedOutput"]))
    check("Manage can refresh expected outputs", contains_all(APP_HTML, ["refreshManagedTestOutputs", "managerTestOutputNotice", "markManagerOutputsStale"]))
    check("Manage draft commit uses authoring create endpoint", contains_all(APP_HTML, ["managerIsNewDraft", "/api/authoring/problems", "Case staged in this draft"]))
    check("Manage edit/preview toggle is wired", contains_all(MANAGE_VIEW, ["managerEditModeButton", "managerPreviewModeButton", "setManagerEditMode"]) and "setManagerEditMode" in APP_HTML)
    check("Manage full preview syncs live edits", "refreshManagerFullPreview" in APP_HTML and "syncManagerLearningPreviews" in APP_HTML)
    check("Manage adds cases through horizontal tab", "manager-add-case-tab" in APP_HTML and 'id="managerAddTestCard" class="test-card add-test-card" hidden' in MANAGE_VIEW)
    check("Manage tags are edited inline", contains_all(MANAGE_VIEW, ["managerInlineTagInput", "saveManagerTagsFromInline"]) and "prompt(" not in MANAGE_VIEW)
    check("Manage testcase JSON editors are compact", "stringifyEditableJson" in APP_HTML and 'wrap="off"' in APP_HTML)
    check("Manage has draggable column splitter", contains_all(APP_HTML, ["manageModuleSplitter", "--manage-left"]))

    check("Create uses agent chat split", contains_all(CREATE_AGENT_VIEW, ["create-workspace", "create-chat-pane", "create-preview-pane", "llmProvider"]))
    check("Create has draggable column splitter", contains_all(APP_HTML, ["createModuleSplitter", "--create-left"]))
    check("Create matches Stitch model/header order", contains_all(CREATE_AGENT_VIEW, ["create-control-block", "create-preview-actions", "create-preview-tabs-bar"]) and CREATE_AGENT_VIEW.find("create-preview-actions") < CREATE_AGENT_VIEW.find("create-preview-tabs-bar"))
    check("Create has Direct JSON fixed-loop controls", contains_all(CREATE_AGENT_VIEW, ["New Chat", "Direct JSON", "submitCreateComposer", "directJsonInstructionBubble"]))
    check("Create Direct JSON can toggle back to model chat", "toggleCreateDirectJsonMode" in APP_HTML and "aria-pressed" in APP_HTML)
    check("Create Direct JSON prompts are copied from shortened previews", contains_all(APP_HTML, ["copyCreatePrimaryText", "compactPromptPreview", "Prompt shortened", "llmPrimaryCopyButton"]))
    check("Create Direct JSON prompt is copyable user task", contains_all(AUTHORING_PROMPT, ["Generate the contents of a .json file", "User request:", "raw valid JSON only", "First character must be { or [", "Last character must be } or ]"]) and "add your actual request at the very end under" not in AUTHORING_PROMPT)
    check("Create Direct JSON prompt asks for JSON file contents", contains_all(APP_HTML, ["mnemosyne_problems.json", "Direct JSON box", "Do not copy chat prose", "generated .json file contents"]))
    check("Create Direct JSON submits as chat messages", contains_all(APP_HTML, ["appendCreateChatBubble", "clearCreateChatHistory", "copyCreateChatBubble", "Verifier feedback"]))
    check("Create Direct JSON file upload avoids duplicate draft bubble", contains_all(APP_HTML, ["directJsonUploadedDraft", "submittedFromUploadedFile", "title: 'Uploaded JSON'", "title: 'JSON draft'"]))
    check("Create Direct JSON upload clears attachment chip", contains_all(APP_HTML, ["clearDirectJsonAttachmentPicker", "llmAttachmentFiles = []", "renderLlmAttachmentList()"]) and direct_upload_state_at >= 0 and direct_upload_clear_after_state > direct_upload_state_at)
    check("Create verifier feedback stays visible and resizable", contains_all(APP_HTML, ["createVerifierSplitter", "initCreateVerifierSplitter", "--create-verifier-height", "llmDecisionOutput"]) and "llmVerifierLayers" not in APP_HTML and "Verifier Layers" not in APP_HTML)
    check("Create exposes provider/model/key controls", contains_all(CREATE_AGENT_VIEW, ["llmProvider", "llmModel", "llmApiKey"]))
    check("Create preview tabs are wired", contains_all(CREATE_AGENT_VIEW, ["createPreviewProblemTab", "setCreatePreviewSection('problem')", "createPreviewSolutionTab"]))
    check("Create uses one lower verifier console", contains_all(CREATE_AGENT_VIEW, ["llmResultPreviewPane", "llmResultReportPane", "llmResultJsonPane", "Verifier Run Report", "llmDecisionOutput"]) and "llmReportResultTab" not in CREATE_AGENT_VIEW and "llmJsonResultTab" not in CREATE_AGENT_VIEW)

    check("App navigation defines central view router", contains_all(APP_HTML, ["function setView(view)", "codeView", "catalogView", "manageView", "llmView"]))
    check("App navigation routes top tabs through views", contains_all(APP_HTML, ["setView('catalog')", "setView('manage')", "setView('llm')"]))
    check("APP_HTML public entry remains assembled", contains_all(APP_HTML, ["<!doctype html>", "</html>", "<body data-mode=\"practice\">"]))

    print()
    print(f"Summary: {CHECKS_RUN - len(FAILURES)}/{CHECKS_RUN} Stitch UI checks passed")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
