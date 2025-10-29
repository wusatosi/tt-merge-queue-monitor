# GitHub Merge Queue Monitor

Monitor the merge queue status for `tenstorrent/tt-metal` repository using the GitHub GraphQL API.

## Features

- Track number of PRs in the merge queue
- Display PR titles, numbers, and authors
- Show time each PR has been in the queue
- Display queue position for each PR
- Show CI status (overall state and individual check runs)
- Estimated time to merge
- Export data to JSON format

## Setup

1. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up GitHub token (required):
```bash
export GITHUB_TOKEN=$(gh auth token)
```

## Usage

### Display merge queue status (console output)
```bash
python merge_queue_monitor.py
```

### Export to JSON file
```bash
python merge_queue_monitor.py -o merge_queue_status.json
```

### Monitor a different branch
```bash
python merge_queue_monitor.py -b dev
```

### Help
```bash
python merge_queue_monitor.py --help
```

## Command Line Options

- `-o, --output FILE` - Export merge queue data to a JSON file
- `-b, --branch BRANCH` - Branch name to monitor (default: main)
- `-h, --help` - Show help message

## JSON Output Format

The JSON export includes:
```json
{
  "timestamp": "2025-10-28T13:33:22.242282",
  "repository": "tenstorrent/tt-metal",
  "branch": "main",
  "total_prs": 23,
  "entries": [
    {
      "position": 1,
      "state": "AWAITING_CHECKS",
      "pr_number": 30533,
      "pr_title": "...",
      "pr_url": "...",
      "author": "...",
      "enqueued_at": "...",
      "time_in_queue": "6.3 hours",
      "estimated_time_to_merge_seconds": 3756,
      "commit": {
        "sha": "...",
        "url": "..."
      },
      "ci_status": {
        "overall_state": "FAILURE",
        "total_checks": 100,
        "running": 0,
        "completed": 100,
        "queued": 0,
        "checks": [...]
      }
    }
  ]
}
```

## Automated Statistics Collection

### One-time collection
Run the collection script once to save current merge queue status:
```bash
./collect_stats.sh
```

This will create a timestamped JSON file in the `stats/` directory, e.g., `stats/merge_queue_20251028_133802.json`

### Continuous monitoring
Run the monitor loop to collect statistics every 30 minutes:
```bash
./monitor_loop.sh
```

This will run indefinitely until stopped with Ctrl+C. Each run will:
1. Refresh the GitHub token
2. Collect current merge queue status
3. Save to a timestamped file in `stats/`
4. Wait 30 minutes before repeating

### Running in background
To run the monitor in the background:
```bash
nohup ./monitor_loop.sh > monitor.log 2>&1 &
```

To stop the background process:
```bash
# Find the process ID
ps aux | grep monitor_loop.sh

# Kill the process
kill <PID>
```

## CSV Report Generation

Generate a CSV report from all collected statistics:

```bash
python generate_csv.py
```

This will create `merge_queue_report.csv` with the following columns:
- **date**: Date of collection
- **time**: Time of collection
- **num_prs**: Number of PRs in queue
- **estimated_clear_time_hours**: Estimated time to clear entire queue (hours)
- **top_job_ci_runtime_minutes**: CI runtime for the top job in queue (minutes)

### Options

```bash
# Specify custom stats directory
python generate_csv.py -s /path/to/stats

# Specify custom output file
python generate_csv.py -o custom_report.csv
```

The script also prints summary statistics including averages for PRs in queue, estimated clear time, and CI runtime.

## Graph Generation

Generate visualizations from the collected statistics:

```bash
python generate_graphs.py
```

This creates a bar chart showing the average number of PRs in the merge queue by hour of day (PST), saved to `prs_by_hour.png` in the current directory.

### Options

```bash
# Specify custom input CSV
python generate_graphs.py -i custom_report.csv

# Specify custom output directory
python generate_graphs.py -o output_dir
```

The graph includes value labels on top of each bar for easy reading.

## Requirements

- Python 3.7+
- GitHub token with repository access
- `gh` CLI (for easy token retrieval)
- Bash shell
