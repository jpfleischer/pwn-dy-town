import subprocess
import os
import platform

def get_python_interpreter_path():
    # Detect if the OS is Linux or Windows
    home_dir = os.path.expanduser('~')
    if platform.system() == 'Linux':
        return os.path.join(home_dir, 'ENV3', 'bin', 'python')
    elif platform.system() == 'Windows':
        return os.path.join(home_dir, 'ENV3', 'Scripts', 'python.exe')
    else:
        raise EnvironmentError("Unsupported OS")

def run_script(script_path, use_wsl=False, python_interpreter=None):
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
