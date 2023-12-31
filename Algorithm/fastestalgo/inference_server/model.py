import os
import shutil
import time
import glob
import torch
from PIL import Image
import cv2
import random
import string
import numpy as np
import random

def load_model():
    """
    Load the model from the local directory
    """
    path = "TrainedWeek9Sunlight.pt" # "sunlightWeek9.pt" # "Week_9.pt"
    model = torch.hub.load('../yolov5', 'custom', path=path, source='local')
    print("USING MODEL: ", path)
    return model

def predict_image_week_9(img, model):

    # Run inference
    results = model(img)

    # Convert the results to a dataframe
    df_results = results.pandas().xyxy[0]
    # Calculate the height and width of the bounding box and the area of the bounding box
    df_results['bboxHt'] = df_results['ymax'] - df_results['ymin']
    df_results['bboxWt'] = df_results['xmax'] - df_results['xmin']
    df_results['bboxArea'] = df_results['bboxHt'] * df_results['bboxWt']

    # Label with largest bbox height will be last
    df_results = df_results.sort_values('bboxArea', ascending=False)
    pred_list = df_results 
    pred = 'NA'
    # If prediction list is not empty
    if pred_list.size != 0:
        # Go through the predictions, and choose the first one with confidence > 0.5
        for _, row in pred_list.iterrows():
            if row['name'] != 'Bullseye' and row['confidence'] > 0.5:
                pred = row    
                break

    # Dictionary is shorter as only two symbols, left and right are needed
    name_to_id = {
        "NA": 'NA',
        "Bullseye": 10,
        "Right": 38,
        "Left": 39,
        "Right Arrow": 38,
        "Left Arrow": 39,
    }
    # Return the image id
    if not isinstance(pred,str):
        image_id = str(name_to_id[pred['name']])
        width = pred['bboxWt']
        height = pred['bboxHt']
        confidence = pred['confidence']
        x = (pred['xmin'] + pred['xmax']) / 2
        y = (pred['ymin'] + pred['ymax']) / 2
        result = {
            'predictions': [{
                'class': f'id{image_id}',
                'confidence': confidence,
                'x': x,
                'y': y,
                'width': width,
                'height': height
            }]
        }
        return result
    return {
        'predictions': []
    }