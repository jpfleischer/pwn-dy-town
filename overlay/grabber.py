import re
import time
import os
import glob
import platform
from datetime import datetime
from PIL import Image

# Windows-only imports
if platform.system() == "Windows":
    import win32gui
    import win32ui
    from ctypes import windll

# Cross-platform screenshot library
try:
    # set os display
    os.environ['DISPLAY'] = ':1'
    import pyautogui
except ImportError:
    print("PyAutoGUI is required for Linux screenshots. Install it via 'pip install pyautogui'.", flush=True)

def get_next_output_filename(directory, prefix):
    # Ensure the directory exists
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Get the current timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Return the filename with the timestamp
    return os.path.join(directory, f"{prefix}-{timestamp}.png")

def take_screenshot(output_file, window_title=None):
    if platform.system() == "Windows":
        # Windows-specific screenshot using win32gui
        hwnd = win32gui.FindWindow(None, window_title)
        if not hwnd:
            print(f"Window with title '{window_title}' not found.", flush=True)
            return

        # Set the process to be DPI aware to handle high DPI displays
        windll.user32.SetProcessDPIAware()

        # Get the window rectangle
        left, top, right, bot = win32gui.GetWindowRect(hwnd)
        w = right - left
        h = bot - top

        hwndDC = win32gui.GetWindowDC(hwnd)
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)
        saveDC = mfcDC.CreateCompatibleDC()

        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, w, h)

        saveDC.SelectObject(saveBitMap)

        # Capture the window
        result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 3)
        print(result, flush=True)

        bmpinfo = saveBitMap.GetInfo()
        bmpstr = saveBitMap.GetBitmapBits(True)

        im = Image.frombuffer(
            'RGB',
            (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
            bmpstr, 'raw', 'BGRX', 0, 1)

        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwndDC)

        if result == 1:
            # PrintWindow Succeeded
            im.save(output_file)
            print(f"Screenshot saved to {output_file}", flush=True)
        else:
            print("Failed to capture the window.", flush=True)

    elif platform.system() == "Linux":
        # Linux-specific screenshot using PyAutoGUI
        screenshot = pyautogui.screenshot()
        screenshot.save(output_file)
        print(f"Screenshot saved to {output_file}", flush=True)

def find_window_with_title_partials(partials):
    if platform.system() == "Windows":
        def callback(hwnd, extra):
            title = win32gui.GetWindowText(hwnd)
            if all(partial in title for partial in partials):
                extra.append(hwnd)
            return True

        hwnds = []
        win32gui.EnumWindows(callback, hwnds)
        return hwnds[0] if hwnds else None
    elif platform.system() == "Linux":
        print("Linux version does not support partial title window finding.", flush=True)
        return None

def main():
    directory = 'overlay/input_grabs'
    prefix = 'screengrab-input'
    partial_titles = ['Pony Town', 'Mozilla Firefox']

    while True:
        if platform.system() == "Windows":
            # Find the window with the specified partial titles on Windows
            hwnd = find_window_with_title_partials(partial_titles)
            if hwnd:
                # Generate the output filename with a timestamp
                output_file = get_next_output_filename(directory, prefix)
                # Take the screenshot
                take_screenshot(output_file, win32gui.GetWindowText(hwnd))
            else:
                print("Window with 'Pony Town' and 'Mozilla Firefox' not found!", flush=True)

        elif platform.system() == "Linux":
            # Direct screenshot on Linux
            output_file = get_next_output_filename(directory, prefix)
            take_screenshot(output_file)

        # Sleep for 1 second before taking the next screenshot
        time.sleep(1)

if __name__ == "__main__":
    main()
