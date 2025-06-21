# Manual Test Procedures for Anvyl

This document contains manual test procedures to verify Anvyl functionality across different scenarios.

## 1. Installation Tests

### 1.1 Fresh Installation from PyPI

**Objective**: Verify Anvyl can be installed from PyPI and basic commands work.

**Prerequisites**:
- Clean Python 3.10+ environment
- Docker Desktop installed and running
- Internet connection

**Steps**:
1. Create a new virtual environment:
   ```bash
   python -m venv anvyl-test-env
   source anvyl-test-env/bin/activate  # On Windows: anvyl-test-env\Scripts\activate
   ```

2. Install Anvyl:
   ```bash
   pip install anvyl
   ```

3. Verify installation:
   ```bash
   anvyl version
   ```
   **Expected**: Version information is displayed

4. Test basic help:
   ```bash
   anvyl --help
   ```
   **Expected**: Help text with available commands is shown

5. Test Docker connectivity:
   ```bash
   anvyl status
   ```
   **Expected**: Status shows system health information

**Pass Criteria**: All commands execute without errors and display expected output.

### 1.2 Development Installation

**Objective**: Verify development installation works correctly.

**Prerequisites**:
- Git installed
- Python 3.10+ with pip
- Docker Desktop

**Steps**:
1. Clone repository:
   ```bash
   git clone https://github.com/kessler-frost/anvyl.git
   cd anvyl
   ```

2. Install in development mode:
   ```bash
   pip install -e ".[dev]"
   ```

3. Verify development tools:
   ```bash
   pytest --version
   black --version
   mypy --version
   ```

4. Run tests:
   ```bash
   pytest tests/unit/
   ```
   **Expected**: Tests pass without failures

5. Test CLI from development:
   ```bash
   anvyl version
   ```
   **Expected**: Shows development version

**Pass Criteria**: Installation completes successfully and all development tools are available.

## 2. Core Functionality Tests

### 2.1 Infrastructure Management

**Objective**: Test complete infrastructure lifecycle.

**Steps**:
1. Start infrastructure stack:
   ```bash
   anvyl up
   ```
   **Expected**: 
   - Docker containers start successfully
   - Web UI becomes available at http://localhost:3000
   - API becomes available at http://localhost:8000

2. Check infrastructure status:
   ```bash
   anvyl ps
   ```
   **Expected**: Shows running services and containers

3. View logs:
   ```bash
   anvyl logs
   ```
   **Expected**: Displays container logs

4. Stop infrastructure:
   ```bash
   anvyl down
   ```
   **Expected**: All containers stop cleanly

**Pass Criteria**: Infrastructure can be started, monitored, and stopped without errors.

### 2.2 Host Management

**Objective**: Test host registration and management.

**Steps**:
1. List initial hosts:
   ```bash
   anvyl host list
   ```
   **Expected**: Shows local host

2. Add a new host:
   ```bash
   anvyl host add test-host 192.168.1.100 --os "Linux" --tag "production"
   ```
   **Expected**: Host is added successfully

3. List hosts again:
   ```bash
   anvyl host list
   ```
   **Expected**: Shows both local and new host

4. Get host metrics:
   ```bash
   anvyl host metrics <host-id>
   ```
   **Expected**: Shows CPU, memory, and disk metrics

5. Test JSON output:
   ```bash
   anvyl host list --output json
   ```
   **Expected**: Valid JSON output with host data

**Pass Criteria**: Hosts can be added, listed, and monitored successfully.

### 2.3 Container Management

**Objective**: Test container lifecycle management.

**Prerequisites**: Infrastructure stack is running

**Steps**:
1. List initial containers:
   ```bash
   anvyl container list
   ```

2. Create a new container:
   ```bash
   anvyl container create test-nginx nginx:latest --port 8080:80
   ```
   **Expected**: Container is created and started

3. List containers:
   ```bash
   anvyl container list
   ```
   **Expected**: Shows new container with "running" status

4. Get container logs:
   ```bash
   anvyl container logs <container-id>
   ```
   **Expected**: Shows nginx access/error logs

5. Execute command in container:
   ```bash
   anvyl container exec <container-id> ls -la
   ```
   **Expected**: Shows directory listing from inside container

