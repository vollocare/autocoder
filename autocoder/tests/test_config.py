"""
Tests for the configuration module.
"""

import os
import tempfile
from pathlib import Path
import pytest
import yaml

from autocoder.utils.config import Config, DEFAULT_CONFIG


def test_default_config():
    """Test that default configuration is loaded correctly."""
    config = Config()
    
    # Check that default values are set
    assert config.get("model.api_endpoint") == DEFAULT_CONFIG["model"]["api_endpoint"]
    assert config.get("model.temperature") == DEFAULT_CONFIG["model"]["temperature"]
    assert config.get("model.top_p") == DEFAULT_CONFIG["model"]["top_p"]
    assert config.get("max_test_iterations") == DEFAULT_CONFIG["max_test_iterations"]
    assert config.get("verbose") == DEFAULT_CONFIG["verbose"]
    assert config.get("colors_enabled") == DEFAULT_CONFIG["colors_enabled"]


def test_config_get_nonexistent():
    """Test getting a nonexistent configuration value."""
    config = Config()
    
    # Should return None for nonexistent key
    assert config.get("nonexistent_key") is None
    
    # Should return default value for nonexistent key if provided
    assert config.get("nonexistent_key", "default_value") == "default_value"


def test_config_set_and_get():
    """Test setting and getting configuration values."""
    config = Config()
    
    # Set and get simple value
    config.set("test_key", "test_value")
    assert config.get("test_key") == "test_value"
    
    # Set and get nested value
    config.set("nested.key", "nested_value")
    assert config.get("nested.key") == "nested_value"
    
    # Overwrite existing value
    original_temp = config.get("model.temperature")
    config.set("model.temperature", original_temp + 0.1)
    assert config.get("model.temperature") == original_temp + 0.1


def test_config_isolated():
    """Test configuration in an isolated environment without external config files."""
    # Use a temporary directory as home to avoid loading the real config
    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock the home directory and cwd to be our temp directory
        original_home = Path.home
        original_cwd = os.getcwd
        
        try:
            Path.home = lambda: Path(temp_dir)
            os.getcwd = lambda: temp_dir
            
            # Create a fresh config in the isolated environment
            config = Config()
            
            # Now we can test against the default values
            assert config.get("model.api_endpoint") == DEFAULT_CONFIG["model"]["api_endpoint"]
            assert config.get("model.temperature") == DEFAULT_CONFIG["model"]["temperature"]
            assert config.get("model.top_p") == DEFAULT_CONFIG["model"]["top_p"]
            assert config.get("max_test_iterations") == DEFAULT_CONFIG["max_test_iterations"]
            assert config.get("verbose") == DEFAULT_CONFIG["verbose"]
            assert config.get("colors_enabled") == DEFAULT_CONFIG["colors_enabled"]
        
        finally:
            # Restore original functions
            Path.home = original_home
            os.getcwd = original_cwd


def test_config_save_and_load():
    """Test saving and loading configuration."""
    # Create a temporary directory for the config file
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir) / ".autocoder.yaml"
        
        # Mock the home directory and cwd to be our temp directory
        original_home = Path.home
        original_cwd = os.getcwd
        
        try:
            Path.home = lambda: Path(temp_dir)
            os.getcwd = lambda: temp_dir
            
            # Create a new config in the isolated environment
            config1 = Config()
            test_temp = 0.9
            test_key = "test_value"
            
            config1.set("model.temperature", test_temp)
            config1.set("test_key", test_key)
            
            # Save to the temporary file
            config1.save(global_config=True)
            
            # Verify file was created and contains expected values
            assert temp_path.exists()
            
            with open(temp_path, "r") as f:
                saved_config = yaml.safe_load(f)
            
            assert saved_config["model"]["temperature"] == test_temp
            assert saved_config["test_key"] == test_key
            
            # Create a new config which should load from the file
            config2 = Config()
            assert config2.get("model.temperature") == test_temp
            assert config2.get("test_key") == test_key
        
        finally:
            # Restore original functions
            Path.home = original_home
            os.getcwd = original_cwd


def test_config_environment_variables(monkeypatch):
    """Test loading configuration from environment variables."""
    # Use a temporary directory to avoid interference from real config files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock the home directory and cwd to be our temp directory
        original_home = Path.home
        original_cwd = os.getcwd
        
        try:
            Path.home = lambda: Path(temp_dir)
            os.getcwd = lambda: temp_dir
            
            # Set environment variables
            monkeypatch.setenv("AUTOCODER_API_ENDPOINT", "http://test-api.local")
            monkeypatch.setenv("AUTOCODER_TEMPERATURE", "0.75")
            monkeypatch.setenv("AUTOCODER_MAX_TEST_ITERATIONS", "100")
            monkeypatch.setenv("AUTOCODER_VERBOSE", "false")
            
            # Create config which should load from env vars
            config = Config()
            
            # Check that values from environment variables are used
            assert config.get("model.api_endpoint") == "http://test-api.local"
            assert config.get("model.temperature") == 0.75
            assert config.get("max_test_iterations") == 100
            assert config.get("verbose") is False
        
        finally:
            # Restore original functions
            Path.home = original_home
            os.getcwd = original_cwd 