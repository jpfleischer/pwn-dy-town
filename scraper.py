from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import json
import time
import os
import mysql.connector

# Load saved cookies from the JSON file
with open('cookies.json', 'r') as file:
    cookies = json.load(file)

# Start a new Firefox WebDriver session
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
        print(f"Error adding cookie: {cookie['name']}, {e}")

# Navigate to the specific page
driver.get('https://pony.town/')

# Allow time for the page to load and check for the update panel
try:
    # Wait for the update panel to appear and find the close button if it exists
    close_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CLASS_NAME, 'btn-close'))
    )
    close_button.click()
    print("Closed the update panel.")
except Exception:
    print("Update panel not found; proceeding.")

time.sleep(2)
# Now wait for and click the "Play" button
play_button = WebDriverWait(driver, 20).until(
    EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'btn-success') and contains(., 'Play')]"))
)
play_button.click()

time.sleep(3)

# Perform additional setup steps
print('going to click settings now')
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
print('sending file path now')

current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, "pony-town-settings.json")
file_input.send_keys(file_path)
print('file path sent')

ok_button = WebDriverWait(driver, 20).until(
    EC.element_to_be_clickable((By.XPATH, "//button[@class='btn btn-wide btn-outline-secondary ms-2' and contains(text(), 'OK')]"))
)
ok_button.click()
print('OK button clicked')

time.sleep(1)

# Activate the page (just in case)
webdriver.ActionChains(driver).send_keys(Keys.F6).perform()

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
    print(f'Pressed {key}')

# Duration for each interval (14 minutes = 840 seconds)
interval_duration = 14 * 60
check_interval = 30  # Interval to check chat lines (30 seconds)

# Database connection details
db_config = {
    'user': 'myuser',
    'password': 'mypassword',
    'host': 'localhost',
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
        print(f"Error: {err}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Start an infinite loop to alternate between pressing 'D' and 'A'
while True:
    # Alternate between pressing '2' and '3'
    for key in ['2', '3']:
        # 14-minute loop
        for _ in range(0, interval_duration, check_interval):
            # Retrieve the chat lines collected by the MutationObserver
            chat_lines = driver.execute_script("return window.getChatLines();")

            if chat_lines:
                # Read existing chat lines from the JSON file
                if os.path.exists('chat_lines.json'):
                    with open('chat_lines.json', 'r', encoding='utf-8') as file:
                        existing_chat_lines = json.load(file)
                else:
                    existing_chat_lines = []

                # Remove duplicates between the new chat lines and existing ones
                new_chat_lines = remove_duplicates(chat_lines, existing_chat_lines)

                if new_chat_lines:
                    # Append new chat lines to the existing chat lines
                     insert_chat_lines_to_db(new_chat_lines)

                    # Save the updated chat lines to the JSON file
                    # with open('chat_lines.json', 'w', encoding='utf-8') as file:
                        # json.dump(existing_chat_lines, file, ensure_ascii=False, indent=4)

                     print(f'Added {len(new_chat_lines)} new chat lines.')

            # Wait for the next 30 seconds to check chat lines again
            time.sleep(check_interval)
        
        # After 14 minutes, press the key ('2' or '3')
        press_key(key)