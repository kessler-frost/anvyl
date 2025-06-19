# gRPC Server Restructure Summary

## Overview

This document summarizes the changes made to move the Anvyl gRPC server from running in a Docker container to running directly with Python. This change was made to resolve Docker socket permission issues on macOS with Docker Desktop.

## Changes Made

### 1. Removed Docker Container for gRPC Server

**Files Modified:**
- `ui/docker-compose.yml` - Removed `anvyl-grpc-server` service
- `Dockerfile.grpc-server` - **Deleted** (no longer needed)

**Changes:**
- Removed the entire `anvyl-grpc-server` service from docker-compose.yml
- Removed dependencies on the gRPC server container
- Added `extra_hosts` configuration to allow backend container to connect to host gRPC server

### 2. Updated Backend Configuration

**Files Modified:**
- `ui/docker-compose.yml` - Updated backend environment and networking

**Changes:**
- Added `extra_hosts: - "host.docker.internal:host-gateway"` to allow backend container to connect to host gRPC server
- Removed dependency on gRPC server container
- Backend now connects to gRPC server running on host at `host.docker.internal:50051`

### 3. Created New Startup Scripts

**New Files:**
- `scripts/start_anvyl_ui.sh` - Main startup script
- `scripts/stop_anvyl_ui.sh` - Stop script

**Features:**
- Starts gRPC server with Python (`python -m anvyl.grpc_server`)
- Starts UI stack with Docker Compose
- Checks for existing gRPC server processes
- Provides clear status messages and access URLs

### 4. Updated Existing Scripts

**Files Modified:**
- `scripts/start_ui.sh` - Updated to use new startup approach

**Changes:**
- Updated to use the new `start_anvyl_ui.sh` script
- Removed references to Docker-based gRPC server
- Added fallback method for manual startup

### 5. Updated Documentation

**Files Modified:**
- `README.md` - Updated quick start and development sections

**Changes:**
- Updated installation instructions to use new scripts
- Added information about gRPC server running with Python
- Updated development mode instructions
- Added new startup/stop commands

## Benefits

### 1. Resolved Docker Permission Issues
- No more Docker socket permission errors on macOS
- gRPC server has direct access to Docker daemon when running on host

### 2. Simplified Architecture
- Reduced container complexity
- Fewer moving parts in Docker setup
- Easier debugging and development

### 3. Better Development Experience
- gRPC server can be started/stopped independently
- Easier to modify and test gRPC server code
- No need to rebuild Docker images for gRPC server changes

### 4. Improved Performance
- No container overhead for gRPC server
- Direct access to system resources
- Faster startup times

## Usage

### Starting the Infrastructure

```bash
# Option 1: Use the new startup script
./scripts/start_anvyl_ui.sh

# Option 2: Use the updated quick start script
./scripts/start_ui.sh

# Option 3: Manual startup
# Terminal 1: Start gRPC server
python -m anvyl.grpc_server

# Terminal 2: Start UI stack
cd ui && docker-compose up -d
```

### Stopping the Infrastructure

```bash
# Stop everything
./scripts/stop_anvyl_ui.sh

# Or stop UI stack only
cd ui && docker-compose down

# Stop gRPC server manually
pkill -f "python -m anvyl.grpc_server"
```

## Access Points

After starting the infrastructure:

- **Web UI**: http://localhost:3000
- **API Server**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **gRPC Server**: localhost:50051

## Troubleshooting

### gRPC Server Won't Start
```bash
# Check if port is in use
lsof -i :50051

# Kill existing processes
pkill -f "python -m anvyl.grpc_server"

# Start manually to see errors
python -m anvyl.grpc_server
```

### Backend Can't Connect to gRPC Server
```bash
# Check if gRPC server is running
curl http://localhost:8000/health

# Check backend logs
docker-compose logs anvyl-ui-backend
```

### Docker Permission Issues
- This should no longer occur since gRPC server runs outside Docker
- If issues persist, ensure Docker Desktop is running and accessible

## Migration Notes

### For Existing Users
1. Stop any running containers: `docker-compose down`
2. Use the new startup script: `./scripts/start_anvyl_ui.sh`
3. The gRPC server will now run with Python instead of Docker

### For Developers
1. gRPC server code changes no longer require Docker rebuilds
2. Use `python -m anvyl.grpc_server` for development
3. UI components still use Docker for consistency

## Future Considerations

1. **Production Deployment**: Consider using systemd or similar for gRPC server process management
2. **Monitoring**: Add process monitoring for the gRPC server
3. **Logging**: Configure proper logging for the gRPC server process
4. **Security**: Review security implications of running gRPC server on host

---

This restructure successfully resolves the Docker permission issues while maintaining all functionality and improving the development experience.