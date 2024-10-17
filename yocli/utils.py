import argparse
import os
import sys

import yaml


def get_config_path():
    # Set up command-line arguments
    parser = argparse.ArgumentParser(description="yocli configuration")
    parser.add_argument(
        "--config",
        type=str,
        help="Path to a custom configuration file (YAML format)"
    )
    args = parser.parse_args()

    # If a custom config file is provided, use it
    if args.config and os.path.exists(args.config):
        return args.config

    # Default locations to look for yocli.yml
    possible_paths = [
        # Common config directory
        os.path.expanduser("~/.config/yocli/yocli.yml"),
        # Hidden file in home directory
        os.path.expanduser("~/.yocli.yml"),
        os.path.join(os.getcwd(), "yocli.yml")  # Current directory
    ]

    # Check if yocli.yml exists in one of the possible paths
    for path in possible_paths:
        if os.path.exists(path):
            return path

    # If no config file is found, raise an error
    raise FileNotFoundError(
        "Configuration file not found. Please provide a yocli.yml.")


def load_yaml_config(file_path):
    """Load configuration from YAML file"""

    with open(file_path, 'r') as file:
        return yaml.safe_load(file)


def signal_handler(active_processes):
    """Signal handler for graceful shutdown"""
    for process in active_processes.values():
        if process.poll() is None:
            print("\nTerminating SSH connection...")
            process.terminate()

    sys.exit(0)
