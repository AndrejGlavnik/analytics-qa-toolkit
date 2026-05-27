from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass
class Finding:
    check: str
    severity: str
    message: str
    rows: int
    next_action: str


def load_table(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    return pd.read_csv(path)


def load_config(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _missing_dates(df: pd.DataFrame, date_column: str) -> Finding | None:
    dates = pd.to_datetime(df[date_column], errors="coerce")
    expected = pd.date_range(dates.min(), dates.max(), freq="D")
    missing = expected.difference(pd.DatetimeIndex(dates.dropna().unique()))
    if missing.empty:
        return None
    return Finding(
        "missing_dates",
        "high",
        "Missing reporting dates: " + ", ".join(d.strftime("%Y-%m-%d") for d in missing),
        len(missing),
        "Confirm whether the source export skipped days or the dashboard should use a different date range.",
    )


def _null_kpis(df: pd.DataFrame, required_kpis: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    for column in required_kpis:
        null_count = int(df[column].isna().sum())
        if null_count:
            findings.append(
                Finding(
                    "null_kpis",
                    "high",
                    f"Required KPI '{column}' has {null_count} null value(s).",
                    null_count,
                    "Check source export completeness and confirm whether null should be converted to zero.",
                )
            )
    return findings


def _duplicates(df: pd.DataFrame, grain_columns: list[str]) -> Finding | None:
    duplicate_mask = df.duplicated(subset=grain_columns, keep=False)
    duplicate_count = int(duplicate_mask.sum())
    if not duplicate_count:
        return None
    return Finding(
        "duplicate_rows",
        "high",
        f"{duplicate_count} rows duplicate the expected reporting grain.",
        duplicate_count,
        "Review export grain and remove or aggregate duplicate records before dashboard refresh.",
    )


def _spikes(df: pd.DataFrame, date_column: str, kpi_columns: list[str], threshold: float) -> list[Finding]:
    findings: list[Finding] = []
    ordered = df.copy()
    ordered[date_column] = pd.to_datetime(ordered[date_column], errors="coerce")
    daily = ordered.groupby(date_column)[kpi_columns].sum(numeric_only=True).sort_index()
    for column in kpi_columns:
        prior = daily[column].shift(1)
        ratio = daily[column] / prior.replace({0: pd.NA})
        flagged = ratio[ratio >= threshold]
        if not flagged.empty:
            findings.append(
                Finding(
                    "abnormal_spikes",
                    "medium",
                    f"KPI '{column}' has {len(flagged)} day(s) above {threshold:.1f}x the previous day.",
                    len(flagged),
                    "Check whether the spike is real demand, duplicate data, a grain change or a source-system export issue.",
                )
            )
    return findings


def _mapping_issues(df: pd.DataFrame, mapping_df: pd.DataFrame, key_columns: list[str]) -> Finding | None:
    approved = mapping_df[key_columns].drop_duplicates()
    merged = df.merge(approved.assign(_approved=True), on=key_columns, how="left")
    invalid_count = int(merged["_approved"].isna().sum())
    if not invalid_count:
        return None
    return Finding(
        "mapping_validation",
        "high",
        f"{invalid_count} row(s) use country/brand combinations missing from the approved mapping.",
        invalid_count,
        "Update the mapping table or correct the source labels before reporting.",
    )


def _naming_issues(df: pd.DataFrame, expected_sources: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    invalid_source_count = int((~df["source"].isin(expected_sources)).sum())
    if invalid_source_count:
        findings.append(
            Finding(
                "source_naming",
                "medium",
                f"{invalid_source_count} row(s) contain source values outside the approved taxonomy.",
                invalid_source_count,
                "Normalize source names before dashboard ingestion.",
            )
        )
    campaign_pattern = r"^[A-Z]{2}_[A-Z0-9]+_[A-Z0-9_]+$"
    invalid_campaigns = int((~df["campaign"].astype(str).str.match(campaign_pattern)).sum())
    if invalid_campaigns:
        findings.append(
            Finding(
                "campaign_naming",
                "medium",
                f"{invalid_campaigns} row(s) do not match the campaign naming pattern.",
                invalid_campaigns,
                "Confirm campaign taxonomy with media owners and update naming rules if needed.",
            )
        )
    return findings


def run_checks(df: pd.DataFrame, mapping_df: pd.DataFrame, config: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    missing = _missing_dates(df, config["date_column"])
    if missing:
        findings.append(missing)
    findings.extend(_null_kpis(df, config["required_kpis"]))
    duplicate = _duplicates(df, config["grain_columns"])
    if duplicate:
        findings.append(duplicate)
    findings.extend(_spikes(df, config["date_column"], config["required_kpis"], config["spike_threshold_ratio"]))
    mapping = _mapping_issues(df, mapping_df, config["mapping_key_columns"])
    if mapping:
        findings.append(mapping)
    findings.extend(_naming_issues(df, config["expected_source_values"]))
    return findings


def render_markdown(findings: list[Finding], input_name: str) -> str:
    high = sum(1 for finding in findings if finding.severity == "high")
    medium = sum(1 for finding in findings if finding.severity == "medium")
    lines = [
        "# Analytics QA Report",
        "",
        f"Input file: `{input_name}`",
        "",
        f"Summary: {len(findings)} finding(s), {high} high severity, {medium} medium severity.",
        "",
        "| Check | Severity | Rows | Finding | Next action |",
        "|---|---:|---:|---|---|",
    ]
    for finding in findings:
        lines.append(
            f"| {finding.check} | {finding.severity} | {finding.rows} | {finding.message} | {finding.next_action} |"
        )
    lines.extend(
        [
            "",
            "## Why this matters",
            "",
            "These checks help separate source data issues, mapping issues, naming issues and dashboard logic questions before stakeholders rely on the report.",
        ]
    )
    return "\n".join(lines) + "\n"
