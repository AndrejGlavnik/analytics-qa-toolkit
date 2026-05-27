from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from analytics_qa_toolkit.qa import load_config, load_table, render_markdown, run_checks


def main() -> None:
    parser = argparse.ArgumentParser(description="Run analytics QA checks on a dashboard export.")
    parser.add_argument("--input", required=True, help="CSV or Excel dashboard export.")
    parser.add_argument("--mapping", required=True, help="CSV mapping reference.")
    parser.add_argument("--config", default="config/qa_config.json", help="QA config JSON.")
    parser.add_argument("--out", default="reports/qa_report.md", help="Markdown output path.")
    args = parser.parse_args()

    df = load_table(args.input)
    mapping_df = load_table(args.mapping)
    config = load_config(args.config)
    findings = run_checks(df, mapping_df, config)
    report = render_markdown(findings, Path(args.input).name)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")
    print(f"Wrote {out} with {len(findings)} finding(s).")


if __name__ == "__main__":
    main()
