"""
Configuration loader for environment-aware settings
Loads configuration from credentials/config.{env}.json based on ENV environment variable
"""
import os
import json
import logging
from typing import Dict, Any
from pathlib import Path

logger = logging.getLogger('EmailReader.Config')

# Cache for loaded configuration
_config_cache: Dict[str, Any] | None = None
_service_account_temp_path: str | None = None


def get_environment() -> str:
    """
    Get current environment from ENV variable

    Returns:
        str: Environment name ('dev' or 'prod'), defaults to 'dev'
    """
    env = os.getenv('ENV', 'dev')
    logger.debug("Environment: %s", env)
    return env


def load_config(force_reload: bool = False) -> Dict[str, Any]:
    """
    Load configuration based on ENV environment variable
    Configuration is cached after first load

    Args:
        force_reload: If True, reload config even if cached

    Returns:
        dict: Configuration dictionary

    Raises:
        FileNotFoundError: If config file doesn't exist
        json.JSONDecodeError: If config file is invalid JSON
    """
    global _config_cache

    # Return cached config if available
    if _config_cache is not None and not force_reload:
        logger.debug("Returning cached configuration")
        return _config_cache

    env = get_environment()
    config_file = os.path.join(
        os.getcwd(), 'credentials', f'config.{env}.json'
    )

    logger.info("Loading configuration from: %s", config_file)

    if not os.path.exists(config_file):
        logger.error("Configuration file not found: %s", config_file)
        raise FileNotFoundError(
            f"Configuration file not found: {config_file}\n"
            f"Please create credentials/config.{env}.json or set ENV variable"
        )

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            logger.debug(
                "Configuration loaded successfully, top-level keys: %s",
                list(config.keys())
            )
            _config_cache = config
            return config

    except json.JSONDecodeError as e:
        logger.error("Invalid JSON in config file %s: %s", config_file, e)
        raise
    except Exception as e:
        logger.error("Error loading config file %s: %s", config_file, e)
        raise


def get_service_account_path() -> str:
    """
    Get path to Google service account credentials
    Extracts service account from config and writes to temporary file

    Returns:
        str: Path to service account JSON file

    Raises:
        KeyError: If google_drive.service_account not found in config
        FileNotFoundError: If config file doesn't exist
    """
    global _service_account_temp_path

    # Return cached path if available
    if _service_account_temp_path is not None:
        if os.path.exists(_service_account_temp_path):
            logger.debug("Using cached service account path: %s", _service_account_temp_path)
            return _service_account_temp_path

    config = load_config()

    # Check if service_account exists in config
    if 'google_drive' not in config:
        raise KeyError("'google_drive' section not found in configuration")

    if 'service_account' not in config['google_drive']:
        raise KeyError("'google_drive.service_account' not found in configuration")

    sa_data = config['google_drive']['service_account']

    # Create credentials directory if it doesn't exist
    creds_dir = os.path.join(os.getcwd(), 'credentials')
    os.makedirs(creds_dir, exist_ok=True)

    # Write service account to temporary file
    temp_path = os.path.join(creds_dir, '.service-account-temp.json')
    logger.debug("Writing service account to temporary file: %s", temp_path)

    with open(temp_path, 'w', encoding='utf-8') as f:
        json.dump(sa_data, f, indent=2)

    _service_account_temp_path = temp_path
    return temp_path


def get_config_value(path: str, default: Any = None) -> Any:
    """
    Get configuration value by dot-separated path

    Args:
        path: Dot-separated path to config value (e.g., 'flowise.api_url')
        default: Default value if path not found

    Returns:
        Configuration value or default

    Example:
        api_url = get_config_value('flowise.api_url')
        interval = get_config_value('scheduling.google_drive_interval_minutes', 15)
    """
    config = load_config()

    keys = path.split('.')
    value = config

    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            logger.debug("Config path '%s' not found, using default: %s", path, default)
            return default

    return value


def cleanup_temp_files() -> None:
    """
    Clean up temporary files created by config loader
    Call this on application shutdown
    """
    global _service_account_temp_path

    if _service_account_temp_path and os.path.exists(_service_account_temp_path):
        try:
            os.remove(_service_account_temp_path)
            logger.debug("Cleaned up temporary service account file")
            _service_account_temp_path = None
        except Exception as e:
            logger.warning("Failed to clean up temporary file: %s", e)
