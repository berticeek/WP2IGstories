from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory, session

from create_stories import create_stories, get_story_template, get_elements
from get_posts_metadata import get_posts_metadata

from create_stories import Template, PostData, ImageElements

import os
import tempfile
import shutil
import time
import secrets
import json

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


@app.route("/get_stories_template", methods=["GET"])
def get_stories_template():
    site = request.args.get("site")
    template = get_story_template(site)
    return jsonify(template)


@app.route("/get_posts_data", methods=["GET"])
def get_posts_data():
    site = request.args.get("site")
    links = list(filter(None, request.args.getlist("links")))
    posts_data = get_posts_metadata(site, links)
    return jsonify(posts_data)


@app.route("/get_posts_elements", methods=["GET"])
def get_posts_elements():
    posts_json = json.loads(request.args.get("posts"))
    posts = [PostData.model_validate(x) for x in posts_json]
    
    template_json = json.loads(request.args.get("template"))
    template = Template.model_validate(template_json)
    posts_elements = get_elements(posts, template)
    return jsonify(posts_elements)


@app.route("/create_images", methods=["POST"])
def create_images():
    data = request.get_json()
    site = data["site"]
    
    posts_elements_json = data["posts_elements"]
    posts_elements = [ImageElements.model_validate(x) for x in posts_elements_json]
    
    stories_metadata  = create_stories(site, posts_elements)
    session["stories_metadata"] = stories_metadata
    return jsonify({'redirect_url': url_for("show_images", site=site)})
        
        
@app.route("/show_images", methods=["GET", "POST"])
def show_images():
    site = request.args.get("site")
    metadata = session.get("stories_metadata", {})
    
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
    session["stories_metadata"] = new_metadata
    return jsonify({'redirect_url': url_for("show_images", site=site)})
    

if __name__ == "__main__":
    app.run(debug=True)