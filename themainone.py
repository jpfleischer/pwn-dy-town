import subprocess
import os

def run_script(script_path, use_wsl=False, python_interpreter='python'):
    if use_wsl:
        command = ['wsl', '/home/fat/ENV3/bin/python', script_path]
    else:
        command = [python_interpreter, script_path]
    
    return subprocess.Popen(command)

def main():
    # Get the home directory dynamically
    home_dir = os.path.expanduser('~')

    # Start grabber.py
    grabber_process = run_script(
        'overlay/grabber.py', 
        python_interpreter=os.path.join(home_dir, 'ENV3', 'Scripts', 'python')
    )

    # Start overlay.py in WSL
    # overlay_process = run_script('overlay/overlay.py', use_wsl=True)

    # Start scraper.py using the specified Python interpreter
    cool_process = run_script(
        'scraper.py', 
        python_interpreter=os.path.join(home_dir, 'ENV3', 'Scripts', 'python')
    )

    # Wait for all processes to complete
    grabber_process.wait()
    # overlay_process.wait()
    cool_process.wait()

if __name__ == "__main__":
    main()