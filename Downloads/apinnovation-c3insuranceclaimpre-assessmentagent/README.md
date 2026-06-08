# ClaimSense AI – Insurance Claim Pre-Assessment Agent

An AI-assisted insurance claim pre-assessment system built as a Calibo AI Academy Capstone project. ClaimSense AI helps human reviewers by validating claim context, retrieving relevant policy clauses, and producing structured pre-assessment outputs — without making final approval or rejection decisions.

---

## 1. Project Overview

ClaimSense AI is a **FastAPI** backend application that supports insurance claim pre-assessment workflows across multiple insurance types: Health, Vehicle, Life, Home, and Crop.

The system is designed around a clear principle:

> **AI does not approve or reject claims.**  
> AI validates, retrieves policy knowledge, and recommends `REVIEW_REQUIRED`. Human reviewers make final decisions.

**Current implementation (Phase 1):**

- CSV-based data persistence (no database)
- REST APIs for claims, policies, dashboard statistics, RAG search, and pre-assessment
- Keyword-based policy clause retrieval
- Append-only audit logging
- Modular, service-oriented architecture
- 14 automated tests passing

**Tech stack:** Python 3.12, FastAPI, pandas, Pydantic, pytest, uvicorn

---

## 2. Problem Statement

Insurance claim processing is time-consuming and policy-heavy. Reviewers must:

- Locate the correct claim and policy records
- Cross-reference policy clauses, exclusions, waiting periods, and document requirements
- Assess whether a claim warrants further review
- Maintain an audit trail of system-assisted decisions

Manual review at scale is slow, inconsistent, and error-prone. ClaimSense AI addresses the **pre-assessment** stage by automating data retrieval, policy clause lookup, and structured evidence packaging — while keeping humans in control of final outcomes.

---

## 3. Current Architecture

The application follows a layered architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                        Routers                              │
│   HTTP handling · response models · dependency injection   │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│                       Services                              │
│   Claim · Policy · Assessment · Audit orchestration         │
└────────────┬───────────────────────────────┬────────────────┘
             │                               │
┌────────────▼────────────┐    ┌─────────────▼───────────────┐
│      CSV Stores         │    │      Domain (RAG)           │
│  Read / write CSV data  │    │  Keyword clause retrieval   │
└─────────────────────────┘    └─────────────────────────────┘
```

| Layer | Responsibility |
|-------|----------------|
| **Routers** | HTTP endpoints, request/response handling, dependency injection |
| **Services** | Business workflows and orchestration |
| **CSV Stores** | Thread-safe CSV read/write via pandas |
| **Domain** | Pure business logic (RAG keyword search) |
| **Schemas** | Pydantic response models |
| **Config** | Application settings via Pydantic Settings |

On startup, the application validates that all required CSV datasets exist before serving requests.

---

## 4. Folder Structure

```
app/
├── config.py              # Pydantic Settings (DATA_DIR, APP_NAME, VERSION, etc.)
├── main.py                # FastAPI app factory and router registration
├── startup.py             # Dataset validation on startup
├── dependencies.py        # Service wiring and dependency injection
├── constants.py           # Shared application constants
├── routers/
│   ├── health.py          # Root and health endpoints
│   ├── claims.py          # Claims API
│   ├── policies.py        # Policies API
│   ├── rag.py             # RAG search API
│   ├── assessment.py      # Pre-assessment API
│   └── dashboard.py       # Dashboard statistics API
├── services/
│   ├── claim_service.py
│   ├── policy_service.py
│   ├── assessment_service.py
│   └── audit_service.py
├── csv_store/
│   ├── base.py            # Thread-safe BaseCSVStore
│   ├── claim_store.py
│   ├── policy_store.py
│   └── audit_store.py
├── schemas/
│   ├── claim.py
│   ├── policy.py
│   └── assessment.py
├── domain/
│   └── rag/
│       └── retriever.py   # RAGRetriever (keyword search)
└── static/
    └── index.html

data/
├── claims.csv
├── policies.csv
├── policy_clauses.csv
└── audit_events.csv

tests/
└── test_main.py           # API integration tests

