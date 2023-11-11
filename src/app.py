from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory, session

from create_stories import create_stories

import os
import tempfile
import shutil
import time


# def create_tmp_dir():
#     return tempfile.mkdtemp


# def delete_tmp_dir(tmp_dir):
#     shutil.rmtree(tmp_dir)

app = Flask(__name__)
script_dir = os.getcwd()
scipt_parent_dir = os.path.abspath(os.path.join(script_dir, os.pardir))
app.config["UPLOAD_FOLDER"] = os.path.join(scipt_parent_dir, "stories")


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/create", methods=["GET"])
def create():
    if request.method == "GET":
        site = request.args.get('option')
        # upload_folder = os.path.join("stories", site)
        # app.config["UPLOAD_FOLDER"] = upload_folder
         
        stories  = create_stories(site)
        return jsonify({'redirect_url': url_for("show_images", site=site, images=",".join(stories))})
        
@app.route("/show_images", methods=["GET"])
def show_images():
    site = request.args.get("site")
    image_paths_param = request.args.get("images")
    image_paths = image_paths_param.split(",")
    return render_template("stories.html", stories=image_paths, site=site)


@app.route("/stories/<site>/<filename>")
def uploaded_file(site, filename):
    upload_folder = os.path.join(app.config['UPLOAD_FOLDER'], site)
    return send_from_directory(upload_folder, filename)
    

if __name__ == "__main__":
    app.run(debug=True)