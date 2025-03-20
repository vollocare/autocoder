"""
Configuration management module for the Autocoder tool.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

DEFAULT_CONFIG = {
    "model": {
        "api_endpoint": "http://localhost:11434/v1",
        "temperature": 0.6,
        "top_p": 0.9,
        "max_tokens": 8192,
        "quantize": "none",
        "seed": None,
        "system_prompt": None,
    },
    "max_test_iterations": 50,
    "verbose": True,
    "colors_enabled": True,
}

class Config:
    """Configuration manager for the Autocoder tool."""
    
    def __init__(self):
        self.config = DEFAULT_CONFIG.copy()
        self._load_config()
        
    def _load_config(self):
        """Load configuration from files and environment variables."""
        # Load global config
        global_config_path = Path.home() / ".autocoder.yaml"
        if global_config_path.exists():
            with open(global_config_path, "r") as f:
                global_config = yaml.safe_load(f)
                if global_config:
                    self._merge_config(global_config)
        
        # Load project config
        project_config_path = Path.cwd() / ".autocoder.yaml"
        if project_config_path.exists():
            with open(project_config_path, "r") as f:
                project_config = yaml.safe_load(f)
                if project_config:
                    self._merge_config(project_config)
        
        # Load environment variables
        self._load_from_env()
    
    def _merge_config(self, new_config: Dict[str, Any]):
        """Merge new configuration with existing one."""
        for key, value in new_config.items():
            if isinstance(value, dict) and key in self.config and isinstance(self.config[key], dict):
                self.config[key].update(value)
            else:
                self.config[key] = value
    
    def _load_from_env(self):
        """Load configuration from environment variables."""
        # Handle model configuration
        if "AUTOCODER_API_ENDPOINT" in os.environ:
            self.config["model"]["api_endpoint"] = os.environ["AUTOCODER_API_ENDPOINT"]
        
        if "AUTOCODER_TEMPERATURE" in os.environ:
            self.config["model"]["temperature"] = float(os.environ["AUTOCODER_TEMPERATURE"])
        
        if "AUTOCODER_TOP_P" in os.environ:
            self.config["model"]["top_p"] = float(os.environ["AUTOCODER_TOP_P"])
        
        if "AUTOCODER_MAX_TOKENS" in os.environ:
            self.config["model"]["max_tokens"] = int(os.environ["AUTOCODER_MAX_TOKENS"])
        
        if "AUTOCODER_QUANTIZE" in os.environ:
            self.config["model"]["quantize"] = os.environ["AUTOCODER_QUANTIZE"]
        
        if "AUTOCODER_SEED" in os.environ:
            self.config["model"]["seed"] = int(os.environ["AUTOCODER_SEED"])
        
        if "AUTOCODER_SYSTEM_PROMPT" in os.environ:
            self.config["model"]["system_prompt"] = os.environ["AUTOCODER_SYSTEM_PROMPT"]
        
        # Handle other configurations
        if "AUTOCODER_MAX_TEST_ITERATIONS" in os.environ:
            self.config["max_test_iterations"] = int(os.environ["AUTOCODER_MAX_TEST_ITERATIONS"])
        
        if "AUTOCODER_VERBOSE" in os.environ:
            self.config["verbose"] = os.environ["AUTOCODER_VERBOSE"].lower() in ("true", "1", "yes")
        
        if "AUTOCODER_COLORS_ENABLED" in os.environ:
            self.config["colors_enabled"] = os.environ["AUTOCODER_COLORS_ENABLED"].lower() in ("true", "1", "yes")
    
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get a configuration value."""
        keys = key.split(".")
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """Set a configuration value."""
        keys = key.split(".")
        target = self.config
        
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]
        
        target[keys[-1]] = value
    
    def save(self, global_config: bool = False):
        """Save the current configuration to a file."""
        if global_config:
            config_path = Path.home() / ".autocoder.yaml"
        else:
            config_path = Path.cwd() / ".autocoder.yaml"
        
        with open(config_path, "w") as f:
            yaml.dump(self.config, f, default_flow_style=False)


# Create a singleton instance
config = Config() 