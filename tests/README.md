# Testing Guide

This directory contains tests for the Slackbot application.

## Test Structure

```
tests/
├── __init__.py              # Makes tests a Python package
├── conftest.py              # Shared fixtures and configuration
├── test_router.py           # Tests for message routing
├── test_pandas_agent.py     # Tests for data agent functions
└── test_pandasai_service.py # Tests for PandasAI integration
```

## Running Tests

### Run All Tests
```bash
poetry run pytest
```

### Run Specific Test File
```bash
poetry run pytest tests/test_router.py
```

### Run Specific Test
```bash
poetry run pytest tests/test_router.py::TestRouter::test_help_intent
```

### Run with Verbose Output
```bash
poetry run pytest -v
```

### Run with Coverage Report
```bash
poetry run pytest --cov=core --cov-report=html
```

## Test Categories

Tests are organized by module:
- **test_router.py**: Message routing and intent classification
- **test_pandas_agent.py**: Data queries, predictions, SQL execution
- **test_pandasai_service.py**: PandasAI integration and LLM functions

## Writing New Tests

### Basic Test Structure

```python
import pytest
from core.module import function

def test_function_name():
    """Test description."""
    result = function("input")
    assert result == "expected_output"
```

### Using Fixtures

```python
def test_with_fixture(mock_env_vars):
    """Test using environment variable fixture."""
    # mock_env_vars is automatically provided
    result = function_that_uses_env()
    assert result is not None
```

### Mocking External Dependencies

```python
from unittest.mock import patch

@patch('core.module.external_function')
def test_with_mock(mock_external):
    """Test with mocked external dependency."""
    mock_external.return_value = "mocked_result"
    result = function_that_calls_external()
    assert result == "expected"
```

## Test Best Practices

1. **Test one thing at a time** - Each test should verify one behavior
2. **Use descriptive names** - Test names should explain what they test
3. **Arrange-Act-Assert** - Structure tests clearly
4. **Mock external dependencies** - Don't hit real databases/APIs in unit tests
5. **Keep tests fast** - Unit tests should run quickly
6. **Test edge cases** - Include tests for error conditions

## Example Test

```python
def test_safe_sql_query():
    """Test that SELECT queries are considered safe."""
    from core.subsystem_2.pandas_agent import _is_safe_sql_query
    
    # Arrange
    safe_query = "SELECT * FROM users"
    
    # Act
    result = _is_safe_sql_query(safe_query)
    
    # Assert
    assert result is True
```

## Continuous Integration

Tests should be run:
- Before committing code
- In CI/CD pipeline
- Before deploying

## Troubleshooting

### Import Errors
Make sure you're running tests from the project root:
```bash
cd /path/to/project
poetry run pytest
```

### Database Connection Errors
Use mocks for database connections in unit tests. See `conftest.py` for examples.

### Missing Dependencies
Install test dependencies:
```bash
poetry install --with dev
```

