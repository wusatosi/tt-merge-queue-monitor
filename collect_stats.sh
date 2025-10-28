#!/bin/bash

# GitHub Merge Queue Stats Collector
# Collects merge queue statistics every 30 minutes

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Create stats directory if it doesn't exist
mkdir -p stats

# Activate virtual environment
source venv/bin/activate

# Refresh GitHub token
export GITHUB_TOKEN=$(gh auth token)

# Generate timestamp for filename
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
OUTPUT_FILE="stats/merge_queue_${TIMESTAMP}.json"

# Run the Python script and save output
echo "Collecting merge queue statistics at $(date)..."
python merge_queue_monitor.py -o "$OUTPUT_FILE"

if [ $? -eq 0 ]; then
    echo "Successfully saved to: $OUTPUT_FILE"
else
    echo "Error: Failed to collect statistics"
    exit 1
fi
