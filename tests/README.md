# Anvyl Test Suite

This directory contains comprehensive tests for the Anvyl infrastructure orchestration platform.

## Test Structure

```
tests/
├── unit/                   # Unit tests for individual components
│   ├── test_cli.py        # CLI functionality tests
│   ├── test_host_agent.py # AI agent tests
│   ├── test_infrastructure_service.py # Infrastructure service tests
│   ├── test_agent_tools.py # Agent communication tests
│   └── test_models.py     # Database model tests
├── integration/           # Integration tests
│   └── test_cli_integration.py # End-to-end CLI workflows
├── manual/               # Manual test procedures
│   └── test_installation.md # Installation and user workflow tests
└── conftest.py          # Shared test fixtures
```

## Running Tests

### Quick Start

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run all tests
python scripts/run_tests.py all

# Run specific test types
python scripts/run_tests.py unit      # Unit tests only
python scripts/run_tests.py integration # Integration tests only
python scripts/run_tests.py lint     # Code quality checks
python scripts/run_tests.py smoke    # Quick smoke tests
```

### Using pytest directly

```bash
# Run all unit tests with coverage
pytest tests/unit/ --cov=anvyl --cov-report=html

# Run specific test file
pytest tests/unit/test_cli.py -v

# Run tests with specific markers
pytest -m "not slow" 

# Run integration tests
pytest tests/integration/ -v
```

### Test Runner Script

The `scripts/run_tests.py` script provides comprehensive test management:

```bash
# Setup test environment
python scripts/run_tests.py setup

# Run smoke tests (quick validation)
python scripts/run_tests.py smoke

# Run all automated tests with coverage
python scripts/run_tests.py all -v

# Generate comprehensive test report
python scripts/run_tests.py report

# Clean test artifacts
python scripts/run_tests.py clean

# Show manual test procedures
python scripts/run_tests.py manual
```

## Test Categories

### Unit Tests

Unit tests focus on testing individual components in isolation:

- **CLI Tests** (`test_cli.py`): Test all CLI commands with mocked dependencies
- **Host Agent Tests** (`test_host_agent.py`): Test AI agent functionality, model integration, and query processing
- **Infrastructure Service Tests** (`test_infrastructure_service.py`): Test host and container management
- **Agent Tools Tests** (`test_agent_tools.py`): Test inter-agent communication
- **Model Tests** (`test_models.py`): Test database models and operations

**Key Features:**
- Comprehensive mocking of external dependencies
- Fast execution (should complete in under 30 seconds)
- High code coverage (target: >90%)
- Isolated testing of business logic

### Integration Tests

Integration tests verify component interactions and end-to-end workflows:

- **CLI Integration** (`test_cli_integration.py`): Test complete CLI workflows with real database
- **Agent Communication**: Test multi-agent scenarios
- **Database Integration**: Test with real SQLite database
- **Service Integration**: Test service interactions

**Key Features:**
- Real database interactions (temporary test databases)
- Cross-component communication testing
- Realistic data scenarios
- Error handling validation

### Manual Tests

Manual tests require human interaction and real infrastructure:

- **Installation Procedures**: Fresh installation testing
- **User Workflows**: Complete user scenarios
- **Performance Testing**: Real-world performance validation
- **Web UI Testing**: Browser-based interface testing
- **Multi-host Scenarios**: Network-based testing

## Test Configuration

### pytest.ini Settings

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --verbose
    --tb=short
    --strict-markers
    --cov=anvyl
    --cov-report=term-missing
    --cov-report=html:htmlcov
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
    manual: marks tests as manual test scripts
```

### Coverage Configuration

Coverage reporting is configured to:
- Generate HTML reports in `htmlcov/` directory
- Show missing lines in terminal output
- Target >90% code coverage
- Exclude generated files and test files

## Writing New Tests

### Unit Test Guidelines

1. **Test Structure**: Use descriptive class and method names
   ```python
   class TestCLIHostManagement:
       def test_add_host_success(self):
           """Test successfully adding a host."""
   ```

2. **Mocking**: Mock external dependencies
   ```python
   @patch('anvyl.cli.get_infrastructure')
   def test_command(self, mock_get_infra):
       mock_service = Mock()
       mock_get_infra.return_value = mock_service
   ```

3. **Assertions**: Use descriptive assertions
   ```python
   assert result.exit_code == 0
   assert "Host added successfully" in result.stdout
   ```

### Integration Test Guidelines

1. **Real Dependencies**: Use real databases and services where appropriate
2. **Cleanup**: Ensure proper cleanup of test artifacts
3. **Isolation**: Each test should be independent
4. **Performance**: Keep integration tests reasonably fast

### Manual Test Guidelines

1. **Clear Steps**: Provide step-by-step instructions
2. **Expected Results**: Define clear success criteria
3. **Prerequisites**: List all requirements
4. **Troubleshooting**: Include common issues and solutions

## Continuous Integration

The test suite is designed for CI/CD integration:

```yaml
# Example GitHub Actions workflow
- name: Run Tests
  run: |
    pip install -e ".[dev]"
    python scripts/run_tests.py all
    
- name: Upload Coverage
  uses: codecov/codecov-action@v1
  with:
    file: ./coverage.xml
```

## Test Data and Fixtures

### Shared Fixtures (conftest.py)

```python
@pytest.fixture
def mock_docker_client():
    """Fixture for mocked Docker client."""
    
@pytest.fixture
def temp_database():
    """Fixture for temporary test database."""
```

### Test Data Patterns

- Use factories for generating test data
- Prefer small, focused test datasets
- Clean up test data after each test
- Use realistic data that matches production patterns

## Performance Considerations

### Test Execution Times

- **Unit Tests**: < 30 seconds total
- **Integration Tests**: < 2 minutes total
- **Smoke Tests**: < 10 seconds total

### Parallel Execution

Tests are designed to support parallel execution:

```bash
# Run tests in parallel
pytest -n auto tests/unit/
```

## Debugging Tests

### Common Issues

1. **Import Errors**: Ensure `pip install -e ".[dev]"` is run
2. **Mock Issues**: Verify mock paths match actual import paths
3. **Async Tests**: Use `pytest-asyncio` for async test functions
4. **Database Tests**: Ensure proper cleanup of test databases

### Debugging Commands

```bash
# Run single test with verbose output
pytest tests/unit/test_cli.py::TestCLIHostManagement::test_add_host_success -v -s

# Run with pdb debugger
pytest tests/unit/test_cli.py --pdb

# Show test coverage for specific module
pytest tests/unit/ --cov=anvyl.cli --cov-report=term-missing
```

## Contributing

When adding new functionality:

1. **Write Tests First**: Follow TDD when possible
2. **Test Categories**: Add unit tests for all new functions/classes
3. **Integration Tests**: Add integration tests for new workflows
4. **Manual Tests**: Update manual procedures for user-facing changes
5. **Documentation**: Update this README for new testing patterns

## Test Maintenance

### Regular Tasks

- Review and update test dependencies
- Remove obsolete tests
- Update manual test procedures
- Monitor test execution times
- Review code coverage reports

### Quality Metrics

- **Code Coverage**: Target >90% for unit tests
- **Test Speed**: Unit tests should remain fast
- **Reliability**: Tests should be deterministic
- **Maintainability**: Tests should be easy to understand and modify