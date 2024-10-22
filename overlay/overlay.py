from datetime import datetime
import argparse
import os
import time
import cv2
import darknet
import yaml
import glob
import re

def get_next_output_filename():
    # Find all files matching the pattern screengrab_output_*.png
    files = glob.glob("overlay/output/screengrab_output_*.png")
    if not files:
        return "screengrab_output_1.png"

    # Extract numbers from filenames and find the highest number
    numbers = [int(re.search(r"screengrab_output_(\d+).png", f).group(1)) for f in files]
    next_number = max(numbers) + 1
    return f"screengrab_output_{next_number}.png"


def get_latest_input_filename(directory, prefix):
    # Find all files matching the pattern prefix-*.png
    files = glob.glob(os.path.join(directory, f"{prefix}-*.png"))
    if len(files) < 2:
        return None

    # Extract numbers from filenames and sort them
    files.sort(key=lambda f: int(re.search(rf"{prefix}-(\d+).png", os.path.basename(f)).group(1)), reverse=True)
    # Return the second-to-last file
    return files[1]


# Define a function named 'parser' to create and configure an argument parser
def parser():
    parser = argparse.ArgumentParser(description="YOLO Object Detection")
    parser.add_argument("--input", type=str, default="screengrab.png",
                        help="image source. It can be a single image, a txt with paths to them, or a folder. Image valid formats are jpg, jpeg, or png.")
    parser.add_argument("--batch_size", default=1, type=int, help="number of images to be processed at the same time")
    parser.add_argument("--weights", default="screenshots/screenshots_best.weights", help="yolo weights path")
    parser.add_argument("--dont_show", action='store_true', help="window inference display. For headless systems")
    parser.add_argument("--ext_output", action='store_true', help="display bbox coordinates of detected objects")
    parser.add_argument("--save_labels", action='store_true', help="save detections bbox for each image in yolo format")
    parser.add_argument("--config_file", default="screenshots/screenshots.cfg", help="path to config file")
    parser.add_argument("--data_file", default="screenshots/screenshots.data", help="path to data file")
    parser.add_argument("--thresh", type=float, default=.25, help="remove detections with lower confidence")
    parser.add_argument("--output_file", type=str, default="detections.yaml", help="YAML file to write detections to")
    parser.add_argument("--output_image", type=str, default="output_with_detections.png", help="Output image file with detections superimposed")
    return parser.parse_args()

# Define the function that performs YOLO object detection on a given image
def image_detection(image_or_path, network, class_names, class_colors, thresh):
    # Get the width and height of the Darknet network
    width = 1920
    height = 1088

    # Create a Darknet IMAGE object with the specified width, height, and 3 channels
    darknet_image = darknet.make_image(width, height, 3)

    # Check if 'image_or_path' is a path to an image file (string) or an image array
    if isinstance(image_or_path, str):
        # Load the image from the provided file path
        image = cv2.imread(image_or_path)

        # Check if the image loading was successful
        if image is None:
            raise ValueError(f"Unable to load image {image_or_path}")
    else:
        # Use the provided image array
        image = image_or_path

    # Convert the input image from BGR to RGB color space
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Resize the image to match the dimensions of the Darknet network
    image_resized = cv2.resize(image_rgb, (width, height), interpolation=cv2.INTER_LINEAR)

    # Copy the resized image data into the Darknet IMAGE object
    darknet.copy_image_from_bytes(darknet_image, image_resized.tobytes())

    # Perform object detection on the image using Darknet
    detections = darknet.detect_image(network, class_names, darknet_image, thresh=thresh)

    # Free the memory used by the Darknet IMAGE object
    darknet.free_image(darknet_image)

    # Draw bounding boxes and labels on the image based on the detected objects
    image_with_boxes = darknet.draw_boxes(detections, image_resized, class_colors)

    # Convert the image back to BGR color space (OpenCV format) and return it along with detections
    return cv2.cvtColor(image_with_boxes, cv2.COLOR_BGR2RGB), detections

# Function to write detections to a YAML file
def write_detections_to_yaml(detections, output_file, timestamp):
    detections_serializable = [(label, confidence, list(bbox)) for label, confidence, bbox in detections]
    data = {
        'timestamp': timestamp,
        'detections': detections_serializable
    }
    with open(output_file, 'w') as file:
        yaml.dump(data, file)


def main():
    # Parse the arguments
    args = parser()

        # Load the YOLO model
    network, class_names, class_colors = darknet.load_network(
        args.config_file,
        args.data_file,
        args.weights,
        batch_size=args.batch_size
    )

    os.makedirs("overlay/output", exist_ok=True)

    while True:
        # Sleep for 1 second before processing the next image
        time.sleep(1)

        # Get the latest input filename
        input_directory = 'overlay/input_grabs'
        input_prefix = 'screengrab-input'
        image_path = get_latest_input_filename(input_directory, input_prefix)

        if image_path is None:
            print(f"No images found in {input_directory}")
            return

        # Get the creation timestamp of the image
        timestamp = os.path.getctime(image_path)
        human_readable_timestamp = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

        # Read the image from the file
        image = cv2.imread(image_path)

        if image is None:
            print(f"Error: Unable to read image from {image_path}")
            time.sleep(0.2)
            continue

        # Run the YOLO object detection and get the resized dimensions
        image, detections = image_detection(image, network, class_names, class_colors, args.thresh)

        # Get the next output filename
        output_filename = get_next_output_filename()

        yaml_output_file = f"overlay/output/{output_filename.split('.png')[0]}.yaml"
        write_detections_to_yaml(detections, yaml_output_file, human_readable_timestamp)


        # Save the image with detections
        cv2.imwrite(f"overlay/output/{output_filename}", image)

        print(f"Detections saved to {output_filename}")

if __name__ == "__main__":
    main()