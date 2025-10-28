#!/usr/bin/env python3
"""
GitHub Merge Queue Monitor for tenstorrent/tt-metal

Tracks merge queue status including:
- Number of PRs in queue
- PR names/titles
- Time in queue
- CI/check run status
"""

import os
import sys
import json
import argparse
from datetime import datetime, timezone
import requests
from typing import List, Dict, Optional


class MergeQueueMonitor:
    def __init__(self, token: Optional[str] = None):
        """Initialize the monitor with GitHub API token."""
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            print("Warning: No GitHub token provided. API rate limits will be restrictive.")

        self.headers = {
            "Authorization": f"Bearer {self.token}" if self.token else ""
        }

        self.repo_owner = "tenstorrent"
        self.repo_name = "tt-metal"
        self.graphql_url = "https://api.github.com/graphql"

    def get_merge_queue_entries(self, branch: str = "main") -> List[Dict]:
        """Fetch merge queue entries for the repository using GraphQL."""
        query = """
        query($owner: String!, $name: String!, $branch: String!) {
          repository(owner: $owner, name: $name) {
            mergeQueue(branch: $branch) {
              entries(first: 100) {
                totalCount
                nodes {
                  id
                  position
                  state
                  estimatedTimeToMerge
                  enqueuedAt
                  headCommit {
                    oid
                    commitUrl
                    statusCheckRollup {
                      state
                      contexts(first: 100) {
                        nodes {
                          ... on CheckRun {
                            name
                            status
                            conclusion
                            startedAt
                            completedAt
                            detailsUrl
                          }
                          ... on StatusContext {
                            context
                            state
                            targetUrl
                          }
                        }
                      }
                    }
                  }
                  pullRequest {
                    number
                    title
                    author {
                      login
                    }
                    createdAt
                    url
                  }
                }
              }
            }
          }
        }
        """

        variables = {
            "owner": self.repo_owner,
            "name": self.repo_name,
            "branch": branch
        }

        try:
            response = requests.post(
                self.graphql_url,
                json={"query": query, "variables": variables},
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()

            if "errors" in data:
                print(f"GraphQL errors: {data['errors']}")
                return []

            entries = data.get("data", {}).get("repository", {}).get("mergeQueue", {}).get("entries", {}).get("nodes", [])
            return entries
        except Exception as e:
            print(f"Error fetching merge queue: {e}")
            return []

    def process_check_runs(self, head_commit: Dict) -> Dict:
        """Process check runs from the GraphQL response."""
        if not head_commit or not head_commit.get("statusCheckRollup"):
            return {"total": 0, "in_progress": 0, "completed": 0, "queued": 0, "checks": [], "ci_started_at": None}

        overall_state = head_commit["statusCheckRollup"].get("state", "UNKNOWN")
        contexts = head_commit["statusCheckRollup"].get("contexts", {}).get("nodes", [])

        in_progress = 0
        completed = 0
        queued = 0
        earliest_start_time = None

        for context in contexts:
            status = context.get("status", "").upper()
            if status == "IN_PROGRESS":
                in_progress += 1
            elif status == "COMPLETED":
                completed += 1
            elif status == "QUEUED":
                queued += 1

            # Track the earliest start time across all checks
            started_at = context.get("startedAt")
            if started_at:
                if earliest_start_time is None:
                    earliest_start_time = started_at
                else:
                    # Compare ISO timestamp strings
                    if started_at < earliest_start_time:
                        earliest_start_time = started_at

        return {
            "total": len(contexts),
            "in_progress": in_progress,
            "completed": completed,
            "queued": queued,
            "overall_state": overall_state,
            "ci_started_at": earliest_start_time,
            "checks": contexts
        }

    def calculate_time_in_queue(self, queued_at: str) -> str:
        """Calculate how long a PR has been in the queue."""
        queued_time = datetime.fromisoformat(queued_at.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        delta = now - queued_time

        hours = delta.total_seconds() / 3600
        if hours < 1:
            minutes = delta.total_seconds() / 60
            return f"{int(minutes)} minutes"
        elif hours < 24:
            return f"{hours:.1f} hours"
        else:
            days = hours / 24
            return f"{days:.1f} days"

    def display_queue_status(self):
        """Display the current merge queue status."""
        print(f"\n{'='*80}")
        print(f"Merge Queue Status for {self.repo_owner}/{self.repo_name}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}\n")

        entries = self.get_merge_queue_entries()

        if not entries:
            print("No entries in merge queue (or merge queue not accessible).\n")
            return

        print(f"Total PRs in queue: {len(entries)}\n")

        for idx, entry in enumerate(entries, 1):
            pr = entry.get("pullRequest", {})
            print(f"[{idx}] PR #{pr.get('number', 'N/A')}: {pr.get('title', 'N/A')}")
            print(f"    Author: {pr.get('author', {}).get('login', 'N/A')}")
            print(f"    Position in queue: {entry.get('position', 'N/A')}")
            print(f"    State: {entry.get('state', 'N/A')}")
            print(f"    PR URL: {pr.get('url', 'N/A')}")

            queued_at = entry.get("enqueuedAt")
            if queued_at:
                time_in_queue = self.calculate_time_in_queue(queued_at)
                print(f"    Time in queue: {time_in_queue}")
                print(f"    Enqueued at: {queued_at}")

            estimated_time = entry.get("estimatedTimeToMerge")
            if estimated_time:
                print(f"    Estimated time to merge: {estimated_time} seconds (~{estimated_time // 60} minutes)")

            # Get CI status
            head_commit = entry.get("headCommit")
            if head_commit:
                print(f"    Commit: {head_commit.get('oid', 'N/A')[:7]}")
                check_status = self.process_check_runs(head_commit)
                print(f"    CI Status (Overall: {check_status.get('overall_state', 'UNKNOWN')}):")

                # Show when CI started
                ci_started_at = check_status.get('ci_started_at')
                if ci_started_at:
                    print(f"      - CI started at: {ci_started_at}")

                print(f"      - Total checks: {check_status['total']}")
                print(f"      - Running: {check_status['in_progress']}")
                print(f"      - Completed: {check_status['completed']}")
                print(f"      - Queued: {check_status['queued']}")

                # Show individual check statuses
                if check_status['checks']:
                    print(f"      Check details:")
                    for check in check_status['checks'][:10]:  # Show first 10 checks
                        name = check.get('name') or check.get('context', 'Unknown')
                        status = check.get('status', check.get('state', 'UNKNOWN')).upper()
                        conclusion = check.get('conclusion')
                        conclusion_upper = conclusion.upper() if conclusion else ''

                        if status == "COMPLETED":
                            if conclusion_upper == "SUCCESS":
                                status_emoji = "✓"
                            elif conclusion_upper == "FAILURE":
                                status_emoji = "✗"
                            elif conclusion_upper == "CANCELLED":
                                status_emoji = "⊘"
                            else:
                                status_emoji = "?"
                        elif status == "IN_PROGRESS":
                            status_emoji = "▶"
                        elif status == "QUEUED":
                            status_emoji = "⏸"
                        else:
                            status_emoji = "?"

                        status_str = f"{conclusion_upper}" if conclusion_upper else status
                        print(f"        {status_emoji} {name}: {status_str}")

                    if len(check_status['checks']) > 10:
                        print(f"        ... and {len(check_status['checks']) - 10} more")

            print()

        print(f"{'='*80}\n")

    def export_to_json(self, output_file: str, branch: str = "main"):
        """Export merge queue data to a JSON file."""
        entries = self.get_merge_queue_entries(branch)

        export_data = {
            "timestamp": datetime.now().isoformat(),
            "repository": f"{self.repo_owner}/{self.repo_name}",
            "branch": branch,
            "total_prs": len(entries),
            "entries": []
        }

        for entry in entries:
            pr = entry.get("pullRequest", {})
            head_commit = entry.get("headCommit")

            entry_data = {
                "position": entry.get("position"),
                "state": entry.get("state"),
                "pr_number": pr.get("number"),
                "pr_title": pr.get("title"),
                "pr_url": pr.get("url"),
                "author": pr.get("author", {}).get("login"),
                "enqueued_at": entry.get("enqueuedAt"),
                "estimated_time_to_merge_seconds": entry.get("estimatedTimeToMerge"),
            }

            # Add time in queue calculation
            queued_at = entry.get("enqueuedAt")
            if queued_at:
                entry_data["time_in_queue"] = self.calculate_time_in_queue(queued_at)

            # Add commit and CI information
            if head_commit:
                check_status = self.process_check_runs(head_commit)
                entry_data["commit"] = {
                    "sha": head_commit.get("oid"),
                    "url": head_commit.get("commitUrl")
                }
                entry_data["ci_status"] = {
                    "overall_state": check_status.get("overall_state"),
                    "ci_started_at": check_status.get("ci_started_at"),
                    "total_checks": check_status["total"],
                    "running": check_status["in_progress"],
                    "completed": check_status["completed"],
                    "queued": check_status["queued"],
                    "checks": []
                }

                # Add individual check information
                for check in check_status['checks']:
                    check_info = {
                        "name": check.get('name') or check.get('context', 'Unknown'),
                        "status": check.get('status', check.get('state', 'UNKNOWN')),
                        "conclusion": check.get('conclusion'),
                        "started_at": check.get('startedAt'),
                        "completed_at": check.get('completedAt'),
                        "details_url": check.get('detailsUrl') or check.get('targetUrl')
                    }
                    entry_data["ci_status"]["checks"].append(check_info)

            export_data["entries"].append(entry_data)

        # Write to file
        try:
            with open(output_file, 'w') as f:
                json.dump(export_data, f, indent=2)
            print(f"Successfully exported merge queue data to: {output_file}")
        except Exception as e:
            print(f"Error writing to file {output_file}: {e}")
            sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Monitor GitHub merge queue status for tenstorrent/tt-metal",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "-o", "--output",
        metavar="FILE",
        help="Export merge queue data to a JSON file"
    )
    parser.add_argument(
        "-b", "--branch",
        default="main",
        help="Branch name to monitor (default: main)"
    )

    args = parser.parse_args()

    token = os.getenv("GITHUB_TOKEN")

    if not token:
        print("\nNote: Set GITHUB_TOKEN environment variable for higher API rate limits")
        print("Example: export GITHUB_TOKEN='your_token_here'\n")

    monitor = MergeQueueMonitor(token)

    if args.output:
        monitor.export_to_json(args.output, args.branch)
    else:
        monitor.display_queue_status()


if __name__ == "__main__":
    main()
