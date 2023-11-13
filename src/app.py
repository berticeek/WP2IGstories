from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory, session

from create_stories import create_stories

import os
import tempfile
import shutil
import time
import secrets

# def create_tmp_dir():
#     return tempfile.mkdtemp


# def delete_tmp_dir(tmp_dir):
#     shutil.rmtree(tmp_dir)


app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

script_dir = os.getcwd()
# script_parent_dir = os.path.abspath(os.path.join(script_dir, os.pardir))
app.config["UPLOAD_FOLDER"] = os.path.join(script_dir, "stories")


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/create", methods=["GET"])
def create():
    if request.method == "GET":
        site = request.args.get('option')       
        metadata  = create_stories(site, recreate=False)
        session["metadata"] = metadata
        return jsonify({'redirect_url': url_for("show_images", site=site)})
        
@app.route("/show_images", methods=["GET", "POST"])
def show_images():
    site = request.args.get("site")
    metadata = session.get("metadata", {})
    
    # images = [str(x["number"]) + ".png" for x in metadata]
    return render_template("stories.html", stories=metadata, site=site)


@app.route("/stories/<site>/<filename>")
def uploaded_file(site, filename):
    upload_folder = os.path.join(app.config['UPLOAD_FOLDER'], site)
    return send_from_directory(upload_folder, filename)


@app.route("/recreate", methods=["POST"])
def recreate():
    data = request.get_json()
    site = data['site']
    metadata = data['metadata']
    new_metadata = create_stories(site, recreate=True, metadata=metadata)
    session["metadata"] = new_metadata
    return jsonify({'redirect_url': url_for("show_images", site=site)})
    

if __name__ == "__main__":
    app.run(debug=True)