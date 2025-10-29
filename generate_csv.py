#!/usr/bin/env python3
"""
Generate CSV report from merge queue statistics

Processes all JSON files in the stats/ directory and generates a CSV with:
- Date
- Time
- Number of PRs in queue
- Estimated time to clear queue (hours)
- CI runtime for top job (minutes)
"""

import os
import json
import csv
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict, Optional


def parse_timestamp(iso_timestamp: str) -> datetime:
    """Parse ISO timestamp to datetime object with timezone."""
    # Handle both formats: with and without timezone
    if iso_timestamp.endswith('Z'):
        return datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
    elif '+' in iso_timestamp or iso_timestamp.endswith(('00:00', '00')):
        return datetime.fromisoformat(iso_timestamp)
    else:
        # No timezone info, assume UTC
        return datetime.fromisoformat(iso_timestamp).replace(tzinfo=timezone.utc)


def calculate_ci_runtime(ci_started_at: Optional[str], current_time: datetime) -> Optional[float]:
    """Calculate CI runtime in minutes."""
    if not ci_started_at:
        return None

    started = parse_timestamp(ci_started_at)
    runtime_seconds = (current_time - started).total_seconds()

    # If negative, CI started after our measurement (shouldn't happen normally)
    # Return None instead of negative value
    if runtime_seconds < 0:
        return None

    return runtime_seconds / 60  # Convert to minutes


def calculate_queue_clear_time(entries: List[Dict]) -> Optional[float]:
    """
    Calculate estimated time to clear the queue in minutes.
    Uses the last PR's estimated_time_to_merge_seconds as the total time.
    """
    if not entries:
        return None

    # Get the last entry's estimated time (this should be the cumulative time)
    last_entry = entries[-1]
    estimated_seconds = last_entry.get("estimated_time_to_merge_seconds")

    if estimated_seconds is None:
        return None

    return estimated_seconds / 60  # Convert to minutes


def process_json_file(file_path: Path) -> Optional[Dict]:
    """Process a single JSON stats file and extract relevant data."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)

        timestamp = data.get("timestamp")
        if not timestamp:
            print(f"Warning: No timestamp in {file_path}")
            return None

        dt = parse_timestamp(timestamp)

        # Convert UTC to PST (UTC-8)
        pst_offset = timedelta(hours=-8)
        dt_pst = dt + pst_offset

        entries = data.get("entries", [])
        total_prs = data.get("total_prs", len(entries))

        # Calculate estimated time to clear queue
        clear_time_hours = calculate_queue_clear_time(entries)

        # Get top job (first entry) CI runtime
        ci_runtime_minutes = None
        if entries:
            top_entry = entries[0]
            ci_status = top_entry.get("ci_status", {})
            ci_started_at = ci_status.get("ci_started_at")

            if ci_started_at:
                ci_runtime_minutes = calculate_ci_runtime(ci_started_at, dt)

        return {
            "date_pst": dt_pst.strftime("%Y-%m-%d"),
            "time_pst": dt_pst.strftime("%H:%M:%S"),
            "num_prs": total_prs,
            "estimated_clear_time_minutes": clear_time_hours,
            "top_job_ci_runtime_minutes": ci_runtime_minutes
        }

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None


def generate_csv(stats_dir: str = "stats", output_file: str = "merge_queue_report.csv"):
    """Generate CSV report from all JSON files in stats directory."""
    stats_path = Path(stats_dir)

    if not stats_path.exists():
        print(f"Error: Stats directory '{stats_dir}' does not exist")
        return

    # Find all JSON files
    json_files = sorted(stats_path.glob("merge_queue_*.json"))

    if not json_files:
        print(f"No JSON files found in {stats_dir}")
        return

    print(f"Found {len(json_files)} JSON files")

    # Process all files
    rows = []
    for json_file in json_files:
        result = process_json_file(json_file)
        if result:
            rows.append(result)

    if not rows:
        print("No valid data extracted from JSON files")
        return

    # Write CSV
    fieldnames = [
        "date_pst",
        "time_pst",
        "num_prs",
        "estimated_clear_time_minutes",
        "top_job_ci_runtime_minutes"
    ]

    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Successfully generated {output_file} with {len(rows)} entries")

    # Print summary statistics
    if rows:
        avg_prs = sum(r["num_prs"] for r in rows) / len(rows)

        clear_times = [r["estimated_clear_time_minutes"] for r in rows if r["estimated_clear_time_minutes"] is not None]
        avg_clear_time = sum(clear_times) / len(clear_times) if clear_times else 0

        ci_runtimes = [r["top_job_ci_runtime_minutes"] for r in rows if r["top_job_ci_runtime_minutes"] is not None]
        avg_ci_runtime = sum(ci_runtimes) / len(ci_runtimes) if ci_runtimes else 0

        print(f"\nSummary Statistics:")
        print(f"  Average PRs in queue: {avg_prs:.1f}")
        print(f"  Average estimated clear time: {avg_clear_time:.1f} minutes")
        print(f"  Average top job CI runtime: {avg_ci_runtime:.1f} minutes")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate CSV report from merge queue statistics"
    )
    parser.add_argument(
        "-s", "--stats-dir",
        default="stats",
        help="Directory containing JSON stats files (default: stats)"
    )
    parser.add_argument(
        "-o", "--output",
        default="merge_queue_report.csv",
        help="Output CSV file name (default: merge_queue_report.csv)"
    )

    args = parser.parse_args()
    generate_csv(args.stats_dir, args.output)


if __name__ == "__main__":
    main()
