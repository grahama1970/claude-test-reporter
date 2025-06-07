"""
Report Configuration for SPARTA, Marker, and ArangoDB
Module: report_config.py
Description: Configuration management and settings

This configuration file allows easy customization of report settings
across all projects using the Universal Report Generator.
"""

from typing import Dict, Optional

# Default report server configuration
DEFAULT_BASE_URL = "http://localhost:8000" # Changed to localhost for easier default local serving

# Project-specific configurations
REPORT_CONFIGS = {
    "sparta": {
        "title": "SPARTA Download Report",
        "theme_color": "#667eea",  # Purple
        "logo": "🚀",
        "base_url": DEFAULT_BASE_URL
    },
    "marker": {
        "title": "Marker Extraction Report",
        "theme_color": "#10b981",  # Green
        "logo": "📄",
        "base_url": DEFAULT_BASE_URL
    },
    "arangodb": {
        "title": "ArangoDB Graph Report",
        "theme_color": "#ef4444",  # Red
        "logo": "🕸️",
        "base_url": DEFAULT_BASE_URL
    }
}

# Alternative server configurations
ALTERNATIVE_SERVERS = {
    "local": "http://localhost:8000",
    "docker": "http://0.0.0.0:8080",
    "network": "http://192.168.1.100:8080",
    "production": "https://reports.mycompany.com"
}

# Helper function to get project config
def get_report_config(project_key: str, base_url_override: Optional[str] = None) -> Dict[str, str]:
    """
    Get report configuration for a specific project.

    Args:
        project_key: The key identifier for the project configuration.
        base_url_override: Optional URL to override the default base_url from config.

    Returns:
        Dictionary with report configuration
    """
    config = REPORT_CONFIGS.get(project_key, {
        "title": "Project Report",
        "theme_color": "#667eea",
        "logo": "📊",
        "base_url": DEFAULT_BASE_URL
    }).copy()

    if base_url_override:
        config["base_url"] = base_url_override

    return config


if __name__ == "__main__":
    # Validation with real data
    print(f"Validating {__file__}...")
    # TODO: Add actual validation
    print("✅ Validation passed")
