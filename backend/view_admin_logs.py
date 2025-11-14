#!/usr/bin/env python3
"""
Admin Activity Log Viewer
Displays and analyzes admin panel activity logs
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import sys

def load_logs(log_file):
    """Load and parse JSONL log file."""
    logs = []
    if not log_file.exists():
        return logs

    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    logs.append(json.loads(line))
                except json.JSONDecodeError:
                    print(f"Warning: Invalid JSON line: {line[:100]}...")
    return logs

def format_timestamp(ts):
    """Format ISO timestamp for display."""
    try:
        dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return ts

def display_logs(logs, limit=None, activity_filter=None):
    """Display logs in a readable format."""
    if not logs:
        print("No logs found.")
        return

    # Filter logs if requested
    if activity_filter:
        logs = [log for log in logs if log.get('activity') == activity_filter]

    # Sort by timestamp (newest first)
    logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

    # Limit results
    if limit:
        logs = logs[:limit]

    print(f"\n{'='*80}")
    print(f"ADMIN ACTIVITY LOGS ({len(logs)} entries)")
    print(f"{'='*80}")

    for log in logs:
        timestamp = format_timestamp(log.get('timestamp', 'Unknown'))
        activity = log.get('activity', 'Unknown')
        admin_user = log.get('admin_user', 'Unknown')
        client_ip = log.get('client_ip', 'Unknown')
        details = log.get('details', {})

        print(f"\n[{timestamp}] {activity.upper()}")
        print(f"  Admin: {admin_user}")
        print(f"  IP: {client_ip}")

        if details:
            print("  Details:")
            for key, value in details.items():
                if isinstance(value, (dict, list)):
                    print(f"    {key}: {json.dumps(value, indent=6)}")
                else:
                    print(f"    {key}: {value}")

def show_statistics(logs):
    """Show statistics about admin activities."""
    if not logs:
        print("No logs available for statistics.")
        return

    print(f"\n{'='*80}")
    print("ADMIN ACTIVITY STATISTICS")
    print(f"{'='*80}")

    # Activity counts
    activities = Counter(log['activity'] for log in logs if 'activity' in log)
    print(f"\nActivity Breakdown ({len(logs)} total actions):")
    for activity, count in activities.most_common():
        print(f"  {activity}: {count}")

    # Admin users
    users = Counter(log['admin_user'] for log in logs if 'admin_user' in log)
    print(f"\nAdmin Users ({len(users)} unique):")
    for user, count in users.most_common():
        print(f"  {user}: {count}")

    # Time-based stats
    now = datetime.now()
    today_logs = [log for log in logs if 'timestamp' in log and
                  (now - datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00'))).days < 1]
    week_logs = [log for log in logs if 'timestamp' in log and
                 (now - datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00'))).days < 7]

    print("\nTime-based Activity:")
    print(f"  Today: {len(today_logs)} actions")
    print(f"  This week: {len(week_logs)} actions")
    print(f"  All time: {len(logs)} actions")

def main():
    """Main function."""
    # Determine log directory
    script_dir = Path(__file__).parent
    log_dir = script_dir / "logs"
    admin_log_file = log_dir / "admin_activity.jsonl"

    print("Admin Activity Log Viewer")
    print(f"Log file: {admin_log_file}")

    # Load logs
    logs = load_logs(admin_log_file)

    if not logs:
        print("No admin activity logs found.")
        print(f"Expected location: {admin_log_file}")
        return

    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="View admin activity logs")
    parser.add_argument("--limit", type=int, help="Limit number of entries to show")
    parser.add_argument("--activity", help="Filter by specific activity type")
    parser.add_argument("--stats", action="store_true", help="Show statistics only")

    args = parser.parse_args()

    if args.stats:
        show_statistics(logs)
    else:
        display_logs(logs, limit=args.limit, activity_filter=args.activity)

if __name__ == "__main__":
    main()