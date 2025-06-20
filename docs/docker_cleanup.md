# Docker Cleanup for Anvyl Agents

This document explains the Docker cleanup functionality in Anvyl, which ensures that Docker containers and images created by Anvyl agents are properly cleaned up. **Docker's own intermediate build containers and dangling images are not removed by Anvyl; users should use Docker's built-in cleanup commands for those.**

## Overview

When an Anvyl AI agent fails to start, the system automatically cleans up any Docker resources that were created by Anvyl during the startup process. This prevents orphaned agent containers and images from accumulating on your system.

**Note:** Docker may create intermediate build containers and dangling images (with `<none>` as the repository/tag) during failed builds. These are not removed by Anvyl. See below for how to clean them up.

## Automatic Cleanup (Anvyl-managed)

The cleanup happens automatically in the following scenarios:

1. **Agent container/image creation failure** - If the agent's container or image fails to be created or started
2. **Infrastructure service failure** - If the agent can't register with the infrastructure service
3. **No hosts available** - If no hosts are available for the agent
4. **Any other exception** - For any other error during startup

## What Gets Cleaned Up by Anvyl

The automatic cleanup removes:

- **Anvyl agent containers** - Any containers created for the failed agent (with the `anvyl-agent-` prefix or label)
- **Anvyl agent images** - The Docker image built for the agent (with the `anvyl-agent-` prefix)
- **Temporary build directories** - Build artifacts and scripts
- **Agent configuration status** - Resets the agent status to "stopped"

## What Does NOT Get Cleaned Up by Anvyl

- **Dangling images** (`<none>:<none>`) created by Docker during failed builds
- **Intermediate build containers** created by Docker during the build process

These are not labeled or tagged by Anvyl and cannot be reliably identified. **Users should clean these up using Docker's own commands.**

## Manual Cleanup

If you need to manually clean up orphaned resources created by Anvyl, you can use the CLI command:

```bash
# Clean up orphaned resources for a specific agent
anvyl agent cleanup <agent_name>

# Clean up all orphaned resources for all agents
anvyl agent cleanup

# Clean up without confirmation prompts
anvyl agent cleanup --yes
```

## Cleaning Up Docker's Own Intermediates

To remove Docker's intermediate build containers and dangling images, run:

```bash
docker system prune -f
```

This will remove:
- All stopped containers (including intermediate build containers)
- All dangling images (images with `<none>` as the repository/tag)
- All unused build cache and networks

**Warning:** This is a global operation and will remove all such resources, not just those created by Anvyl.

## Testing Cleanup

You can test the cleanup functionality using the provided test script:

```bash
python test_build_failure.py
```

This script:
1. Creates a test agent with invalid configuration
2. Attempts to start the agent (which will fail)
3. Verifies that Anvyl agent containers and images are properly cleaned up

## Cleanup Process

The cleanup process follows these steps:

1. **Container cleanup** - Removes any Anvyl agent containers by name and ID
2. **Image cleanup** - Removes Anvyl agent Docker images by name and pattern matching
3. **Build directory cleanup** - Removes temporary build artifacts
4. **Configuration reset** - Resets agent status to "stopped"

## Error Handling

The cleanup process is designed to be robust:

- **Graceful failures** - If one cleanup step fails, others continue
- **Pattern matching** - Uses multiple methods to find and remove Anvyl agent resources
- **Logging** - Detailed logging of cleanup operations
- **Exception handling** - Catches and logs any cleanup errors

## Troubleshooting

If you encounter issues with cleanup:

1. **Check Docker status** - Ensure Docker is running
2. **Manual cleanup** - Use the CLI cleanup command for Anvyl resources
3. **Run Docker prune** - Use `docker system prune -f` to remove Docker's own intermediates
4. **Check logs** - Look for cleanup-related log messages
5. **Force removal** - Use Docker commands directly if needed

## Example Log Output

When cleanup occurs, you'll see log messages like:

```
🧹 Cleaning up failed startup for agent 'my-agent'
Removed failed container for agent 'my-agent'
Removed container by name: anvyl-agent-my-agent
Removed Docker image: anvyl-agent-my-agent
Removed temporary build directory: /path/to/temp/build
Reset agent 'my-agent' status to stopped
```

## Best Practices

1. **Monitor logs** - Check agent startup logs for cleanup messages
2. **Regular cleanup** - Run manual cleanup periodically
3. **Resource monitoring** - Monitor Docker resource usage
4. **Test failures** - Test cleanup with invalid configurations
5. **Run Docker prune** - Periodically run `docker system prune -f` to keep your Docker environment clean

## Related Commands

- `anvyl agent start <name>` - Start an agent (triggers cleanup on failure)
- `anvyl agent stop <name>` - Stop a running agent
- `anvyl agent remove <name>` - Remove an agent and its resources
- `anvyl agent cleanup` - Manual cleanup of orphaned Anvyl agent resources
- `docker system prune -f` - Remove Docker's own intermediate build containers and dangling images