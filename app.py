from flask import Flask, request
from markupsafe import escape

app = Flask(__name__)

# @app.route("/predict")
# def hello_world(name):
#     return f"Hello, {escape(name)}!"  
@app.route("/predict/<path:img_path>")
def hello_world(img_path):
    return f"Hello, {escape(img_path)}!"

# @app.post("/predict/<path:img_path>")
# def hello_world(name):
#     return {
#     "age": user.username,
#     "gender": user.theme,
#     "ethnicity": url_for("user_image", filename=user.image),
#     }