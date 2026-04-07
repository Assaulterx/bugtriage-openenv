"""Task definitions: 3 difficulty levels with deterministic ground truth."""

from typing import Dict, List


TASK_EASY = {
    "task_id": "bug_triage_easy",
    "difficulty": "easy",
    "task_description": "Triage a single, straightforward frontend bug report. Classify its severity, assign the correct component, and label it.",
    "max_steps": 5,
    "ground_truth": {
        "severity": "major",
        "component": "ui",
        "label": "bug"
    }
}

TASK_MEDIUM = {
    "task_id": "bug_triage_medium",
    "difficulty": "medium",
    "task_description": "Triage a backend authentication bug report that may be a duplicate. Classify severity, assign component and label, and detect if it duplicates a known issue.",
    "max_steps": 6,
    "ground_truth": {
        "severity": "critical",
        "component": "auth",
        "label": "duplicate",
        "duplicate_of": "BUG-1042"
    }
}

TASK_HARD = {
    "task_id": "bug_triage_hard",
    "difficulty": "hard",
    "task_description": "Triage a complex production database performance incident. Classify severity, assign component and label, detect duplication, and write a concise triage summary. The summary must be at least 20 characters and contain key terms from the report.",
    "max_steps": 8,
    "ground_truth": {
        "severity": "blocker",
        "component": "database",
        "label": "hotfix",
        "duplicate_of": None,
        "summary_min_length": 20,
        "summary_required_terms": ["slow", "query", "timeout", "production"]
    }
}


class BugTask:
    """A single bug to triage."""

    def __init__(self, report_id: str, title: str, body: str, reporter: str,
                 stack_trace: str, related_issues: List[str]):
        self.report_id = report_id
        self.title = title
        self.body = body
        self.reporter = reporter
        self.stack_trace = stack_trace
        self.related_issues = related_issues


# Canonical bug reports for each task
BUG_EASY = BugTask(
    report_id="BUG-2201",
    title="Login modal closes unexpectedly when clicking outside on mobile",
    body=(
        "When a user opens the login modal on a mobile device and clicks outside the modal area, "
        "the modal closes even though the user has not submitted the form. This is inconsistent "
        "with the desktop version where an explicit close action is required.\n\n"
        "Steps to reproduce:\n"
        "1. Open the app on a mobile device or use mobile emulation in devtools\n"
        "2. Navigate to any page and click the login button\n"
        "3. Tap outside the modal overlay\n"
        "4. Observe the modal closes without submitting\n\n"
        "Expected: Modal should require an explicit close action on mobile similar to desktop."
    ),
    reporter="dev_sarah",
    stack_trace="No error trace — UI behavior issue.\n"
                "Console: Warning: Modal overlay click handler fires on touch events without preventDefault.",
    related_issues=["BUG-1998 (desktop modal works correctly)"]
)

BUG_MEDIUM = BugTask(
    report_id="BUG-2247",
    title="OAuth token refresh returns 401 after password change",
    body=(
        "After a user changes their password, the subsequent OAuth token refresh request returns "
        "HTTP 401 instead of issuing a new token. This affects all users who recently changed their "
        "password.\n\n"
        "The issue started after the auth-service v2.4.0 deployment on 2025-11-02.\n\n"
        "Steps to reproduce:\n"
        "1. Log in with valid credentials\n"
        "2. Change your password via account settings\n"
        "3. Wait until the current access token expires (or invalidate it)\n"
        "4. Observe refresh_token endpoint returns 401 Unauthorized\n\n"
        "Impact: Users are forced to log in again after every password change, defeating SSO. "
        "This is blocking the onboarding automation team.\n\n"
        "Note: This appears related to how the refresh token HMAC is computed after credential rotation."
    ),
    reporter="dev_marcus",
    stack_trace=(
        "INFO  auth-service[pid=14]: Refresh token validated for user_id=8832\n"
        "ERROR auth-service[pid=14]: HMAC verification failed for refresh token, old_password_hash != current\n"
        "  File \"auth/token.py\", line 214, in verify_refresh\n"
        "    raise TokenValidationError(\"HMAC mismatch\", code=401)\n"
        "TokenValidationError: HMAC mismatch on refresh for user_id 8832"
    ),
    related_issues=[
        "BUG-1042 (OAuth refresh breaks on credential rotation — closed as wontfix in v2.3)",
        "PR-3100 (updated token hashing — merged v2.4.0)"
    ]
)

BUG_HARD = BugTask(
    report_id="BUG-2299",
    title="Production database queries timing out causing 503 cascading failure",
    body=(
        "Multiple production database queries are experiencing severe slowdowns (>60s latency), "
        "causing API request timeouts and a cascading 503 failure across services.\n\n"
        "On-call alert triggered at 14:23 UTC. Root cause appears to be a missing index on the "
        "orders table after the schema migration v3.12.0 that was rolled out during the maintenance window.\n\n"
        "Impact assessment:\n"
        "- Checkout flow: completely broken (HTTP 503)\n"
        "- Order history UI: loading indefinitely\n"
        "- Admin dashboard: partial data with stale reads from cache\n"
        "- Estimated revenue impact: $12k–$18k per hour of downtime\n\n"
        "Temporary mitigation: Traffic has been routed to read-replica but it is now at 95% CPU.\n\n"
        "The migration added a new column 'fulfillment_status' to orders but did NOT create an "
        "index on (user_id, fulfillment_status, created_at) which the order history query requires. "
        "This causes full table scans on ~40M rows."
    ),
    reporter="oncall_team",
    stack_trace=(
        "WARN  api-gateway[pid=512]: upstream timeout after 60s for /api/v3/orders\n"
        "ERROR db-proxy[pid=88]: query exceeded slow_query_threshold=5000ms\n"
        "  query: SELECT * FROM orders WHERE user_id=$1 AND fulfillment_status=$2 ORDER BY created_at DESC\n"
        "  duration: 62431ms\n"
        "  plan: Seq Scan on orders (cost=0.00..847291.34 rows=40123091 width=234)\n"
        "          Filter: (user_id = 9012 AND fulfillment_status = 'pending')\n"
        "  rows examined: 40,123,091  rows returned: 142\n"
        "CRITICAL api-gateway[pid=512]: circuit breaker OPEN for downstream /api/v3/orders\n"
        "WARN  api-gateway[pid=513]: circuit breaker OPEN for downstream /api/v3/orders\n"
        "INFO  read-replica[pid=22]: CPU at 95%, connection pool exhausted (48/50 active)"
    ),
    related_issues=[
        "MIG-445 (schema migration v3.12.0 — rolled out 2025-11-10 02:00 UTC)",
        "BUG-2150 (slow query alerts on staging during migration review — dismissed)"
    ]
)


ALL_BUG_REPORTS: Dict[str, BugTask] = {
    "bug_triage_easy": BUG_EASY,
    "bug_triage_medium": BUG_MEDIUM,
    "bug_triage_hard": BUG_HARD,
}

ALL_TASKS: Dict[str, dict] = {
    "bug_triage_easy": TASK_EASY,
    "bug_triage_medium": TASK_MEDIUM,
    "bug_triage_hard": TASK_HARD,
}
