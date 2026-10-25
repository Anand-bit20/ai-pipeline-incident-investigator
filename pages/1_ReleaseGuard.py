import hashlib
import json
import sys
import time
from pathlib import Path

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from assess_release import assess_release


ASSESSMENT_DIR = PROJECT_ROOT / "evaluation" / "release_assessments"

SECTION_NAMES = {
    "observed_failure": "Observed failure",
    "pipeline_impact": "Pipeline impact",
    "root_cause_status": "Root-cause status",
    "troubleshooting": "Troubleshooting",
    "additional_evidence": "Additional evidence needed",
}


def evidence_lookup(record):
    evidence = {}
    log = record.get("log_evidence", {})

    for line in log.get("lines", []):
        label = f"{log['source']}:L{line['line_number']}"
        evidence[label] = line["text"]

    for passage in record.get("retrieved_passages", []):
        label = (
            f"{passage['source']}:"
            f"L{passage['start_line']}-L{passage['end_line']}"
        )
        evidence[label] = passage["text"]

    return evidence


st.set_page_config(page_title="ReleaseGuard AI", layout="wide")

st.title("ReleaseGuard AI")
st.write("Assess release readiness and investigate blocking incidents.")
st.caption(
    "Prototype using declared release-check results. "
    "Underlying check evidence is not independently verified. "
    "Recommendations require human review; no deployment is performed."
)

release_paths = sorted(
    (PROJECT_ROOT / "data" / "sample_releases").glob("*.json")
)

if not release_paths:
    st.info("No release samples found in data/sample_releases.")
    st.stop()

selected = st.selectbox(
    "Select a release",
    release_paths,
    format_func=lambda path: path.stem.replace("_", " ").title(),
)

try:
    release = json.loads(selected.read_text(encoding="utf-8"))
    if not isinstance(release, dict):
        raise ValueError("Release evidence must be a JSON object.")
except (OSError, ValueError) as error:
    st.error(f"Could not read release evidence: {error}")
    st.stop()

# Separate results when the selected evidence changes.
release_key = hashlib.sha256(
    json.dumps(release, sort_keys=True).encode("utf-8")
).hexdigest()

if "releaseguard_results" not in st.session_state:
    st.session_state["releaseguard_results"] = {}

with st.expander("View release evidence"):
    st.json(release)

left, right = st.columns(2)
assess_clicked = left.button("Assess release", type="primary")
load_clicked = right.button("Open latest saved assessment")

if assess_clicked:
    st.session_state["releaseguard_results"].pop(release_key, None)

    try:
        with st.spinner("Checking release rules and investigating incidents..."):
            assessment = assess_release(release, retriever="semantic")

            ASSESSMENT_DIR.mkdir(parents=True, exist_ok=True)
            output_path = ASSESSMENT_DIR / (
                f"release_assessment_{time.time_ns()}.json"
            )
            output_path.write_text(
                json.dumps(assessment, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

        st.session_state["releaseguard_results"][release_key] = {
            "assessment": assessment,
            "filename": output_path.name,
        }
        st.success("Assessment generated and saved.")
    except Exception as error:
        st.error(f"Assessment could not be completed: {error}")

if load_clicked:
    st.session_state["releaseguard_results"].pop(release_key, None)

    try:
        candidates = sorted(
            ASSESSMENT_DIR.glob("*.json"),
            key=lambda path: path.stat().st_mtime_ns,
            reverse=True,
        )

        for path in candidates:
            try:
                saved = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue

            if (
                isinstance(saved, dict)
                and saved.get("release_evidence") == release
            ):
                st.session_state["releaseguard_results"][release_key] = {
                    "assessment": saved,
                    "filename": path.name,
                }
                st.success("Saved assessment opened. No AI call was made.")
                break
        else:
            st.info("No saved assessment matches this release evidence.")
    except OSError as error:
        st.error(f"Could not load saved assessments: {error}")

current = st.session_state["releaseguard_results"].get(release_key)

if current:
    assessment = current["assessment"]
    readiness = assessment["readiness"]
    recommendation = readiness["recommendation"]

    st.subheader(f"Release: {readiness['release_id']}")

    if recommendation == "NO-GO":
        st.error("NO-GO — a required check failed.")
    elif recommendation == "REVIEW":
        st.warning("REVIEW — evidence or unresolved issues need attention.")
    else:
        st.success("GO — declared evidence meets the prototype rules.")

    st.caption(
        f"Assessment created: {assessment['created_at_utc']} | "
        f"Human review: {assessment.get('human_review_status', 'pending')}"
    )

    for reason in readiness["blocking_reasons"]:
        st.error(f"Blocker: {reason}")

    for reason in readiness["review_reasons"]:
        st.warning(f"Review required: {reason}")

    st.subheader("Required checks")
    st.dataframe(readiness["check_results"], use_container_width=True)

    st.subheader("Incident investigations")

    if not assessment["investigations"]:
        st.info("No incident investigations were requested.")

    for investigation in assessment["investigations"]:
        st.markdown(
            f"**Incident: {investigation.get('incident_id', 'Unspecified')}**"
        )
        st.write(f"Investigation status: {investigation['status']}")

        if investigation["status"] != "generated":
            st.warning(
                investigation.get("reason", "Investigation unavailable.")
            )
            continue

        record = investigation["record"]
        report = json.loads(record["report"])
        evidence = evidence_lookup(record)

        st.caption(
            "AI guidance requires evidence review. "
            "A generated investigation is not release approval."
        )

        for section, title in SECTION_NAMES.items():
            st.markdown(f"**{title}**")

            for finding in report.get(section, []):
                st.write(finding["statement"])

                for citation in finding["citations"]:
                    with st.expander(f"Source: {citation}"):
                        st.code(
                            evidence.get(citation, "Source unavailable."),
                            language="text",
                        )

    st.download_button(
        "Download complete release assessment",
        data=json.dumps(assessment, indent=2, ensure_ascii=False),
        file_name=current["filename"],
        mime="application/json",
    )