import re
import time
import os
import glob
import win32gui
import win32ui
from ctypes import windll
from PIL import Image

def get_next_output_filename(directory, prefix):
    # Ensure the directory exists
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Find all files matching the pattern prefix-*.png
    files = glob.glob(os.path.join(directory, f"{prefix}-*.png"))
    if not files:
        return os.path.join(directory, f"{prefix}-1.png")

    # Extract numbers from filenames and find the highest number
    numbers = [int(re.search(rf"{prefix}-(\d+).png", os.path.basename(f)).group(1)) for f in files]
    next_number = max(numbers) + 1
    return os.path.join(directory, f"{prefix}-{next_number}.png")

def take_screenshot(output_file, window_title):
    # Find the window with the specified title
    hwnd = win32gui.FindWindow(None, window_title)
    if not hwnd:
        print(f"Window with title '{window_title}' not found.")
        return

    # Set the process to be DPI aware to handle high DPI displays
    windll.user32.SetProcessDPIAware()

    # Get the window rectangle
    left, top, right, bot = win32gui.GetWindowRect(hwnd)
    w = right - left
    h = bot - top

    hwndDC = win32gui.GetWindowDC(hwnd)
    mfcDC  = win32ui.CreateDCFromHandle(hwndDC)
    saveDC = mfcDC.CreateCompatibleDC()

    saveBitMap = win32ui.CreateBitmap()
    saveBitMap.CreateCompatibleBitmap(mfcDC, w, h)

    saveDC.SelectObject(saveBitMap)

    # Capture the window
    result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 3)
    print(result)

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
        print(f"Screenshot saved to {output_file}")
    else:
        print("Failed to capture the window.")

def find_window_with_title_partials(partials):
    # Iterate over all windows and find one that matches the partial titles
    def callback(hwnd, extra):
        title = win32gui.GetWindowText(hwnd)
        if all(partial in title for partial in partials):
            extra.append(hwnd)
        return True

    hwnds = []
    win32gui.EnumWindows(callback, hwnds)
    return hwnds[0] if hwnds else None

def main():
    directory = 'overlay/input_grabs'
    prefix = 'screengrab-input'
    partial_titles = ['Pony Town', 'Mozilla Firefox']

    while True:
        # Find the window with the specified partial titles
        hwnd = find_window_with_title_partials(partial_titles)
        if hwnd:
            # Generate the next output filename
            output_file = get_next_output_filename(directory, prefix)
            # Take the screenshot
            take_screenshot(output_file, win32gui.GetWindowText(hwnd))
        else:
            print("Window with 'Pony Town' and 'Mozilla Firefox' not found!")

        # Sleep for 1 second before taking the next screenshot
        time.sleep(1)

if __name__ == "__main__":
    main()