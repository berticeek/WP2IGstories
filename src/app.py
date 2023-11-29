from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory, session, send_file
from flask_mail import Mail, Message

from create_stories import create_stories, get_story_template, get_elements, adjust_elements
from get_posts_metadata import get_posts_metadata, modify_posts_metadata

from create_stories import Template, PostData, ImageElements

from file_paths import project_folder

import os
import tempfile
import shutil
import time
import secrets
import json
import yaml
from zipfile import ZipFile
from urllib.parse import unquote
import logging

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

script_dir = os.getcwd()
app.config["UPLOAD_FOLDER"] = os.path.join(script_dir, "stories")

logging.basicConfig(level=logging.INFO, filename=os.path.join(script_dir, "app.log"), filemode="w", format='%(name)s - %(asctime)s - %(levelname)s - %(message)s')
LOG = logging.getLogger(__name__)

def get_mail_credentials() -> dict:
    """!Should be changed when deployed to use some other SMTP server!"""
    
    with open(project_folder() / "email_conf.yaml", "r") as yamlf:
        credentials = yaml.safe_load(yamlf)
    return({
        "mail_addr": credentials["mail_address"],
        "mail_passwd": credentials["app_password"]
    })
    
    
def url_decode(value):
    return unquote(value)

app.jinja_env.filters['url_decode'] = url_decode
    
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = get_mail_credentials()["mail_addr"]
app.config['MAIL_PASSWORD'] = get_mail_credentials()["mail_passwd"]
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
     
mail = Mail(app)

@app.route("/")
def index():
    """Main page"""
    
    return render_template("index.html")


@app.route("/get_posts_data", methods=["GET"])
def get_posts_data():
    """
    Requests data about posts on selected wordpress site.
    Includes data about predefined posts if any.
    """
    
    site = request.args.get("site")
    links = list(filter(None, request.args.getlist("links")[0].split(",")))
    posts_number = request.args.get("number")
    
    if not posts_number and links:
        posts_number = len(links)
    
    posts_data = get_posts_metadata(site, links, int(posts_number))
    return jsonify(posts_data)


@app.route("/get_stories_template", methods=["GET"])
def get_stories_template():
    """Loads template file and returns stories configuration for selected site"""
    
    site = request.args.get("site")
    template = get_story_template(site)
    return jsonify(template)


@app.route("/get_posts_elements", methods=["GET"])
def get_posts_elements():
    """From posts metadata and template creates object with data about all elements needed for image creation"""
    
    posts_json = json.loads(request.args.get("posts"))
    posts = [PostData.model_validate(x) for x in posts_json]
    
    template_json = json.loads(request.args.get("template"))
    template = Template.model_validate(template_json)
    
    posts_elements = get_elements(posts, template)
    return jsonify(posts_elements)


@app.route("/create_images", methods=["POST"])
def create_images():
    """Create images based on posts elements objects"""
    
    data = request.get_json()
    site = data["site"]
    
    posts_elements_json = data["posts_elements"]
    posts_elements = [ImageElements.model_validate(x) for x in posts_elements_json]
    
    stories_metadata  = create_stories(site, posts_elements)
    session["stories_metadata"] = stories_metadata
    return jsonify({'redirect_url': url_for("show_images", site=site)})


@app.route("/show_images", methods=["GET", "POST"])
def show_images():
    """Display generated images along with neccessary data"""
    
    site = request.args.get("site")
    metadata = session.get("stories_metadata", {})
    
    return render_template("stories.html", stories=metadata, site=site)


@app.route("/stories/<site>/<filename>")
def uploaded_file(site, filename):
    """Retrieves image file"""
    
    upload_folder = os.path.join(app.config['UPLOAD_FOLDER'], site)
    return send_from_directory(upload_folder, filename)


@app.route("/recreate_posts_metadata", methods=["POST"])
def recreate_posts_metadata():
    """Recreate images with modified data"""
    
    LOG.info("Recreating images started")
    data = request.get_json()
    metadata = data['data_stories']
    
    new_metadata = modify_posts_metadata(metadata)
    return jsonify(new_metadata)


@app.route("/adjust_posts_elements", methods=["GET"])
def adjust_posts_elements():
    """Rewrite posts elements if recreate was requested"""
    
    elements_json = json.loads(request.args.get("elements"))
    elements = [ImageElements.model_validate(x) for x in elements_json]
    
    metadata = json.loads(request.args.get("metadata"))
    
    adjusted_elements = []
    for image_elements, image_metadata in zip(elements, metadata):
        adjusted_elements.append(adjust_elements(image_elements, image_metadata))
        
    return jsonify(adjusted_elements)    
    

@app.route("/download_stories", methods=["GET"])
def download_stories():
    """Download generated images together with links to posts"""
        
    site = request.args.get("site");
    stories_path = project_folder() / "stories" / site
    zip_filename = "%s_stories.zip" % site
    zip_stories_path = stories_path.parent / zip_filename
    
    shutil.make_archive(os.path.splitext(zip_stories_path)[0], "zip", stories_path)
    
    try:
        return send_file(zip_stories_path, as_attachment=True, download_name=zip_filename)
    except:
        pass
        # Handle error
    finally:
        os.remove(zip_stories_path)
    
    
@app.route("/send_by_email", methods=["POST"])
def send_by_email():
    """Send generated images along with posts links to the email"""
    
    data = request.get_json()
    site = data["site"]
    links_encoded = data["links"]
    links = [unquote(x) for x in links_encoded]
    recipient_mail = data["mail"]
    
    # Generate email with subject, body and attachments 
    try:    
        msg = Message(f"Storkoprístroj 3000", sender=get_mail_credentials()["mail_addr"], recipients=[recipient_mail])
        msg.html = render_template("stories_email.html", site=site, links=links)
        
        stories_path = project_folder() / "stories" / site
        png_files = [png for png in os.listdir(stories_path) if os.path.splitext(png)[1] == ".png"]
        for story_file in png_files:
            with app.open_resource(stories_path / story_file) as png_f:
                msg.attach(story_file, "application/png", png_f.read())
        
        mail.send(message=msg)
        return jsonify({"status": "success"})
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return jsonify({"status": "fail"})


if __name__ == "__main__":
    app.run(debug=True)