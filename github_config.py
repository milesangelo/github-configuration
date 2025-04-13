#!/usr/bin/env python3
"""
GitHub Organization Configurator - Main entry point script

Sets up milestones and labels across repositories based on a YAML configuration file.

Usage:
    python github_config.py --token <personal_access_token> --config <config_file.yml> [options]
"""

import sys
import argparse
import os
from dotenv import load_dotenv
from datetime import datetime

from src.utils.logging import setup_logging
from src.configurator import GitHubConfigurator
from src.utils.config import load_config


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Configure GitHub repositories with milestones and labels."
    )
    parser.add_argument("--token", help="GitHub Personal Access Token (can also be set via .env as GITHUB_TOKEN)")
    parser.add_argument(
        "--config", required=True, help="Path to YAML configuration file"
    )
    parser.add_argument("--organization", help="GitHub organization name (optional)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run without making changes",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose (DEBUG) logging"
    )
    parser.add_argument("--log-file", help="Path to log file for output")
    parser.add_argument(
        "--summary", action="store_true", help="Print summary statistics at the end"
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        help="Remove milestones and labels not defined in the config",
    )
    parser.add_argument(
        "--sync-labels",
        action="store_true",
        help="Remove only labels not defined in the config",
    )
    parser.add_argument(
        "--sync-milestones",
        action="store_true",
        help="Remove only milestones not defined in the config",
    )

    args = parser.parse_args()

    load_dotenv()
    args.token = args.token or os.getenv("GITHUB_TOKEN")
    if not args.token:
        print("Error: GitHub token must be provided either via --token argument or GITHUB_TOKEN in .env file.")
        sys.exit(1)

    # Set up enhanced logging
    logger = setup_logging(verbose=args.verbose, log_file=args.log_file)

    # Log script start with configuration details
    logger.info(f"Starting GitHub Configurator script")
    logger.info(f"Configuration file: {args.config}")
    logger.info(
        f"Organization: {args.organization if args.organization else 'None (using user repositories)'}"
    )
    logger.info(f"Dry run: {args.dry_run}")

    if args.sync or args.sync_labels or args.sync_milestones:
        logger.info(f"Sync mode enabled: Will remove items not defined in config")
        if args.sync:
            logger.info(f"Syncing both labels and milestones")
        else:
            if args.sync_labels:
                logger.info(f"Syncing labels only")
            if args.sync_milestones:
                logger.info(f"Syncing milestones only")

    start_time = datetime.now()

    try:
        # Load configuration
        config = load_config(args.config)

        # Initialize and run configurator
        configurator = GitHubConfigurator(
            token=args.token,
            organization=args.organization,
            dry_run=args.dry_run,
            sync_labels=args.sync_labels,
            sync_milestones=args.sync_milestones,
            sync_all=args.sync,
        )

        exit_code = configurator.apply_config(config)

        end_time = datetime.now()
        duration = end_time - start_time

        # Print summary statistics if requested
        if args.summary:
            logger.info("=" * 60)
            logger.info(f"SUMMARY STATISTICS")
            logger.info(f"Total execution time: {duration}")
            logger.info(
                f"Configuration applied to: {len(configurator.processed_repos)} repositories"
            )
            logger.info(f"Successful operations: {configurator.success_count}")
            logger.info(f"Failed operations: {configurator.error_count}")
            logger.info(
                f"Total operations: {configurator.success_count + configurator.error_count}"
            )
            logger.info("-" * 30)
            logger.info(f"Milestone operations:")
            logger.info(f"  Created: {configurator.milestone_stats['created']}")
            logger.info(f"  Updated: {configurator.milestone_stats['updated']}")
            logger.info(f"  Removed: {configurator.milestone_stats['removed']}")
            logger.info(f"  Skipped: {configurator.milestone_stats['skipped']}")
            logger.info(f"  Failed: {configurator.milestone_stats['failed']}")
            logger.info(f"Label operations:")
            logger.info(f"  Created: {configurator.label_stats['created']}")
            logger.info(f"  Updated: {configurator.label_stats['updated']}")
            logger.info(f"  Removed: {configurator.label_stats['removed']}")
            logger.info(f"  Skipped: {configurator.label_stats['skipped']}")
            logger.info(f"  Failed: {configurator.label_stats['failed']}")
            logger.info("=" * 60)

        logger.info(f"Script completed in {duration}")
        return exit_code

    except KeyboardInterrupt:
        logger.warning("Script interrupted by user")
        return 130
    except Exception as e:
        logger.exception(f"Unhandled exception: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
