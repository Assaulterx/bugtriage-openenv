# BugTriage OpenEnv

A real-world bug triage environment for the OpenAI / PyTorch OpenEnv hackathon.
An AI agent triages software bug reports by classifying severity, assigning components and labels, detecting duplicate issues, and writing triage summaries.

## Motivation

Every software team spends significant engineering hours triaging incoming bug reports — reading descriptions, classifying severity, routing to the right team, detecting duplicates, and writing summaries. This environment simulates the end-to-end triage workflow so an AI agent can learn to do it automatically.

## Observation Space

| Field | Type | Description |
|---|---|---|
| `task_id` | string | Identifier of the current task |
| `task_description` | string | Human-readable task description |
| `bug_report` | string | Full formatted bug report (title, body, stack trace, related issues) |
| `step` | int | Current step count |
| `max_steps` | int | Maximum steps allowed |
| `available_actions` | list[str] | Valid action templates for this task |
| `assigned_severity` | str\|null | Severity already assigned |
| `assigned_component` | str\|null | Component already assigned |
| `assigned_label` | str\|null | Label already assigned |
| `duplicate_of` | str\|null | Duplicate issue ID if marked |
| `summary` | str\|null | Triage summary text |
| `done` | bool | Whether episode is finished |
| `error` | str\|null | Error message from the last action |

## Action Space

| Action Type | Value | Description |
|---|---|---|
| `classify_severity` | `blocker`, `critical`, `major`, `minor`, `trivial` | Classify bug severity |
| `assign_component` | `ui`, `api`, `database`, `auth`, `performance`, `security`, `devops` | Assign responsible component |
| `assign_label` | `bug`, `feature_request`, `duplicate`, `wontfix`, `needs_more_info`, `regression`, `hotfix` | Assign label |
| `mark_duplicate` | issue ID or `none` | Mark as duplicate of another issue |
| `write_summary` | free text | Write triage summary (hard task) |
| `noop` | - | No operation (costs a step) |

## Tasks

### Easy — `bug_triage_easy` (max 5 steps)
Triage a single straightforward frontend bug report.
Classify severity, assign component, and label it.

### Medium — `bug_triage_medium` (max 6 steps)
Triage a backend authentication bug that may be a duplicate.
Classify severity, assign component/label, and detect if it duplicates BUG-1042.

### Hard — `bug_triage_hard` (max 8 steps)
Triage a complex production database performance incident.
All triage fields plus a summary that must capture key terms (slow, query, timeout, production).

## Reward Function

| Signal | Description |
|---|---|
| **Partial progress** | Correct severity/component/label/duplicate each give partial reward |
| **Step cost** | -0.01 per step to penalize inefficiency |
| **Invalid action penalty** | -0.05 for invalid values |
| **Repeated action penalty** | -0.03 for repeating the same action+value |
| **Completion bonus** | Final grader score (0-1) added on the final step |

## Quickstart

### Prerequisites
Python 3.10+, pip

### Install
```bash
pip install -r requirements.txt
```

### Local Validation
```bash
bash scripts/validate-local.sh
```

### Run Tests
```bash
python -m pytest tests/test_env.py -v
```

### Run Inference
```bash
export API_BASE_URL="https://your-api-endpoint"
export MODEL_NAME="your-model-name"
export API_KEY="your-api-key"
python inference.py
```

### Docker
```bash
docker build -t bugtriage-openenv .
docker run -p 7860:7860 bugtriage-openenv
```

### Hugging Face Spaces Deployment
1. Create a new Space on huggingface.co/spaces
2. Select "Docker" as the SDK
3. Push all files to the Space repo:
```bash
cd /path/to/bugtriage-env
huggingface-cli login
huggingface-cli repo create bugtriage-env --type space --space_sdk docker
git init
git remote add origin https://huggingface.co/spaces/<your-username>/bugtriage-env
git add .
git commit -m "Initial commit"
git push origin main
```
4. Add environment variables in Space Settings: `API_BASE_URL`, `MODEL_NAME`, `HF_TOKEN`
