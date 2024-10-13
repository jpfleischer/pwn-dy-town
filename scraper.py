from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
import json
import time
import os
import pyautogui

# Load saved cookies from the JSON file
with open('cookies.json', 'r') as file:
    cookies = json.load(file)

# Start a new Edge WebDriver session
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

# Navigate to the specific page (search query)
driver.get('https://pony.town/')

# Allow time for the page to load
WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, 'btn-success')))

# Locate the button by its class name and text content
button = WebDriverWait(driver, 20).until(
    EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'btn-success') and contains(., 'Play')]"))
)

# Click the button
button.click()

time.sleep(3)



print('going to click settings now')

# Click the settings button (ui-button with specific attributes)
settings_button = WebDriverWait(driver, 20).until(
    EC.element_to_be_clickable((By.XPATH, "//ui-button[@title='Settings' and @aria-haspopup='true']"))
)
settings_button.click()

# Click the second button (Settings link)
settings_link = WebDriverWait(driver, 20).until(
    EC.element_to_be_clickable((By.XPATH, "//a[@title='Open game settings' and contains(@class, 'dropdown-item')]"))
)
settings_link.click()

# # Click the third button (Import settings button)
# import_settings_button = WebDriverWait(driver, 20).until(
#     EC.element_to_be_clickable((By.XPATH, "//button[@title='Import settings' and contains(@class, 'btn-outline-secondary')]"))
# )
# import_settings_button.click()

# Locate the file input element and send the file path to it
file_input = WebDriverWait(driver, 20).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
)
time.sleep(1)
print('sending file path now')

# Get the current directory and construct the file path
current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, "pony-town-settings.json")
file_input.send_keys(file_path)
print('file path sent')

# Click the OK button
ok_button = WebDriverWait(driver, 20).until(
    EC.element_to_be_clickable((By.XPATH, "//button[@class='btn btn-wide btn-outline-secondary ms-2' and contains(text(), 'OK')]"))
)
ok_button.click()
print('OK button clicked')

time.sleep(1)

# # Press the 'O' key
# webdriver.ActionChains(driver).send_keys('O').perform()

# Press the 'F6' key
webdriver.ActionChains(driver).send_keys(Keys.F6).perform()

# JavaScript code to use MutationObserver to watch for new chat lines and extract details
mutation_observer_script = """
const chatLines = [];
const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
        mutation.addedNodes.forEach((node) => {
            if (node.classList && node.classList.contains('chat-line')) {
                const now = new Date();
                const time = new Intl.DateTimeFormat('en-US', {
                    timeZone: 'America/New_York',
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit',
                    hour12: false
                }).format(now);
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
window.getChatLines = () => chatLines;
"""

# Execute the JavaScript code
driver.execute_script(mutation_observer_script)

# Monitor and update chat lines for 15 minutes (900 seconds), updating every 30 seconds
end_time = time.time() + 900  # Run for 15 minutes
while time.time() < end_time:
    # Retrieve the chat lines collected by the MutationObserver
    chat_lines = driver.execute_script("return window.getChatLines();")
    
    # Read existing chat lines from the JSON file
    if os.path.exists('chat_lines.json'):
        with open('chat_lines.json', 'r', encoding='utf-8') as file:
            existing_chat_lines = json.load(file)
    else:
        existing_chat_lines = []

    # Append new chat lines to the existing chat lines
    existing_chat_lines.extend(chat_lines)

    # Save the updated chat lines to the JSON file
    with open('chat_lines.json', 'w', encoding='utf-8') as file:
        json.dump(existing_chat_lines, file, ensure_ascii=False, indent=4)
    
    print('Chat lines updated')
    
    # Wait 30 seconds before the next update
    time.sleep(30)


# Take a screenshot as proof of session reuse
driver.save_screenshot('session_with_cookies.png')

# Quit the browser
driver.quit()