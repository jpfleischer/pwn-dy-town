import numpy as np
import os
import time
import cv2
import darknet
import yaml
import glob
import re
from datetime import datetime, timedelta
from PIL import Image
import pytesseract
import json
from difflib import SequenceMatcher

# Track processed images to avoid duplicate processing
processed_images = set()

# Helper function to calculate text similarity
def text_similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

# Load chat lines from JSON
def load_chat_lines(json_path):
    with open(json_path, 'r') as file:
        return json.load(file)

# Extract the timestamp from the input filename
def extract_timestamp_from_filename(filename):
    timestamp_match = re.search(r"screengrab-input-(\d{8}_\d{6})", filename)
    if not timestamp_match:
        return None
    timestamp_str = timestamp_match.group(1)
    return datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")

# Find messages in chat_lines.json within 10 seconds of the timestamp
def find_messages_within_timeframe(chat_lines, target_time):
    messages_in_timeframe = []
    for chat in chat_lines:
        message_time = datetime.strptime(chat['time'], "%m/%d/%Y, %H:%M:%S")
        if abs((message_time - target_time).total_seconds()) <= 10:
            messages_in_timeframe.append({'message': chat['message'], 'name': chat['name']})
    return messages_in_timeframe


# Match OCR text to chat messages with 80% similarity
def find_matching_message(ocr_text, messages):
    for entry in messages:
        message = entry['message']
        if len(message) > 8 and text_similarity(ocr_text, message) >= 0.8:
            return entry  # Return both message and name
    return None


# Generate the next output filename from the input filename
def get_output_filename_from_input(input_file):
    timestamp_match = re.search(r"screengrab-input-(\d+_\d+).png", input_file)
    if not timestamp_match:
        return None
    timestamp = timestamp_match.group(1)
    return f"output/screengrab-output-{timestamp}.png"

# Get unprocessed input files based on the prefix and directory
def get_unprocessed_input_filenames(directory, prefix):
    files = glob.glob(os.path.join(directory, f"{prefix}-*.png"))
    unprocessed_files = []
    for file in files:
        output_file = get_output_filename_from_input(file)
        if output_file and not os.path.exists(output_file):
            unprocessed_files.append(file)
    return unprocessed_files

# Write detections to a YAML file
def write_detections_to_yaml(detections, output_file, timestamp):
    detections_serializable = [(label, confidence, list(bbox)) for label, confidence, bbox in detections]
    data = {'timestamp': timestamp, 'detections': detections_serializable}
    with open(output_file, 'w') as file:
        yaml.dump(data, file)

# Extract the message coordinates from the YAML data
def extract_message_coordinates(yaml_data):
    message_coordinates = []
    if 'detections' in yaml_data:
        for entry in yaml_data['detections']:
            if entry[0] == 'message':  # Assuming 'message' label indicates the region of interest
                message_coordinates.append(entry[2])
    return message_coordinates

# Perform OCR on the image based on the scaled bounding box coordinates
def perform_ocr_on_image(image_path, coordinates):
    # Scaling factors based on the resolution difference
    width_scale_factor = 1614 / 1920
    height_scale_factor = 885 / 1088
    
    # Scale the bounding box coordinates
    center_x, center_y, width, height = coordinates
    center_x *= width_scale_factor
    center_y *= height_scale_factor
    width *= width_scale_factor
    height *= height_scale_factor

    # Calculate the bounding box coordinates in the input resolution
    x1 = center_x - (width / 2)
    y1 = center_y - (height / 2)
    x2 = center_x + (width / 2)
    y2 = center_y + (height / 2)

    # Open the original input image and crop it using the adjusted coordinates
    image = Image.open(image_path)
    cropped_image = image.crop((x1, y1, x2, y2))

    # Convert the cropped image to OpenCV format and up-sample it
    cropped_image_cv = np.array(cropped_image)
    cropped_image_cv = cv2.cvtColor(cropped_image_cv, cv2.COLOR_RGB2BGR)
    cropped_image_cv = cv2.resize(cropped_image_cv, (0, 0), fx=2, fy=2)

    # Convert the image to HSV color-space and get the binary mask
    hsv = cv2.cvtColor(cropped_image_cv, cv2.COLOR_BGR2HSV)
    lower_bound = np.array([0, 0, 123])
    upper_bound = np.array([179, 255, 255])
    msk = cv2.inRange(hsv, lower_bound, upper_bound)

    # Perform OCR on the masked image
    text = pytesseract.image_to_string(msk, lang='eng', config='--oem 3 --psm 7')

    return text

