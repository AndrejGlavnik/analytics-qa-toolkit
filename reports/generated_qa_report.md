# Analytics QA Report

Input file: `dashboard_export.csv`

Summary: 7 finding(s), 4 high severity, 3 medium severity.

| Check | Severity | Rows | Finding | Next action |
|---|---:|---:|---|---|
| missing_dates | high | 1 | Missing reporting dates: 2026-04-04 | Confirm whether the source export skipped days or the dashboard should use a different date range. |
| null_kpis | high | 1 | Required KPI 'orders' has 1 null value(s). | Check source export completeness and confirm whether null should be converted to zero. |
| duplicate_rows | high | 2 | 2 rows duplicate the expected reporting grain. | Review export grain and remove or aggregate duplicate records before dashboard refresh. |
| abnormal_spikes | medium | 1 | KPI 'sessions' has 1 day(s) above 2.5x the previous day. | Check whether the spike is real demand, duplicate data, a grain change or a source-system export issue. |
| mapping_validation | high | 1 | 1 row(s) use country/brand combinations missing from the approved mapping. | Update the mapping table or correct the source labels before reporting. |
| source_naming | medium | 1 | 1 row(s) contain source values outside the approved taxonomy. | Normalize source names before dashboard ingestion. |
| campaign_naming | medium | 1 | 1 row(s) do not match the campaign naming pattern. | Confirm campaign taxonomy with media owners and update naming rules if needed. |

## Why this matters

These checks help separate source data issues, mapping issues, naming issues and dashboard logic questions before stakeholders rely on the report.
