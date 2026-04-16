# TDMS Module Guide

TDMS is the system of record for evaluation data used by execution and analysis workflows.

## Main TDMS Pages

Configured routes in TDMS frontend include:

- `/dashboard`
- `/test-cases`
- `/targets`
- `/domains`
- `/strategies`
- `/languages`
- `/responses`
- `/prompts`
- `/llm-prompts`
- `/test-plans`
- `/metrics`
- `/users`
- `/user-history/:username`

## Dashboard Page Inside TDMS

The TDMS dashboard summarizes counts for key entities:

- test cases
- targets
- domains
- strategies
- languages
- responses
- prompts
- LLM prompts
- test plans
- metrics

Each card supports quick navigation to its management page.

## Typical Data Preparation Sequence

- Create or update targets.
- Maintain supporting domains and languages.
- Create prompts and LLM prompts.
- Curate responses and strategies.
- Build test plans and metric mappings.
- Register and validate test cases.

## User And Activity Views

- User management endpoints are available under `/api/users`.
- Entity and user activity history is exposed through user activity APIs.
- Visibility of user-management actions is role-dependent.

## Operational Notes

- TDMS frontend defaults to `VITE_API_BASE_URL=http://localhost:7250`.
- TDMS API supports both legacy and `/api/v2/*` endpoints; v2 resources are preferred for current CRUD flows.
