#!/usr/bin/env python3
"""
Organize stats files into YYYY-MM directory structure
"""
import os
import re
import shutil
from pathlib import Path

def organize_stats():
    stats_dir = Path("stats")

    # Find all JSON files recursively
    json_files = list(stats_dir.rglob("merge_queue_*.json"))

    print(f"Found {len(json_files)} files to organize")

    for json_file in json_files:
        # Extract date from filename: merge_queue_YYYYMMDD_HHMMSS.json
        match = re.match(r'merge_queue_(\d{8})_\d{6}\.json', json_file.name)
        if match:
            date_str = match.group(1)
            year = date_str[0:4]
            month = date_str[4:6]

            # Create target directory YYYY-MM
            target_dir = stats_dir / f"{year}-{month}"
            target_dir.mkdir(parents=True, exist_ok=True)

            # Move file to target directory
            target_path = target_dir / json_file.name

            # Only move if not already in the right place
            if json_file.parent != target_dir:
                print(f"Moving {json_file} -> {target_path}")
                shutil.move(str(json_file), str(target_path))

    # Clean up empty directories
    for dirpath, dirnames, filenames in os.walk(stats_dir, topdown=False):
        # Don't remove the root stats directory or YYYY-MM directories
        if dirpath != str(stats_dir) and not re.match(r'.*\d{4}-\d{2}$', dirpath):
            try:
                os.rmdir(dirpath)
                print(f"Removed empty directory: {dirpath}")
            except OSError:
                pass  # Directory not empty, skip

    print("\nOrganization complete!")
    print("\nFinal structure:")
    for month_dir in sorted(stats_dir.glob("*-*")):
        if month_dir.is_dir():
            file_count = len(list(month_dir.glob("*.json")))
            print(f"  {month_dir.name}/: {file_count} files")

if __name__ == "__main__":
    organize_stats()
