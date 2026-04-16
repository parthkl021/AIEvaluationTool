# Dashboard Workflows

The Test Case Execution Dashboard is the primary UI for run orchestration, monitoring, analysis, and reporting.

## Home And Test Runs

The home page shows all test runs with:

- sorting (`Started At` / `End`) 
- filters (`Target`, `Status`, `Domain`)
- pagination (10 runs per page)
- actions (`Continue`, `Analyse`, `Report`)

Important behavior:

- opening run details is blocked for `RUNNING` and `NEW` runs
- row click opens details for completed runs

![Test Runs](../../screenshots/TRDB_first_page.png)

## Create New Test Run

Path: `/create-test-run`

Main fields:

- run name (optional)
- target
- test plan
- metric (depends on selected plan)
- test case name (optional)
- max test cases
- domain and language (loaded from target metadata)

Execution loop stages shown in UI:

1. Prepare
2. Finding elements
3. Execute
4. Store

![Create Run](../../screenshots/TRDB_add_test_run.png)

## Continue Existing Run

Path: `/continue-run/:runName`

Flow:

- load existing run context
- inspect grouped `metrics by plan`
- choose plan and optional filters
- continue execution using `continue-run-with-plan`

## Analyse Run

Path: `/analyse/:runName`

Capabilities:

- live status via API and WebSocket updates
- grouped progress by metric
- per-testcase status (`PENDING`, `RUNNING`, `COMPLETED`, `FAILED`)
- retry mode support (for failed cases)

![Run Analysis](../../screenshots/TRDB_test_run_details.png)

## Run Details And Reporting

Path: `/test-runs/:runName`

Details page includes:

- run summary card (target, domain, timestamps, duration)
- timeline view
- filterable run-details table
- conversation modal per testcase
- report download trigger

![Run Details](../../screenshots/TRDB_test_run_details.png)
![Single Testcase](../../screenshots/TRDB_single_testcase_eval_details.png)
