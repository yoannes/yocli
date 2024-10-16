import curses
import sys
import time

from yocli.ssh import create_ssh_tunnel_from_config
from yocli.vscode import open_vscode


def init_curses_colors():
    """Initialize color mode"""

    if curses.has_colors():
        curses.start_color()
        try:
            # Define some color pairs with adaptable background
            # Cyan text with terminal default background
            curses.init_pair(1, curses.COLOR_CYAN, -1)
        except curses.error:
            # Fallback to black background if default fails
            curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)


def interactive_menu(stdscr, config, active_processes):
    """Interactive menu with curses"""

    init_curses_colors()
    curses.curs_set(0)  # Hide the cursor
    stdscr.clear()

    active_ports = {}  # Dictionary to track the ports forwarded by each active connection

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
            0, 0, "Hi, welcome. Choose your actions:\n", curses.A_BOLD | curses.color_pair(1))

        # Space between sections
        stdscr.addstr(2, 0, "*SSH connections:*", curses.A_UNDERLINE)
        ssh_row_start = 3

        # Display SSH connection options
        row_offset = 0
        for idx, option in enumerate(ssh_options):
            row = ssh_row_start + row_offset
            if idx in active_processes and active_processes[idx].poll() is None:
                # Display "Connected to server" and show bound ports below
                status_text = " (Connected)"
                if idx == current_row:
                    stdscr.addstr(
                        row, 2, f"> {option}{status_text}", curses.A_REVERSE | curses.color_pair(1))
                else:
                    stdscr.addstr(
                        row, 2, f"  {option}{status_text}", curses.color_pair(1))

                # Display forwarded ports
                ports = active_ports.get(idx, [])
                for port in ports:
                    row_offset += 1
                    stdscr.addstr(row + row_offset, 4, f"    {port}")
            elif idx == current_row:
                stdscr.addstr(row, 2, f"> {option}", curses.A_REVERSE)
            else:
                stdscr.addstr(row, 2, f"  {option}")

            row_offset += 1

        # Space between SSH and VSCode options
        vscode_row_start = ssh_row_start + row_offset + 2
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
                    del active_ports[ssh_index]
                else:
                    stdscr.addstr(
                        0, 0, f"Connecting to {ssh_config['name']}...")
                    active_process = create_ssh_tunnel_from_config(ssh_config)
                    if active_process is not None:
                        active_processes[ssh_index] = active_process
                        active_ports[ssh_index] = [port.split(
                            ":")[0] for port in ssh_config['ports']]
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


def signal_handler(active_processes):
    """Signal handler for graceful shutdown"""
    for process in active_processes.values():
        if process.poll() is None:
            print("\nTerminating SSH connection...")
            process.terminate()

    sys.exit(0)
