#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

EMAILS_FILE="${1:-$ROOT_DIR/emails_candidate.json}"
HANDLER_ID="${HANDLER_ID:-live-demo-handler}"
BATCH_SIZE="${BATCH_SIZE:-2}"
SAMPLE_REDACTED_COUNT="${SAMPLE_REDACTED_COUNT:-3}"
SAMPLE_AUDIT_COUNT="${SAMPLE_AUDIT_COUNT:-8}"
BASE_URL="${BASE_URL:-http://localhost:8002}"
API_PREFIX="$BASE_URL/api/v1"

if [[ ! -f "$EMAILS_FILE" ]]; then
  echo "ERROR: emails file not found: $EMAILS_FILE" >&2
  exit 1
fi

echo "==> Starting infrastructure"
if [[ "${FORCE_BUILD:-0}" == "1" ]]; then
  docker compose up -d --build
else
  docker compose up -d
fi

# If model/provider env overrides are passed for this run, force app recreate so
# container env is refreshed even when image/config is otherwise unchanged.
if [[ -n "${LLM_MODEL:-}" || -n "${LLM_BASE_URL:-}" || -n "${LLM_PROVIDER:-}" || -n "${LLM_API_KEY:-}" ]]; then
  docker compose up -d --force-recreate app
fi

echo "==> Applying migrations"
docker compose exec -T app alembic upgrade head

echo "==> Waiting for API readiness"
READY_OK=0
for _ in $(seq 1 60); do
  if curl -fsS --connect-timeout 2 --max-time 5 "$BASE_URL/ready" >/tmp/cmi_ready.json 2>/dev/null; then
    READY_OK=1
    break
  fi
  printf "."
  sleep 2
done
echo
if [[ "$READY_OK" -ne 1 ]]; then
  echo "ERROR: API not ready at $BASE_URL/ready" >&2
  curl -sS --connect-timeout 2 --max-time 5 "$BASE_URL/health" || true
  docker compose ps
  docker compose logs --no-color --tail=80 app || true
  exit 1
fi
cat /tmp/cmi_ready.json
echo

echo "==> Waiting for Chroma heartbeat"
CHROMA_OK=0
for _ in $(seq 1 30); do
  if curl -fsS --connect-timeout 2 --max-time 5 "http://localhost:8001/api/v2/heartbeat" >/tmp/cmi_chroma.json 2>/dev/null; then
    CHROMA_OK=1
    break
  fi
  printf "."
  sleep 2
done
echo
if [[ "$CHROMA_OK" -ne 1 ]]; then
  echo "ERROR: Chroma heartbeat failed on http://localhost:8001/api/v2/heartbeat" >&2
  docker compose ps
  exit 1
fi
cat /tmp/cmi_chroma.json
echo

RUN_TS="$(date +%Y%m%d_%H%M%S)"
RUN_STARTED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
WORK_DIR="/tmp/cmi_demo_$RUN_TS"
mkdir -p "$WORK_DIR"

PAYLOAD_JSON="$WORK_DIR/process_payload.json"
PROCESS_RESPONSE_JSON="$WORK_DIR/process_response.json"
DIGEST_RESPONSE_JSON="$WORK_DIR/digest_response.json"
QUERY_1_JSON="$WORK_DIR/query_1.json"
QUERY_2_JSON="$WORK_DIR/query_2.json"
QUERY_3_JSON="$WORK_DIR/query_3.json"
EMAIL_HASHES_TXT="$WORK_DIR/email_hashes.txt"
PERSISTED_EMAIL_HASHES_TXT="$WORK_DIR/email_hashes_persisted.txt"

python3 - "$EMAILS_FILE" "$HANDLER_ID" "$BATCH_SIZE" "$PAYLOAD_JSON" <<'PY'
import json
import sys
import uuid

emails_file, handler_id, batch_size, out_path = sys.argv[1:]
with open(emails_file, "r", encoding="utf-8") as f:
    data = json.load(f)

emails = data.get("emails")
if not isinstance(emails, list):
    raise SystemExit("emails_candidate.json must contain a top-level 'emails' list")

payload = {
    "emails": emails,
    "handler_id": handler_id,
    "batch_size": int(batch_size),
    "correlation_id": str(uuid.uuid4()),
}
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(payload, f)
PY

EXPECTED_EMAILS="$(python3 - "$PAYLOAD_JSON" <<'PY'
import json
import sys
with open(sys.argv[1], "r", encoding="utf-8") as f:
    payload = json.load(f)
print(len(payload.get("emails", [])))
PY
)"

CORRELATION_ID="$(python3 - "$PAYLOAD_JSON" <<'PY'
import json
import sys
with open(sys.argv[1], "r", encoding="utf-8") as f:
    payload = json.load(f)
