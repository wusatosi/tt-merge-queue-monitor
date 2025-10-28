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

## Requirements

- Python 3.7+
- GitHub token with repository access
- `gh` CLI (for easy token retrieval)
