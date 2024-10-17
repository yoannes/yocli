import curses
import threading
import time
from threading import Lock

from yocli.ssh import create_ssh_tunnel_from_config
from yocli.vscode import open_vscode

lock = Lock()

HEADER_POSITION = 0
SECTION_INDENTATION = 1
ROW_OFFSET_INCREMENT = 1
STATUS_CONNECTED = " (Connected)"


def init_curses_colors():
    """Initialize color mode"""
    if curses.has_colors():
        curses.start_color()
        try:
            # Define some color pairs with adaptable background
            curses.init_pair(1, curses.COLOR_CYAN, -1)
        except curses.error:
            # Fallback to black background if default fails
            curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)


def check_ssh_connections(active_processes, active_ports):
    """Continuously check the status of SSH connections."""
    while True:
        with lock:
            for idx, process in list(active_processes.items()):
                if process.poll() is not None:  # Process has ended
                    del active_processes[idx]
                    if idx in active_ports:
                        del active_ports[idx]
        time.sleep(1)  # Check every 1 second


def generate_options(config):
    ssh_configs = config['services']['ssh']
    ssh_options = [f"Connect to {ssh['name']}" for ssh in ssh_configs]

    vscode_projects = config['services']['vscode']
    vscode_options = [
        f"VSCode: {project['name']}" for project in vscode_projects]
    menu_options = ssh_options + vscode_options + ["Exit"]

    return ssh_options, vscode_options, menu_options


def display_ssh_options(stdscr, active_processes, active_ports, current_row, ssh_options, ssh_row_start):
    row_offset = 0
    for idx, option in enumerate(ssh_options):
        row = ssh_row_start + row_offset
        if idx in active_processes and active_processes[idx].poll() is None:
            status_text = STATUS_CONNECTED
            add_styled_option(stdscr, row, option, status_text,
                              current_row, idx, active_processes)
            # Display forwarded ports
            ports = active_ports.get(idx, [])
            for port in ports:
                row_offset += ROW_OFFSET_INCREMENT
                stdscr.addstr(row + row_offset,
                              SECTION_INDENTATION + 2, f"{port}")
        else:
            add_styled_option(stdscr, row, option, "",
                              current_row, idx, active_processes)

        row_offset += ROW_OFFSET_INCREMENT

    row_offset += ROW_OFFSET_INCREMENT

    return row_offset


def display_vscode_options(stdscr, current_row, vscode_options, ssh_options, ssh_row_start, row_offset):
    vscode_row_start = ssh_row_start + row_offset + ROW_OFFSET_INCREMENT
    stdscr.addstr(vscode_row_start - 1, HEADER_POSITION,
                  "*VSCode projects:*", curses.A_UNDERLINE)

    for idx, project in enumerate(vscode_options):
        row = vscode_row_start + idx
        add_styled_option(
            stdscr, row, project[7:], "", current_row, idx + len(ssh_options), active_processes=None)

    return vscode_row_start, row_offset


def display_exit(stdscr, current_row, menu_options, vscode_options, vscode_row_start):
    exit_row = vscode_row_start + len(vscode_options) + ROW_OFFSET_INCREMENT
    if current_row == len(menu_options) - 1:
        stdscr.addstr(exit_row, SECTION_INDENTATION,
                      "> Exit", curses.A_REVERSE)
    else:
        stdscr.addstr(exit_row, SECTION_INDENTATION, "  Exit")


def connect_to_ssh_server(stdscr, ssh_configs, active_processes, active_ports, current_row):
    ssh_index = current_row
    ssh_config = ssh_configs[ssh_index]
    stdscr.clear()
    with lock:
        if ssh_index in active_processes and active_processes[ssh_index].poll() is None:
            stdscr.addstr(HEADER_POSITION, HEADER_POSITION,
                          f"Disconnecting from {ssh_config['name']}...")
            active_processes[ssh_index].terminate()
            del active_processes[ssh_index]
            if ssh_index in active_ports:
                del active_ports[ssh_index]
        else:
            stdscr.addstr(HEADER_POSITION, HEADER_POSITION,
                          f"Connecting to {ssh_config['name']}...")
            active_process = create_ssh_tunnel_from_config(ssh_config)
            if active_process is not None and active_process.poll() is None:
                active_processes[ssh_index] = active_process
                active_ports[ssh_index] = [port.split(
                    ":")[0] for port in ssh_config['ports']]

    stdscr.refresh()
    time.sleep(1)


def add_styled_option(stdscr, row, option, status, current_row, idx, active_processes):
    """Add styled text for the menu options, highlighting the current row"""
    text = f"> {option}{status}" if idx == current_row else f"  {option}{status}"
    if idx == current_row:
        stdscr.addstr(row, SECTION_INDENTATION, text,
                      curses.A_REVERSE | curses.color_pair(1))
    else:
        stdscr.addstr(row, SECTION_INDENTATION, text)


# Main interactive menu function
def interactive_menu(stdscr, config, active_processes):
    init_curses_colors()
    curses.curs_set(0)
    stdscr.clear()

    ssh_configs = config['services']['ssh']
    vscode_projects = config['services']['vscode']
    active_ports = {}
    ssh_options, vscode_options, menu_options = generate_options(config)
    current_row = 0

    # Start a background thread to monitor SSH connections
    threading.Thread(target=check_ssh_connections, args=(
        active_processes, active_ports), daemon=True).start()

    while True:
        stdscr.clear()
        stdscr.addstr(HEADER_POSITION, HEADER_POSITION,
                      "Hi, welcome. Choose your actions:\n", curses.A_BOLD | curses.color_pair(1))

        stdscr.addstr(2, HEADER_POSITION,
                      "*SSH connections:*", curses.A_UNDERLINE)
        ssh_row_start = 3

        row_offset = display_ssh_options(
            stdscr, active_processes, active_ports, current_row, ssh_options, ssh_row_start)

        vscode_row_start, row_offset = display_vscode_options(
            stdscr, current_row, vscode_options, ssh_options, ssh_row_start, row_offset)

        display_exit(stdscr, current_row, menu_options,
                     vscode_options, vscode_row_start)

        key = stdscr.getch()

        # Navigate the menu
        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(menu_options) - 1:
            current_row += 1
        elif key == curses.KEY_ENTER or key in [10, 13]:
            if current_row < len(ssh_options):
                connect_to_ssh_server(
                    stdscr, ssh_configs, active_processes, active_ports, current_row)
            elif current_row == len(menu_options) - 1:
                for process in active_processes.values():
                    if process.poll() is None:
                        process.terminate()
                break
            else:
                project_index = current_row - len(ssh_options)
                project = vscode_projects[project_index]
                stdscr.clear()
                stdscr.addstr(HEADER_POSITION, HEADER_POSITION,
                              f"Opening VSCode for Project {project['name']}...")
                stdscr.refresh()
                time.sleep(1)
                open_vscode(project['commands'])

        stdscr.refresh()
