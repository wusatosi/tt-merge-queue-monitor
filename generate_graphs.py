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


def plot_prs_by_hour_individual(df: pd.DataFrame, output_file: str, time_period: str):
    """Generate bar chart showing individual data points for each hour (for short time periods)."""
    # Extract date and hour
    df['date'] = df['datetime_pst'].dt.date
    df['hour'] = df['datetime_pst'].dt.hour
    df['day_of_week'] = df['datetime_pst'].dt.dayofweek

    # Filter for workdays only (Monday-Friday) and work hours (6AM-11PM)
    df = df[(df['day_of_week'] < 5) & (df['hour'] >= 6) & (df['hour'] <= 23)].copy()

    hours = range(6, 24)
    fig, ax = plt.subplots(figsize=(16, 6))

    # Get unique dates
    dates = sorted(df['date'].unique())
    num_dates = len(dates)
    bar_width = 0.8 / max(num_dates, 1)

    # Use different colors for different dates
    colors = plt.cm.Set3(range(num_dates))

    for date_idx, date in enumerate(dates):
        hour_values = []
        for hour in hours:
            value = df[(df['hour'] == hour) & (df['date'] == date)]['num_prs'].values
            hour_values.append(value[0] if len(value) > 0 else 0)

        positions = [h + (date_idx - num_dates/2 + 0.5) * bar_width for h in hours]
        ax.bar(positions, hour_values, bar_width, label=str(date), color=colors[date_idx], alpha=0.8)

        # Add value labels
        for pos, val in zip(positions, hour_values):
            if val > 0:
                ax.text(pos, val, f'{int(val)}', ha='center', va='bottom', fontsize=8, fontweight='bold')

    # Labels and title
    ax.set_xlabel('Hour of Day (PST)', fontsize=12)
    ax.set_ylabel('Number of PRs', fontsize=12)
    title = f'PRs by Hour of Day ({time_period})'
    ax.set_title(title, fontsize=14, fontweight='bold')

    # Set x-axis ticks
    ax.set_xticks(hours)
    ax.set_xticklabels([f'{h:02d}:00' for h in hours], rotation=45, ha='right')

    # Grid and legend
    ax.grid(True, alpha=0.3, axis='y')
    ax.legend(loc='upper right', fontsize=10)

    # Adjust layout
    plt.tight_layout()

    # Save figure
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"Saved graph to: {output_file}")

    plt.close()


def plot_prs_by_hour_of_day(df: pd.DataFrame, output_file: str = "prs_by_hour.png", time_period: str = "all"):
    """Generate grouped bar chart showing Max, Median, and Min PRs for each hour.

    Args:
        df: DataFrame with stats data
        output_file: Output filename
        time_period: Time period label for the graph title
    """
    # Extract date and hour
    df['date'] = df['datetime_pst'].dt.date
    df['hour'] = df['datetime_pst'].dt.hour
    df['day_of_week'] = df['datetime_pst'].dt.dayofweek  # Monday=0, Sunday=6

    # Filter for workdays only (Monday-Friday) and work hours (6AM-11PM)
    df = df[(df['day_of_week'] < 5) & (df['hour'] >= 6) & (df['hour'] <= 23)].copy()

    hours = range(6, 24)  # 6AM to 11PM

    # Calculate max, median, min for each hour
    hour_stats = {}
    for hour in hours:
        hour_data = df[df['hour'] == hour]['num_prs'].values
        if len(hour_data) > 0:
            hour_stats[hour] = {
                'max': float(hour_data.max()),
                'median': float(pd.Series(hour_data).median()),
                'min': float(hour_data.min())
            }
        else:
            hour_stats[hour] = {'max': 0, 'median': 0, 'min': 0}

    fig, ax = plt.subplots(figsize=(16, 6))

    # Bar width and positions for grouped bars
    bar_width = 0.25
    positions_max = [h - bar_width for h in hours]
    positions_median = [h for h in hours]
    positions_min = [h + bar_width for h in hours]

    # Extract values
    max_values = [hour_stats[h]['max'] for h in hours]
    median_values = [hour_stats[h]['median'] for h in hours]
    min_values = [hour_stats[h]['min'] for h in hours]

    # Plot grouped bars
    ax.bar(positions_max, max_values, bar_width, label='Max', color='crimson', alpha=0.8)
    ax.bar(positions_median, median_values, bar_width, label='Median', color='steelblue', alpha=0.8)
    ax.bar(positions_min, min_values, bar_width, label='Min', color='seagreen', alpha=0.8)

    # Add value labels on bars
    for i, hour in enumerate(hours):
        # Label max
        if max_values[i] > 0:
            ax.text(positions_max[i], max_values[i], f'{int(max_values[i])}',
                   ha='center', va='bottom', fontsize=8, fontweight='bold')
        # Label median
        if median_values[i] > 0:
            ax.text(positions_median[i], median_values[i], f'{median_values[i]:.1f}',
                   ha='center', va='bottom', fontsize=8, fontweight='bold')
        # Label min
        if min_values[i] > 0:
            ax.text(positions_min[i], min_values[i], f'{int(min_values[i])}',
                   ha='center', va='bottom', fontsize=8, fontweight='bold')

    # Labels and title
    ax.set_xlabel('Hour of Day (PST)', fontsize=12)
    ax.set_ylabel('Number of PRs', fontsize=12)
    title = f'Average PRs by Hour of Day ({time_period})'
    ax.set_title(title, fontsize=14, fontweight='bold')

    # Set x-axis ticks
    ax.set_xticks(hours)
    ax.set_xticklabels([f'{h:02d}:00' for h in hours], rotation=45, ha='right')

    # Grid and legend
    ax.grid(True, alpha=0.3, axis='y')
    ax.legend(loc='upper right', fontsize=10)

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

    # Get the most recent date in the dataset
    max_date = df['datetime_pst'].max()

    # Define time periods
    time_periods = {
        'last_day': (max_date - pd.Timedelta(days=1), 'Last Day'),
        'last_week': (max_date - pd.Timedelta(weeks=1), 'Last Week'),
        'last_month': (max_date - pd.Timedelta(days=30), 'Last Month'),
        'all': (df['datetime_pst'].min(), 'All Time')
    }

    # Generate graphs for each time period
    for period_key, (start_date, period_label) in time_periods.items():
        df_filtered = df[df['datetime_pst'] >= start_date].copy()

        if len(df_filtered) == 0:
            print(f"Warning: No data for {period_label}, skipping...")
            continue

        output_file = str(output_path / f"prs_by_hour_{period_key}.png")

        # For "Last Day", show individual data points instead of max/median/min
        if period_key == 'last_day':
            plot_prs_by_hour_individual(df_filtered, output_file, period_label)
        else:
            plot_prs_by_hour_of_day(df_filtered, output_file, period_label)

    # Optionally generate other graphs (commented out by default)
    # plot_prs_over_time(df, str(output_path / "prs_over_time.png"))
    # plot_estimated_clear_time(df, str(output_path / "clear_time_over_time.png"))
    # plot_ci_runtime(df, str(output_path / "ci_runtime_over_time.png"))

    print("\nGraphs generated successfully!")


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
