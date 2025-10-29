#!/usr/bin/env python3
"""
Generate graphs from merge queue statistics

Creates visualizations including:
- Bar chart of number of PRs across time of day (PST)
- Other potential graphs (estimated clear time, CI runtime, etc.)
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import argparse
from pathlib import Path


def load_csv_data(csv_file: str) -> pd.DataFrame:
    """Load CSV data into pandas DataFrame."""
    df = pd.read_csv(csv_file)

    # Combine date_pst and time_pst into a datetime column
    df['datetime_pst'] = pd.to_datetime(df['date_pst'] + ' ' + df['time_pst'])

    return df


def plot_prs_over_time(df: pd.DataFrame, output_file: str = "prs_over_time.png"):
    """Generate bar chart of number of PRs over time."""
    fig, ax = plt.subplots(figsize=(14, 6))

    # Create bar chart
    ax.bar(df['datetime_pst'], df['num_prs'], width=0.02, color='steelblue', alpha=0.7)

    # Format x-axis to show date and time
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M', tz=None))
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=3))
    plt.xticks(rotation=45, ha='right')

    # Labels and title
    ax.set_xlabel('Time (PST)', fontsize=12)
    ax.set_ylabel('Number of PRs in Queue', fontsize=12)
    ax.set_title('Merge Queue Size Over Time', fontsize=14, fontweight='bold')

    # Grid for better readability
    ax.grid(True, alpha=0.3, axis='y')

    # Adjust layout to prevent label cutoff
    plt.tight_layout()

    # Save figure
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"Saved graph to: {output_file}")

    plt.close()


def plot_prs_by_hour_of_day(df: pd.DataFrame, output_file: str = "prs_by_hour.png"):
    """Generate grouped bar chart showing number of PRs by hour for each day."""
    # Extract date and hour
    df['date'] = df['datetime_pst'].dt.date
    df['hour'] = df['datetime_pst'].dt.hour

    # Get unique dates
    dates = sorted(df['date'].unique())
    hours = range(24)

    fig, ax = plt.subplots(figsize=(16, 6))

    # Calculate bar width and positions
    num_days = len(dates)
    bar_width = 0.8 / num_days if num_days > 0 else 0.8

    # Prepare data: for each hour, get values for each day
    hour_data = {}
    for hour in hours:
        hour_data[hour] = []
        for date in dates:
            value = df[(df['hour'] == hour) & (df['date'] == date)]['num_prs'].values
            if len(value) > 0:
                hour_data[hour].append(value[0])
            else:
                hour_data[hour].append(0)

    # Plot grouped bars with single color
    for day_idx, date in enumerate(dates):
        positions = [h + (day_idx - num_days/2 + 0.5) * bar_width for h in hours]
        values = [hour_data[h][day_idx] for h in hours]

        bars = ax.bar(positions, values, bar_width,
                     label=f'{date}', color='coral', alpha=0.7)

        # For each hour group, add label only on median bar
        for hour in hours:
            if hour_data[hour]:
                # Get all values for this hour
                hour_values = hour_data[hour]
                # Find median value
                sorted_vals = sorted(hour_values)
                median_val = sorted_vals[len(sorted_vals) // 2]

                # Check if this day's value is the median
                if values[hour] == median_val and values[hour] > 0:
                    ax.text(positions[hour], values[hour],
                           f'{int(values[hour])}',
                           ha='center', va='bottom', fontsize=8, fontweight='bold')

    # Labels and title
    ax.set_xlabel('Hour of Day (PST)', fontsize=12)
    ax.set_ylabel('Number of PRs', fontsize=12)
    ax.set_title('Merge Queue Size by Hour of Day (Grouped by Date)', fontsize=14, fontweight='bold')

    # Set x-axis ticks
    ax.set_xticks(hours)
    ax.set_xticklabels([f'{h:02d}:00' for h in hours], rotation=45, ha='right')

    # Grid and legend
    ax.grid(True, alpha=0.3, axis='y')
    ax.legend(loc='upper right', fontsize=8, ncol=min(num_days, 5))

    # Adjust layout
    plt.tight_layout()

    # Save figure
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"Saved graph to: {output_file}")

    plt.close()


def plot_estimated_clear_time(df: pd.DataFrame, output_file: str = "clear_time_over_time.png"):
    """Generate line chart of estimated clear time over time."""
    # Filter out rows with missing clear time data
    df_filtered = df[df['estimated_clear_time_minutes'].notna()].copy()

    if df_filtered.empty:
        print("No data available for estimated clear time graph")
        return

    fig, ax = plt.subplots(figsize=(14, 6))

    # Create line chart with markers
    ax.plot(df_filtered['datetime_pst'], df_filtered['estimated_clear_time_minutes'],
            marker='o', linestyle='-', linewidth=1.5, markersize=4,
            color='darkgreen', alpha=0.7)

    # Format x-axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M', tz=None))
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=3))
    plt.xticks(rotation=45, ha='right')

    # Labels and title
    ax.set_xlabel('Time (PST)', fontsize=12)
    ax.set_ylabel('Estimated Clear Time (minutes)', fontsize=12)
    ax.set_title('Estimated Time to Clear Queue Over Time', fontsize=14, fontweight='bold')

    # Grid
    ax.grid(True, alpha=0.3)

    # Adjust layout
    plt.tight_layout()

    # Save figure
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"Saved graph to: {output_file}")

    plt.close()


def plot_ci_runtime(df: pd.DataFrame, output_file: str = "ci_runtime_over_time.png"):
    """Generate line chart of CI runtime for top job over time."""
    # Filter out rows with missing CI runtime data
    df_filtered = df[df['top_job_ci_runtime_minutes'].notna()].copy()

    if df_filtered.empty:
        print("No data available for CI runtime graph")
        return

    fig, ax = plt.subplots(figsize=(14, 6))

    # Create line chart with markers
    ax.plot(df_filtered['datetime_pst'], df_filtered['top_job_ci_runtime_minutes'],
            marker='o', linestyle='-', linewidth=1.5, markersize=4,
            color='purple', alpha=0.7)

    # Format x-axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M', tz=None))
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=3))
    plt.xticks(rotation=45, ha='right')

    # Labels and title
    ax.set_xlabel('Time (PST)', fontsize=12)
    ax.set_ylabel('CI Runtime (minutes)', fontsize=12)
    ax.set_title('Top Job CI Runtime Over Time', fontsize=14, fontweight='bold')

    # Grid
    ax.grid(True, alpha=0.3)

    # Adjust layout
    plt.tight_layout()

    # Save figure
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"Saved graph to: {output_file}")

    plt.close()


def generate_all_graphs(csv_file: str, output_dir: str = "."):
    """Generate graphs from CSV data."""
    print(f"Loading data from {csv_file}...")
    df = load_csv_data(csv_file)

    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    print(f"Generating graphs in {output_dir}...")

    # Generate PRs by hour of day graph
    plot_prs_by_hour_of_day(df, str(output_path / "prs_by_hour.png"))

    # Optionally generate other graphs (commented out by default)
    # plot_prs_over_time(df, str(output_path / "prs_over_time.png"))
    # plot_estimated_clear_time(df, str(output_path / "clear_time_over_time.png"))
    # plot_ci_runtime(df, str(output_path / "ci_runtime_over_time.png"))

    print("\nGraph generated successfully!")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate graphs from merge queue statistics CSV"
    )
    parser.add_argument(
        "-i", "--input",
        default="merge_queue_report.csv",
        help="Input CSV file (default: merge_queue_report.csv)"
    )
    parser.add_argument(
        "-o", "--output-dir",
        default=".",
        help="Output directory for graphs (default: current directory)"
    )

    args = parser.parse_args()

    generate_all_graphs(args.input, args.output_dir)


if __name__ == "__main__":
    main()
