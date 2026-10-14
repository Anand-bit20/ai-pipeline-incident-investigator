# Runbook: API Request Timeout

Runbook ID: RB-002
Version: 1.0
Source type: Project-authored troubleshooting guide
Applicable error: API_REQUEST_TIMEOUT

## Symptoms

An extraction request exceeds its configured timeout before receiving
a response. Repeated timeouts may exhaust the configured attempts.

## Evidence to inspect

- The endpoint, timeout setting, attempt count, and timestamps.
- Whether any HTTP status or response body was received.
- Request parameters and expected response size.
- Connectivity diagnostics from the pipeline execution environment.
- Proxy configuration and relevant connection logs.
- Upstream service health information for the incident time.

## Possible causes

These are hypotheses until supported by additional evidence:

- The upstream service responded too slowly or was unavailable.
- A network or proxy issue prevented a timely response.
- The request required more processing time than the configured timeout.
- The request parameters produced an unexpectedly expensive operation.

A timeout alone does not establish any of these causes.

## Troubleshooting steps

1. Confirm the endpoint, configured timeout, and number of attempts.
2. Check whether the client received an HTTP status or response body.
3. Check connectivity and proxy diagnostics from the execution environment.
4. Review upstream service health information for the incident time.
5. Compare the failed request with a previously successful request.
6. Inspect request parameters and expected response size.

## Recovery

- Correct connectivity or proxy configuration if diagnostics identify an issue.
- If the upstream service was unavailable, retry after recovery is confirmed.
- If the request is too expensive, consider supported pagination or filtering.
- Adjust the timeout only when measured response times justify the change.
- Use bounded retries with backoff; avoid retrying indefinitely.
- Before rerunning, check whether partial outputs exist and whether
  repeated processing could create duplicates.

## Verification

1. Confirm that a subsequent request returns a usable response.
2. Confirm that response validation and downstream stages complete.
3. Confirm that the expected output was written.
4. Check for duplicate or partial outputs after the rerun.

## Limits

Timeouts describe an observed failure, not a confirmed underlying cause.
Do not infer rate limiting without HTTP status or other supporting evidence.
Do not infer an empty API dataset when no response body was received.
This runbook does not establish what caused a specific incident.