import curses
import os
import signal
import socket
import subprocess
import sys
import time

import yaml

# Load configuration from YAML file


def load_yaml_config(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

# Function to check and free any ports that are already in use


def free_ports(ports_to_free):
    for port in ports_to_free:
        # Find the process using the port
        result = subprocess.run(
            ['lsof', '-i', f':{port}'], capture_output=True, text=True)
        if result.stdout:
            # Extract the PID from the output
            lines = result.stdout.splitlines()
            if len(lines) > 1:  # The first line is the header
                pid = lines[1].split()[1]
                # Kill the process
                os.system(f'kill -9 {pid}')
                print(f"Port {port} freed (killed process {pid}).")
            else:
                print(f"No process found using port {port}.")
        else:
            print(f"No process found using port {port}.")

# Function to create and manage SSH tunnel connection


def create_ssh_tunnel_from_config(ssh_config):
    # Extract configuration
    local_host = ssh_config['host-local']
    remote_host = ssh_config['host']
    user = ssh_config['user']
    remote_port = ssh_config['port']
    local_port = ssh_config.get('port-local', remote_port)
    identity_file = os.path.expanduser(ssh_config['identity_file'])
    ports = ssh_config['ports']

    # Determine which host and port to use
    if is_host_reachable(local_host, local_port):
        host = local_host
        port = local_port
    else:
        host = remote_host
        port = remote_port

    ssh_command = [
        "ssh",
        "-N",
        "-i", identity_file,
        f"{user}@{host}",
        "-p", str(port)
    ]

    # Adding port forwarding details
    for port_mapping in ports:
        local_port, remote_port = port_mapping.split(":")
        ssh_command += ["-L",
                        f"127.0.0.1:{local_port}:127.0.0.1:{remote_port}"]

    # Start the SSH process
    try:
        process = subprocess.Popen(ssh_command)
        return process  # Return the process so we can manage it later
    except Exception as e:
        print(f"Error: {e}")
        return None

# Helper function to check if host is reachable


def is_host_reachable(host, port):
    try:
        # Try to connect to the host on the given port
        socket.create_connection((host, port), timeout=5)
        return True
    except (socket.timeout, socket.error):
        return False

# Function to open VS Code for a specified project


def open_vscode(commands):
    try:
        for command in commands:
            subprocess.call(command, shell=True)
    except Exception as e:
        print(f"Error opening VS Code for project: {e}")

# Interactive menu with curses


def interactive_menu(stdscr, config):
    curses.curs_set(0)  # Hide the cursor
    stdscr.clear()

    active_processes = {}  # Dictionary to track active SSH connections

    # Dynamically generate the menu options from the config
    ssh_configs = config['services']['ssh']
    ssh_options = [f"Connect to {ssh['name']}" for ssh in ssh_configs]
    vscode_projects = config['services']['vscode']
    vscode_options = [
        f"VSCode: {project['name']}" for project in vscode_projects]
    menu_options = ssh_options + vscode_options + ["Exit"]

    current_row = 0

    while True:
        stdscr.clear()
        # Styling and Header
        stdscr.addstr(
            0, 0, "Hi, welcome. Choose your action:\n", curses.A_BOLD)

        # Space between sections
        stdscr.addstr(2, 0, "*SSH connections:*", curses.A_UNDERLINE)
        ssh_row_start = 3

        # Display SSH connection options
        for idx, option in enumerate(ssh_options):
            row = ssh_row_start + idx
            if idx == current_row and idx in active_processes and active_processes[idx].poll() is None:
                # Display "Connected to server" in green
                status_text = " (Connected)"
                stdscr.addstr(
                    row, 2, f"> {option}{status_text}", curses.A_REVERSE | curses.color_pair(1))
            elif idx == current_row:
                stdscr.addstr(row, 2, f"> {option}", curses.A_REVERSE)
            elif idx in active_processes and active_processes[idx].poll() is None:
                stdscr.addstr(
                    row, 2, f"  {option} (Connected)", curses.color_pair(1))
            else:
                stdscr.addstr(row, 2, f"  {option}")

        # Space between SSH and VSCode options
        vscode_row_start = ssh_row_start + len(ssh_options) + 2
        stdscr.addstr(vscode_row_start - 1, 0,
                      "*VSCode projects:*", curses.A_UNDERLINE)

        # Display VSCode projects options
        for idx, project in enumerate(vscode_options):
            row = vscode_row_start + idx
            if current_row == idx + len(ssh_options):
                # Remove "VSCode: " prefix for display
                stdscr.addstr(row, 2, f"> {project[7:]}", curses.A_REVERSE)
            else:
                stdscr.addstr(row, 2, f"  {project[7:]}")

        # Display Exit option
        exit_row = vscode_row_start + len(vscode_options) + 2
        if current_row == len(menu_options) - 1:
            stdscr.addstr(exit_row, 2, "> Exit", curses.A_REVERSE)
        else:
            stdscr.addstr(exit_row, 2, "  Exit")

        # Get user input
        key = stdscr.getch()

        # Navigate the menu
        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(menu_options) - 1:
            current_row += 1
        elif key == curses.KEY_ENTER or key in [10, 13]:
            if current_row < len(ssh_options):  # Connect to SSH server
                ssh_index = current_row
                ssh_config = ssh_configs[ssh_index]
                stdscr.clear()
                if ssh_index in active_processes and active_processes[ssh_index].poll() is None:
                    stdscr.addstr(
                        0, 0, f"Disconnecting from {ssh_config['name']}...")
                    active_processes[ssh_index].terminate()
                    del active_processes[ssh_index]
                else:
                    stdscr.addstr(
                        0, 0, f"Connecting to {ssh_config['name']}...")
                    active_process = create_ssh_tunnel_from_config(ssh_config)
                    if active_process is not None:
                        active_processes[ssh_index] = active_process
                stdscr.refresh()
                time.sleep(1)
            elif current_row == len(menu_options) - 1:  # Exit
                for process in active_processes.values():
                    if process.poll() is None:
                        process.terminate()
                break
            else:  # VSCode project options
                project_index = current_row - len(ssh_options)
                project = vscode_projects[project_index]
                stdscr.clear()
                stdscr.addstr(
                    0, 0, f"Opening VSCode for Project {project['name']}...")
                stdscr.refresh()
                time.sleep(1)
                open_vscode(project['commands'])

            time.sleep(1)

        stdscr.refresh()

# Signal handler for graceful shutdown


def signal_handler(sig, frame, active_processes):
    for process in active_processes.values():
        if process.poll() is None:
            print("\nTerminating SSH connection...")
            process.terminate()
    sys.exit(0)


if __name__ == "__main__":
    config_path = 'config.yml'
    config = load_yaml_config(config_path)

    # Extract the ports from all SSH configs to free them
    ports_to_free = []
    for ssh in config['services']['ssh']:
        ports_to_free.extend([int(port_mapping.split(":")[0])
                             for port_mapping in ssh['ports']])
    free_ports(ports_to_free)  # Free any ports that are already in use

    # Register the signal handler to intercept Ctrl+C
    signal.signal(signal.SIGINT, lambda sig, frame: signal_handler(sig, {}))

    # Use curses wrapper to run the interactive menu
    try:
        curses.wrapper(interactive_menu, config)
    except KeyboardInterrupt:
        print("\nProgram terminated by user.")
