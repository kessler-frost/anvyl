#!/usr/bin/env python3
"""
Cleanup script to remove non-localhost hosts from the Anvyl database.
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from anvyl.database.models import DatabaseManager

def main():
    """Clean up non-localhost hosts."""
    print("🧹 Cleaning up non-localhost hosts...")

    # Initialize database manager
    db = DatabaseManager()

    # Get current hosts
    hosts = db.list_hosts()
    print(f"📊 Found {len(hosts)} total hosts")

    # Show all hosts
    for host in hosts:
        print(f"   - {host.name} ({host.ip}) - {host.status}")

    # Find non-localhost hosts
    non_localhost_hosts = [h for h in hosts if h.ip != "127.0.0.1"]

    if not non_localhost_hosts:
        print("✅ No non-localhost hosts found!")
        return

    print(f"\n🗑️  Found {len(non_localhost_hosts)} non-localhost hosts to remove:")
    for host in non_localhost_hosts:
        print(f"   - {host.name} ({host.ip}) - {host.status}")

    # Remove non-localhost hosts
    deleted_count = 0
    for host in non_localhost_hosts:
        if db.delete_host(host.id):
            deleted_count += 1
            print(f"   ✅ Deleted: {host.name} ({host.ip})")

    # Show results
    remaining_hosts = db.list_hosts()
    print(f"\n✅ Cleanup complete!")
    print(f"   - Deleted {deleted_count} non-localhost hosts")
    print(f"   - Remaining hosts: {len(remaining_hosts)}")

    print(f"\n📋 Remaining hosts:")
    for host in remaining_hosts:
        print(f"   - {host.name} ({host.ip}) - {host.status}")

if __name__ == "__main__":
    main()