6. Stop container:
   ```bash
   anvyl container stop <container-id>
   ```
   **Expected**: Container stops successfully

**Pass Criteria**: Containers can be created, monitored, and managed through their lifecycle.

## 3. AI Agent Tests

### 3.1 Agent Setup and Basic Queries

**Objective**: Test AI agent functionality with a local model provider.

**Prerequisites**:
- Local model provider running (LMStudio, Ollama, etc.)
- Model loaded (e.g., llama-3.2-3b-instruct)
- Model API available at http://localhost:11434/v1

**Steps**:
1. Start the agent:
   ```bash
   anvyl agent up --model-provider-url http://localhost:11434/v1 --model llama-3.2-3b-instruct
   ```
   **Expected**: Agent starts successfully

2. Check agent status:
   ```bash
   anvyl agent info
   ```
   **Expected**: Shows agent information including model and available tools

3. Query the agent:
   ```bash
   anvyl agent query "List all containers on this host"
   ```
   **Expected**: Agent returns information about running containers

4. Query host information:
   ```bash
   anvyl agent query "What's the current CPU and memory usage?"
   ```
   **Expected**: Agent returns system resource information

5. Test container management:
   ```bash
   anvyl agent query "Create a new nginx container on port 8090"
   ```
   **Expected**: Agent creates container or explains any limitations

6. Stop the agent:
   ```bash
   anvyl agent down
   ```
   **Expected**: Agent stops cleanly

**Pass Criteria**: Agent can start, process queries, and interact with infrastructure.

### 3.2 Multi-Host Agent Communication

**Objective**: Test agent communication between multiple hosts.

**Prerequisites**:
- Two hosts with Anvyl installed
- Agents running on both hosts
- Network connectivity between hosts

**Steps**:
1. On Host A, start agent:
   ```bash
   anvyl agent up --port 4201
   ```

2. On Host B, start agent:
   ```bash
   anvyl agent up --port 4201
   ```

3. On Host A, add Host B as known host:
   ```bash
   anvyl agent add-host host-b-id 192.168.1.101
   ```

4. Query remote host from Host A:
   ```bash
   anvyl agent query "List containers on host-b" --host-id host-b-id
   ```
   **Expected**: Shows containers from Host B

5. Test broadcast functionality:
   ```bash
   anvyl agent query "Broadcast system status to all hosts"
   ```
   **Expected**: Receives responses from all known hosts

**Pass Criteria**: Agents can communicate across hosts and share information.

## 4. Web UI Tests

### 4.1 Dashboard Access and Navigation

**Objective**: Test web interface functionality.

**Prerequisites**: Infrastructure stack running (`anvyl up`)

**Steps**:
1. Open web browser and navigate to http://localhost:3000
   **Expected**: Anvyl dashboard loads without errors

2. Verify dashboard components:
   - System overview
   - Host status
   - Container status
   - Resource metrics
   **Expected**: All components display data correctly

3. Navigate to different sections:
   - Hosts page
   - Containers page
   - Agents page (if available)
   **Expected**: Navigation works smoothly

4. Test real-time updates:
   - Create a container via CLI
   - Refresh web UI
   **Expected**: New container appears in web interface

**Pass Criteria**: Web UI is accessible and displays current system state.

### 4.2 Container Management via Web UI

**Objective**: Test container operations through web interface.

**Steps**:
1. In web UI, navigate to containers section

2. Create a new container:
   - Click "Create Container" button
   - Fill in container details (name, image, ports)
   - Submit form
   **Expected**: Container is created and appears in list

3. View container details:
   - Click on a container
   **Expected**: Shows detailed container information

4. Check container logs:
   - Open container details
   - View logs section
   **Expected**: Logs are displayed

5. Stop container:
   - Use stop button in web UI
   **Expected**: Container status changes to "stopped"

**Pass Criteria**: Container management operations work through web interface.

## 5. Error Handling and Edge Cases

### 5.1 Service Unavailability Tests

**Objective**: Test behavior when dependencies are unavailable.

**Steps**:
1. Test with Docker stopped:
   ```bash
   # Stop Docker Desktop
   anvyl container list
   ```
   **Expected**: Graceful error message about Docker unavailability

