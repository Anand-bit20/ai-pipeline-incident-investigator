# AI-Powered Data Pipeline Incident Investigator & ReleaseGuard AI

An evidence-grounded AI application for investigating data pipeline failures and assessing software release readiness.

Built using **Python, Streamlit, Ollama, Gemma 3, semantic retrieval, and rule-based release evaluation**.

The application operates locally, generates cited investigation reports, and provides GO, NO-GO, or REVIEW release recommendations while retaining human oversight.

## 1. Problem Statement

Data pipeline incidents can delay software releases and require engineers to manually inspect logs, identify failure patterns, consult troubleshooting documentation, and assess deployment risks.

Release decisions may also depend on incomplete test evidence, unresolved incidents, and inconsistent readiness checks.

This project combines two capabilities:

- **AI Incident Investigator:** Analyzes pipeline logs and retrieves relevant troubleshooting evidence.
- **ReleaseGuard AI:** Evaluates release readiness and incorporates incident investigations into a structured release assessment.

## 2. Core Features

### AI Incident Investigator

- Structured extraction of facts from synthetic pipeline logs.
- Keyword-based and semantic retrieval of troubleshooting runbooks.
- Local AI generation using Ollama and `gemma3:4b`.
- Semantic embeddings using `embeddinggemma`.
- Evidence-grounded investigation reports with source citations.
- Separation of observed failures from unconfirmed root causes.
- Automatic report-structure and citation-label checks.
- Saved investigation reports and manual review records.
- Streamlit interface for incident investigation and review.
- Evaluation scripts for retrieval quality.

### ReleaseGuard AI

- Rule-based release readiness assessment.
- Three supported recommendations: GO, NO-GO, and REVIEW.
- Validation of automated test evidence, data validation, and release checklists.
- Identification of missing evidence and unresolved incidents.
- AI incident investigation for referenced pipeline failures.
- Combined release assessment and investigation reporting.
- Saved assessment records.
- Streamlit dashboard for evaluating synthetic releases.
- Mandatory human review.
- No automatic deployment execution.

**Important:** GO indicates that declared evidence meets the prototype policy. It is not deployment authorization.

## 3. System Architecture

```text
                  PIPELINE INCIDENT LOGS
                           |
                           v
                    Fact Extraction
                           |
                           v
               Keyword / Semantic Retrieval
                           |
                           v
               Troubleshooting Runbooks
                           |
                           v
                  Ollama + Gemma 3
                           |
                           v
                 Cited Investigation
                           |
                           v
                    Saved AI Report
                           |
                           |
RELEASE EVIDENCE ----------+
        |
        v
Rule-Based Readiness Evaluation
        |
        v
 GO / NO-GO / REVIEW
        |
        v
Combined Release Assessment
        |
        v
Human Review Required
```

Release recommendations are determined by explicit rules. AI-generated investigations provide supporting information but cannot override these recommendations.

## 4. Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.10 | Application logic |
| Streamlit | User interface |
| Ollama | Local model runtime |
| Gemma 3 4B | Investigation generation |
| EmbeddingGemma | Semantic embeddings |
| JSON | Evidence and report storage |
| Git / GitHub | Version control |

The semantic index stores embeddings for troubleshooting documentation and supports similarity-based evidence retrieval.

## 5. Installation and Setup

### Requirements

- Python 3.10 (developed using 3.10.11)
- Ollama installed and running locally
- Sufficient system resources for local AI models

### Install Python dependencies

```powershell
python -m pip install -r requirements.txt
```

### Download the AI models

```powershell
ollama pull gemma3:4b
ollama pull embeddinggemma
```

If Ollama is not available in PowerShell:

```powershell
& "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" pull gemma3:4b
& "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" pull embeddinggemma
```

Keep Ollama running.

### Prepare troubleshooting documentation

```powershell
python .\src\chunk_runbooks.py
```

### Build the semantic index

```powershell
python .\src\build_semantic_index.py
```

### Launch the application

```powershell
python -m streamlit run .\app.py --server.address 127.0.0.1
```

