import pytest
import tempfile
import shutil
import os
from pathlib import Path
from unittest.mock import Mock, MagicMock
import yaml


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def mock_config():
    """Provide a mock configuration dictionary."""
    return {
        'username': 'test@example.com',
        'password': 'test_password',
        'positions': ['Software Engineer', 'Python Developer'],
        'locations': ['New York', 'San Francisco'],
        'distance': 25,
        'outputFileDirectory': './output',
        'blacklistCompanies': ['Test Company'],
        'blackListTitles': ['Intern'],
        'experienceLevel': {
            'internship': False,
            'entry': True,
            'associate': True,
            'mid-senior level': True,
            'director': False,
            'executive': False
        }
    }


@pytest.fixture
def mock_config_file(temp_dir, mock_config):
    """Create a temporary config.yaml file."""
    config_path = temp_dir / "config.yaml"
    with open(config_path, 'w') as f:
        yaml.dump(mock_config, f)
    return config_path


@pytest.fixture
def mock_selenium_driver():
    """Provide a mock Selenium WebDriver."""
    driver = MagicMock()
    driver.current_url = "https://www.linkedin.com"
    driver.page_source = "<html><body>Test Page</body></html>"
    return driver


@pytest.fixture
def mock_webdriver_wait():
    """Provide a mock WebDriverWait."""
    wait = Mock()
    wait.until = Mock(return_value=Mock())
    return wait


@pytest.fixture
def sample_html():
    """Provide sample HTML for testing."""
    return """
    <html>
        <body>
            <div class="job-card">
                <h3>Software Engineer</h3>
                <span class="company">Tech Corp</span>
                <span class="location">New York, NY</span>
            </div>
        </body>
    </html>
    """


@pytest.fixture
def mock_csv_data():
    """Provide mock CSV data for testing."""
    return [
        {'Company': 'Tech Corp', 'Job Title': 'Software Engineer', 'Location': 'New York'},
        {'Company': 'Data Inc', 'Job Title': 'Data Scientist', 'Location': 'San Francisco'}
    ]


@pytest.fixture
def mock_browser_options():
    """Provide mock browser options."""
    options = Mock()
    options.add_argument = Mock()
    options.add_experimental_option = Mock()
    return options


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment variables before each test."""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def capture_logs():
    """Capture log messages during tests."""
    import logging
    from io import StringIO
    
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.DEBUG)
    
    logger = logging.getLogger()
    logger.addHandler(handler)
    
    yield log_capture
    
    logger.removeHandler(handler)


@pytest.fixture
def mock_time():
    """Mock time-related functions."""
    with pytest.mock.patch('time.sleep'):
        with pytest.mock.patch('time.time', return_value=1234567890):
            yield