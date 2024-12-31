import platform
import os
import json
import time
import mysql.connector
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import (
    StaleElementReferenceException,
    NoSuchElementException,
    TimeoutException
)
import sys

def ts_print(message, flush=True):
    """
    Print a message with a timestamp prepended.
    """
    now = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    print(f"[{now}] {message}", flush=flush)


def setup_pony_town(driver):
    """
    Perform all the steps needed to get from a blank browser session
    into the Pony Town game with the desired settings.
    If *anything* fails, raise an exception to indicate we should retry.
    """
    driver.get('https://pony.town')

    # Load cookies from JSON
    if os.path.exists('cookies.json'):
        with open('cookies.json', 'r') as f:
            cookies = json.load(f)
        for cookie in cookies:
            if 'sameSite' in cookie and cookie['sameSite'] not in ["Strict", "Lax", "None"]:
                cookie['sameSite'] = 'None'
            driver.add_cookie(cookie)

    # Go to the main page
    driver.get('https://pony.town/')

    # Close update panel if present
    try:
        close_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, 'btn-close'))
        )
        close_button.click()
        ts_print("Closed the update panel.")
    except Exception:
        ts_print("Update panel not found; proceeding.")

    time.sleep(2)

    # Click "Play" button
    play_button = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'btn-success') and contains(., 'Play')]"))
    )
    play_button.click()
    ts_print("Clicked Play")

    # Wait a bit for the world to load
    time.sleep(3)

    # Example: click settings
    ts_print("Going to click settings now...")
    # time.sleep(7)
    found_settings = False

    for attempt in range(6):
        try:
            # time.sleep(1)
            settings_button = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//ui-button[@title='Settings' and @aria-haspopup='true']"))
            )
            settings_button.click()
            found_settings = True
            break
        except StaleElementReferenceException:
            ts_print("StaleElementReferenceException: Re-locating settings_button and retrying...")

    if not found_settings:
        raise Exception("Could not click 'Settings' even after multiple retries.")

    # Next step: click "Open game settings" link
    # time.sleep(3)
    found_link = False
    for attempt in range(6):
        try:
            # time.sleep(1)
            settings_link = driver.find_element(
                By.XPATH,
                "//a[@title='Open game settings' and contains(@class, 'dropdown-item')]"
            )
            settings_link.click()
            ts_print("Clicked settings link")
            found_link = True
            break
        except StaleElementReferenceException:
            ts_print("StaleElementReferenceException: trying to click open settings again")
        except NoSuchElementException:
            ts_print("NoSuchElementException: trying again")

    if not found_link:
        raise Exception("Could not click 'Open game settings' even after multiple retries.")

    # Wait for the file input and send your file
    file_input = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
    )
    # time.sleep(1)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "pony-town-settings.json")
    file_input.send_keys(file_path)
    ts_print("Pony Town settings file sent")

    ok_button = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, "//button[@class='btn btn-wide btn-outline-secondary ms-2' and contains(text(), 'OK')]"))
    )
    ok_button.click()
    ts_print("OK button clicked")

    # time.sleep(2)

    # Attempt to toggle the UI off
    for attempt in range(3):
        try:
            settings_button = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//ui-button[@title='Settings']"))
            )
            settings_button.click()
            break
        except StaleElementReferenceException:
            ts_print("StaleElementReferenceException: Re-locating settings_button and retrying...")
        except Exception as e:
            ts_print(f"the exception was {e}")

    # time.sleep(2)

    uitoggle = driver.find_element(By.XPATH, "//a[@title='Toggle showing game UI' and contains(@class, 'dropdown-item')]")
    uitoggle.click()
    ts_print("UI Disabled")

    time.sleep(2)
        
    for attempt in range(3):
        try:
            settings_button = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//ui-button[@title='Settings']"))
            )
            settings_button.click()
            break
        except StaleElementReferenceException:
            ts_print("StaleElementReferenceException: Re-locating settings_button and retrying...")

    ts_print("Setup completed successfully. (Starting grabber now)")


