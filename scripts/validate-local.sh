#!/usr/bin/env bash
# Local validation script for BugTriage OpenEnv
# Run: bash scripts/validate-local.sh

set -e
cd "$(dirname "$0")/.."

PASS=0
FAIL=0

check() {
  local desc="$1"
  shift
  if eval "$@"; then
    echo "[PASS] $desc"
    PASS=$((PASS + 1))
  else
    echo "[FAIL] $desc"
    FAIL=$((FAIL + 1))
  fi
}

echo "=== BugTriage OpenEnv Local Validation ==="
echo ""

# 1. Required files exist
echo "-- File existence checks --"
for f in README.md inference.py openenv.yaml requirements.txt Dockerfile app.py envs/__init__.py envs/models.py envs/tasks.py envs/graders.py envs/rewards.py envs/bug_triage.py; do
  check "$f exists" "[[ -f '$f' ]]"
done
echo ""

# 2. Python imports work
echo "-- Import checks --"
check "pydantic importable" "python -c 'import pydantic'" 2>/dev/null || true
check "envs modules importable" "python -c 'from envs.bug_triage import BugTriageEnv; from envs.models import ActionModel, Observation, Reward, EnvState'" 2>/dev/null || true
echo ""

# 3. OpenEnv YAML parses
check "openenv.yaml is valid YAML" "python -c 'import yaml; yaml.safe_load(open(\"openenv.yaml\"))'" 2>/dev/null || true
echo ""

# 4. Basic environment startup
echo "-- Environment smoke test --"
python -c "
from envs.bug_triage import BugTriageEnv
from envs.tasks import ALL_TASKS
from envs.models import ActionModel, ActionType

env = BugTriageEnv()
for task_id in ALL_TASKS:
    obs = env.reset(task_id)
    assert obs.task_id == task_id, f'reset failed for {task_id}'
    assert obs.step == 0
    assert obs.max_steps > 0
    assert not obs.done
    assert len(obs.available_actions) > 0

    # Take one step
    action = ActionModel(action_type=ActionType.NOOP, value='')
    obs2, reward = env.step(action)
    assert obs2.step == 1
    assert reward.value <= 0  # step cost

    # Check state
    st = env.state()
    assert st.task_id == task_id
    assert st.step == 1
    print(f'  {task_id}: reset/step/state OK')

print('All environments smoke-tested successfully.')
" 2>/dev/null && { check "environment smoke test passed" "true"; } || { check "environment smoke test passed" "false"; }
echo ""

# 5. Grader score range
echo "-- Grader range checks --"
python -c "
from envs.graders import GRADERS
from envs.tasks import ALL_TASKS, ALL_BUG_REPORTS

for task_id, grader in GRADERS.items():
    gt = ALL_TASKS[task_id]['ground_truth']

    # Score with empty state (should be 0)
    empty = {'assigned_severity': '', 'assigned_component': '', 'assigned_label': '', 'duplicate_of': '', 'summary': ''}
    s = grader(empty, gt)
    assert 0.0 <= s <= 1.0, f'{task_id} empty score {s} out of range'

    # Score with perfect state
    perfect = {
        'assigned_severity': gt['severity'],
        'assigned_component': gt['component'],
        'assigned_label': gt['label'],
        'duplicate_of': gt.get('duplicate_of', '') or '',
        'summary': 'This is a slow query causing timeout in production database' if task_id == 'bug_triage_hard' else ''
    }
    s = grader(perfect, gt)
    assert 0.0 <= s <= 1.0, f'{task_id} perfect score {s} out of range'
    assert s >= 0.8, f'{task_id} perfect score should be high, got {s}'

    empty_score = grader(empty, gt)
    print(f'  {task_id}: empty={empty_score:.2f}, perfect={s:.2f}')

print('All grader scores in [0.0, 1.0].')
" 2>/dev/null && { check "grader scores in range" "true"; } || { check "grader scores in range" "false"; }
echo ""

# 6. Docker build test
echo "-- Docker build test --"
check "Dockerfile exists" "[[ -f 'Dockerfile' ]]"
if command -v docker &>/dev/null; then
  check "docker build succeeds" "docker build -t bugtriage-test ."
else
  echo "[SKIP] docker not installed"
fi
echo ""

echo "=== Results: $PASS passed, $FAIL failed ==="
if [ "$FAIL" -gt 0 ]; then
  exit 1
fi
