# AI-Powered Data Pipeline Incident Investigator & ReleaseGuard AI

An evidence-grounded prototype for investigating data pipeline failures and assessing software release readiness. It combines retrieval-augmented generation (RAG) with **deterministic release rules** and **human oversight**.

**AI options:** Local Ollama (Gemma 3 + embeddinggemma) or Amazon Bedrock (Nova 2 Lite + Titan Text Embeddings V2).
**Interface:** Streamlit.
**Scope:** Synthetic demonstration data; no automatic deployments.

## 1. Problem statement

Before releasing software or data pipelines, engineers often need to review test results, validation failures, incident logs, and troubleshooting documentation. Manual review takes time and can make the reasoning behind a release recommendation difficult to trace.

This project brings together two capabilities:

- **AI Incident Investigator:** Extracts observable facts from pipeline logs, retrieves relevant runbooks, and produces structured findings with evidence citations.
- **ReleaseGuard AI:** Evaluates declared release checks and unresolved incidents, recommends **GO**, **NO-GO**, or **REVIEW**, and attaches incident investigations when needed.

**A GO recommendation is not deployment approval.** The application records human review as pending and does not deploy software.

## 2. Key features

### Incident investigation

- Parses facts from synthetic pipeline logs, separating observed behavior from root-cause hypotheses.
- Retrieves troubleshooting material using keyword matching or semantic similarity.
- Supports two selectable AI providers:
  - **Ollama:** `gemma3:4b` for generation; `embeddinggemma` for 768-dimensional vectors.
  - **Amazon Bedrock:** `global.amazon.nova-2-lite-v1:0` for generation; `amazon.titan-embed-text-v2:0` for 1024-dimensional vectors.
- Produces five report sections: observed failure, pipeline impact, root-cause status, troubleshooting, and additional evidence.
- Enforces required report structure, allowed citation labels, and source-type restrictions.
- Performs a **limited file-path support check**: when a generated finding includes a recognized quoted file path, at least one cited evidence passage must include that path.
- Saves investigation and evaluation records and exposes evidence excerpts through Streamlit.

### ReleaseGuard AI

- Applies deterministic rules to declared automated-test, data-validation, and release-checklist results.
- Handles unresolved incident references and invokes the chosen investigation provider when needed.
- Preserves the rule-based readiness decision when an investigation fails, with the failure recorded for review.
- Saves combined release assessments and allows provider-specific loading and JSON download in the dashboard.
- Sets `human_review_status` to `pending` and `deployment_performed` to `false`.

## 3. Architecture

```text
Synthetic release JSON ----------------> Deterministic readiness rules
    |                                      |
    | unresolved incident                  | GO / NO-GO / REVIEW
    v                                      |
Incident log -> Fact extraction           |
    |                                      |
    v                                      |
Runbook retrieval                          |
  |-- Keyword retrieval                    |
  |-- Ollama semantic index (768-d)         |
  '-- Titan V2 semantic index (1024-d)      |
    |                                      |
    v                                      |
AI explanation: Gemma 3 or Nova 2 Lite    |
    |                                      |
    v                                      |
Structure + citation checks                |
    |                                      |
    +------------> Combined assessment <---+
                         |
                         v
                 Streamlit dashboard
                         |
                         v
            Human review pending / no deploy
```

The model **does not determine or override** the release recommendation. Both provider-specific semantic indexes are saved separately so their vector dimensions are not mixed.

## 4. Technology stack

| Component | Technology |
|---|---|
| Application and rules | Python (developed locally with Python 3.10) |
| Dashboard | Streamlit |
| Local generation | Ollama + Gemma 3 4B |
| Local embeddings | embeddinggemma (768 dimensions) |
| Cloud generation | Amazon Bedrock + Nova 2 Lite |
| Cloud embeddings | Amazon Titan Text Embeddings V2 (1024 dimensions) |
| Cloud SDK/authentication | Boto3, Botocore, AWS CRT, AWS CLI |
| Retrieval and records | Python, JSON, cosine similarity, runbook chunks |
| Version control | Git / GitHub |

