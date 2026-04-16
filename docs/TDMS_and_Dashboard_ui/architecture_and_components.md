# Architecture And Components

TDMS and the Test Case Execution Dashboard share authentication, core data models, and database state, while serving different operational needs.

## Runtime Architecture

```text
TDMS Frontend (Vite/React)  ------> TDMS Backend (FastAPI) ------>
                                     Shared Database (SQLite/MariaDB)
Dashboard Frontend (CRA/React) --> Dashboard Backend (FastAPI) -->

Both frontends <-------------------- Auth Service (FastAPI)
Dashboard Backend <----------------> Interface Manager (FastAPI)
Dashboard Frontend <---------------> Dashboard WebSocket (/ws/test-run)
```

## Core Components

| Component | Path | Purpose |
|---|---|---|
| TDMS Frontend | `src/app/TDMS/front-end` | CRUD UI for test data entities and user-facing administration flows |
| TDMS Backend | `src/app/TDMS/back-end` | REST APIs for dashboard counts, users, and v2 data management resources |
| Dashboard Frontend | `src/app/TestCaseExecutorDashboard/front-end` | Run orchestration UI, live tracking, analysis trigger, and report download |
| Dashboard Backend | `src/app/TestCaseExecutorDashboard/back-end` | Run execution orchestration, filtering APIs, analysis APIs, reporting, WebSocket push |
| Auth Service | `src/app/auth_service` | Central login, token issuance, refresh, logout, and role-based redirect |
| Interface Manager | `src/app/interface_manager` | Target interaction bridge used during test run execution |

## Shared Data Model Scope

Both TDMS and dashboard operate on common entities and run records.

- TDMS core entities: test cases, targets, prompts, responses, strategies, domains, languages, test plans, metrics, LLM prompts
- Dashboard execution entities: test runs, run details, conversations, timelines, evaluation summaries

## Why The Split Exists

- TDMS optimizes for data governance and curation.
- Dashboard optimizes for execution, monitoring, and post-run analysis.
- Auth service ensures one login boundary across both applications.
