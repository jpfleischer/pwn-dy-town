import subprocess
import os
import platform

def is_running_in_docker():
    """
    Return True if we're running in Docker. We can detect by:
    1) Checking an environment variable like 'IS_DOCKER'
    2) Checking for the /.dockerenv file.
    """
    # Method 1: Check an env variable set in Dockerfile, e.g. ENV IS_DOCKER=1
    if os.environ.get('IS_DOCKER') == '1':
        return True

    # Method 2: Check for /.dockerenv file.
    if os.path.exists('/.dockerenv'):
        return True

    return False

def get_python_interpreter_path():
    """
    Determine which Python interpreter to use.
    1) If running in Docker, just use 'python' or 'python3' from the container.
    2) Otherwise, fallback to the user's local virtual environment.
    """
    if is_running_in_docker():
        # Inside Docker, just use the system python
        return 'python'  # or 'python3'
    else:
        # Not in Docker; use local virtual environment
        home_dir = os.path.expanduser('~')
        if platform.system() == 'Linux':
            return os.path.join(home_dir, 'ENV3', 'bin', 'python')
        elif platform.system() == 'Windows':
            return os.path.join(home_dir, 'ENV3', 'Scripts', 'python.exe')
        else:
            raise EnvironmentError("Unsupported OS")

def run_script(script_path, use_wsl=False, python_interpreter=None):
    """
    Spawn a subprocess to run the given script with the chosen interpreter.
    If 'use_wsl' is set, we assume a special WSL-based command. Otherwise, we just
    run `[python_interpreter, script_path]`.
    """
    if use_wsl:
        command = ['wsl', '/home/fat/ENV3/bin/python', script_path]
    else:
        command = [python_interpreter, script_path]

    return subprocess.Popen(command)

def main():
    # Determine the appropriate Python interpreter path
    python_interpreter = get_python_interpreter_path()

    # Start grabber.py
    grabber_process = run_script(
        'overlay/grabber.py',
        python_interpreter=python_interpreter
    )

    # Start scraper.py
    cool_process = run_script(
        'scraper.py',
        python_interpreter=python_interpreter
    )

    # Wait for all processes to complete
    grabber_process.wait()
    cool_process.wait()

if __name__ == "__main__":
    main()
