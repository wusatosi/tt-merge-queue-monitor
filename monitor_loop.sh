#!/bin/bash

# Continuous Merge Queue Monitor
# Runs the stats collector every 30 minutes indefinitely

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Starting continuous merge queue monitoring..."
echo "Stats will be collected every 30 minutes"
echo "Press Ctrl+C to stop"
echo ""

# Run continuously
while true; do
    # Run the collection script
    ./collect_stats.sh

    echo ""
    echo "Next collection in 30 minutes (at $(date -v+30M '+%Y-%m-%d %H:%M:%S'))..."
    echo "---"
    echo ""

    # Sleep for 30 minutes (1800 seconds)
    sleep 1800
done
