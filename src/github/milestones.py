"""
Milestone operations for the GitHub Organization Configurator
"""

import logging
import requests
from datetime import datetime

# Initialize logger
logger = logging.getLogger("github-configurator")


class MilestoneManager:
    """
    Manager for GitHub milestone operations.
    """

    def __init__(self, api_client, dry_run=False):
        """
        Initialize the milestone manager.

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

    def _format_due_date(self, due_date_str):
        """
        Format a due date string into ISO 8601 format.

        Args:
            due_date_str (str): Due date string

        Returns:
            str: Formatted date string in ISO 8601 format

        Raises:
            ValueError: If the date format is invalid
        """
        if not due_date_str:
            return None

        # Try several date formats
        date_formats = [
            "%Y-%m-%d",  # 2025-05-04
            "%Y/%m/%d",  # 2025/05/04
            "%d-%m-%Y",  # 04-05-2025
            "%d/%m/%Y",  # 04/05/2025
            "%b %d, %Y",  # May 04, 2025
            "%B %d, %Y",  # May 04, 2025
            "%d %b %Y",  # 04 May 2025
            "%d %B %Y",  # 04 May 2025
        ]

        for date_format in date_formats:
            try:
                date_obj = datetime.strptime(due_date_str, date_format)
                return date_obj.strftime("%Y-%m-%dT23:59:59Z")
            except ValueError:
                continue

        # If we get here, none of the formats worked
        raise ValueError(f"Could not parse date '{due_date_str}' with any known format")

    def create_milestone(self, repo, milestone_data):
        """
        Create a milestone in a repository.

        Args:
            repo (str): Repository name (owner/repo)
            milestone_data (dict): Milestone configuration

        Returns:
            bool: True if successful, False otherwise
        """
        milestone_title = milestone_data.get("title", "Unknown")
        logger.debug(f"Processing milestone '{milestone_title}' for repository {repo}")

        try:
            # Make a copy of the milestone data to avoid modifying the original
            milestone_data_copy = milestone_data.copy()

            # Convert due_on date format if present
            if "due_on" in milestone_data_copy and milestone_data_copy["due_on"]:
                try:
                    original_date = milestone_data_copy["due_on"]
                    milestone_data_copy["due_on"] = self._format_due_date(original_date)
                    logger.debug(
                        f"Converted date format from '{original_date}' to '{milestone_data_copy['due_on']}'"
                    )
                except ValueError as e:
                    logger.warning(
                        f"Invalid date format in milestone {milestone_title}: {str(e)}"
                    )
                    logger.warning(f"Date should be in YYYY-MM-DD format")

            # Check if milestone already exists
            logger.debug(
                f"Checking for existing milestone '{milestone_title}' in {repo}"
            )

            try:
                existing_milestones = self.api.paginate(
                    f"/repos/{repo}/milestones", {"state": "all"}
                )

                # Check if milestone already exists
                for existing in existing_milestones:
                    if existing["title"] == milestone_title:
                        existing_id = existing["number"]
                        logger.debug(
                            f"Found existing milestone '{milestone_title}' (ID: {existing_id}) in {repo}"
                        )

                        # Update the milestone instead of creating a new one
                        if not self.dry_run:
                            logger.debug(
                                f"Updating milestone '{milestone_title}' (ID: {existing_id}) in {repo}"
                            )

                            try:
                                # When updating, don't change the due date if our conversion failed
                                if (
                                    "due_on" in milestone_data_copy
                                    and milestone_data_copy["due_on"] is None
                                ):
                                    logger.debug(
                                        f"Keeping existing due date for milestone '{milestone_title}'"
                                    )
                                    del milestone_data_copy["due_on"]

                                self.api.patch(
                                    f"/repos/{repo}/milestones/{existing_id}",
                                    milestone_data_copy,
                                )
                                logger.info(
                                    f"✓ Updated milestone '{milestone_title}' in {repo}"
                                )
                                self.success_count += 1
                                self.stats["updated"] += 1
                                return True
                            except requests.RequestException as e:
                                logger.error(
                                    f"✗ Failed to update milestone '{milestone_title}' in {repo}: {str(e)}"
                                )
                                self.error_count += 1
                                self.stats["failed"] += 1
                                return False
                        else:
                            logger.info(
                                f"[DRY RUN] Would update milestone '{milestone_title}' in {repo}"
                            )
                            return True
            except requests.RequestException as e:
                logger.warning(f"Error checking for existing milestone: {str(e)}")
                # Continue with create attempt

            if self.dry_run:
                logger.info(
                    f"[DRY RUN] Would create milestone '{milestone_title}' in {repo}"
                )
                return True

            # Don't create a milestone with an invalid due date
            if (
                "due_on" in milestone_data_copy
                and milestone_data_copy["due_on"] is None
            ):
                logger.warning(
                    f"Skipping milestone creation for '{milestone_title}' due to invalid date format"
                )
                self.stats["skipped"] += 1
                return False

            logger.debug(f"Creating milestone '{milestone_title}' in {repo}")
            logger.debug(f"Request data: {milestone_data_copy}")

            try:
                response = self.api.post(
                    f"/repos/{repo}/milestones", milestone_data_copy
                )
                logger.info(f"✓ Created milestone '{milestone_title}' in {repo}")
                self.success_count += 1
                self.stats["created"] += 1
                # Log the milestone URL for convenience
                if "html_url" in response:
                    logger.debug(f"Milestone URL: {response['html_url']}")
                return True
            except requests.RequestException as e:
                # Handle case where milestone might already exist
                if (
                    hasattr(e, "response")
                    and e.response
                    and e.response.status_code == 422
                ):
                    logger.info(
                        f"⚠ Milestone '{milestone_title}' already exists in {repo}"
                    )
                    self.stats["skipped"] += 1
                    return True
                else:
                    logger.error(
                        f"✗ Failed to create milestone '{milestone_title}' in {repo}: {str(e)}"
                    )
                    self.error_count += 1
                    self.stats["failed"] += 1
                    return False

        except Exception as e:
            logger.error(
                f"✗ Failed to process milestone '{milestone_title}' in {repo}: {str(e)}"
            )
            self.error_count += 1
            self.stats["failed"] += 1
            return False

    def sync_repository_milestones(self, repo, configured_milestones):
        """
        Remove milestones from a repository that aren't in the config.

        Args:
            repo (str): Repository name (owner/repo)
            configured_milestones (list): List of milestone titles from config

        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"Syncing milestones for {repo}")
        success = True

        try:
            # Get all milestones
            all_milestones = self.api.paginate(
                f"/repos/{repo}/milestones", {"state": "all"}
            )

            # Find milestones to remove (those not in config)
            for milestone in all_milestones:
                milestone_title = milestone.get("title", "")
                milestone_number = milestone.get("number")

                if milestone_title not in configured_milestones:
                    logger.debug(f"Found milestone '{milestone_title}' not in config")

                    if self.dry_run:
                        logger.info(
                            f"[DRY RUN] Would remove milestone '{milestone_title}' from {repo}"
                        )
                    else:
                        # Delete the milestone
                        try:
                            self.api.delete(
                                f"/repos/{repo}/milestones/{milestone_number}"
                            )
                            logger.info(
                                f"✓ Removed milestone '{milestone_title}' from {repo}"
                            )
                            self.stats["removed"] += 1
                        except requests.RequestException as e:
                            logger.error(
                                f"✗ Failed to remove milestone '{milestone_title}' from {repo}: {str(e)}"
                            )
                            self.error_count += 1
                            success = False

            return success

        except Exception as e:
            logger.error(f"✗ Failed to sync milestones in {repo}: {str(e)}")
            self.error_count += 1
            return False
