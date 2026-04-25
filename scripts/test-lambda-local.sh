#!/bin/bash
# test-lambda-local.sh
# End-to-end test for the Lambda RIE running at http://localhost:8765.
#
# Prerequisites:
#   docker compose up -d db localstack lambda worker
#
# Usage:
#   bash scripts/test-lambda-local.sh

set -euo pipefail

BASE_URL="http://localhost:8765/2015-03-31/functions/function/invocations"
API_KEY="test"
POLL_INTERVAL=2
MAX_POLLS=15

# ── Colours ──────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Colour

pass()  { echo -e "  ${GREEN}✓${NC} $1"; }
fail()  { echo -e "  ${RED}✗${NC} $1"; FAILED=1; }
header(){ echo -e "\n${BOLD}${CYAN}── $1 ──${NC}"; }

FAILED=0

# ── Helper: invoke Lambda ───────────────────────────────────────────────────
# Usage: invoke_lambda <json-event>
invoke_lambda() {
  curl -s -X POST "$BASE_URL" \
    -H "Content-Type: application/json" \
    -d "$1"
}

# Build an API-Gateway-v1 (REST) proxy event
# Usage: apigw_event <METHOD> <PATH> [BODY]
apigw_event() {
  local method="$1" path="$2" body="${3:-null}"
  # Escape body for JSON embedding (wrap in quotes if non-null)
  if [[ "$body" != "null" ]]; then
    # Escape inner double-quotes and wrap
    body=$(echo "$body" | sed 's/\\/\\\\/g; s/"/\\"/g')
    body="\"$body\""
  fi
  cat <<EOF
{
  "resource": "$path",
  "httpMethod": "$method",
  "path": "$path",
  "headers": { "Host": "localhost", "X-API-KEY": "$API_KEY", "Content-Type": "application/json" },
  "queryStringParameters": null,
  "pathParameters": null,
  "stageVariables": null,
  "requestContext": { "resourcePath": "$path", "httpMethod": "$method", "path": "$path" },
  "body": $body,
  "isBase64Encoded": false
}
EOF
}

# ─────────────────────────────────────────────────────────────────────────────
# 1) Migration
# ─────────────────────────────────────────────────────────────────────────────
header "1/6  Run Migration"
RESP=$(invoke_lambda '{"event_type": "Migration"}')
STATUS=$(echo "$RESP" | python -c "import sys,json; print(json.load(sys.stdin).get('statusCode',0))")
if [[ "$STATUS" == "200" ]]; then
  pass "Migration completed (status $STATUS)"
else
  fail "Migration failed – response: $RESP"
fi

# ─────────────────────────────────────────────────────────────────────────────
# 2) Seed Languages
# ─────────────────────────────────────────────────────────────────────────────
header "2/6  Seed Languages"
RESP=$(invoke_lambda '{"event_type": "Seed_Languages"}')
STATUS=$(echo "$RESP" | python -c "import sys,json; print(json.load(sys.stdin).get('statusCode',0))")
if [[ "$STATUS" == "200" ]]; then
  pass "Languages seeded (status $STATUS)"
else
  fail "Seed failed – response: $RESP"
fi

# ─────────────────────────────────────────────────────────────────────────────
# 3) Health Check
# ─────────────────────────────────────────────────────────────────────────────
header "3/6  Health Check"
EVENT=$(apigw_event GET "/api/v1/health")
RESP=$(invoke_lambda "$EVENT")
BODY=$(echo "$RESP" | python -c "import sys,json; print(json.load(sys.stdin).get('body',''))")
if echo "$BODY" | grep -q '"ok"'; then
  pass "Health OK"
else
  fail "Health check failed – body: $BODY"
fi

# ─────────────────────────────────────────────────────────────────────────────
# 4) List Languages
# ─────────────────────────────────────────────────────────────────────────────
header "4/6  List Languages"
EVENT=$(apigw_event GET "/api/v1/languages")
RESP=$(invoke_lambda "$EVENT")
BODY=$(echo "$RESP" | python -c "import sys,json; print(json.load(sys.stdin).get('body',''))")
LANG_COUNT=$(echo "$BODY" | python -c "import sys,json; print(len(json.load(sys.stdin).get('data',[])))")
if [[ "$LANG_COUNT" -gt 0 ]]; then
  pass "Found $LANG_COUNT language(s)"
