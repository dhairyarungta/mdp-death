import torch
from PIL import Image
import os
from model import predict_image_week_9

model = torch.hub.load('../yolov5', 'custom', path='Week_9.pt', source='local')
img_pth = '/home/charlestran/mdp-death/Algorithm/mdpalgo/test_images_2/img_1696332454.jpg'

print(predict_image_week_9(img_pth, model))