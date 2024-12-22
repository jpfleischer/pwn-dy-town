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

# Load saved cookies from the JSON file
with open('cookies.json', 'r') as file:
    cookies = json.load(file)

# Determine the OS and set up the appropriate WebDriver
if platform.system() == 'Linux':
    # Use Chrome WebDriver with custom chromedriver path
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options

    # Path to your chromedriver
    chrome_driver_path = '/usr/bin/chromedriver'  # Adjust this path if necessary

    # Set Chrome options
    chrome_options = Options()
    # Uncomment the following line to run in headless mode
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("--display=:1")  # Specify display if needed

    # Set up the Chrome WebDriver with the service parameter and options
    service = Service(chrome_driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    # driver.maximize_window()
    driver.set_window_size(1920, 1080)


else:
    # Use Firefox WebDriver
    driver = webdriver.Firefox()

# Open the base domain (needed to add cookies)
driver.get('https://pony.town')

# Add the cookies to the current session
for cookie in cookies:
    if 'sameSite' in cookie and cookie['sameSite'] not in ["Strict", "Lax", "None"]:
        cookie['sameSite'] = 'None'  # Adjust 'sameSite' attribute if necessary
    try:
        driver.add_cookie(cookie)
    except Exception as e:
        print(f"Error adding cookie: {cookie['name']}, {e}", flush=True)

# Navigate to the specific page
driver.get('https://pony.town/')

# Allow time for the page to load and check for the update panel
try:
    # Wait for the update panel to appear and find the close button if it exists
    close_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CLASS_NAME, 'btn-close'))
    )
    close_button.click()
    print("Closed the update panel.", flush=True)
except Exception:
    print("Update panel not found; proceeding.", flush=True)

time.sleep(2)
# Now wait for and click the "Play" button
play_button = WebDriverWait(driver, 20).until(
    EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'btn-success') and contains(., 'Play')]"))
)
play_button.click()

time.sleep(3)

# Perform additional setup steps
print('going to click settings now', flush=True)
settings_button = WebDriverWait(driver, 20).until(
    EC.element_to_be_clickable((By.XPATH, "//ui-button[@title='Settings' and @aria-haspopup='true']"))
)
settings_button.click()

settings_link = WebDriverWait(driver, 20).until(
    EC.element_to_be_clickable((By.XPATH, "//a[@title='Open game settings' and contains(@class, 'dropdown-item')]"))
)
settings_link.click()

file_input = WebDriverWait(driver, 20).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
)
time.sleep(1)
print('sending file path now', flush=True)

current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, "pony-town-settings.json")
file_input.send_keys(file_path)
print('file path sent', flush=True)

ok_button = WebDriverWait(driver, 20).until(
    EC.element_to_be_clickable((By.XPATH, "//button[@class='btn btn-wide btn-outline-secondary ms-2' and contains(text(), 'OK')]"))
)
ok_button.click()
print('OK button clicked', flush=True)

time.sleep(1)

# Activate the page (just in case)
ActionChains(driver).send_keys(Keys.F6).perform()

# JavaScript code to use MutationObserver to watch for new chat lines and extract details
mutation_observer_script = """
const chatLines = [];
const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
        mutation.addedNodes.forEach((node) => {
            if (node.classList && node.classList.contains('chat-line')) {
                const now = new Date();
                const time = now.toISOString().slice(0, 19).replace('T', ' ');
                   
                // Extract and replace emoji <img> tags with their alt text in the name content
                let name = node.querySelector('.chat-line-name-content').innerHTML;
                name = name.replace(/<img[^>]*alt="([^"]*)"[^>]*>/g, (match, alt) => alt);

                // Extract and replace emoji <img> tags with their alt text in the message content
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
    chatLines.length = 0;  // Clear the chatLines array after returning the lines
    return collectedLines;
};
"""

# Execute the JavaScript code
driver.execute_script(mutation_observer_script)

# Function to press a key using Selenium ActionChains
def press_key(key):
    actions = ActionChains(driver)
    actions.send_keys(key)
    actions.perform()
    print(f'Pressed {key}', flush=True)

# Duration for each interval (9 minutes = 840 seconds)
interval_duration = 9 * 60
check_interval = 30  # Interval to check chat lines (30 seconds)

# Database connection details
db_config = {
    'user': 'myuser',
    'password': 'mypassword',
    'host': 'db',
    'database': 'mydatabase'
}

# Function to remove duplicates
def remove_duplicates(new_chat_lines, existing_chat_lines):
    existing_set = {json.dumps(line) for line in existing_chat_lines}
    return [line for line in new_chat_lines if json.dumps(line) not in existing_set]

# Function to insert chat lines into the database
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
        print(f"Error: {err}", flush=True)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Start an infinite loop to alternate between pressing '2' and '3'
while True:
    # Alternate between pressing '2' and '3'
    for key in ['2', '3']:
        # 9-minute loop
        for _ in range(0, interval_duration, check_interval):
            # Retrieve the chat lines collected by the MutationObserver
            chat_lines = driver.execute_script("return window.getChatLines();")

            if chat_lines:
                # Read existing chat lines from the JSON file (if needed)
                if os.path.exists('chat_lines.json'):
                    with open('chat_lines.json', 'r', encoding='utf-8') as file:
                        existing_chat_lines = json.load(file)
                else:
                    existing_chat_lines = []

                # Remove duplicates between the new chat lines and existing ones
                new_chat_lines = remove_duplicates(chat_lines, existing_chat_lines)

                if new_chat_lines:
                    # Insert new chat lines into the database
                    insert_chat_lines_to_db(new_chat_lines)
                    print(f'Added {len(new_chat_lines)} new chat lines.', flush=True)

            # Wait for the next 30 seconds to check chat lines again
            time.sleep(check_interval)
        
        # After 9 minutes, press the key ('2' or '3')
        press_key(key)
