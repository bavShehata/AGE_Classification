from flask import Flask, request
from markupsafe import escape
import os

app = Flask(__name__)
port = int(os.environ.get('PORT', 5000))
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)
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