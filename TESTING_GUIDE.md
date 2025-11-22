# Testing Guide - How to Use Your Test Folder

## ✅ What's Been Set Up

Your `tests/` folder is now fully configured with:

1. **pytest** - Testing framework
2. **pytest-cov** - Code coverage reporting
3. **pytest-mock** - Mocking utilities
4. **Test files** for all major modules:
   - `test_router.py` - Message routing tests
   - `test_pandas_agent.py` - Data agent tests
   - `test_pandasai_service.py` - PandasAI integration tests
5. **conftest.py** - Shared fixtures and configuration
6. **pytest.ini** - Pytest configuration

## 🚀 Quick Start

### Run All Tests
```bash
poetry run pytest
```

### Run Specific Test File
```bash
poetry run pytest tests/test_router.py
```

### Run with Coverage Report
```bash
poetry run pytest --cov=core --cov-report=html
```
Then open `htmlcov/index.html` in your browser to see coverage.

### Run with Verbose Output
```bash
poetry run pytest -v
```

## 📊 Current Test Status

**31 tests** covering:
- ✅ SQL safety validation (6 tests)
- ✅ SQL extraction (4 tests)
- ✅ Data question handling (2 tests)
- ✅ Prediction functions (2 tests)
- ✅ SQL query execution (3 tests)
- ✅ PandasAI configuration (2 tests)
- ✅ LLM functions (2 tests)
- ✅ PandasAI queries (1 test)
- ✅ Router functionality (9 tests)

## 📝 Writing Your Own Tests

### Example: Test a New Function

```python
# tests/test_my_module.py
import pytest
from core.my_module import my_function

def test_my_function_success():
    """Test that my_function works correctly."""
    result = my_function("input")
    assert result == "expected_output"

def test_my_function_error():
    """Test error handling."""
    with pytest.raises(ValueError):
        my_function(None)
```

### Using Fixtures

```python
def test_with_database(mock_database_connection):
    """Test using the database fixture."""
    # mock_database_connection is automatically provided
    result = function_that_uses_db()
    assert result is not None
```

### Mocking External Calls

```python
from unittest.mock import patch

@patch('core.module.external_api_call')
def test_with_mock(mock_api):
    """Test with mocked external API."""
    mock_api.return_value = {"status": "success"}
    result = function_that_calls_api()
    assert result["status"] == "success"
```

## 🎯 Test Best Practices

1. **Test one thing** - Each test should verify one behavior
2. **Descriptive names** - `test_user_login_success()` not `test1()`
3. **Arrange-Act-Assert** - Structure tests clearly
4. **Mock external dependencies** - Don't hit real APIs/databases
5. **Test edge cases** - Include error conditions
6. **Keep tests fast** - Unit tests should run quickly

## 📁 Test File Structure

```
tests/
├── __init__.py              # Makes tests a package
├── conftest.py              # Shared fixtures (auto-loaded)
├── test_router.py           # Router tests
├── test_pandas_agent.py     # Data agent tests
├── test_pandasai_service.py # PandasAI tests
└── README.md                # Detailed testing docs
```

## 🔧 Common Commands

| Command | What It Does |
|---------|-------------|
| `poetry run pytest` | Run all tests |
| `poetry run pytest -v` | Verbose output |
| `poetry run pytest -k "router"` | Run tests matching "router" |
| `poetry run pytest tests/test_router.py::TestRouter::test_help_intent` | Run specific test |
| `poetry run pytest --cov=core` | Run with coverage |
| `poetry run pytest --cov=core --cov-report=html` | Generate HTML coverage report |
| `poetry run pytest -x` | Stop on first failure |
| `poetry run pytest --lf` | Run last failed tests only |

## 🐛 Debugging Tests

### See What's Being Tested
```bash
poetry run pytest --collect-only
```

### Run with Print Statements
```bash
poetry run pytest -s
```

### Run with Debugger
```bash
poetry run pytest --pdb
```

## 📈 Coverage Reports

### Generate Coverage Report
```bash
poetry run pytest --cov=core --cov-report=term-missing
```

### HTML Coverage Report
```bash
poetry run pytest --cov=core --cov-report=html
# Then open htmlcov/index.html
```

### See What's Not Covered
```bash
poetry run pytest --cov=core --cov-report=term-missing | grep -E "TOTAL|Missing"
```

## 🎨 Test Markers

You can mark tests for selective running:

```python
@pytest.mark.slow
def test_slow_function():
    """This test takes a long time."""
    pass

@pytest.mark.requires_api
def test_api_function():
    """This test requires API access."""
    pass
```

Run only fast tests:
```bash
poetry run pytest -m "not slow"
```

## 🔄 Continuous Integration

Add to your CI/CD pipeline:
```yaml
# .github/workflows/test.yml
- name: Run tests
  run: poetry run pytest --cov=core --cov-report=xml
```

## 📚 Learn More

- [pytest documentation](https://docs.pytest.org/)
- [pytest-mock documentation](https://pytest-mock.readthedocs.io/)
- See `tests/README.md` for detailed examples

## 🎉 Next Steps

1. **Run the tests** to see what's covered
2. **Add tests** for new features as you build them
3. **Check coverage** to find untested code
4. **Fix failing tests** (2 tests need attention)
5. **Run tests before committing** to catch issues early

Happy testing! 🧪

