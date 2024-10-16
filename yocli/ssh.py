import os
import socket
import subprocess


def create_ssh_tunnel_from_config(ssh_config):
    """Function to create and manage SSH tunnel connection"""

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


def is_host_reachable(host, port):
    """Helper function to check if host is reachable"""

    try:
        # Try to connect to the host on the given port
        socket.create_connection((host, port), timeout=5)
        return True
    except (socket.timeout, socket.error):
        return False


def free_ports(ports_to_free):
    """Function to check and free any ports that are already in use"""

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
