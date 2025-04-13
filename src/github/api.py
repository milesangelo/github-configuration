"""
GitHub API client for the GitHub Organization Configurator
"""

import sys
import requests
import logging
from datetime import datetime

# Initialize logger
logger = logging.getLogger("github-configurator")


class GitHubApiClient:
    """
    Client for interacting with the GitHub API.
    """

    API_URL = "https://api.github.com"

    def __init__(self, token):
        """
        Initialize the API client.

        Args:
            token (str): GitHub Personal Access Token
        """
        self.token = token
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        }
        self.rate_limit_remaining = None
        self.rate_limit_reset = None

        # Check rate limit on initialization
        self.check_rate_limit()

    def check_rate_limit(self):
        """
        Check and log the current GitHub API rate limit status.

        Returns:
            dict: Rate limit information
        """
        try:
            url = f"{self.API_URL}/rate_limit"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()

            data = response.json()
            core_rate = data.get("resources", {}).get("core", {})

            self.rate_limit_remaining = core_rate.get("remaining")
            reset_time = core_rate.get("reset")

            if reset_time:
                reset_datetime = datetime.fromtimestamp(reset_time)
                self.rate_limit_reset = reset_datetime
                reset_str = reset_datetime.strftime("%Y-%m-%d %H:%M:%S")
            else:
                reset_str = "Unknown"

            logger.debug(
                f"Rate limit: {self.rate_limit_remaining}/{core_rate.get('limit')} requests remaining, resets at {reset_str}"
            )

            # Warn if rate limit is getting low
            if self.rate_limit_remaining and self.rate_limit_remaining < 100:
                logger.warning(
                    f"GitHub API rate limit is low: {self.rate_limit_remaining} requests remaining"
                )
                if self.rate_limit_reset:
                    now = datetime.now()
                    wait_time = (self.rate_limit_reset - now).total_seconds()
                    if wait_time > 0:
                        logger.warning(
                            f"Rate limit will reset in {wait_time:.1f} seconds"
                        )

            return core_rate

        except requests.RequestException as e:
            logger.warning(f"Failed to check rate limit: {str(e)}")
            return None

    def get_repositories(self, organization=None):
        """
        Get a list of repositories for the user or organization.

        Args:
            organization (str, optional): GitHub organization name

        Returns:
            list: A list of repository names

        Raises:
            SystemExit: If repositories cannot be retrieved
        """
        try:
            if organization:
                url = f"{self.API_URL}/orgs/{organization}/repos"
                logger.info(f"Fetching repositories for organization: {organization}")
            else:
                url = f"{self.API_URL}/user/repos"
                logger.info(f"Fetching repositories for authenticated user")

            repos = []
            page = 1
            total_fetched = 0

            logger.debug(f"Starting repository pagination with page size 100")
            while True:
                logger.debug(f"Fetching page {page} of repositories")
                response = requests.get(
                    f"{url}?per_page=100&page={page}", headers=self.headers
                )
                response.raise_for_status()

                # Update rate limit information from response headers
                if "X-RateLimit-Remaining" in response.headers:
                    self.rate_limit_remaining = int(
                        response.headers["X-RateLimit-Remaining"]
                    )
                    logger.debug(f"Rate limit remaining: {self.rate_limit_remaining}")

                batch = response.json()
                batch_size = len(batch)
                total_fetched += batch_size
                logger.debug(f"Retrieved {batch_size} repositories in page {page}")

                if not batch:
                    logger.debug(f"No more repositories found, ending pagination")
                    break

                # Extract repo information with more details for debugging
                for repo in batch:
                    repo_full_name = repo["full_name"]
                    repos.append(repo_full_name)
                    logger.debug(
                        f"Found repository: {repo_full_name} (visibility: {repo.get('visibility', 'unknown')})"
                    )

                page += 1

            logger.info(f"Found {len(repos)} repositories in total")
            if len(repos) == 0:
                logger.warning(
                    "No repositories found! Check your token permissions and organization name."
                )
            elif len(repos) > 50:
                logger.warning(
                    f"Large number of repositories found ({len(repos)}). This may take a while."
                )

            return repos
        except requests.RequestException as e:
            logger.error(f"Failed to retrieve repositories: {str(e)}")
            if hasattr(e, "response") and e.response:
                logger.error(f"Response status code: {e.response.status_code}")
                logger.error(f"Response headers: {e.response.headers}")
                logger.error(f"Response body: {e.response.text}")

                if e.response.status_code == 401:
                    logger.error("Authentication failed. Check your GitHub token.")
                elif e.response.status_code == 403:
                    logger.error(
                        "Permission denied. Check if your token has the required scopes."
                    )
                elif e.response.status_code == 404:
                    if organization:
                        logger.error(
                            f"Organization '{organization}' not found or you don't have access to it."
                        )

            sys.exit(1)

    def get(self, endpoint, params=None):
        """
        Make a GET request to the GitHub API.

        Args:
            endpoint (str): API endpoint (without base URL)
            params (dict, optional): Query parameters

        Returns:
            dict: API response JSON

        Raises:
            requests.RequestException: If the request fails
        """
        url = f"{self.API_URL}{endpoint}"
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def post(self, endpoint, data):
        """
        Make a POST request to the GitHub API.

        Args:
            endpoint (str): API endpoint (without base URL)
            data (dict): Request data

        Returns:
            dict: API response JSON

        Raises:
            requests.RequestException: If the request fails
        """
        url = f"{self.API_URL}{endpoint}"
        response = requests.post(url, headers=self.headers, json=data)
        if response.status_code not in (200, 201, 204):
            logger.error(
                f"POST request to {endpoint} failed with status {response.status_code}"
            )
            logger.error(f"Response: {response.text}")
        response.raise_for_status()
        return response.json() if response.text else {}

    def patch(self, endpoint, data):
        """
        Make a PATCH request to the GitHub API.

        Args:
            endpoint (str): API endpoint (without base URL)
            data (dict): Request data

        Returns:
            dict: API response JSON

        Raises:
            requests.RequestException: If the request fails
        """
        url = f"{self.API_URL}{endpoint}"
        response = requests.patch(url, headers=self.headers, json=data)
        if response.status_code not in (200, 201, 204):
            logger.error(
                f"PATCH request to {endpoint} failed with status {response.status_code}"
            )
            logger.error(f"Response: {response.text}")
        response.raise_for_status()
        return response.json() if response.text else {}

    def delete(self, endpoint):
        """
        Make a DELETE request to the GitHub API.

        Args:
            endpoint (str): API endpoint (without base URL)

        Returns:
            bool: True if successful

        Raises:
            requests.RequestException: If the request fails
        """
        url = f"{self.API_URL}{endpoint}"
        response = requests.delete(url, headers=self.headers)
        if response.status_code not in (200, 201, 204):
            logger.error(
                f"DELETE request to {endpoint} failed with status {response.status_code}"
            )
            logger.error(f"Response: {response.text}")
        response.raise_for_status()
        return True

    def paginate(self, endpoint, params=None):
        """
        Paginate through all results of a GET request.

        Args:
            endpoint (str): API endpoint (without base URL)
            params (dict, optional): Query parameters

        Returns:
            list: All results from all pages

        Raises:
            requests.RequestException: If any request fails
        """
        if params is None:
            params = {}

        results = []
        page = 1
        while True:
            params["page"] = page
            params["per_page"] = 100

            url = f"{self.API_URL}{endpoint}"
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()

            batch = response.json()
            if not batch:
                break

            results.extend(batch)
            page += 1

        return results

    def put(self, endpoint, data=None):
        """
        Make a PUT request to the GitHub API.

        Args:
            endpoint (str): API endpoint (without base URL)
            data (dict, optional): Request data

        Returns:
            dict: API response JSON (if present)

        Raises:
            requests.RequestException: If the request fails
        """
        url = f"{self.API_URL}{endpoint}"
        response = requests.put(url, headers=self.headers, json=data)
        if response.status_code not in (200, 201, 204):
            logger.error(
                f"PUT request to {endpoint} failed with status {response.status_code}"
            )
            logger.error(f"Response: {response.text}")
        response.raise_for_status()
        return response.json() if response.text else {}
