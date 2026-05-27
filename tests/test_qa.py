import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from analytics_qa_toolkit.qa import run_checks


def test_run_checks_flags_expected_sample_issues():
    df = pd.read_csv(ROOT / "sample_data" / "dashboard_export.csv")
    mapping = pd.read_csv(ROOT / "sample_data" / "mapping_reference.csv")
    config = {
        "date_column": "date",
        "grain_columns": ["date", "country", "brand", "source", "campaign"],
        "required_kpis": ["sessions", "orders", "revenue"],
        "spike_threshold_ratio": 2.5,
        "expected_source_values": ["google_ads", "meta_ads", "retailer_sales", "ga4"],
        "mapping_key_columns": ["country", "brand"],
    }
    checks = {finding.check for finding in run_checks(df, mapping, config)}
    assert "missing_dates" in checks
    assert "duplicate_rows" in checks
    assert "null_kpis" in checks
    assert "mapping_validation" in checks
    assert "source_naming" in checks
