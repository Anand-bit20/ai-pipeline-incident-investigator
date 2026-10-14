# Runbook: Required Column Missing

Runbook ID: RB-001
Version: 1.0
Source type: Project-authored troubleshooting guide
Applicable error: SCHEMA_MISSING_COLUMN

## Symptoms

Input schema validation reports that one or more required columns
are absent. The pipeline may stop before transformation and loading.

## Evidence to inspect

- Required columns and observed columns recorded in the incident log.
- The header of the exact input file used by the failed run.
- Extraction code and field mappings.
- The upstream schema and recent changes to it.

## Possible causes

These are hypotheses until supported by additional evidence:

- The extraction code omitted a required field.
- An upstream field was renamed or removed.
- The pipeline read an unexpected input file.
- A delimiter, encoding, or header-parsing issue changed column names.
- Leading or trailing whitespace caused a column-name mismatch.

## Troubleshooting steps

1. Compare the logged required columns with the observed columns.
2. Inspect the header of the exact input file referenced in the log.
3. Check column names for whitespace, spelling, and case differences.
4. Compare extraction mappings with the expected input schema.
5. Check upstream schema changes and confirm the correct file was read.

## Recovery

- If extraction omitted the field, correct the mapping and regenerate
  the input from its original source.
- If a field was renamed, confirm that its meaning is equivalent
  before updating the mapping.
- If parsing caused the mismatch, correct the parser configuration.
- If the wrong file was read, correct the input selection.

Do not fabricate trip_id values or silently remove the validation rule.
If the upstream source cannot supply a required field, review the
schema contract before changing the pipeline.

## Verification

1. Run schema validation again and confirm all required columns exist.
2. Check that trip_id values meet the pipeline's documented value rules.
3. Confirm transformation and loading complete successfully.
4. Confirm the expected output was written for the new run.

## Limits

This runbook describes possible causes and recommended checks.
It does not establish the root cause of any specific incident.
Use incident evidence to support conclusions.