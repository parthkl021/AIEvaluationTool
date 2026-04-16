# Troubleshooting

Use this guide when TDMS and dashboard are running but not behaving as expected.

## Auth Redirect Loop

Symptoms:

- repeated redirect between app and login
- immediate return to login after sign-in

Checks:

- verify auth service is up on `http://localhost:7500`
- verify app auth URLs (`VITE_AUTH_SERVICE_URL`, `REACT_APP_AUTH_SERVICE_URL`)
- clear local storage tokens and sign in again

## TDMS Loads But Data APIs Fail

Symptoms:

- dashboard cards show errors or zero values unexpectedly
- CRUD tables fail to load

Checks:

- confirm TDMS backend is running on `http://localhost:7250`
- confirm bearer token is included in API calls
- verify database config in root `config.json`

## Dashboard Filters Or Start-Run Options Are Empty

Symptoms:

- target/plan filters not populated
- metric list not loading after plan selection

Checks:

- verify `GET /get_all_filters` returns data
- confirm seeded test data exists in database
- ensure TDMS-managed entities are available (targets, plans, metrics)

## Run Starts But No Live Progress

Symptoms:

- run starts but progress loop does not update

Checks:

- ensure dashboard backend WebSocket endpoint is reachable: `/ws/test-run`
- verify frontend `REACT_APP_API_BASE_URL` points to dashboard backend
- check backend logs for WebSocket disconnects

## Continue Run Fails

Symptoms:

- `continue-run` returns not found or validation errors

Checks:

- confirm run name is valid and already exists
- verify run was created in the same connected database
- confirm run detail records exist for the selected run

## Report Download Fails

Symptoms:

- report action completes without file download

Checks:

- verify `/report/{run_name}` responds successfully
- check write permissions for temporary file generation
- confirm run has analysis outputs before report generation

## SQLite Locking Or Concurrency Issues

Symptoms:

- intermittent write failures during heavy activity

Checks:

- avoid running multiple conflicting write-heavy operations in parallel
- switch to MariaDB for multi-user or high-throughput usage

## Recommended Operational Practices

- keep `config.json` under version control for team-consistent ports
- align `db.engine` and `db.engine_type` values
- start auth and backends before frontends
- verify interface manager before long run executions
