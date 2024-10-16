import subprocess


def open_vscode(commands):
    """Function to open VS Code for a specified project"""
    try:
        for command in commands:
            subprocess.call(command, shell=True)
    except Exception as e:
        print(f"Error opening VS Code for project: {e}")