print(payload.get("correlation_id", ""))
PY
)"

echo "==> Processing emails via API"
curl -fsS -X POST "$API_PREFIX/process" \
  -H "Content-Type: application/json" \
  --data-binary "@$PAYLOAD_JSON" \
  >"$PROCESS_RESPONSE_JSON" &
PROCESS_PID=$!

while kill -0 "$PROCESS_PID" 2>/dev/null; do
  PROGRESS_SQL="select count(*) from audit_events where event_type='READ_MODELS_WRITTEN' and payload_json->>'batch_correlation_id'='${CORRELATION_ID}';"
  PROCESSED_COUNT="$(docker compose exec -T postgres psql -U postgres -d aviva_claims -At -c \
    "$PROGRESS_SQL" 2>/dev/null || echo 0)"
  PROCESSED_COUNT="${PROCESSED_COUNT:-0}"
  LAST_PROCESSED_COUNT="$PROCESSED_COUNT"
  printf "\rProcessing emails: %s/%s" "$PROCESSED_COUNT" "$EXPECTED_EMAILS"
  sleep 2
done

wait "$PROCESS_PID"
LAST_PROCESSED_COUNT="${LAST_PROCESSED_COUNT:-0}"
printf "\rProcessing emails: %s/%s\n" "$LAST_PROCESSED_COUNT" "$EXPECTED_EMAILS"

read -r RESPONSE_CORRELATION_ID TOTAL_PROCESSED EMAIL_COUNT UNIQUE_EMAIL_HASHES FALLBACK_EMAIL_HASHES < <(
  python3 - "$PROCESS_RESPONSE_JSON" <<'PY'
import json
import sys
from collections import OrderedDict

with open(sys.argv[1], "r", encoding="utf-8") as f:
    resp = json.load(f)

decisions = resp.get("decisions", [])
hashes = [d.get("email_hash", "") for d in decisions if d.get("email_hash")]
unique_hashes = list(OrderedDict.fromkeys(hashes))
fallback_hashes = [h for h in unique_hashes if h.startswith("fallback_")]

print(
    resp.get("correlation_id", ""),
    resp.get("total_processed", 0),
    len(decisions),
    len(unique_hashes),
    len(fallback_hashes),
)
PY
)

if [[ -z "$RESPONSE_CORRELATION_ID" ]]; then
  echo "ERROR: missing correlation_id in process response" >&2
  exit 1
fi

if [[ "$TOTAL_PROCESSED" -le 0 ]]; then
  echo "ERROR: total_processed is 0" >&2
  cat "$PROCESS_RESPONSE_JSON"
  exit 1
fi

python3 - "$PROCESS_RESPONSE_JSON" "$EMAIL_HASHES_TXT" <<'PY'
import json
import sys
from collections import OrderedDict

resp_file, out_file = sys.argv[1], sys.argv[2]
with open(resp_file, "r", encoding="utf-8") as f:
    resp = json.load(f)

hashes = [d.get("email_hash", "") for d in resp.get("decisions", []) if d.get("email_hash")]
unique = list(OrderedDict.fromkeys(hashes))

with open(out_file, "w", encoding="utf-8") as f:
    for h in unique:
        f.write(f"{h}\n")
PY

grep -v '^fallback_' "$EMAIL_HASHES_TXT" >"$PERSISTED_EMAIL_HASHES_TXT" || true

EMAIL_HASH_SQL_LIST="$(awk '{printf "'\''%s'\'',", $0}' "$EMAIL_HASHES_TXT" | sed 's/,$//')"
if [[ -z "$EMAIL_HASH_SQL_LIST" ]]; then
  echo "ERROR: no email hashes captured from process response" >&2
  exit 1
fi
PERSISTED_EMAIL_HASH_SQL_LIST="$(awk '{printf "'\''%s'\'',", $0}' "$PERSISTED_EMAIL_HASHES_TXT" | sed 's/,$//')"
PERSISTED_EMAIL_HASHES="$(wc -l < "$PERSISTED_EMAIL_HASHES_TXT" | tr -d ' ')"
PERSISTED_EMAIL_HASHES="${PERSISTED_EMAIL_HASHES:-0}"
if [[ -z "$PERSISTED_EMAIL_HASH_SQL_LIST" ]]; then
  PERSISTED_EMAIL_HASH_SQL_LIST="NULL"
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                     PROCESS COMPLETED                            ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""
echo "  📧 Batch Summary:"
echo "  ─────────────────────────────────────────────────────────────────"
echo "  correlation_id:       $RESPONSE_CORRELATION_ID"
echo "  emails processed:     $TOTAL_PROCESSED / $EXPECTED_EMAILS"
echo "  unique email hashes: $UNIQUE_EMAIL_HASHES"
echo "  persisted:           $PERSISTED_EMAIL_HASHES"
echo "  fallbacks:          $FALLBACK_EMAIL_HASHES"