############################################
# Driver setup (just like your original code)
if platform.system() == 'Linux':
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options

    chrome_driver_path = '/usr/bin/chromedriver'  # Adjust path if needed
    chrome_options = Options()
    # chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("--display=:1")

    service = Service(chrome_driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_window_size(1920, 1080)
else:
    driver = webdriver.Firefox()

############################################
# 1) Attempt the setup, retry if there's an exception
while True:
    try:
        setup_pony_town(driver)
        break  # If we got here, the setup succeeded; break the retry loop
    except Exception as e:
        ts_print(f"Setup failed with exception: {e}")
        ts_print("Re-navigating to pony.town and retrying setup in 5 seconds...")
        time.sleep(5)
        driver.get("https://pony.town")

############################################
# 2) Once setup is complete, run your main loop
ts_print("Now entering the main chat-collecting loop...")

# JavaScript code for the mutation observer
mutation_observer_script = """
const chatLines = [];
const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
        mutation.addedNodes.forEach((node) => {
            if (node.classList && node.classList.contains('chat-line')) {
                const now = new Date();
                const time = now.toISOString().slice(0, 19).replace('T', ' ');

                let name = node.querySelector('.chat-line-name-content').innerHTML;
                name = name.replace(/<img[^>]*alt="([^"]*)"[^>]*>/g, (match, alt) => alt);

                let message = node.querySelector('.chat-line-message').innerHTML;
                message = message.replace(/<img[^>]*alt="([^"]*)"[^>]*>/g, (match, alt) => alt);

                chatLines.push({ time, name, message });
            }
        });
    });
});
observer.observe(document.body, { childList: true, subtree: true });
window.getChatLines = () => {
    const collectedLines = [...chatLines];
    chatLines.length = 0;
    return collectedLines;
};
"""
driver.execute_script(mutation_observer_script)

def press_key(key):
    actions = ActionChains(driver)
    actions.send_keys(key)
    actions.perform()
    ts_print(f'Pressed {key}')

interval_duration = 9 * 60
check_interval = 15

db_config = {
    'user': 'myuser',
    'password': 'mypassword',
    'host': 'db',
    'database': 'mydatabase'
}

def remove_duplicates(new_chat_lines, existing_chat_lines):
    existing_set = {json.dumps(line) for line in existing_chat_lines}
    return [line for line in new_chat_lines if json.dumps(line) not in existing_set]

def insert_chat_lines_to_db(chat_lines):
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        for line in chat_lines:
            cursor.execute("""
                INSERT INTO messages (content, sender, timestamp, coordinates)
                VALUES (%s, %s, %s, ST_GeomFromText(%s))
            """, (line['message'], line['name'], line['time'], 'POINT(0 0)'))
        connection.commit()
    except mysql.connector.Error as err:
        ts_print(f"Error: {err}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()


############################################
# 3) The final loop for pressing keys, checking lines, etc.
while True:
    # Alternate between pressing '2' and '3'
    for key in ['2', '3']:
        # 9-minute loop
        for _ in range(0, interval_duration, check_interval):
            # We wrap execute_script in a try/except to handle TimeoutException
            try:
                chat_lines = driver.execute_script("return window.getChatLines();")
            except TimeoutException:
                ts_print("Script timeout encountered. Possibly 'Play' reappeared.")
                chat_lines = []

            if not chat_lines:
                # If no chat lines, let's see if "Play" reappeared
                ts_print("No chat lines found. Checking 'Play' button...")
                try:
                    play_button = driver.find_element(
                        By.XPATH,
                        "//button[contains(@class, 'btn-success') and contains(., 'Play')]"
                    )
                    time.sleep(2)
                    play_button.click()
                    ts_print("Clicked 'Play' button again.")
                except Exception as e:
                    ts_print(f"No 'Play' button or error: {e}")
            else:
                if os.path.exists('chat_lines.json'):
                    with open('chat_lines.json', 'r', encoding='utf-8') as file:
                        existing_chat_lines = json.load(file)
                else:
                    existing_chat_lines = []

                new_chat_lines = remove_duplicates(chat_lines, existing_chat_lines)
                if new_chat_lines:
                    insert_chat_lines_to_db(new_chat_lines)
                    ts_print(f'Added {len(new_chat_lines)} new chat lines.')

            time.sleep(check_interval)

        # After 9 minutes, press the key ('2' or '3')
        press_key(key)