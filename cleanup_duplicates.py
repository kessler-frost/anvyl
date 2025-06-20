#!/usr/bin/env python3
"""
Cleanup script to remove duplicate hosts from the Anvyl database.
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from anvyl.database.models import DatabaseManager

def main():
    """Clean up duplicate hosts."""
    print("🧹 Cleaning up duplicate hosts...")

    # Initialize database manager
    db = DatabaseManager()

    # Get current hosts
    hosts = db.list_hosts()
    print(f"📊 Found {len(hosts)} total hosts")

    # Group hosts by IP
    ip_groups = {}
    for host in hosts:
        if host.ip not in ip_groups:
            ip_groups[host.ip] = []
        ip_groups[host.ip].append(host)

    # Show duplicates
    duplicates_found = False
    for ip, host_list in ip_groups.items():
        if len(host_list) > 1:
            duplicates_found = True
            print(f"\n🔍 IP {ip} has {len(host_list)} hosts:")
            for host in host_list:
                print(f"   - {host.name} (ID: {host.id[:8]}...) - {host.status}")

    if not duplicates_found:
        print("✅ No duplicate hosts found!")
        return

    # Clean up duplicates
    print(f"\n🗑️  Cleaning up duplicates...")
    deleted_count = db.cleanup_duplicate_hosts()

    # Show results
    remaining_hosts = db.list_hosts()
    print(f"✅ Cleanup complete!")
    print(f"   - Deleted {deleted_count} duplicate hosts")
    print(f"   - Remaining hosts: {len(remaining_hosts)}")

    print(f"\n📋 Remaining hosts:")
    for host in remaining_hosts:
        print(f"   - {host.name} ({host.ip}) - {host.status}")

if __name__ == "__main__":
    main()