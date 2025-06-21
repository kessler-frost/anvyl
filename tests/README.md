# Anvyl Tests

This directory contains all tests for the Anvyl project, organized by type.

## Directory Structure

```
tests/
├── unit/                    # Unit tests (fast, isolated)
│   ├── test_agent.py       # Agent unit tests
│   ├── test_models.py      # Database model tests
│   ├── test_client.py      # Infrastructure client tests
│   └── test_api.py         # API unit tests
├── integration/             # Integration tests (slower, test interactions)
│   ├── test_agent_integration.py
│   └── test_infra_integration.py
├── manual/                  # Manual test scripts
│   ├── test_async_agent.py # Manual async agent test
│   └── test_full_workflow.py
├── conftest.py             # Shared pytest configuration
└── __init__.py
```

## Test Types

### Unit Tests (`tests/unit/`)
- **Purpose**: Test individual components in isolation
- **Speed**: Fast (< 1 second each)
- **Dependencies**: Minimal, mostly mocked
- **Run with**: `pytest tests/unit/`

### Integration Tests (`tests/integration/`)
- **Purpose**: Test how components work together
- **Speed**: Slower (may require external services)
- **Dependencies**: May require actual services running
- **Run with**: `pytest tests/integration/`

### Manual Tests (`tests/manual/`)
- **Purpose**: Manual verification scripts
- **Speed**: Variable (may require user interaction)
- **Dependencies**: Often require full system setup
- **Run with**: `python tests/manual/test_async_agent.py`

## Running Tests

### All Tests
```bash
pytest
```

### Unit Tests Only
```bash
pytest tests/unit/
```

### Integration Tests Only
```bash
pytest tests/integration/
```

### Skip Slow Tests
```bash
pytest -m "not slow"
```

### Run with Coverage
```bash
pytest --cov=anvyl --cov-report=html
```

## Manual Test Scripts

Manual test scripts are not part of the automated test suite. They're useful for:

- Verifying functionality with real services
- Debugging issues
- Demonstrating features
- Testing full workflows

To run a manual test:
```bash
python tests/manual/test_async_agent.py
```

## Adding New Tests

### Unit Tests
- Place in `tests/unit/`
- Use descriptive names: `test_<component>_<functionality>.py`
- Mock external dependencies
- Keep tests fast and isolated

### Integration Tests
- Place in `tests/integration/`
- Mark with `@pytest.mark.integration`
- Test component interactions
- May require service setup

### Manual Tests
- Place in `tests/manual/`
- Include clear usage instructions
- Document required setup
- Make them runnable standalone