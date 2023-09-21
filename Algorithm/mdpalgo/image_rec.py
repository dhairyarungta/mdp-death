import base64
from typing import Dict, List

import requests
import cv2
import json
import subprocess

# Run this command in the terminal to start the server
# docker run --mount source=roboflow,target=/tmp/cache -it --rm -p 9001:9001 roboflow/roboflow-inference-server-cpu

infer_server_url = "http://localhost:9001/mdp-project/1?api_key=3cR60WzeoK9LNrEVOyPT"

def visualise_predictions(predictions: List[Dict], input_path, output_path, stroke=2):
        # Load image based on image path as an array
        image = cv2.imread(input_path)
        stroke_color = (255, 0, 0)

        # Iterate through predictions and add prediction to image
        for prediction in predictions:
            # Get different dimensions/coordinates
            x = prediction["x"]
            y = prediction["y"]
            width = prediction["width"]
            height = prediction["height"]
            class_name = prediction["class"]
            # Draw bounding boxes for object detection prediction
            cv2.rectangle(
                image,
                (int(x - width / 2), int(y + height / 2)),
                (int(x + width / 2), int(y - height / 2)),
                stroke_color,
                stroke,
            )
            # Get size of text
            text_size = cv2.getTextSize(
                class_name, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1
            )[0]
            # Draw background rectangle for text
            cv2.rectangle(
                image,
                (int(x - width / 2), int(y - height / 2 + 1)),
                (
                    int(x - width / 2 + text_size[0] + 1),
                    int(y - height / 2 + int(1.5 * text_size[1])),
                ),
                stroke_color,
                -1,
            )
            # Write text onto image
            cv2.putText(
                image,
                class_name,
                (int(x - width / 2), int(y - height / 2 + text_size[1])),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                (255, 255, 255),
                thickness=1,
            )
        cv2.imwrite(output_path, image)

def encode_image_to_base64(image_path):
    """Encode image to Base64."""
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    return encoded_string

def send_post_request(encoded_image, url):
    """Send a POST request with the Base64 encoded image."""
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    response = requests.post(url, data=encoded_image, headers=headers)
    return response


def image_rec(image_path, save_path=None):
    """Send a POST request with the Base64 encoded image."""

    # Encode the image to Base64
    encoded_image = encode_image_to_base64(image_path)

    # Send the POST request
    response = send_post_request(encoded_image, infer_server_url)

    # Optional: print the response
    result_str = response.text
    result_dict = json.loads(result_str)
    if save_path is not None:
        visualise_predictions(result_dict["predictions"], image_path, save_path)
    return result_dict
