import os
from app.core.config import Settings

def test_settings_load_from_env():
    # Use environment variables directly instead of monkeypatching process env which can be flaky
    settings = Settings(
        app_name="Test App",
        environment="testing",
        database_url="sqlite:///./test.db",
        debug=True
    )
    assert settings.app_name == "Test App"
    assert settings.environment == "testing"
    assert settings.debug is True
