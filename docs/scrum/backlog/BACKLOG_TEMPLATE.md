---
id: 000
slug: example-slug
title: Example Task
epic: placeholder-epic
okr: OBJ-YYYY-QQ-KP1
state: backlog
priority: medium
story_points: 0
confidence: 0.5
created: 2025-10-30
updated: 2025-10-30
owners:
  - squad-backend
reviewers:
  - qa-lead
tags:
  - backend
  - ai-ready
linked_adr:
  - adr/2025-09-backend-strategy.md
dependencies:
  - 033
ai_ready:
  summary: >
    Capture the task in a form that lets an AI agent start without clarifying questions.
  entry_points:
    - repo: packages/backend
    - command: scripts/run_example_task.sh
  expected_output:
    - artifact: docs/public/example.md
---

## Context
Summarise why the task matters now: business driver, user persona, deadlines. Link supporting FDD/FSD, architecture diagrams, ADRs.

## Problem Statement
Describe the current pain, quantitative impact, and risks of doing nothing. Separate facts from assumptions.

## Desired Outcome
State the Definition of Ready/Done, measurable success criteria, and any SLA/OKR targets.

## Solution Sketch
- Outline the preferred implementation steps or architecture shape.
- Call out constraints, risks, alternatives that were considered.
- List open questions for grooming or discovery.

## Acceptance Criteria
- [ ] Verifiable functional requirements are documented.
- [ ] Required artefacts delivered (docs, diagrams, migrations, scripts).
- [ ] Metrics/alerts wired up and dashboards updated.

## AI Handoff
| Kind            | Value                                                          |
|-----------------|----------------------------------------------------------------|
| Command         | `make example-task`                                            |
| Sample input    | `packages/backend/example/input.json`                          |
| Tests           | `pytest tests/example --maxfail=1`                             |
| Review guideline| Confirm ADR + changelog updates and lint/test status.          |

## Validation & Observability
List unit/integration/smoke tests, manual checklists, and monitoring hooks (Grafana, Sentry, alerts). Assign ownership for verification.

## Traceability
- Jira/Linear issue ID
- Related PRs/merges
- Updated documents (changelog, release notes, ADRs)

## Notes
Capture decisions from grooming, timing constraints, cross-team dependencies, useful references.

---

# Backlog Management Practices

## Unified Index
- Maintain `packages/backend/docs/scrum/backlog/_index.md` with a table (ID, Title, State, Priority, Owners, Updated).
- Generate JSON/CSV from the front matter so AI agents can filter and prioritise programmatically.

## Encoding and Format
- Keep every document in UTF-8; avoid legacy encodings and pseudo-graphics.
- Normalise use of `state`, `priority`, `tags`, `owners`, and `epic` for consistent search and analytics.

## Traceability
- Reference ADR/FDD/FSD documents in `linked_adr` and keep them up to date.
- Populate `dependencies` so agents understand ordering and blocking work.

## AI-ready Fieldset
- Refresh `ai_ready.summary`, `entry_points`, `expected_output` whenever scope changes.
- Record canonical commands and artefacts so an agent can execute the task end-to-end.

## Quality Control
- Adopt explicit Definition of Ready/Done checklists per squad.
- Add a pre-commit/CI linter that validates mandatory fields in the front matter.
- Review `state` and `priority` on a cadence to close or re-triage stale items.
