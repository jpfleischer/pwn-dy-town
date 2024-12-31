import subprocess
import os
import platform
import time
import sys

def is_running_in_docker():
    """
    Return True if we're running in Docker. We can detect by:
    1) Checking an environment variable like 'IS_DOCKER'
    2) Checking for the /.dockerenv file.
    """
    print("[themainone] Checking if running in Docker...", flush=True)
    if os.environ.get('IS_DOCKER') == '1':
        print("[themainone] IS_DOCKER=1 found.", flush=True)
        return True

    if os.path.exists('/.dockerenv'):
        print("[themainone] /.dockerenv found.", flush=True)
        return True

    print("[themainone] Not running in Docker.", flush=True)
    return False

def get_python_interpreter_path():
    """
    Determine which Python interpreter to use.
    1) If running in Docker, just use 'python' or 'python3' from the container.
    2) Otherwise, fallback to the user's local virtual environment.
    """
    print("[themainone] Determining Python interpreter path...", flush=True)
    if is_running_in_docker():
        print("[themainone] Running in Docker. Using 'python'.", flush=True)
        return 'python'  # or 'python3'
    else:
        print("[themainone] Not in Docker. Using ENV3 from home directory.", flush=True)
        home_dir = os.path.expanduser('~')
        if platform.system() == 'Linux':
            return os.path.join(home_dir, 'ENV3', 'bin', 'python')
        elif platform.system() == 'Windows':
            return os.path.join(home_dir, 'ENV3', 'Scripts', 'python.exe')
        else:
            raise EnvironmentError("Unsupported OS")

def run_script(script_path, use_wsl=False, python_interpreter=None, capture_output=False):
    """
    Spawn a subprocess to run the given script with the chosen interpreter.
    If 'use_wsl' is set, we assume a special WSL-based command. Otherwise, we just
    run `[python_interpreter, script_path]`.

    If 'capture_output' is True, stdout will be piped so we can read it.
    """
    if use_wsl:
        command = ['wsl', '/home/fat/ENV3/bin/python', script_path]
    else:
        command = [python_interpreter, script_path]

    print(f"[themainone] Starting script: {script_path} with command: {command}, capture_output={capture_output}", flush=True)
    if capture_output:
        return subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
    else:
        return subprocess.Popen(command)

def main():
    """
    Main entrypoint:
    1) Start scraper.py and wait for its output line "Starting grabber now".
    2) If that line appears, start grabber.py.
    3) If either process exits unexpectedly, terminate the other and exit.
    """
    print("[themainone] main() started.", flush=True)
    python_interpreter = get_python_interpreter_path()

    # Start the scraper with captured stdout
    scraper_process = run_script(
        'scraper.py',
        python_interpreter=python_interpreter,
        capture_output=True
    )

    grabber_process = None
    grabber_started = False

    # Continuously read the scraper's stdout
    while True:
        line = scraper_process.stdout.readline()

        # If we read an empty string, check if scraper has actually exited:
        if not line:
            # Check if scraper ended
            poll_value = scraper_process.poll()
            print(f"[themainone] Read empty line. scraper.poll()={poll_value}", flush=True)
            if poll_value is not None:
                # Scraper truly ended; no more lines to read
                print("[themainone] Scraper ended. Exiting read loop.", flush=True)
                break
            # Otherwise, keep waiting for more output
            continue

        # Show each line from scraper (optional)
        print(f"[themainone] Scraper output: {line.rstrip()}", flush=True)

        # Check if "Starting grabber now" is in the scraper output
        if "Starting grabber now" in line and not grabber_started:
        # if not grabber_started:
            print("[themainone] Trigger found. Starting grabber...", flush=True)
            grabber_process = run_script(
                'overlay/grabber.py',
                python_interpreter=python_interpreter
            )
            grabber_started = True

        # If the scraper has exited, stop reading
        spoll = scraper_process.poll()
        if spoll is not None:
            print(f"[themainone] Scraper poll={spoll}; stopping read loop.", flush=True)
            break

        # If grabber has been started, check if it exited unexpectedly
        if grabber_process is not None:
            gpoll = grabber_process.poll()
            if gpoll is not None:
                print(f"[themainone] Grabber exited unexpectedly with code {gpoll}. Terminating scraper.", flush=True)
                scraper_process.terminate()
                scraper_process.wait(timeout=5)
                sys.exit(gpoll)

    # When we exit the loop, the scraper has finished or crashed
    scraper_return = scraper_process.poll()
    if scraper_return is None:
        print("[themainone] Scraper still running; waiting for it to exit...", flush=True)
        scraper_return = scraper_process.wait()

    print(f"[themainone] Scraper returned code={scraper_return}", flush=True)

    # If the grabber was started, check if it's still running; if so, kill it
    if grabber_process is not None:
        grabber_return = grabber_process.poll()
        if grabber_return is None:
            print("[themainone] Grabber is still running; terminating it now.", flush=True)
            grabber_process.terminate()
            grabber_process.wait(timeout=5)
        else:
            print(f"[themainone] Grabber already ended with code={grabber_return}.", flush=True)
        sys.exit(scraper_return)
    else:
        # Grabber was never started, just exit with scraper's code
        print("[themainone] Grabber was never started; exiting with scraper code.", flush=True)
        sys.exit(scraper_return)

if __name__ == "__main__":
    main()
