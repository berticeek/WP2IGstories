import os
import shutil

from flask import jsonify, request, send_file

from app import LOG, app
from app.utils.file_paths import project_folder


@app.route("/download_stories", methods=["GET"])
def download_stories():
    """Download generated images together with links to posts"""
      
    LOG.info("Downloading stories...")
        
    site = request.args.get("site");
    if site is None:
        LOG.error("Missing 'site' in the request.")
        return jsonify({"success": False, "error": "Missing 'site' in the request."}), 400 
    
    # get path to the zip archive
    stories_path = project_folder() / "stories" / site
    if not stories_path.exists():
        LOG.error(f"Stories folder '{str(stories_path)}' does not exist")
        return jsonify({"success": False, "error": f"Stories folder '{str(stories_path)}' does not exist"}), 400 
    
    zip_filename = "%s_stories.zip" % site
    zip_stories_path = stories_path.parent / zip_filename
    
    # create zip archive
    try:
        shutil.make_archive(os.path.splitext(zip_stories_path)[0], "zip", stories_path)
    except (PermissionError, shutil.Error) as e:
        LOG.exception(f"Cannot create zip archive {zip_stories_path}")
        return jsonify({"success": False, "error": f"Cannot create zip archive {zip_stories_path}"}), 400 
    
    try:
        return send_file(zip_stories_path, as_attachment=True, download_name=zip_filename)
    except Exception as e:
        LOG.exception("Error while sending files")
    finally:
        LOG.info("Folder with stories and links has been downloaded successfully...")
        try:
            os.remove(zip_stories_path)
        except PermissionError as e:
            LOG.exception(f"Error while removing zip archive: '{zip_stories_path}'")