## 5. Setup

### 5.1 Prerequisites

- Python 3.10 or a compatible Python version.
- Access to the repository and its **synthetic** sample logs, runbooks, and releases.
- For the local option: Ollama running with the required models.
- For the Bedrock option: authorized AWS account access, Bedrock permissions, and network/certificate configuration compliant with your organization.

Install Python packages:

```powershell
python -m pip install -r requirements.txt
```

For the Bedrock option, ensure the following additional packages are installed in the **same Python environment** used to run Streamlit:

```powershell
python -m pip install --upgrade "boto3[crt]"
```

> Check `requirements.txt` before relying on it for a complete reproducible install; the project's dependencies should be pinned and reviewed separately. Never commit cloud credentials.

### 5.2 Prepare runbook chunks

From the repository root in Windows PowerShell:

```powershell
python .\src\chunk_runbooks.py
```

### 5.3 Option A â€” Local Ollama

Install and start Ollama, then download the models:

```powershell
ollama pull gemma3:4b
ollama pull embeddinggemma
```

Build the local semantic index:

```powershell
python .\src\build_semantic_index.py --provider ollama
```

This writes `data/semantic_index.json`.

### 5.4 Option B â€” Amazon Bedrock

Sign in using an **organization-approved** AWS authentication method. For AWS CLI versions that support IAM console login:

```powershell
aws login --region ap-south-1
aws sts get-caller-identity --region ap-south-1
```

If applicable, verify access to the configured Nova inference profile:

```powershell
aws bedrock get-inference-profile `
  --inference-profile-identifier global.amazon.nova-2-lite-v1:0 `
  --region ap-south-1 `
  --query "status"
```

Build the Bedrock semantic index:

```powershell
python .\src\build_semantic_index.py --provider bedrock
```

This writes `data/titan_semantic_index.json` with 1024-dimensional vectors. Index creation and subsequent inference **make billable Bedrock requests**. Use only approved/synthetic evidence. The configured Nova model uses a global inference profile; check organizational data-residency requirements before using any real data.

If `aws login` works in AWS CLI but Boto3 reports a missing login-provider dependency, install `boto3[crt]` in the Python environment executing the application. Certificate-validation issues should be fixed using approved CA trust settings, **not** by disabling TLS verification.

### 5.5 Run the Streamlit dashboard

```powershell
python -m streamlit run .\app.py --server.address 127.0.0.1
```

Open `http://localhost:8501` and navigate to the **ReleaseGuard AI** page, or launch it directly:

```powershell
python -m streamlit run .\pages\1_ReleaseGuard.py --server.address 127.0.0.1
```

Select a sample release and the **Local Ollama** or **Amazon Bedrock** investigation provider. Click **Assess release** to save a new assessment, or **Open latest saved assessment** to inspect an existing matching assessment without making a new model call.

## 6. Command-line examples

Run an incident investigation with Bedrock RAG:

```powershell
python .\src\generate_investigation.py `
  .\data\sample_logs\incident_001_missing_trip_id.log `
  --provider bedrock `
  --retriever semantic
```

Run the combined release assessment:

```powershell
python .\src\assess_release.py `
  .\data\sample_releases\release_001_blocked.json `
  --provider bedrock `
  --retriever semantic
```

For local Ollama, use `--provider ollama` after building its semantic index. The default provider is Ollama.

## 7. Demonstration scenarios and observed tests

| Release | Synthetic evidence scenario | Expected | Observed |
|---|---|---|---|
| REL-001 | Failed data validation (`trip_id` missing), unresolved INC-001 | NO-GO | NO-GO; investigation generated in successful tests |
| REL-002 | All required declared checks passed | GO | GO; no investigation requested |
| REL-003 | Automated-test evidence missing or invalid | REVIEW | REVIEW; no investigation requested |