2. Test with model provider unavailable:
   ```bash
   anvyl agent up --model-provider-url http://localhost:9999/v1
   ```
   **Expected**: Falls back to mock model or shows helpful error

3. Test invalid commands:
   ```bash
   anvyl host add invalid-host invalid-ip
   ```
   **Expected**: Validation error with helpful message

4. Test network connectivity issues:
   ```bash
   anvyl agent query "test" --host-id nonexistent-host
   ```
   **Expected**: Connection error with clear message

**Pass Criteria**: All error conditions are handled gracefully with informative messages.

### 5.2 Resource Limitation Tests

**Objective**: Test behavior under resource constraints.

**Steps**:
1. Create multiple containers:
   ```bash
   for i in {1..10}; do
     anvyl container create test-$i nginx:latest --port $((8080+i)):80
   done
   ```
   **Expected**: System handles multiple containers appropriately

2. Monitor resource usage:
   ```bash
   anvyl status
   ```
   **Expected**: Shows current resource utilization

3. Test with large log output:
   ```bash
   anvyl container logs <container-id> --tail 10000
   ```
   **Expected**: Handles large log volumes without issues

**Pass Criteria**: System operates correctly under various load conditions.

## 6. Data Persistence Tests

### 6.1 Data Integrity

**Objective**: Verify data persistence across restarts.

**Steps**:
1. Add hosts and containers:
   ```bash
   anvyl host add persistent-host 192.168.1.200
   anvyl container create persistent-nginx nginx:latest
   ```

2. Stop Anvyl services:
   ```bash
   anvyl down
   ```

3. Restart services:
   ```bash
   anvyl up
   ```

4. Verify data persistence:
   ```bash
   anvyl host list
   anvyl container list
   ```
   **Expected**: Previously added hosts and containers are still present

5. Test data purge:
   ```bash
   anvyl purge --force
   ```
   **Expected**: All data is cleared

6. Verify purge:
   ```bash
   anvyl host list
   anvyl container list
   ```
   **Expected**: No hosts or containers remain

**Pass Criteria**: Data persists correctly across service restarts and can be purged when needed.

## 7. Performance Tests

### 7.1 Response Time Tests

**Objective**: Verify acceptable response times for common operations.

**Steps**:
1. Time host listing:
   ```bash
   time anvyl host list
   ```
   **Expected**: Response time < 2 seconds

2. Time container operations:
   ```bash
   time anvyl container list
   time anvyl container create perf-test nginx:latest
   ```
   **Expected**: List < 3 seconds, Create < 10 seconds

3. Time agent queries:
   ```bash
   time anvyl agent query "Show system status"
   ```
   **Expected**: Response time < 5 seconds

**Pass Criteria**: All operations complete within acceptable time limits.

## 8. Documentation and Help Tests

### 8.1 Help System

**Objective**: Verify help documentation is complete and accurate.

**Steps**:
1. Test main help:
   ```bash
   anvyl --help
   ```

2. Test command-specific help:
   ```bash
   anvyl host --help
   anvyl container --help
   anvyl agent --help
   ```

3. Test subcommand help:
   ```bash
   anvyl host add --help
   anvyl container create --help
   ```

4. Verify examples work:
   - Copy examples from help text
   - Execute them
   **Expected**: Examples work as documented

**Pass Criteria**: All help text is accurate and examples are functional.

## Test Report Template

### Test Summary
- **Test Date**: 
- **Tester**: 
- **Environment**: (OS, Python version, Docker version)
- **Anvyl Version**: 

### Results
| Test Category | Total Tests | Passed | Failed | Notes |
|---------------|-------------|--------|--------|-------|
| Installation | | | | |
| Core Functionality | | | | |
| AI Agent | | | | |
| Web UI | | | | |
| Error Handling | | | | |
| Data Persistence | | | | |
| Performance | | | | |
| Documentation | | | | |

### Issues Found
1. **Issue**: Description
   **Severity**: High/Medium/Low
   **Reproducible**: Yes/No
   **Steps**: How to reproduce

### Recommendations
- List any recommendations for improvements
- Note any performance concerns
- Suggest additional test scenarios