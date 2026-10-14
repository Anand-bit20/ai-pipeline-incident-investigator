import json
import time

from extract_incident_facts import extract_facts
from load_evidence import PROJECT_ROOT, load_evidence
from retrieve_evidence import retrieve


def main() -> None:
    chunks_path = PROJECT_ROOT / "data" / "runbook_chunks.json"
    chunks = json.loads(chunks_path.read_text(encoding="utf-8"))

    case_paths = sorted(
        (PROJECT_ROOT / "evaluation" / "cases").glob("*.json")
    )
    if not case_paths:
        raise ValueError("No evaluation cases found.")

    results = []

    for case_path in case_paths:
        case = json.loads(case_path.read_text(encoding="utf-8"))
        facts = extract_facts(load_evidence(case["incident_source"]))

        error_codes = sorted({
            entry["fields"]["error_code"]
            for entry in facts["explicit_errors"]
        })
        if not error_codes:
            raise ValueError(f"No error codes in case {case['case_id']}.")

        query = " ".join(error_codes)
        passages = retrieve(query, chunks, top_k=3)
        reference = case.get("troubleshooting_reference")

        result = {
            "case_id": case["case_id"],
            "query": query,
            "retrieved_chunks": [
                passage["chunk_id"] for passage in passages
            ],
        }

        if reference is None:
            if case.get("expected_behavior") != "ABSTAIN_FROM_AI_GENERATION":
                raise ValueError(
                    f"Missing retrieval expectation: {case['case_id']}"
                )

            result.update({
                "case_type": "unknown_error",
                "correct_abstention": not passages,
                "passed": not passages,
            })
        else:
            correct_top_runbook = bool(
                passages and passages[0]["source"] == reference["source"]
            )

            # Check whether the expected troubleshooting passage was
            # included among the first three raw retrieval results.
            troubleshooting_hit = any(
                passage["source"] == reference["source"]
                and passage["start_line"] <= reference["start_line"]
                and passage["end_line"] >= reference["end_line"]
                for passage in passages
            )

            result.update({
                "case_type": "known_error",
                "correct_runbook_at_1": correct_top_runbook,
                "troubleshooting_passage_at_3": troubleshooting_hit,
                "passed": correct_top_runbook,
            })

        results.append(result)

    known = [r for r in results if r["case_type"] == "known_error"]
    unknown = [r for r in results if r["case_type"] == "unknown_error"]

    summary = {
        "evaluation_scope": "Small development set; not held-out",
        "retriever": "Error-code applicability filter plus keyword cosine similarity",
        "top_k": 3,
        "total_cases": len(results),
        "runbook_selection_or_abstention_passes": sum(
            r["passed"] for r in results
        ),
        "known_error_runbook_accuracy_at_1": (
            sum(r["correct_runbook_at_1"] for r in known) / len(known)
            if known else None
        ),
        "known_error_troubleshooting_hit_rate_at_3": (
            sum(r["troubleshooting_passage_at_3"] for r in known) / len(known)
            if known else None
        ),
        "unknown_error_abstention_rate": (
            sum(r["correct_abstention"] for r in unknown) / len(unknown)
            if unknown else None
        ),
        "results": results,
    }

    output_dir = PROJECT_ROOT / "evaluation" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"retrieval_{time.time_ns()}.json"
    output_path.write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(summary, indent=2))
    print(f"\nSaved results: {output_path}")


if __name__ == "__main__":
    main()