datasets/                  # Sample source datasets (not used at runtime)
```

---

## 5. Implemented Features

| Feature | Description |
|---------|-------------|
| **Claims API** | List all claims and retrieve a claim by ID |
| **Policy API** | Retrieve policy details by policy number |
| **Dashboard Statistics API** | Claim counts by insurance type, computed from `claims.csv` |
| **RAG Clause Retrieval** | Weighted keyword search over policy clauses |
| **Pre-Assessment Workflow** | Claim → policy → relevant clauses → structured `REVIEW_REQUIRED` response |
| **Audit Logging** | Append-only audit events for every pre-assessment (`PRE_ASSESSMENT` / `SYSTEM`) |
| **CSV-Based Storage** | All persistence via pandas and CSV files (no database) |
| **Modular Architecture** | Routers, services, stores, schemas, and domain layers |
| **Automated Testing** | 14 pytest integration tests covering all endpoints |

**Not yet implemented:** OCR, document upload, LLM integration, vector embeddings, evidence brief generation, or claim approval/rejection automation.

---

## 6. API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Application status message |
| `GET` | `/health` | Health check |
| `GET` | `/claims` | List all claims |
| `GET` | `/claims/{claim_id}` | Retrieve a single claim |
| `GET` | `/policies/{policy_number}` | Retrieve a single policy |
| `GET` | `/rag/search?q={query}` | Search policy clauses by keyword |
| `GET` | `/pre-assessment/{claim_id}` | Generate a structured pre-assessment |
| `GET` | `/dashboard/stats` | Dashboard claim statistics by insurance type |

### Example: Pre-Assessment Response

```json
{
  "claim_id": "CP-H-001",
  "claimant_name": "Ravi Shankar Rao",
  "policy_number": "HG-2023-001",
  "claimed_amount": 9000,
  "policy_found": true,
  "relevant_clauses": [
    {
      "clause_id": "HC001",
      "insurance_type": "HEALTH",
      "clause_type": "COVERAGE",
      "clause_name": "Hospitalization Coverage",
      "clause_text": "Hospitalization expenses are covered when admission exceeds 24 hours."
    }
  ],
  "recommendation": "REVIEW_REQUIRED",
  "generated_by": "ClaimSense AI"
}
```

Interactive API documentation is available at `/docs` when the server is running.

---

## 7. Dataset Structure

All runtime data lives in the `data/` directory. The application validates these files exist on startup.

### `claims.csv` (650 records)

| Column | Description |
|--------|-------------|
| `claim_id` | Unique claim identifier (e.g. `CP-H-001`) |
| `insurance_type` | `HEALTH`, `VEHICLE`, `LIFE`, `HOME`, or `CROP` |
| `claim_type` | Claim category (e.g. `HEALTH_REIMBURSEMENT`) |
| `policy_number` | Associated policy number |
| `claimant_name` | Name of the claimant |
| `incident_date` | Date of incident |
| `claimed_amount` | Amount claimed (INR) |
| `status` | Claim processing status |
| `queue_tier` | Review queue tier |
| `triage_score` | Triage priority score |

### `policies.csv` (5 records)

| Column | Description |
|--------|-------------|
| `policy_id` | Internal policy identifier |
| `policy_number` | Policy number (e.g. `HG-2023-001`) |
| `policy_name` | Policy product name |
| `insurance_type` | Insurance category |
| `sum_insured` | Sum insured amount |
| `policy_status` | Policy status (e.g. `ACTIVE`) |

### `policy_clauses.csv` (23 clauses)

| Column | Description |
|--------|-------------|
| `clause_id` | Clause identifier (e.g. `HC001`) |
| `insurance_type` | Applicable insurance type |
| `clause_type` | Category (e.g. `COVERAGE`, `EXCLUSION`, `WAITING_PERIOD`) |
| `clause_name` | Short clause title |
| `clause_text` | Full clause text |

### `audit_events.csv` (append-only)

| Column | Description |
|--------|-------------|
| `event_id` | Sequential audit event ID (e.g. `AUD-001`) |
| `claim_id` | Related claim |
| `event_type` | Event type (e.g. `PRE_ASSESSMENT`) |
| `actor` | Actor (`SYSTEM`) |
| `event_description` | Human-readable description |
| `event_timestamp` | UTC ISO timestamp |

---

## 8. RAG Workflow

ClaimSense AI uses a **keyword-based retrieval** approach (Phase 1 foundation). No vector database or embeddings are used at this stage.

### Search flow

1. Query is tokenized into lowercase keywords.
2. Each policy clause is scored using weighted field matching:
   - `clause_text` — weight **3**
   - `clause_name` — weight **2**
   - `clause_type` — weight **1**
3. Clauses with a score greater than zero are returned, sorted highest score first.

### Pre-assessment RAG flow

1. Load claim by `claim_id`.
2. Build a search query from `insurance_type` and `claim_type`.
3. Filter clauses to the claim's insurance type.
4. Rank clauses by weighted keyword score.
5. If no keyword matches are found, return all clauses for that insurance type as fallback.
6. Attach ranked clauses to the pre-assessment response.
7. Write an audit event (`PRE_ASSESSMENT` / `SYSTEM`).

```
Claim → Policy lookup → RAG clause retrieval → Structured response → Audit log
                              ↓
                    recommendation: REVIEW_REQUIRED
