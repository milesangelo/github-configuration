"""
Configuration utilities for the GitHub Organization Configurator
"""

import sys
import yaml
import logging

# Initialize logger
logger = logging.getLogger("github-configurator")


def load_config(config_file):
    """
    Load the YAML configuration file.

    Args:
        config_file (str): Path to the YAML config file

    Returns:
        dict: The parsed configuration

    Raises:
        SystemExit: If the configuration cannot be loaded
    """
    try:
        with open(config_file, "r") as f:
            config = yaml.safe_load(f)
        logger.info(f"Successfully loaded configuration from {config_file}")

        # Validate the configuration
        validate_config(config)

        return config
    except Exception as e:
        logger.error(f"Failed to load configuration: {str(e)}")
        sys.exit(1)


def validate_config(config):
    """
    Validate the configuration structure.

    Args:
        config (dict): The configuration to validate

    Raises:
        ValueError: If the configuration is invalid
    """
    # Check if milestones or labels are defined
    if "milestones" not in config and "labels" not in config:
        logger.warning(
            "Configuration does not contain 'milestones' or 'labels' sections"
        )

    # Validate milestones if present
    if "milestones" in config:
        for i, milestone in enumerate(config["milestones"]):
            if "title" not in milestone:
                raise ValueError(
                    f"Milestone at index {i} is missing required 'title' field"
                )

    # Validate labels if present
    if "labels" in config:
        for i, label in enumerate(config["labels"]):
            if "name" not in label:
                raise ValueError(f"Label at index {i} is missing required 'name' field")
            if "color" not in label:
                raise ValueError(
                    f"Label at index {i} is missing required 'color' field"
                )
