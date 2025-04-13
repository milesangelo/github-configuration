"""
Label operations for the GitHub Organization Configurator
"""

import logging
import requests

# Initialize logger
logger = logging.getLogger("github-configurator")


class LabelManager:
    """
    Manager for GitHub label operations.
    """

    def __init__(self, api_client, dry_run=False):
        """
        Initialize the label manager.

        Args:
            api_client (GitHubApiClient): GitHub API client
            dry_run (bool): If True, perform a dry run without making changes
        """
        self.api = api_client
        self.dry_run = dry_run
        self.stats = {
            "created": 0,
            "updated": 0,
            "removed": 0,
            "failed": 0,
            "skipped": 0,
        }
        self.success_count = 0
        self.error_count = 0

    def create_label(self, repo, label_data):
        """
        Create a label in a repository.

        Args:
            repo (str): Repository name (owner/repo)
            label_data (dict): Label configuration

        Returns:
            bool: True if successful, False otherwise
        """
        label_name = label_data.get("name", "Unknown")
        label_color = label_data.get("color", "Unknown")

        logger.debug(
            f"Processing label '{label_name}' (#{label_color}) for repository {repo}"
        )

        try:
            # First check if the label exists
            logger.debug(f"Checking if label '{label_name}' already exists in {repo}")

            try:
                existing_label = self.api.get(f"/repos/{repo}/labels/{label_name}")
                label_exists = True

                # Check if update is needed
                needs_update = existing_label.get("color", "") != label_data.get(
                    "color", ""
                ).lstrip("#") or existing_label.get(
                    "description", ""
                ) != label_data.get(
                    "description", ""
                )

                if needs_update:
                    if self.dry_run:
                        logger.info(
                            f"[DRY RUN] Would update label '{label_name}' in {repo}"
                        )
                        return True

                    # Label exists but needs update
                    logger.debug(f"Updating label '{label_name}' in {repo}")
                    logger.debug(
                        f"Current: color=#{existing_label.get('color', '')}, description='{existing_label.get('description', '')}'"
                    )
                    logger.debug(
                        f"New: color=#{label_data.get('color', '')}, description='{label_data.get('description', '')}'"
                    )

                    self.api.patch(f"/repos/{repo}/labels/{label_name}", label_data)
                    logger.info(f"✓ Updated label '{label_name}' in {repo}")
                    self.success_count += 1
                    self.stats["updated"] += 1
                    return True
                else:
                    logger.info(
                        f"✓ Label '{label_name}' already exists with correct properties in {repo}"
                    )
                    self.stats["skipped"] += 1
                    return True

            except requests.RequestException:
                # Label does not exist, continue with creation
                label_exists = False

            if self.dry_run:
                logger.info(f"[DRY RUN] Would create label '{label_name}' in {repo}")
                return True

            if not label_exists:
                # Create the label
                logger.debug(
                    f"Creating label '{label_name}' with color #{label_color} in {repo}"
                )

                try:
                    self.api.post(f"/repos/{repo}/labels", label_data)
                    logger.info(f"✓ Created label '{label_name}' in {repo}")
                    self.success_count += 1
                    self.stats["created"] += 1
                    return True
                except requests.RequestException as e:
                    # Label might exist with a different capitalization
                    if (
                        hasattr(e, "response")
                        and e.response
                        and e.response.status_code == 422
                    ):
                        logger.debug(
                            f"Label creation returned 422, attempting to find case-insensitive match"
                        )

                        # Get all labels to find case-insensitive match
                        all_labels = self.api.paginate(f"/repos/{repo}/labels")
                        for existing in all_labels:
                            if existing["name"].lower() == label_name.lower():
                                existing_name = existing["name"]
                                logger.debug(
                                    f"Found case-insensitive match: '{existing_name}'"
                                )

                                # Update the existing label
                                self.api.patch(
                                    f"/repos/{repo}/labels/{existing_name}", label_data
                                )
                                logger.info(
                                    f"✓ Updated label '{existing_name}' to '{label_name}' in {repo}"
                                )
                                self.success_count += 1
                                self.stats["updated"] += 1
                                return True

                    logger.error(
                        f"✗ Failed to create label '{label_name}' in {repo}: {str(e)}"
                    )
                    self.error_count += 1
                    self.stats["failed"] += 1
                    return False

        except Exception as e:
            logger.error(
                f"✗ Failed to process label '{label_name}' in {repo}: {str(e)}"
            )
            self.error_count += 1
            self.stats["failed"] += 1
            return False

    def sync_repository_labels(self, repo, configured_labels):
        """
        Remove labels from a repository that aren't in the config.

        Args:
            repo (str): Repository name (owner/repo)
            configured_labels (list): List of label names from config

        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"Syncing labels for {repo}")
        success = True

        try:
            # Get all labels
            all_labels = self.api.paginate(f"/repos/{repo}/labels")

            # Find labels to remove (those not in config)
            for label in all_labels:
                label_name = label.get("name", "")

                if label_name not in configured_labels:
                    logger.debug(f"Found label '{label_name}' not in config")

                    if self.dry_run:
                        logger.info(
                            f"[DRY RUN] Would remove label '{label_name}' from {repo}"
                        )
                    else:
                        # Delete the label
                        try:
                            self.api.delete(f"/repos/{repo}/labels/{label_name}")
                            logger.info(f"✓ Removed label '{label_name}' from {repo}")
                            self.stats["removed"] += 1
                        except requests.RequestException as e:
                            logger.error(
                                f"✗ Failed to remove label '{label_name}' from {repo}: {str(e)}"
                            )
                            self.error_count += 1
                            success = False

            return success

        except Exception as e:
            logger.error(f"✗ Failed to sync labels in {repo}: {str(e)}")
            self.error_count += 1
            return False
