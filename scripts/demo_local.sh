#!/usr/bin/env bash
set -euo pipefail

API_URL="${API_URL:-http://localhost:8000}"

payload='{
  "name": "demo-local",
  "description": "deterministic local demo",
  "provider": "local_simulator",
  "circuit": {
    "qasm": "OPENQASM 2.0; include \"qelib1.inc\"; qreg q[1]; creg c[1]; h q[0]; measure q[0] -> c[0];",
    "shots": 64
  },
  "retry_policy": {"max_attempts": 2, "timeout_seconds": 60}
}'

echo "Submitting local job..."
submit_response="$(curl -sS -X POST "$API_URL/v1/jobs" -H 'Content-Type: application/json' -d "$payload")"
job_id="$(python -c 'import json,sys; print(json.loads(sys.stdin.read())["job"]["id"])' <<<"$submit_response")"
echo "job_id=$job_id"

for _ in {1..20}; do
  job_json="$(curl -sS "$API_URL/v1/jobs/$job_id")"
  status="$(python -c 'import json,sys; print(json.loads(sys.stdin.read())["status"])' <<<"$job_json")"
  echo "status=$status"
  if [[ "$status" == "succeeded" || "$status" == "failed" ]]; then
    break
  fi
  sleep 1
done

result_json="$(curl -sS "$API_URL/v1/jobs/$job_id/result")"
echo "$result_json" | python -m json.tool

echo "Comparison summary:"
curl -sS "$API_URL/v1/comparison" | python -m json.tool
