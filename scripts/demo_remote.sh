#!/usr/bin/env bash
set -euo pipefail

if [[ "${QCP_IBM_RUNTIME_ENABLED:-false}" != "true" || -z "${QCP_IBM_RUNTIME_TOKEN:-}" ]]; then
  echo "Skipping remote demo: IBM Runtime not configured (set QCP_IBM_RUNTIME_ENABLED=true and QCP_IBM_RUNTIME_TOKEN)."
  exit 0
fi

API_URL="${API_URL:-http://localhost:8000}"

payload='{
  "name": "demo-remote",
  "description": "ibm runtime demo",
  "provider": "ibm_runtime",
  "circuit": {
    "qasm": "OPENQASM 2.0; include \"qelib1.inc\"; qreg q[1]; creg c[1]; h q[0]; measure q[0] -> c[0];",
    "shots": 64
  },
  "retry_policy": {"max_attempts": 2, "timeout_seconds": 180}
}'

echo "Submitting IBM Runtime job..."
submit_response="$(curl -sS -X POST "$API_URL/v1/jobs" -H 'Content-Type: application/json' -d "$payload")"
job_id="$(python -c 'import json,sys; print(json.loads(sys.stdin.read())["job"]["id"])' <<<"$submit_response")"

for _ in {1..60}; do
  job_json="$(curl -sS "$API_URL/v1/jobs/$job_id")"
  status="$(python -c 'import json,sys; print(json.loads(sys.stdin.read())["status"])' <<<"$job_json")"
  echo "status=$status"
  if [[ "$status" == "succeeded" || "$status" == "failed" ]]; then
    break
  fi
  sleep 5
done

curl -sS "$API_URL/v1/jobs/$job_id/result" | python -m json.tool || true
curl -sS "$API_URL/v1/comparison" | python -m json.tool
