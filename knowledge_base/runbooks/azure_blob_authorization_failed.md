# Runbook: Azure Blob Upload Authorization Failure

Runbook ID: RB-003
Version: 1.0
Source type: Project-authored guide informed by Microsoft documentation
Applicable error: AZURE_BLOB_AUTHORIZATION_FAILED
Reference: https://learn.microsoft.com/en-us/troubleshoot/azure/azure-storage/blobs/authentication/storage-troubleshoot-403-errors

## Symptoms

A blob upload is rejected with HTTP 403.
AuthorizationPermissionMismatch indicates insufficient permission
for the requested operation.

## Evidence to inspect

- HTTP status and the specific Azure Storage error code.
- Requested operation, storage account, container, and blob.
- Authentication method used by the running process.
- Effective identity and relevant role assignments if using Entra ID.
- SAS permissions and resource scope if using a SAS token.
- Storage diagnostic records for the failed request.

## Possible causes

These are hypotheses until supported by evidence:

- The SAS lacks permissions required by the operation.
- The identity lacks a suitable blob data role.
- A role assignment or credential targets the wrong resource scope.
- The process is using a different identity than expected.

## Troubleshooting steps

1. Confirm HTTP status, storage error code, and requested operation.
2. Identify the authentication method actually used by the process.
3. For SAS authentication, inspect permitted operations and resource scope.
4. For Entra ID, inspect the effective identity's blob data roles and scope.
5. Compare the configured destination with the intended resource.
6. Review storage diagnostics to establish the configuration issue.

## Recovery

- Correct only the permission or scope issue identified by evidence.
- Have the appropriate resource owner apply required access changes.
- Check for existing outputs before rerunning the upload.
- Avoid logging credential values or granting unnecessary access.

## Verification

1. Confirm the upload succeeds after the identified issue is corrected.
2. Verify the expected blob and its contents.
3. Check for unintended duplicate or partial outputs.
4. Confirm the pipeline completes successfully.

## Limits

A permission rejection does not identify the exact misconfiguration.
Do not assume the process uses SAS or Entra ID without evidence.
No output from this request does not prove that the container is empty.
This guide does not establish the underlying cause of a specific incident.