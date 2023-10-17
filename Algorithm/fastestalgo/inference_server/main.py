import time
from flask import Flask, request, jsonify
from flask_cors import CORS
from model import *
import io
from PIL import Image
import base64

app = Flask(__name__)
CORS(app)
model = load_model()

@app.route('/image_rec_week9', methods=['POST'])
def image_predict_w9():
    image = request.data
    image_bytes = base64.b64decode(image)
    # convert base64 to PIL image
    img = Image.open(io.BytesIO(image_bytes))
    # Run inference
    result = predict_image_week_9(img, model)

    return jsonify(result)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
