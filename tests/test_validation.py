import pytest
import sys
import os
from pathlib import Path


class TestInfrastructureValidation:
    """Validation tests to ensure the testing infrastructure is properly set up."""

    def test_python_version(self):
        """Verify Python version is 3.8 or higher."""
        assert sys.version_info >= (3, 8), "Python 3.8 or higher is required"

    def test_project_structure(self):
        """Verify the project structure is correctly set up."""
        root_dir = Path(__file__).parent.parent
        
        # Check main project files exist
        assert (root_dir / "pyproject.toml").exists(), "pyproject.toml should exist"
        assert (root_dir / "README.md").exists(), "README.md should exist"
        assert (root_dir / "requirements.txt").exists(), "requirements.txt should exist"
        
        # Check test directories exist
        assert (root_dir / "tests").is_dir(), "tests directory should exist"
        assert (root_dir / "tests" / "unit").is_dir(), "tests/unit directory should exist"
        assert (root_dir / "tests" / "integration").is_dir(), "tests/integration directory should exist"
        
        # Check __init__.py files exist
        assert (root_dir / "tests" / "__init__.py").exists(), "tests/__init__.py should exist"
        assert (root_dir / "tests" / "unit" / "__init__.py").exists(), "tests/unit/__init__.py should exist"
        assert (root_dir / "tests" / "integration" / "__init__.py").exists(), "tests/integration/__init__.py should exist"

    def test_pytest_installed(self):
        """Verify pytest is installed and importable."""
        try:
            import pytest
            assert pytest.__version__, "pytest should have a version"
        except ImportError:
            pytest.fail("pytest is not installed")

    def test_pytest_plugins_installed(self):
        """Verify pytest plugins are installed."""
        try:
            import pytest_cov
            assert pytest_cov, "pytest-cov should be importable"
        except ImportError:
            pytest.fail("pytest-cov is not installed")
        
        try:
            import pytest_mock
            assert pytest_mock, "pytest-mock should be importable"
        except ImportError:
            pytest.fail("pytest-mock is not installed")

    def test_conftest_fixtures(self, temp_dir, mock_config, mock_selenium_driver):
        """Verify conftest fixtures are working."""
        # Test temp_dir fixture
        assert temp_dir.exists(), "temp_dir should exist"
        assert temp_dir.is_dir(), "temp_dir should be a directory"
        
        # Test mock_config fixture
        assert isinstance(mock_config, dict), "mock_config should be a dictionary"
        assert 'username' in mock_config, "mock_config should have username"
        assert 'positions' in mock_config, "mock_config should have positions"
        
        # Test mock_selenium_driver fixture
        assert hasattr(mock_selenium_driver, 'current_url'), "mock driver should have current_url"
        assert mock_selenium_driver.current_url == "https://www.linkedin.com"

    @pytest.mark.unit
    def test_unit_marker(self):
        """Test that unit test marker works."""
        assert True, "Unit test marker should work"

    @pytest.mark.integration
    def test_integration_marker(self):
        """Test that integration test marker works."""
        assert True, "Integration test marker should work"

    @pytest.mark.slow
    def test_slow_marker(self):
        """Test that slow test marker works."""
        assert True, "Slow test marker should work"

    def test_coverage_configuration(self):
        """Verify coverage is properly configured."""
        root_dir = Path(__file__).parent.parent
        pyproject = root_dir / "pyproject.toml"
        
        assert pyproject.exists(), "pyproject.toml should exist"
        
        content = pyproject.read_text()
        assert "[tool.coverage.run]" in content, "Coverage run configuration should exist"
        assert "[tool.coverage.report]" in content, "Coverage report configuration should exist"
        assert "cov-fail-under=80" in content, "Coverage threshold should be set to 80%"

    def test_poetry_scripts(self):
        """Verify Poetry scripts are configured."""
        root_dir = Path(__file__).parent.parent
        pyproject = root_dir / "pyproject.toml"
        
        content = pyproject.read_text()
        assert "[tool.poetry.scripts]" in content, "Poetry scripts section should exist"
        assert 'test = "pytest:main"' in content, "test script should be configured"
        assert 'tests = "pytest:main"' in content, "tests script should be configured"