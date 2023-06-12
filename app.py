from flask import Flask, request
from flask_cors import CORS, cross_origin
from markupsafe import escape
import os
from predict import get_prediction

app = Flask(__name__)
CORS(app, support_credentials=True)

port = int(os.environ.get('PORT', 5000))
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)
 
@app.route("/predict/<path:img_path>")
def hello_world(img_path):
    res = get_prediction([img_path])
    return res

# @app.post("/predict/<path:img_path>")
# def hello_world(name):
#     return {
#     "age": user.username,
#     "gender": user.theme,
#     "ethnicity": url_for("user_image", filename=user.image),
#     }