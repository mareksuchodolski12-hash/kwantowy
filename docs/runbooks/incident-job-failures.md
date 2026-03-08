# Runbook: Job Failure Triage

1. Inspect failed jobs from UI run details.
2. Check API/worker logs for shared correlation ID.
3. Verify provider availability (local simulator runtime or IBM credentials/backend).
4. Inspect retries metric `qcp_job_retries_total` and failure counter.
5. Re-submit with lower shots / longer timeout if failure is transient.