def process_ocr_on_yaml_and_image(yaml_file, png_file, chat_lines):
    with open(yaml_file, 'r') as file:
        yaml_data = yaml.load(file, Loader=yaml.FullLoader)

    message_coordinates_list = extract_message_coordinates(yaml_data)

    if message_coordinates_list:
        # Extract timestamp from the input filename
        timestamp = extract_timestamp_from_filename(png_file)
        if not timestamp:
            print(f"Invalid timestamp in filename {png_file}")
            return
        
        # Find chat messages within 10 seconds of the timestamp
        nearby_messages = find_messages_within_timeframe(chat_lines, timestamp)

        for message_coordinates in message_coordinates_list:
            try:
                # Print the coordinates
                # print(f"Processing coordinates: {message_coordinates}")

                # Perform OCR on the image
                ocr_text = perform_ocr_on_image(png_file, message_coordinates)
                
                # Try to match the OCR text with any chat message
                matching_entry = find_matching_message(ocr_text, nearby_messages)
                
                if matching_entry:
                    matched_message = matching_entry['message']
                    user = matching_entry['name']
                    print(f"OCR Text: '{ocr_text}' matched")
                    print('#'*90)
                    print(f'{user} says {matched_message}')
                    print(f'coords: {message_coordinates}')
                else:
                    pass
                    # print(f"No matching chat message found for OCR text: '{ocr_text}' at coordinates {message_coordinates}")
                    
            except ValueError as e:
                print(f"Error processing {png_file}: {e}")
    else:
        pass
        # print(f"No message coordinates found in {yaml_file}")


# Load chat lines once for the entire script
chat_lines = load_chat_lines('../chat_lines.json')

# Main function
def main():
    # Set up YOLO
    network, class_names, class_colors = darknet.load_network(
        "../screenshots/screenshots.cfg", "../screenshots/screenshots.data", "../screenshots/screenshots_best.weights", batch_size=1
    )

    input_directory = 'input_grabs'
    input_prefix = 'screengrab-input'
    os.makedirs("output", exist_ok=True)

    # Get all unprocessed images
    unprocessed_images = get_unprocessed_input_filenames(input_directory, input_prefix)
    if not unprocessed_images:
        print(f"No new images found in {input_directory}")
        return

    for image_path in unprocessed_images:
        timestamp = os.path.getctime(image_path)
        human_readable_timestamp = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        image = cv2.imread(image_path)

        if image is None:
            print(f"Error: Unable to read image from {image_path}")
            continue

        # Get the width and height of the Darknet network
        width = 1920
        height = 1088

        # Create a Darknet IMAGE object with the specified width, height, and 3 channels
        darknet_image = darknet.make_image(width, height, 3)

        # Convert the input image from BGR to RGB color space
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Resize the image to match the dimensions of the Darknet network
        image_resized = cv2.resize(image_rgb, (width, height), interpolation=cv2.INTER_LINEAR)

        # Copy the resized image data into the Darknet IMAGE object
        darknet.copy_image_from_bytes(darknet_image, image_resized.tobytes())

        # Run YOLO object detection
        detections = darknet.detect_image(network, class_names, darknet_image, thresh=0.25)

        # Free the memory used by the Darknet IMAGE object
        darknet.free_image(darknet_image)

        # Draw bounding boxes and labels on the image based on the detected objects
        image_with_boxes = darknet.draw_boxes(detections, image_resized, class_colors)

        # Fix the output filename to avoid nested "output/output"
        output_filename = get_output_filename_from_input(image_path)
        yaml_output_file = f"{output_filename.split('.png')[0]}.yaml"  # Remove extra "output/" path

        write_detections_to_yaml(detections, yaml_output_file, human_readable_timestamp)

        # Convert image back to BGR color space before saving with OpenCV
        image_bgr = cv2.cvtColor(image_with_boxes, cv2.COLOR_RGB2BGR)

        # Save the annotated image
        cv2.imwrite(f"{output_filename}", image_bgr)

        # Run OCR on the original input image and try to match with chat messages
        process_ocr_on_yaml_and_image(yaml_output_file, image_path, chat_lines)

        # Mark the image as processed
        processed_images.add(image_path)

if __name__ == "__main__":
    main()
