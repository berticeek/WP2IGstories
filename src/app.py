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

from pydantic import ValidationError

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
    if site is None:
        LOG.error("Missing 'site' in the request.")
        return jsonify({"success": False, "error": "Missing 'site' in the request."}), 400
        
    links = list(filter(None, request.args.getlist("links")[0].split(",")))
    if links:
        LOG.info(f"Predefined posts links found: {links}.\nStories will be created also for these posts.")
    else:
        LOG.info("No predefined posts links found. Stories will be created only from latest posts.")
    
    posts_number_value = request.args.get("number")
    
    if not posts_number_value and links:
        posts_number = len(links)
    else:
        try:
            posts_number = int(posts_number_value)
        except ValueError as ve:
            return jsonify({"success": False, "error": str(ve)}), 400
    
    posts_data = get_posts_metadata(site, links, int(posts_number))
    return jsonify({"success": True, "data": posts_data})


@app.route("/get_stories_template", methods=["GET"])
def get_stories_template():
    """Loads template file and returns stories configuration for selected site"""
    
    site = request.args.get("site")
    if site is None:
        LOG.error("Missing 'site' in the request.")
        return jsonify({"success": False, "error": "Missing 'site' in the request."}), 400
    
    template = get_story_template(site)
    if not template:
        LOG.error("Error while getting template.")
        return jsonify({"success": False, "error": "Couldn't load template."}), 500
    
    return jsonify({"success": True, "data": template})


@app.route("/get_posts_elements", methods=["GET"])
def get_posts_elements():
    """From posts metadata and template creates object with data about all elements needed for image creation"""
    
    try:
        posts_value = request.args.get("posts")
        
        if posts_value is None:
            raise ValueError("Missing 'posts' in the request.")
        
        posts_json = json.loads(posts_value)
        
        posts = [PostData.model_validate(x) for x in posts_json]
        
    except ValueError as ve:
        LOG.exception("Error in 'posts' parameter")
        return jsonify({"success": False, "error": str(ve)}), 400
    except Exception as e:
        LOG.exception("Unexpected error occurred")
        return jsonify({"success": False, "error": "Unexpected error occurred"}), 400
    
    try:
        template_value = request.args.get("template")
        
        if template_value is None:
            raise ValueError("Missing 'template' in the request.")
        
        template_json = json.loads(template_value)
        
        template = Template.model_validate(template_json)
    
    except ValueError as ve:
        LOG.exception("Error in 'template' parameter")
        return jsonify({"success": False, "error": str(ve)}), 400
    except Exception as e:
        LOG.exception("Unexpected error occurred")
        return jsonify({"success": False, "error": "Unexpected error occurred"}), 400
    
    posts_elements = get_elements(posts, template)
    return jsonify({"success": True, "data": posts_elements})


@app.route("/create_images", methods=["POST"])
def create_images():
    """Create images based on posts elements objects"""
    
    # Get site and posts elements data from request
    try:
        data = request.get_json()
        site = data["site"]
        posts_elements_json = data["posts_elements"]
    except KeyError as e:
        LOG.error(f'Missing key in request: {str(e)}')
        return jsonify({"success": False, "error": f"Missing key in request {str(e)}"}), 400    
    
    
    try:
        # Create list of ImageElements object from json retrieved from request
        posts_elements = [ImageElements.model_validate(x) for x in posts_elements_json]
        
        # Create images and store their metadata
        stories_metadata  = create_stories(site, posts_elements)
        if stories_metadata is None:
            return jsonify({"success": False, "error": f"Stories creation failed."}), 500
        
        # Store metadata into session so they can be later reused by another endpoint
        session["stories_metadata"] = stories_metadata
        
        # Show created images with metadata
        return jsonify({"success": True, "redirect_url": url_for("show_images", site=site)})
        
    except ValidationError as ve:
        LOG.error(f'ImageElements object cannot be validated: {str(ve)}')
        return jsonify({"success": False, "error": f"ImageElements object cannot be validated: {str(ve)}"}), 400
    
    except Exception as e:
        return jsonify({"success": False, "error": "An unexpected error occurred."}), 500


@app.route("/show_images", methods=["GET", "POST"])
def show_images():
    """Display generated images along with neccessary data"""
    
    site = request.args.get("site")
    if site is None:
        LOG.error("Missing 'site' in the request.")
        return jsonify({"success": False, "error": "Missing 'site' in the request."}), 400 
    
    metadata_key = "stories_metadata"
    metadata = session.get(metadata_key, {})
    if not metadata:
        LOG.error(f"Key '{metadata_key}' not found in the session.")
        return jsonify({"success": False, "error": f"Key '{metadata_key}' not found in the session."}), 500 
    
    LOG.info(f"Showing {len(metadata)} images...")
    return render_template("stories.html", stories=metadata, site=site)


@app.route("/stories/<site>/<filename>")
def uploaded_file(site, filename):
    """Retrieves image file"""
    
    upload_folder = os.path.join(app.config['UPLOAD_FOLDER'], site)
    return send_from_directory(upload_folder, filename)


@app.route("/recreate_posts_metadata", methods=["POST"])
def recreate_posts_metadata():
    """Construct new image metadata by changed parameters"""
    
    LOG.info("Recreating images started...")
    # Get request body
    data = request.get_json()
    if data is None:
        LOG.error("Missing body in the request.")
        return jsonify({"success": False, "error": "Missing body in the request."}), 400 
    
    # Get changed parameters of images from the request body
    try:
        metadata = data['data_stories']
        if not metadata:
            LOG.error("'data_stories' empty.")
            return jsonify({"success": False, "error": "'data_stories' empty."}), 400 
    except KeyError as e:
        LOG.exception("'data_stories' key missing in the request body.")
        return jsonify({"success": False, "error": "'data_stories' key missing in the request body."}), 400 
    
    # Create new list PostData objects with changed parameters
    new_metadata = modify_posts_metadata(metadata)
    if not metadata:
        LOG.error("New PostData object was not created.")
        return jsonify({"success": False, "error": "New PostData object was not created."}), 500
    
    return jsonify({"success": True, "data": new_metadata})


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