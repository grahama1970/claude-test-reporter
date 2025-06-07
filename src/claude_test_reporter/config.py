"""
Module: config.py
Description: Configuration management and settings

External Dependencies:
- dataclasses: [Documentation URL]
- typer: [Documentation URL]
- rich: [Documentation URL]

Sample Input:
>>> # Add specific examples based on module functionality

Expected Output:
>>> # Add expected output examples

Example Usage:
>>> # Add usage examples
"""

#!/usr/bin/env python3
"""
Configuration management for Claude Test Reporter

Purpose: Handle environment variables and API keys for LLM integration
Features: Secure API key handling, environment validation, config loading
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class LLMConfig:
    """Configuration for LLM integration."""
    api_key: Optional[str] = None
    model: str = "gemini-2.5-pro"
    temperature: float = 0.1
    max_tokens: int = 4096
    timeout: int = 30


class Config:
    """Central configuration management."""
    
    def __init__(self):
        self.config_file = Path.home() / ".claude-test-reporter" / "config.json"
        self.env_file = Path.cwd() / ".env"
        self._config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from multiple sources."""
        config = {}
        
        # 1. Load from config file if exists
        if self.config_file.exists():
            with open(self.config_file) as f:
                config.update(json.load(f))
        
        # 2. Load from .env file if exists
        if self.env_file.exists():
            config.update(self._load_env_file())
        
        # 3. Override with environment variables
        config.update(self._load_env_vars())
        
        return config
    
    def _load_env_file(self) -> Dict[str, str]:
        """Load variables from .env file."""
        env_vars = {}
        with open(self.env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip().strip('"\'')
        return env_vars
    
    def _load_env_vars(self) -> Dict[str, str]:
        """Load relevant environment variables."""
        env_vars = {}
        
        # LLM-related variables
        llm_keys = [
            "GEMINI_API_KEY",
            "GOOGLE_API_KEY",
            "ANTHROPIC_API_KEY",
            "OPENAI_API_KEY",
            "LLM_MODEL",
            "LLM_TEMPERATURE",
            "LLM_MAX_TOKENS"
        ]
        
        for key in llm_keys:
            if key in os.environ:
                env_vars[key] = os.environ[key]
        
        # Claude test reporter specific
        if "CLAUDE_TEST_REPORTER_CONFIG" in os.environ:
            env_vars["CLAUDE_TEST_REPORTER_CONFIG"] = os.environ["CLAUDE_TEST_REPORTER_CONFIG"]
        
        return env_vars
    
    def get_llm_config(self) -> LLMConfig:
        """Get LLM configuration."""
        # Try different API key sources
        api_key = (
            self._config.get("GEMINI_API_KEY") or
            self._config.get("GOOGLE_API_KEY") or
            self._config.get("api_key")
        )
        
        return LLMConfig(
            api_key=api_key,
            model=self._config.get("LLM_MODEL", "gemini-2.5-pro"),
            temperature=float(self._config.get("LLM_TEMPERATURE", 0.1)),
            max_tokens=int(self._config.get("LLM_MAX_TOKENS", 4096)),
            timeout=int(self._config.get("LLM_TIMEOUT", 30))
        )
    
    def validate_llm_config(self) -> tuple[bool, str]:
        """Validate LLM configuration is properly set."""
        llm_config = self.get_llm_config()
        
        if not llm_config.api_key:
            return False, "No API key found. Set GEMINI_API_KEY or GOOGLE_API_KEY environment variable."
        
        if llm_config.temperature < 0 or llm_config.temperature > 1:
            return False, f"Invalid temperature: {llm_config.temperature}. Must be between 0 and 1."
        
        return True, "LLM configuration is valid."
    
    def save_config(self, config_data: Dict[str, Any]) -> None:
        """Save configuration to file."""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        self._config[key] = value


def create_env_template() -> str:
    """Create a template .env file."""
    template = """# Claude Test Reporter Environment Configuration

# LLM API Keys (set one of these)
GEMINI_API_KEY=your-gemini-api-key-here
# GOOGLE_API_KEY=your-google-api-key-here
# ANTHROPIC_API_KEY=your-anthropic-api-key-here
# OPENAI_API_KEY=your-openai-api-key-here

# LLM Configuration
LLM_MODEL=gemini-2.5-pro
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=4096
LLM_TIMEOUT=30

# Report Storage
REPORT_STORAGE_PATH=./reports
HISTORY_RETENTION_DAYS=90

# Monitoring
ENABLE_HALLUCINATION_MONITORING=true
HALLUCINATION_LOG_PATH=./logs/hallucinations.log

# GitHub Integration
GITHUB_TOKEN=your-github-token-here
GITHUB_REPO=your-org/your-repo

# Notification Settings
SLACK_WEBHOOK_URL=
EMAIL_NOTIFICATIONS=false
"""
    return template


def setup_environment() -> None:
    """Interactive setup for environment configuration."""
    import typer
    from rich.console import Console
    from rich.prompt import Prompt, Confirm
    
    console = Console()
    
    console.print("[bold cyan]Claude Test Reporter - Environment Setup[/bold cyan]\n")
    
    # Check if .env exists
    env_file = Path.cwd() / ".env"
    if env_file.exists():
        if not Confirm.ask("A .env file already exists. Overwrite?"):
            console.print("[yellow]Setup cancelled.[/yellow]")
            return
    
    # Collect API key
    console.print("Choose your LLM provider:")
    console.print("1. Google (Gemini)")
    console.print("2. Anthropic (Claude)")
    console.print("3. OpenAI (GPT)")
    
    choice = Prompt.ask("Enter choice", choices=["1", "2", "3"], default="1")
    
    api_key = None
    if choice == "1":
        api_key = Prompt.ask("Enter your Gemini API key", password=True)
        key_name = "GEMINI_API_KEY"
    elif choice == "2":
        api_key = Prompt.ask("Enter your Anthropic API key", password=True)
        key_name = "ANTHROPIC_API_KEY"
    else:
        api_key = Prompt.ask("Enter your OpenAI API key", password=True)
        key_name = "OPENAI_API_KEY"
    
    # Create .env content
    env_content = create_env_template()
    env_content = env_content.replace(f"{key_name}=your-", f"{key_name}={api_key[:8]}...")
    
    # Additional settings
    if Confirm.ask("Enable hallucination monitoring?", default=True):
        env_content = env_content.replace("ENABLE_HALLUCINATION_MONITORING=true", "ENABLE_HALLUCINATION_MONITORING=true")
    else:
        env_content = env_content.replace("ENABLE_HALLUCINATION_MONITORING=true", "ENABLE_HALLUCINATION_MONITORING=false")
    
    # Save .env file
    env_file.write_text(env_content)
    console.print(f"\n[green]✓[/green] Created .env file: {env_file}")
    
    # Add to .gitignore
    gitignore = Path.cwd() / ".gitignore"
    if gitignore.exists():
        content = gitignore.read_text()
        if ".env" not in content:
            gitignore.write_text(content + "\n.env\n")
            console.print("[green]✓[/green] Added .env to .gitignore")
    
    console.print("\n[bold green]Setup complete![/bold green]")
    console.print("You can now use LLM features with claude-test-reporter.")


if __name__ == "__main__":
    # Test configuration
    config = Config()
    
    print("Testing configuration loading...")
    llm_config = config.get_llm_config()
    print(f"  Model: {llm_config.model}")
    print(f"  Temperature: {llm_config.temperature}")
    print(f"  API Key: {'Set' if llm_config.api_key else 'Not set'}")
    
    valid, message = config.validate_llm_config()
    print(f"\nValidation: {message}")
    
    if not valid:
        print("\nRun 'claude-test-reporter setup' to configure your environment.")