# AI-Powered Data Pipeline Incident Investigator

A local application that combines pipeline logs with retrieved
troubleshooting documentation to produce investigations with source citations.

## Problem

Investigating pipeline failures requires reading logs, finding relevant
documentation, and deciding which checks to perform next.

This project brings that evidence together and suggests troubleshooting
steps while distinguishing observed failures from unconfirmed causes.

## Current features

- Streamlit interface for selecting synthetic sample incidents.
- Structured extraction of facts from key=value logs.
- Keyword retrieval of relevant runbook passages.
- Expansion of matched runbooks with investigation guidance and limits.
- Local AI generation using Ollama and gemma3:4b.
- Source citations with expandable evidence.
- Saved reports and preservation of original model answers.
- Automatic report-structure and citation-label checks.
- Manual evaluation against five review criteria.
- JSON downloads containing evidence and any matching manual review.

## Architecture

1. Load the incident log and preserve its line numbers.
2. Extract explicit error codes and other recorded facts.
3. Retrieve relevant runbook chunks using keyword similarity.
4. Supply the log, extracted facts, and selected passages to the model.
5. Generate structured findings with constrained citation labels.
6. Build observed-failure and pipeline-impact sections from parsed logs.
7. Save and display the assembled report alongside the original model answer.

## Requirements

- Python 3.10: developed with Python 3.10.11.
- Ollama running locally.
- The gemma3:4b model downloaded in Ollama.
- Dependencies listed in requirements.txt.

Other Python versions have not yet been tested for this project.

## Setup

Install the Python dependencies:

```powershell
python -m pip install -r requirements.txt
```

Download the model:

```powershell
ollama pull gemma3:4b
```

If PowerShell cannot find Ollama, use its default Windows installation path:

```powershell
& "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" pull gemma3:4b
```

Keep the Ollama application running.

Build the runbook chunks:

```powershell
python .\src\chunk_runbooks.py
```

Start the application:

```powershell
python -m streamlit run .\app.py --server.address 127.0.0.1
```

Open http://localhost:8501.

Select an incident and generate an investigation, or open an existing
saved report without making another model call.

## Sample incidents

| Case | Observed failure |
|---|---|
| INC-001 | Missing trip_id column during schema validation |
| INC-002 | API request timeouts during extraction |

All sample logs are synthetic. Runbooks are project-authored guides.
They are not official vendor documentation.

## Evaluation

Automatic checks verify required sections and citation-label validity.

Manual review assesses:

1. Failure identification.
2. Pipeline impact.
3. Root-cause uncertainty.
4. Supported troubleshooting.
5. Supported evidence requests.

Selected assembled reports for both sample incidents passed all five
manual criteria. These are development examples, not a held-out benchmark
or an estimate of general application accuracy.

Citation-label validity does not establish that a statement is supported.

Original model answers are preserved. One timeout answer incorrectly
claimed extraction was skipped. The assembled report used parsed log facts
to correctly distinguish extraction failure from skipped downstream stages.

Manual reviews apply to specific saved reports. Newly generated reports
remain unreviewed until assessed.

## Project folders

| Location | Contents |
|---|---|
| app.py | Streamlit interface |
| src/ | Loading, extraction, retrieval, generation, and review scripts |
| data/sample_logs/ | Synthetic incident logs |
| data/runbook_chunks.json | Generated runbook chunks |
| knowledge_base/runbooks/ | Troubleshooting guides |
| evaluation/cases/ | Expected facts and review requirements |
| evaluation/reports/ | Saved investigation records |
| evaluation/reviews/ | Recorded manual review decisions |

## Current limitations

- Supports our sample key=value log format.
- Uses keyword retrieval; semantic retrieval is not implemented yet.
- No upload interface or validation-results CSV/JSON ingestion yet.
- Suggestions still require evidence review.
- Does not automatically repair pipelines.
- Investigation-time savings have not been measured.
- Local model performance depends on the machine and model configuration.

## Planned improvements

- More incident types and evaluation cases.
- Unknown-error and insufficient-evidence handling.
- Retrieval evaluation and comparison with semantic retrieval.
- Log upload and validation-results ingestion.
- Clearer presentation of repeated attempts.
- Broader testing and measurement of investigation time.