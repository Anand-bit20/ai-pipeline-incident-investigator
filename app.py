import json
import subprocess
import sys
from pathlib import Path

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent
REPORT_DIR = PROJECT_ROOT / "evaluation" / "reports"

SECTION_NAMES = {
    "observed_failure": "Observed failure",
    "pipeline_impact": "Pipeline impact",
    "root_cause_status": "Root-cause status",
    "troubleshooting": "Troubleshooting steps",
    "additional_evidence": "Additional evidence needed",
}


def generate_report(incident_path: Path) -> Path:
    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "src" / "generate_investigation.py"),
            incident_path.relative_to(PROJECT_ROOT).as_posix(),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=240,
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout)

    marker = "Saved evaluation record: "
    saved_paths = [
        line[len(marker):].strip()
        for line in result.stdout.splitlines()
        if line.startswith(marker)
    ]

    if not saved_paths:
        raise RuntimeError(
            result.stdout or "The investigator did not save a report."
        )

    report_path = Path(saved_paths[-1]).resolve()

    if report_path.parent != REPORT_DIR.resolve():
        raise ValueError("The report was saved outside the expected folder.")

    return report_path


def evidence_lookup(record: dict) -> dict:
    evidence = {}

    log = record["log_evidence"]
    for line in log["lines"]:
        label = f"{log['source']}:L{line['line_number']}"
        evidence[label] = line["text"]

    for passage in record["retrieved_passages"]:
        label = (
            f"{passage['source']}:"
            f"L{passage['start_line']}-L{passage['end_line']}"
        )
        evidence[label] = passage["text"]

    return evidence


def find_review(report_path: Path):
    relative_path = report_path.relative_to(PROJECT_ROOT).as_posix()
    review_dir = PROJECT_ROOT / "evaluation" / "reviews"

    reviews = sorted(
        review_dir.glob("*.json"),
        key=lambda path: path.stat().st_mtime_ns,
        reverse=True,
    )

    for path in reviews:
        review = json.loads(path.read_text(encoding="utf-8"))
        if review.get("source_report") == relative_path:
            return review

    return None


st.set_page_config(
    page_title="Pipeline Incident Investigator",
    page_icon="🔎",
    layout="wide",
)

st.title("AI-Powered Data Pipeline Incident Investigator")
st.write(
    "Investigate pipeline failures using log evidence and cited "
    "troubleshooting guides."
)
st.caption("Portfolio demo using synthetic incidents and local AI.")

incidents = sorted((PROJECT_ROOT / "data" / "sample_logs").glob("*.log"))

if not incidents:
    st.error("No sample incident logs were found.")
    st.stop()

incident = st.selectbox(
    "Select an incident",
    incidents,
    format_func=lambda path: path.stem.replace("_", " ").title(),
)

with st.expander("View incident log"):
    st.code(incident.read_text(encoding="utf-8-sig"), language="text")

if "reports_by_incident" not in st.session_state:
    st.session_state["reports_by_incident"] = {}

incident_key = incident.name

left, right = st.columns(2)

with left:
    generate_clicked = st.button(
        "Generate investigation",
        type="primary",
    )

with right:
    load_clicked = st.button("Open latest saved report")

if generate_clicked:
    try:
        with st.spinner("Investigating with the local model..."):
            report_path = generate_report(incident)
            record = json.loads(report_path.read_text(encoding="utf-8"))

        st.session_state["reports_by_incident"][incident_key] = {
            "path": str(report_path),
            "record": record,
        }
        st.success("Investigation generated.")

    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
        st.error(f"Investigation could not be completed: {error}")

if load_clicked:
    try:
        candidates = list(REPORT_DIR.glob(f"{incident.stem}_*.json"))

        if not candidates:
            st.info("No saved report exists for this incident yet.")
        else:
            report_path = max(
                candidates,
                key=lambda path: path.stat().st_mtime_ns,
            )
            record = json.loads(report_path.read_text(encoding="utf-8"))

            st.session_state["reports_by_incident"][incident_key] = {
                "path": str(report_path),
                "record": record,
            }
            st.success("Saved report opened. No model call was made.")

    except (OSError, ValueError) as error:
        st.error(f"Could not open the report: {error}")

current = st.session_state["reports_by_incident"].get(incident_key)

if current:
    record = current["record"]
    report_path = Path(current["path"])
    report = json.loads(record["report"])
    evidence = evidence_lookup(record)

    first, second, third = st.columns(3)
    first.metric("Model", record["model"])
    second.metric(
        "Model request time",
        f"{record['response_seconds']:.1f} seconds",
    )
    third.metric(
        "Citation label validity",
        f"{record['citation_label_validity']:.0%}",
    )

    st.caption(
        "Citation label validity checks source references. "
        "It does not measure whether statements are correct."
    )

    report_tab, evidence_tab, evaluation_tab = st.tabs(
        ["Investigation", "Source evidence", "Evaluation"]
    )

    with report_tab:
        provenance = record.get("section_provenance", {})

        for section, title in SECTION_NAMES.items():
            st.subheader(title)

            origin = provenance.get(section)
            if origin:
                st.caption(
                    "Extracted from logs"
                    if origin == "deterministic_log_extraction"
                    else "AI-generated guidance — review against the evidence"
                )

            for finding in report.get(section, []):
                st.write(finding["statement"])

                for citation in finding["citations"]:
                    with st.expander(f"Source: {citation}"):
                        source_text = evidence.get(citation)
                        if source_text is None:
                            st.warning("This citation is not in the supplied evidence.")
                        else:
                            st.code(source_text, language="text")

    with evidence_tab:
        st.subheader("Evidence supplied to this investigation")

        for citation, text in evidence.items():
            with st.expander(citation):
                st.code(text, language="text")

    with evaluation_tab:
        review = find_review(report_path)

        if review is None:
            st.info("This specific report has not been manually reviewed.")
        else:
            manual = review["manual_review"]
            st.write(
                f"Manual review: {manual['passed']}/{manual['total']} "
                "criteria passed."
            )
            st.json(review)

        with st.expander("Original model answer"):
            st.json(record.get("raw_model_report", report))

    review = find_review(report_path)

    export_record = {
        **record,
        "semantic_review_status": (
            "reviewed" if review is not None else "pending"
        ),
        "manual_evaluation": review,
    }

    st.download_button(
        "Download investigation and evidence",
        data=json.dumps(export_record, indent=2, ensure_ascii=False),
        file_name=report_path.name,
        mime="application/json",
        on_click="ignore",
    )