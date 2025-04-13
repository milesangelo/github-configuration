"""
Main configurator class for the GitHub Organization Configurator
# Supports configuration of milestones, labels, and action secrets
"""

import logging
import sys
from src.github.api import GitHubApiClient
from src.github.labels import LabelManager
from src.github.milestones import MilestoneManager
from src.github.secrets import SecretManager

# Initialize logger
logger = logging.getLogger("github-configurator")


class GitHubConfigurator:
    """
    Configure GitHub repositories with labels and milestones from a YAML file.
    """

    def __init__(
        self,
        token,
        organization=None,
        dry_run=False,
        sync_labels=False,
        sync_milestones=False,
        sync_all=False,
    ):
        """
        Initialize the configurator.

        Args:
            token (str): GitHub Personal Access Token
            organization (str, optional): GitHub organization name
            dry_run (bool): If True, perform a dry run without making changes
            sync_labels (bool): If True, remove labels not in config
            sync_milestones (bool): If True, remove milestones not in config
            sync_all (bool): If True, remove both labels and milestones not in config
        """
        self.organization = organization
        self.dry_run = dry_run
        self.sync_labels = sync_labels or sync_all
        self.sync_milestones = sync_milestones or sync_all

        # Initialize API client
        self.api = GitHubApiClient(token)

        # Initialize managers
        self.label_manager = LabelManager(self.api, dry_run)
        self.milestone_manager = MilestoneManager(self.api, dry_run)
        self.secret_manager = SecretManager(self.api)

        # Statistics tracking
        self.success_count = 0
        self.error_count = 0
        self.processed_repos = set()

    @property
    def milestone_stats(self):
        """Get milestone statistics."""
        return self.milestone_manager.stats

    @property
    def label_stats(self):
        """Get label statistics."""
        return self.label_manager.stats

    def get_repositories(self, config):
        """
        Get a list of repositories to configure.

        Args:
            config (dict): Configuration dictionary

        Returns:
            list: A list of repository names
        """
        # Get repositories based on configuration
        if "repositories" in config and config["repositories"]:
            repositories = config["repositories"]
            # Add organization prefix if needed
            if self.organization:
                repositories = [
                    f"{self.organization}/{repo}" if "/" not in repo else repo
                    for repo in repositories
                ]
            logger.info(
                f"Using {len(repositories)} repositories specified in configuration"
            )
        else:
            # Get all repositories from the organization or user
            repositories = self.api.get_repositories(self.organization)
            logger.info(f"Found {len(repositories)} repositories")

        return repositories

    def apply_config_to_repository(self, repo, config):
        """
        Apply configuration to a single repository.

        Args:
            repo (str): Repository name (owner/repo)
            config (dict): Configuration dictionary

        Returns:
            bool: True if successful, False otherwise
        """
        success = True

        # Track configured items for sync operations
        configured_milestone_titles = []
        configured_label_names = []

        # Apply milestones
        if "milestones" in config:
            for milestone in config["milestones"]:
                if not self.milestone_manager.create_milestone(repo, milestone):
                    success = False
                configured_milestone_titles.append(milestone.get("title", ""))

        # Apply labels
        if "labels" in config:
            for label in config["labels"]:
                if not self.label_manager.create_label(repo, label):
                    success = False
                configured_label_names.append(label.get("name", ""))

        # Apply secrets
        if "secrets" in config:
            for secret in config["secrets"]:
                if not self.secret_manager.create_or_update_secret(repo, secret):
                    success = False

        # Sync operations - remove items not in config
        if self.sync_milestones and "milestones" in config:
            if not self.milestone_manager.sync_repository_milestones(
                repo, configured_milestone_titles
            ):
                success = False

        if self.sync_labels and "labels" in config:
            if not self.label_manager.sync_repository_labels(
                repo, configured_label_names
            ):
                success = False

        return success

    def apply_config(self, config):
        """
        Apply the configuration to all repositories or specified ones.

        Args:
            config (dict): Configuration dictionary

        Returns:
            int: 0 if successful, 1 otherwise
        """
        success = True

        # Get repositories based on configuration
        repositories = self.get_repositories(config)

        logger.info(f"Applying configuration to {len(repositories)} repositories")

        # Apply configuration to each repository
        for repo in repositories:
            logger.info(f"Processing {repo}...")
            self.processed_repos.add(repo)
            if not self.apply_config_to_repository(repo, config):
                success = False

        # Update overall statistics
        self.success_count = (
            self.label_manager.success_count + self.milestone_manager.success_count
        )
        self.error_count = (
            self.label_manager.error_count + self.milestone_manager.error_count
        )

        if success:
            logger.info("Configuration applied successfully")
            return 0
        else:
            logger.warning("Configuration applied with some errors")
            return 1
