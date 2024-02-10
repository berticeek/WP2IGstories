import os
from flask import jsonify, render_template, request, send_from_directory, session

from app import LOG, app

@app.route("/")
def index():
    """Main page"""
    
    return render_template("index.html")


@app.route("/login")
def login():
    """Login page"""
    
    return render_template("login.html")


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
        LOG.warning(f"Key '{metadata_key}' not found in the session.")
        return render_template("stories.html", stories=metadata, site=site, empty_metadata=True)
    
    LOG.info(f"Showing {len(metadata)} images...")
    return render_template("stories.html", stories=metadata, site=site, empty_metadata=False)


@app.route("/stories/<site>/<filename>")
def uploaded_file(site, filename):
    """Retrieves image file"""
    
    upload_folder = os.path.join(app.config['UPLOAD_FOLDER'], site)
    return send_from_directory(upload_folder, filename)