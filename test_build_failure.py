#!/usr/bin/env python3
"""
Test script to verify Docker cleanup when build fails.
"""

import sys
import os
import docker
import time
from pathlib import Path

# Add the anvyl package to the path
sys.path.insert(0, str(Path(__file__).parent))

from anvyl.agent_manager import get_agent_manager

def test_build_failure_cleanup():
    """Test that Docker containers and images are cleaned up when build fails."""

    print("🧪 Testing Docker cleanup on build failure...")

    # Get agent manager
    manager = get_agent_manager()

    # Create a test agent
    test_agent_name = "test-build-failure"

    try:
        # Remove agent if it exists
        try:
            manager.remove_agent(test_agent_name)
        except:
            pass

        # Create agent
        print(f"📝 Creating test agent '{test_agent_name}'...")
        config = manager.create_agent(
            name=test_agent_name,
            provider="lmstudio",
            model_id="test-model",
            verbose=True
        )

        print(f"✅ Agent configuration created")

        # Check Docker state before
        client = docker.from_env()
        print("🔍 Docker state before test:")
        containers_before = client.containers.list(all=True, filters={"label": "anvyl.component=agent"})
        images_before = client.images.list(filters={"reference": "anvyl-agent-*"})
        print(f"   Containers: {len(containers_before)}")
        print(f"   Images: {len(images_before)}")

        # Try to start the agent (this should fail during build)
        print(f"🚀 Attempting to start agent (should fail during build)...")
        success = manager.start_agent(test_agent_name)

        if success:
            print("❌ Expected failure but agent started successfully")
            return False
        else:
            print("✅ Agent startup failed as expected")

        # Wait a moment for cleanup to complete
        time.sleep(2)

        # Check Docker state after
        print("🔍 Docker state after test:")
        containers_after = client.containers.list(all=True, filters={"label": "anvyl.component=agent"})
        images_after = client.images.list(filters={"reference": "anvyl-agent-*"})
        print(f"   Containers: {len(containers_after)}")
        print(f"   Images: {len(images_after)}")

        # Check for specific container
        container_name = f"anvyl-agent-{test_agent_name}"
        try:
            container = client.containers.get(container_name)
            print(f"❌ Container still exists: {container_name}")
            print(f"   Status: {container.status}")
            return False
        except docker.errors.NotFound:
            print(f"✅ Container cleaned up: {container_name}")

        # Check for specific image
        image_name = f"anvyl-agent-{test_agent_name}"
        try:
            image = client.images.get(image_name)
            print(f"❌ Image still exists: {image_name}")
            return False
        except docker.errors.ImageNotFound:
            print(f"✅ Image cleaned up: {image_name}")

        # Check for any anvyl-agent images with similar names
        images = client.images.list(filters={"reference": f"anvyl-agent-{test_agent_name}*"})
        if images:
            print(f"❌ Found {len(images)} related images that weren't cleaned up")
            for img in images:
                print(f"   - {img.tags[0] if img.tags else img.id}")
            return False
        else:
            print(f"✅ All related images cleaned up")

        # Check if any new containers were created
        if len(containers_after) > len(containers_before):
            print(f"❌ New containers were created and not cleaned up")
            for container in containers_after:
                if container not in containers_before:
                    print(f"   - {container.name} ({container.id[:12]})")
            return False

        # Check if any new images were created
        if len(images_after) > len(images_before):
            print(f"❌ New images were created and not cleaned up")
            for image in images_after:
                if image not in images_before:
                    print(f"   - {image.tags[0] if image.tags else image.id}")
            return False

        print("🎉 All cleanup tests passed!")
        return True

    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Clean up test agent configuration
        try:
            manager.remove_agent(test_agent_name)
        except:
            pass

        # Run general cleanup to be safe
        try:
            manager.cleanup_orphaned_resources(test_agent_name)
        except:
            pass

if __name__ == "__main__":
    print("🚀 Starting Docker build failure cleanup test...")

    test_passed = test_build_failure_cleanup()

    print(f"\n📊 Test Results:")
    print(f"   Build failure cleanup: {'✅ PASSED' if test_passed else '❌ FAILED'}")

    if test_passed:
        print("\n🎉 Test passed! Docker cleanup is working properly.")
        sys.exit(0)
    else:
        print("\n❌ Test failed. Docker cleanup needs attention.")
        sys.exit(1)