else
  fail "No languages found – body: $BODY"
fi

# ─────────────────────────────────────────────────────────────────────────────
# 5) Create Submission  (Python: print Hello World)
# ─────────────────────────────────────────────────────────────────────────────
header "5/6  Create Submission (Python)"
SUB_BODY='{"source_code": "print(\"Hello from Lambda + SQS + Worker!\")", "language_id": 3}'
EVENT=$(apigw_event POST "/api/v1/submissions" "$SUB_BODY")
RESP=$(invoke_lambda "$EVENT")

HTTP_STATUS=$(echo "$RESP" | python -c "import sys,json; print(json.load(sys.stdin).get('statusCode',0))")
RESP_BODY=$(echo "$RESP" | python -c "import sys,json; print(json.load(sys.stdin).get('body',''))")
TOKEN=$(echo "$RESP_BODY" | python -c "import sys,json; print(json.load(sys.stdin)['data']['token'])" 2>/dev/null || echo "")

if [[ "$HTTP_STATUS" == "201" && -n "$TOKEN" ]]; then
  pass "Submission created  token=$TOKEN"
else
  fail "Create submission failed (status $HTTP_STATUS) – body: $RESP_BODY"
fi

# ─────────────────────────────────────────────────────────────────────────────
# 6) Poll Submission Until Processed
# ─────────────────────────────────────────────────────────────────────────────
header "6/6  Poll Submission Result"

if [[ -z "$TOKEN" ]]; then
  fail "Skipping poll – no token from previous step"
else
  FINAL_STATUS=""
  for i in $(seq 1 $MAX_POLLS); do
    sleep "$POLL_INTERVAL"
    EVENT=$(apigw_event GET "/api/v1/submissions/$TOKEN")
    RESP=$(invoke_lambda "$EVENT")
    RESP_BODY=$(echo "$RESP" | python -c "import sys,json; print(json.load(sys.stdin).get('body',''))")
    SUB_STATUS=$(echo "$RESP_BODY" | python -c "import sys,json; print(json.load(sys.stdin)['data']['status'])" 2>/dev/null || echo "unknown")

    if [[ "$SUB_STATUS" == "Queued" || "$SUB_STATUS" == "Processing" ]]; then
      echo "  ⏳ Poll $i/$MAX_POLLS – status: $SUB_STATUS"
      continue
    fi

    FINAL_STATUS="$SUB_STATUS"
    break
  done

  if [[ "$FINAL_STATUS" == "Accepted" ]]; then
    STDOUT=$(echo "$RESP_BODY" | python -c "import sys,json; d=json.load(sys.stdin)['data']; print(d.get('stdout','').strip())")
    TIME=$(echo "$RESP_BODY"   | python -c "import sys,json; d=json.load(sys.stdin)['data']; print(d.get('time','?'))")
    MEMORY=$(echo "$RESP_BODY" | python -c "import sys,json; d=json.load(sys.stdin)['data']; print(d.get('memory','?'))")
    pass "Submission accepted!"
    echo "       stdout : $STDOUT"
    echo "       time   : ${TIME}s"
    echo "       memory : ${MEMORY} KB"
  elif [[ -z "$FINAL_STATUS" ]]; then
    fail "Timed out after $((MAX_POLLS * POLL_INTERVAL))s – last status: $SUB_STATUS"
  else
    STDERR=$(echo "$RESP_BODY" | python -c "import sys,json; d=json.load(sys.stdin)['data']; print(d.get('stderr',''))" 2>/dev/null || echo "")
    fail "Unexpected status: $FINAL_STATUS"
    [[ -n "$STDERR" ]] && echo "       stderr: $STDERR"
  fi
fi

# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
echo ""
if [[ "$FAILED" -eq 0 ]]; then
  echo -e "${GREEN}${BOLD}All tests passed!${NC}"
else
  echo -e "${RED}${BOLD}Some tests failed.${NC}"
  exit 1
fi
