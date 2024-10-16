# yocli

yocli is a command-line interface (CLI) tool designed to simplify your development workflow by managing SSH connections and opening VSCode projects. This documentation will guide you through installation, configuration, usage, and advanced features of yocli.

## Table of Contents

- Features
- Installation
- Configuration
- Usage
  - Interactive Menu Example
  - How to Use
- Advanced Usage
  - Running Multiple SSH Connections
  - Port Forwarding
- Troubleshooting
- License
- Contributing

## Features

- **SSH Management**: Establish and manage multiple SSH tunnels simultaneously, with local or remote access options.
- **VSCode Project Launcher**: Launch your development projects in VSCode from a predefined list.
- **Interactive Menu**: User-friendly CLI with an interactive interface for easy selection of SSH connections and VSCode projects.

## Installation

To install yocli as a command-line tool, follow these steps:

1. Clone the repository:

```bash
git clone https://github.com/yourusername/yocli.git
cd yocli
```

1. Install the package using pip:

```bash
pip install .
```

1. Optionally, make the tool executable:

```bash
chmod +x yocli.py
sudo mv yocli.py /usr/local/bin/yocli
```

## Configuration

yocli uses a configuration file (config.yml) to define SSH connections and VSCode projects. Below is an example configuration:

```yaml
services:
  vscode:
    - name: App
      commands:
        - code ~/git/my-repo

    - name: App 2
      commands:
        - code --remote ssh-remote+home /home/myName/git/my-repo

  ssh:
    - name: home
      host: myserver.com
      port: 3456
      host-local: 192.168.3.2
      port-local: 22
      user: me
      identity_file: ~/.ssh/id_rsa
      ports:
        - 3000:3000

    - name: home-2
      host: myserver2.com
      port: 3457
      host-local: 192.168.3.3
      port-local: 22
      user: me
      identity_file: ~/.ssh/id_rsa
      ports:
        - 8080:8080
```

## Configuration Fields

- vscode: List of VSCode projects with commands to open them.

- ssh: List of SSH connections, each with:
  - name: The name of the SSH connection.
  - host and host-local: Remote and local addresses.
  - port and port-local: Remote and local ports.
  - user: The SSH user.
  - identity_file: The private key for authentication.
  - ports: List of port forwarding rules.

## Usage

To run yocli, simply type the following command in your terminal:

```bash
yocli
```

You will be greeted with an interactive menu that allows you to:

- Connect to SSH servers.
- Disconnect from active SSH connections.
- Launch VSCode projects.
- Exit the tool.

### Interactive Menu Example

When you run yocli, you'll see an interactive menu that looks like this:

```bash
Hi, welcome. Choose your action:

*SSH connections:*
> Connect to home
  Connect to home-2

*VSCode projects:*
  App
  App 2

  Exit
```

## How to Use

1. SSH Connections:

- Select "Connect to [name]" to establish an SSH tunnel. If the connection is already active, selecting it again will disconnect it.
- Multiple SSH connections can be active simultaneously, as long as their port configurations do not overlap.

1. VSCode Projects:

- Select a project from the list to open it in VSCode. The commands for each project are predefined in the configuration file.

1. Exit:

- Select "Exit" to close all active SSH connections and exit the tool.

## Advanced Usage

### Running Multiple SSH Connections

yocli allows you to manage multiple SSH connections at the same time, as long as the port forwarding configurations do not overlap. You can connect to one or more SSH servers by selecting them from the interactive menu.

### Port Forwarding

Each SSH connection in the configuration file includes a list of port forwarding rules. These rules allow you to forward local ports to remote services running on the server, making it easy to access those services from your local environment.

## Troubleshooting

- SSH Connection Fails: Make sure that the host, user, and identity_file are correctly specified in the configuration. Check your network connectivity.
- Ports Already in Use: If a port is already in use, modify the port forwarding rules in the configuration file to avoid conflicts.
- VSCode Projects Not Opening: Ensure VSCode is installed and accessible from your command line (code command should work).

## License

This project is licensed under the MIT License. See the LICENSE file for more information.

## Contributing

Feel free to submit issues or pull requests to help improve yocli.