Open:

http://localhost:8501

Use the incident investigator or navigate to the ReleaseGuard AI page.

## 6. Incident Investigation

The application supports synthetic incident scenarios involving:

- Missing required schema columns.
- API request timeouts.
- Unknown errors and insufficient evidence.
- Azure Blob authorization failures.

The investigation process combines extracted facts with retrieved documentation.

Generated findings distinguish recorded pipeline behavior from troubleshooting hypotheses and requests for additional evidence.

## 7. ReleaseGuard AI Demo Scenarios

| Release | Scenario | Expected recommendation |
|---|---|---|
| REL-001 | Failed data validation and unresolved incident | NO-GO |
| REL-002 | All required checks passed with declared evidence | GO |
| REL-003 | Missing required automated test evidence | REVIEW |

### Run individual release checks

```powershell
python .\src\evaluate_release.py data\sample_releases\release_001_blocked.json
python .\src\evaluate_release.py data\sample_releases\release_002_ready.json
python .\src\evaluate_release.py data\sample_releases\release_003_review.json
```

### Run combined release assessment and AI investigation

```powershell
python .\src\assess_release.py data\sample_releases\release_001_blocked.json
```

The combined assessment saves the release recommendation, investigation results, and human review status.

## 8. Evaluation and Testing

The prototype has been tested against three synthetic release scenarios:

- REL-001: NO-GO correctly returned.
- REL-002: GO correctly returned.
- REL-003: REVIEW correctly returned.

An integration test for REL-001 successfully generated an incident investigation with 100% citation-label validity and no invalid citation labels.

A separate failure-handling test confirmed that an investigation failure does not override a NO-GO recommendation, that errors are recorded, and that human review remains pending.

Retrieval evaluation utilities are included to assess keyword and semantic retrieval.

These tests demonstrate the expected behavior for selected synthetic cases. They do not establish production reliability or generalized model accuracy.

Citation-label validity confirms citation formatting and referencing, not necessarily the factual support of every claim.

## 9. Project Structure

| Location | Purpose |
|---|---|
| `app.py` | Main Streamlit application |
| `pages/` | ReleaseGuard dashboard |
| `src/` | Investigation, retrieval, release assessment, and evaluation |
| `data/sample_logs/` | Synthetic incident logs |
| `data/sample_releases/` | Synthetic release evidence |
| `knowledge_base/runbooks/` | Troubleshooting documentation |
| `evaluation/cases/` | Evaluation scenarios |
| `evaluation/reports/` | Locally generated investigation reports |
| `evaluation/reviews/` | Locally generated manual reviews |
| `evaluation/release_assessments/` | Locally generated combined assessments |

Generated investigation reports, review records, assessment results, and the semantic index are excluded from Git tracking.

## 10. Safety and Limitations

- This is a local demonstration prototype, not a production release governance system.
- Release readiness is evaluated from declared evidence, which is not independently verified.
- All sample release and incident data are synthetic.
- Human approval is always required.
- The application does not deploy or automatically repair pipelines.
- AI investigation outputs may be inaccurate and require evidence review.
- The supported log formats and evaluation scenarios remain limited.
- Citation-label validity does not guarantee claim correctness.
- Local model execution requires Ollama and compatible hardware.
- Investigation-time savings and production performance have not been established.

## 11. Future Improvements

- Integrate CI/CD platforms and automated test systems.
- Verify readiness evidence directly from trusted source systems.
- Support additional log formats and data validation artifacts.
- Expand incident and release evaluation datasets.
- Add formal automated regression tests.
- Introduce role-based human approval workflows.
- Measure investigation accuracy, latency, and operational efficiency.

## 12. Project Purpose

This project demonstrates the integration of data engineering, retrieval-augmented generation, local large language models, deterministic decision rules, and human-in-the-loop review.

The goal is to support faster, more transparent incident investigation and release readiness assessment without replacing engineering judgment or deployment controls.

**Project status:** Functional local prototype validated against selected synthetic scenarios.