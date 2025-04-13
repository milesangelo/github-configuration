# GitHub Organization Configurator

A Python utility to set up milestones and labels across multiple GitHub repositories based on a YAML configuration file.

## Features

- Create and update milestones with titles, descriptions, and due dates
- Create and update labels with names, colors, and descriptions
- Option to remove milestones and labels not defined in the configuration (sync mode)
- Support for both organization and personal repositories
- Detailed logging and summary statistics
- Dry run capability to preview changes without executing them

## Installation

### 1. Clone this repository

```bash
git clone https://github.com/Luna-Crypto-Trading/github-configurator.git
cd github-configurator
```

### 2. Set up a Python virtual environment

Create and activate the virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Freeze new dependencies

After installing new packages (e.g. `pip install <package>`), update `requirements.txt`:

```bash
pip freeze > requirements.txt
```

### Alternative: Install as a package

You can also install the tool via pip in editable mode:

```bash
pip install -e .
```

## Configuration

Create a YAML configuration file defining your milestones and labels. See the example in `config/default_config.yml`.

```yaml
# Optional: List of specific repositories to apply configuration to
repositories:
  - project-one
  - project-two

# Milestones to create in each repository
milestones:
  - title: "MVP"
    description: "Minimum Viable Product Release"
    state: "open"
    due_on: "2025-05-04"  # Format: YYYY-MM-DD

# Labels to create in each repository
labels:
  - name: "no-code"
    color: "cccccc"
    description: "Non-code changes like docs or config"
```

## Usage

### Basic Usage

```bash
python github_config.py --token YOUR_GITHUB_TOKEN --config your_config.yml
```

### Using with an Organization

```bash
python github_config.py --token YOUR_GITHUB_TOKEN --config your_config.yml --organization YOUR_ORG_NAME
```

### Preview Changes with Dry Run

```bash
python github_config.py --token YOUR_GITHUB_TOKEN --config your_config.yml --organization YOUR_ORG_NAME --dry-run
```

### Remove Items Not in Config (Sync Mode)

```bash
python github_config.py --token YOUR_GITHUB_TOKEN --config your_config.yml --organization YOUR_ORG_NAME --sync
```

### More Options

```bash
python github_config.py --help
```

## Command Line Arguments

- `--token`: Your GitHub Personal Access Token (required)
- `--config`: Path to your YAML configuration file (required)
- `--organization`: Your GitHub organization name (optional)
- `--dry-run`: Perform a dry run without making any actual changes
- `--verbose`, `-v`: Enable verbose (DEBUG) logging
- `--log-file`: Path to log file for output
- `--summary`: Print summary statistics at the end
- `--sync`: Remove both milestones and labels not defined in the config
- `--sync-labels`: Remove only labels not defined in the config
- `--sync-milestones`: Remove only milestones not defined in the config

## GitHub Token Permissions

Your Personal Access Token needs the following permissions:
- `repo` scope for private repositories
- `public_repo` scope for public repositories

## Project Structure

The project is organized following the Single Responsibility Principle:

- `github_config.py`: Main entry point script
- `src/configurator.py`: Main configurator class
- `src/github/api.py`: GitHub API client
- `src/github/labels.py`: Label operations
- `src/github/milestones.py`: Milestone operations
- `src/utils/config.py`: Configuration loading utilities
- `src/utils/logging.py`: Logging utilities