if [[ "$TOTAL_PROCESSED" -ne "$EXPECTED_EMAILS" ]]; then
  echo "ERROR: total_processed ($TOTAL_PROCESSED) does not match expected emails ($EXPECTED_EMAILS)" >&2
  exit 1
fi

echo "==> Sample redacted emails (PII-safe preview)"
REDACTED_SAMPLES_FILE="$WORK_DIR/redacted_samples.tsv"
docker compose exec -T postgres psql -U postgres -d aviva_claims -At -c \
"select email_hash, payload_json from audit_events
 where event_type='EMAIL_REDACTED'
   and email_hash in ($EMAIL_HASH_SQL_LIST)
 order by timestamp desc
 limit $SAMPLE_REDACTED_COUNT;" \
>"$REDACTED_SAMPLES_FILE"

python3 - "$REDACTED_SAMPLES_FILE" <<'PY'
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as f:
    rows = [line.strip() for line in f if line.strip()]
if not rows:
    print("No EMAIL_REDACTED samples found")
    sys.exit(0)

for idx, row in enumerate(rows, start=1):
    email_hash, payload_json = row.split("|", 1)
    payload = json.loads(payload_json)
    print(f"[Sample {idx}] email_hash={email_hash}")
    print(f"  redacted_subject: {payload.get('redacted_subject', '')}")
    print(f"  redacted_body_preview: {payload.get('redacted_body_preview', '')[:220]}")
    print(f"  pii_counts: {payload.get('pii_counts', {})}")
PY

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                        DIGEST SUMMARY                           ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

curl -fsS "$API_PREFIX/digest/$RESPONSE_CORRELATION_ID" >"$DIGEST_RESPONSE_JSON"
python3 - "$DIGEST_RESPONSE_JSON" <<'PY'
import json
import sys
with open(sys.argv[1], "r", encoding="utf-8") as f:
    d = json.load(f)

counts = d.get("summary_counts", {})
print("  📊 Classification Breakdown:")
print("  ─────────────────────────────────────────────────────────────────")
for k, v in counts.items():
    if v > 0:
        print(f"    {k:20s}: {v:3d}")
print("")

breakdown = d.get("priority_breakdown", {})
print("  🎯 Priority Breakdown:")
print("  ─────────────────────────────────────────────────────────────────")
priority_labels = {"p1_critical": "🔴 P1-Critical", "p2_high": "🟠 P2-High", "p3_medium": "🟡 P3-Medium", "p4_low": "🟢 P4-Low"}
for k, v in breakdown.items():
    label = priority_labels.get(k, k)
    print(f"    {label:20s}: {v:3d}")
print("")

top_prios = d.get("top_priorities", [])
print(f"  ⭐ Top Priorities ({len(top_prios)} emails):")
print("  ─────────────────────────────────────────────────────────────────")
for i, p in enumerate(top_prios, 1):
    print(f"    {i}. [{p.get('priority','')}] {p.get('classification','')} (actions: {p.get('action_count',0)})")
    print(f"       hash: {p.get('email_hash','')[:16]}...")
print("")

actionable = d.get("actionable_emails", [])
action_types = {}
for a in actionable:
    t = a.get("action_type", "unknown")
    action_types[t] = action_types.get(t, 0) + 1

print(f"  📋 Actionable Emails: {len(actionable)} total")
print("  ─────────────────────────────────────────────────────────────────")
for atype, count in sorted(action_types.items(), key=lambda x: -x[1]):
    print(f"    {atype:20s}: {count:3d}")
print("")

PY

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                      QUERY ENDPOINT CHECKS                      ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

Q1_STATUS="$(curl -sS -o "$QUERY_1_JSON" -w "%{http_code}" -X POST "$API_PREFIX/query" \
  -H "Content-Type: application/json" \
  -d '{"question":"What are the highest priority items right now?","top_k":5}')"

Q2_STATUS="$(curl -sS -o "$QUERY_2_JSON" -w "%{http_code}" -X POST "$API_PREFIX/query" \
  -H "Content-Type: application/json" \
  -d '{"question":"Which emails need a callback or escalation?","top_k":6}')"

Q3_STATUS="$(curl -sS -o "$QUERY_3_JSON" -w "%{http_code}" -X POST "$API_PREFIX/query" \
  -H "Content-Type: application/json" \
  -d '{"question":"Summarise the main claim themes in this batch.","top_k":6}')"

python3 - "$QUERY_1_JSON" "$QUERY_2_JSON" "$QUERY_3_JSON" "$Q1_STATUS" "$Q2_STATUS" "$Q3_STATUS" <<'PY'
import json
import sys

