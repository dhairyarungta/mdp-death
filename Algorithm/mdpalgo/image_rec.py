import base64
from typing import Dict, List

import requests
import cv2
import json
import pathlib

# Run this command in the terminal to start the server
# docker run --mount source=roboflow,target=/tmp/cache -it --rm -p 9001:9001 roboflow/roboflow-inference-server-cpu

common_object_url = "http://localhost:9001/mdp-mhgbi/1?api_key=IEwWvsYdPmyXduQYIz3k"
arrow_url = "http://localhost:5000/image_rec_week9"


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

def preprocess_img(img_pth):
    img = cv2.imread(img_pth)
    resized_img = cv2.resize(img, (800, 800))
    resized_path = 'images_resized/' + pathlib.Path(img_pth).stem + '_resized.jpg'
    cv2.imwrite(resized_path, resized_img)
    print("Image resize to 800x800!")
    return resized_path

def encode_image_to_base64(image_path):
    """Encode image to Base64."""
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    return encoded_string


def send_post_request(encoded_image, url, arrow: bool = False):
    """Send a POST request with the Base64 encoded image."""
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    if arrow:
        response = requests.post(url, data=encoded_image)
    else:
        response = requests.post(url, data=encoded_image, headers=headers)
    return response


def image_rec(image_path, save_path=None, arrow: bool = False):
    """Send a POST request with the Base64 encoded image."""

    # Encode the image to Base64
    encoded_image = encode_image_to_base64(image_path)

    # Send the POST request
    if arrow:
        infer_server_url = arrow_url
    else:
        infer_server_url = common_object_url

    response = send_post_request(encoded_image, infer_server_url, arrow)

    # Optional: print the response
    result_str = response.text
    result_dict = json.loads(result_str)
    nretries = 5
    while len(result_dict['predictions']) == 0 and nretries>0:
        print(f'No Object detected. Retrying')
        response = send_post_request(encoded_image, infer_server_url, arrow)
        result_str = response.text
        result_dict = json.loads(result_str)
        nretries-=1
    
    if len(result_dict['predictions']) == 0:
        return None

    if len(result_dict['predictions']) >1:
        largest_box = 0
        largest_box_pre = None
        for pre in result_dict['predictions']:
            # if pre["confidence"] < 0.7:
            #     result_dict['predictions'].remove(pre)
            #     continue
            box_area = pre['width']*pre['height']
            if box_area > largest_box:
                largest_box = box_area
                largest_box_pre = pre
        result_dict['predictions'] = [largest_box_pre]
    
    if len(result_dict['predictions']) == 0:
        return None
    
    print(result_dict)
        
    if save_path is not None:
        visualise_predictions(result_dict["predictions"], image_path, save_path)
    return result_dict

if __name__ == "__main__":
    import os 
    image_dir = 'test_images_2'
    resutl_dir = 'test_images_result_2'
    for img in os.listdir(image_dir):
        if img.endswith('.jpg'):
            image_rec(f'{image_dir}/{img}', f'{resutl_dir}/{img}', arrow=True)