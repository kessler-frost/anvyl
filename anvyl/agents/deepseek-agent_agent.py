#!/usr/bin/env python3
"""
Anvyl AI Agent Container Script
Agent: deepseek-agent
Provider: lmstudio
Model: deepseek/deepseek-r1-0528-qwen3-8b
"""

import sys
import os
import time
import signal
import logging
from pathlib import Path

# Add the anvyl package to Python path
sys.path.insert(0, '/app')

try:
    from anvyl.ai_agent import create_ai_agent
    from anvyl.grpc_client import AnvylClient
except ImportError as e:
    print(f"Error importing anvyl: {e}")
    print("Make sure the anvyl package is installed in the container")
    sys.exit(1)

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    print("\n🛑 Received shutdown signal. Stopping agent...")
    sys.exit(0)

def main():
    """Main agent container entry point."""
    # Set up signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Configure logging
    logging.basicConfig(
        level=logging.INFO if False else logging.WARNING,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print(f"🚀 Starting Anvyl AI Agent: deepseek-agent")
    print(f"   Provider: lmstudio")
    print(f"   Model: deepseek/deepseek-r1-0528-qwen3-8b")
    print(f"   gRPC Server: host.docker.internal:50051")

    # Wait for gRPC server to be available
    print("⏳ Waiting for gRPC server to be available...")
    max_retries = 30
    retry_count = 0

    while retry_count < max_retries:
        try:
            client = AnvylClient("host.docker.internal", 50051)
            if client.connect():
                print("✅ Connected to gRPC server")
                break
            else:
                print(f"❌ Failed to connect to gRPC server (attempt {retry_count + 1}/{max_retries})")
        except Exception as e:
            print(f"❌ Connection error (attempt {retry_count + 1}/{max_retries}): {e}")

        retry_count += 1
        time.sleep(2)

    if retry_count >= max_retries:
        print("❌ Failed to connect to gRPC server after maximum retries")
        sys.exit(1)

    try:
        # Create and initialize the agent
        agent = create_ai_agent(
            model_provider="lmstudio",
            model_id="deepseek/deepseek-r1-0528-qwen3-8b",
            host="host.docker.internal",
            port=50051,
            verbose=False,
            agent_name="deepseek-agent",
            lmstudio_host="host.docker.internal",
            
        )

        print("✅ Agent initialized successfully")
        print("🔄 Agent is running and ready to receive instructions")
        print("💡 Use 'anvyl agent act deepseek-agent "<instruction>"' to execute actions")

        # Keep the container running
        while True:
            time.sleep(60)  # Sleep for 1 minute
            # Optional: Add health check or keepalive logic here

    except Exception as e:
        print(f"❌ Error initializing agent: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
