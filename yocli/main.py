import curses
import platform
import signal
import sys

from yocli.menu import interactive_menu
from yocli.ssh import free_ports
from yocli.utils import get_config_path, load_yaml_config, signal_handler


def main():
    if platform.system() == "Windows":
        sys.exit("yocli is not supported on Windows. Please use Linux or macOS.")

    # Get configuration file path
    config_path = get_config_path()  # Updated to use get_config_path function
    config = load_yaml_config(config_path)

    # Extract the ports from all SSH configs to free them
    ports_to_free = []
    for ssh in config['services']['ssh']:
        ports_to_free.extend([int(port_mapping.split(":")[0])
                             for port_mapping in ssh['ports']])
    free_ports(ports_to_free)  # Free any ports that are already in use

    # Register the signal handler to intercept Ctrl+C
    active_processes = {}  # Create a dictionary for tracking SSH processes
    signal.signal(signal.SIGINT, lambda sig,
                  frame: signal_handler(active_processes))

    # Use curses wrapper to run the interactive menu
    try:
        curses.wrapper(interactive_menu, config, active_processes)
    except KeyboardInterrupt:
        print("\nProgram terminated by user.")


if __name__ == "__main__":
    main()