The three release outcomes were verified in the **local Streamlit dashboard with Ollama and with Amazon Bedrock**, and the Bedrock assessments were checked to confirm:

- Human review remains `pending` for all three releases.
- `deployment_performed` is `false` for all three releases.
- REL-001 supports an AI-generated investigation with cited evidence.

A simulated Bedrock failure was also tested: **REL-001 remained NO-GO**, the investigation was recorded as an error, review stayed pending, and no deployment occurred.

Individual successful investigation runs reported **100% citation-label validity**. A separate regression test showed that a generated finding with a specific file path and no supporting citation was rejected, while a supported citation was accepted. A subsequent full Bedrock investigation and combined REL-001 assessment passed the updated safeguard.

These results concern **selected synthetic cases and individual test runs**, not production reliability or a statistically established model-accuracy rate.

## 8. Project layout

| Path | Purpose |
|---|---|
| `app.py` | Main Streamlit application |
| `pages/1_ReleaseGuard.py` | ReleaseGuard dashboard |
| `src/assess_release.py` | Combines readiness rules and incident investigation |
| `src/evaluate_release.py` | Deterministic release evaluation |
| `src/generate_investigation.py` | Structured generation and validation |
| `src/bedrock_llm.py` | Bedrock model generation client |
| `src/bedrock_embeddings.py` | Titan V2 embeddings client |
| `src/build_semantic_index.py` | Builds provider-specific runbook index |
| `src/retrieve_semantic.py` | Embedding retrieval and similarity ranking |
| `data/sample_logs/` | Synthetic incident logs |
| `data/sample_releases/` | Synthetic release inputs |
| `data/runbook_chunks.json` | Chunked runbook data |
| `data/semantic_index.json` | Ollama semantic index |
| `data/titan_semantic_index.json` | Generated Bedrock semantic index (ignored by Git) |
| `knowledge_base/runbooks/` | Project-authored troubleshooting documentation |
| `evaluation/reports/` | Saved investigation and evaluation reports |
| `evaluation/release_assessments/` | Saved combined assessments |

Do not commit credentials, generated data containing sensitive information, or temporary transfer archives.

## 9. Safety and limitations

- **Synthetic inputs:** The test logs, release records, and runbooks are demonstration data.
- **Declared evidence:** Check statuses are provided by input JSON; the prototype does not independently verify CI/CD systems or test artifacts.
- **No authorization or deployment:** GO is an advisory recommendation. Human review remains pending; no deployment is executed.
- **Evidence support is partial:** Citation-label validation verifies that references exist and satisfy source-type restrictions. The additional file-path check only covers certain explicitly quoted file paths. Neither test establishes the semantic correctness of all claims.
- **Generation variability:** Even with a fixed low temperature, generated findings and citations can vary. Invalid evidence support can cause an investigation to fail safely and require review.
- **Limited evaluation:** The tested synthetic incidents are not representative of all production failures, and time savings have not been measured.
- **Bedrock security/cost:** Cloud access requires authorized credentials and permissions. Requests are billable, and cross-region inference/profile behavior must comply with organizational policy.
- **Prototype scope:** This is not a production governance, approval, or automatic remediation system.

## 10. Future improvements

- Connect CI/CD pipelines and test-artifact systems to verify readiness evidence directly.
- Introduce authenticated, role-based human approval workflows and audit trails.
- Expand incident logs, runbooks, and release scenarios.
- Add repeatable evaluation sets for retrieval, citation support, and model output quality.
- Measure latency, model cost, reliability, and engineer review time.
- Package and deploy privately within an approved environment.

## 11. Project status

**Functional demonstration prototype:** Both local Ollama and Amazon Bedrock workflows have been tested through the Streamlit interface. Three synthetic release decisions and a simulated AI-failure safeguard passed. Production readiness and broader performance have **not** been established.