q_files = sys.argv[1:4]
q_statuses = [int(s) for s in sys.argv[4:7]]
ok_queries = 0
strong_queries = 0

for idx, (path, status) in enumerate(zip(q_files, q_statuses), start=1):
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    print(f"Query {idx}: http_status={status}")
    if status != 200:
        print(f"Query {idx} non-200 payload: {str(payload)[:220]}")
        continue

    ok_queries += 1
    retrieval_count = int(payload.get("retrieval_count") or 0)
    retrieval_weak = bool(payload.get("retrieval_weak"))
    citations = len(payload.get("citations", []))
    if retrieval_count > 0 and not retrieval_weak and citations > 0:
        strong_queries += 1
    print(
        f"Query {idx}: retrieval_count={retrieval_count}, retrieval_weak={retrieval_weak}, citations={citations}"
    )
    answer = (payload.get("answer") or "").strip().replace("\n", " ")
    print(f"Query {idx} answer preview: {answer[:220]}")

if ok_queries == 0:
    raise SystemExit("All query requests failed (no HTTP 200 responses)")
if strong_queries == 0:
    print("Warning: no strong grounded response (all successful responses were weak retrieval)")
PY

echo "==> Audit events sample (processed emails)"
AUDIT_SAMPLE_FILE="$WORK_DIR/audit_samples.tsv"
docker compose exec -T postgres psql -U postgres -d aviva_claims -At -F $'\t' -c \
"select
  to_char(timestamp, 'YYYY-MM-DD\"T\"HH24:MI:SSOF') as ts,
  event_type,
  stage,
  status,
  email_hash,
  left(replace(payload_json::text, E'\n', ' '), 180) as payload_preview
 from audit_events
 where email_hash in ($EMAIL_HASH_SQL_LIST)
   and timestamp >= '${RUN_STARTED_AT}'::timestamptz
 order by timestamp desc
 limit $SAMPLE_AUDIT_COUNT;" \
>"$AUDIT_SAMPLE_FILE"

python3 - "$AUDIT_SAMPLE_FILE" <<'PY'
import sys

with open(sys.argv[1], "r", encoding="utf-8") as f:
    rows = [line.rstrip("\n") for line in f if line.strip()]

if not rows:
    print("No audit events found for this run")
    raise SystemExit(0)

for idx, row in enumerate(rows, start=1):
    parts = row.split("\t")
    while len(parts) < 6:
        parts.append("")
    ts, event_type, stage, status, email_hash, payload_preview = parts[:6]
    print(f"[Audit {idx}] {ts} event={event_type} stage={stage} status={status} email_hash={email_hash}")
    print(f"  payload_preview: {payload_preview}")
PY

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                    DATABASE INTEGRITY CHECKS                     ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

DB_COUNTS_FILE="$WORK_DIR/db_counts.txt"
docker compose exec -T postgres psql -U postgres -d aviva_claims -At -c \
"select
  (select count(*) from email_decisions where email_hash in (${PERSISTED_EMAIL_HASH_SQL_LIST})) as decisions_count,
  (select count(*) from required_actions where email_hash in (${PERSISTED_EMAIL_HASH_SQL_LIST})) as actions_count,
  (select count(*) from audit_events where email_hash in (${PERSISTED_EMAIL_HASH_SQL_LIST}) and event_type='READ_MODELS_WRITTEN' and timestamp >= '${RUN_STARTED_AT}'::timestamptz) as persistence_events,
  (select count(*) from audit_events where email_hash in (${PERSISTED_EMAIL_HASH_SQL_LIST}) and event_type='ACTIONS_EXTRACTED' and timestamp >= '${RUN_STARTED_AT}'::timestamptz) as action_events;" \
>"$DB_COUNTS_FILE"

IFS='|' read -r DB_DECISIONS DB_ACTIONS DB_PERSIST DB_ACTION_EVENTS <"$DB_COUNTS_FILE"

echo "  💾 Database Records:"
echo "  ─────────────────────────────────────────────────────────────────"
echo "    email_decisions:     $DB_DECISIONS"
echo "    required_actions:    $DB_ACTIONS"
echo "    persistence events:  $DB_PERSIST"
echo "    action events:       $DB_ACTION_EVENTS"
echo ""

if [[ "$DB_DECISIONS" -lt "$PERSISTED_EMAIL_HASHES" ]]; then
  echo "ERROR: DB decisions_count ($DB_DECISIONS) is less than persisted email hashes ($PERSISTED_EMAIL_HASHES)" >&2
  exit 1
fi

if [[ "$DB_ACTIONS" -le 0 ]]; then
  echo "ERROR: No required_actions were created for this run" >&2
  exit 1
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                     ✅ LIVE DEMO PASSED                          ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""
echo "📁 Artifacts saved to: $WORK_DIR"
echo ""