```

---

## 9. Running Locally

### Prerequisites

- Python 3.12
- pip

### Setup

```bash
# Clone the repository and navigate to the project root
cd apinnovation-c3insuranceclaimpre-assessmentagent

# Install dependencies
pip install -r requirements.txt

# Start the development server
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

### Configuration

Settings are managed via `app/config.py` and can be overridden with environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATA_DIR` | `./data` | Path to CSV data directory |
| `APP_NAME` | `ClaimSense AI` | Application name |
| `VERSION` | `1.0.0` | Application version |
| `RAG_TOP_K` | `10` | RAG result limit (reserved for future use) |
| `LOW_RAG_SIMILARITY` | `0.0` | Similarity threshold (reserved for future use) |

### Quick API checks

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/claims/CP-H-001
curl "http://127.0.0.1:8000/rag/search?q=waiting"
curl http://127.0.0.1:8000/pre-assessment/CP-H-001
curl http://127.0.0.1:8000/dashboard/stats
```

---

## 10. Testing

The project uses **pytest** for automated integration testing.

```bash
pytest
```

**Current status: 14 automated tests passing.**

Tests cover:

- Health and root endpoints
- Claims listing and retrieval (including 404 handling)
- Policy retrieval (including 404 handling)
- RAG keyword search (matches and no-match cases)
- Pre-assessment generation and audit event creation
- Dashboard statistics
- Startup dataset validation

Tests run against an isolated temporary data directory to avoid modifying production CSV files.

For coverage reporting (as used in CI):

```bash
pytest --cov --cov-report=html
```

---

## 11. Current Project Status

### Phase 1 — Complete

| Area | Status |
|------|--------|
| Backend Foundation | Done |
| Dataset Layer | Done |
| Policy Knowledge Base | Done |
| RAG Foundation (keyword search) | Done |
| Audit Logging | Done |
| Modular Architecture Refactor | Done |
| Automated Testing (14/14) | Done |

### In Progress

| Area | Status |
|------|--------|
| Document Intelligence Layer | Planned — not yet implemented |

---

## 12. Roadmap

### Phase 2 — Document Intelligence *(planned)*

- Document upload
- OCR extraction
- Claim completeness validation

### Phase 3 — Advanced Assessment *(planned)*

- Evidence brief generation
- Advanced RAG (vector search / embeddings)

---

## Design Principles

- **Human-in-the-loop:** AI recommends `REVIEW_REQUIRED` only; humans approve or reject.
- **CSV-first:** No database dependency; all data persisted in CSV files.
- **Modular:** Clear separation between routers, services, stores, and domain logic.
- **Auditable:** Every pre-assessment generates an immutable audit record.
- **Testable:** Full API coverage via pytest integration tests.

---

## License

Calibo AI Academy Capstone Project.
