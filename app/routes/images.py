from flask import jsonify, request, session, url_for
from pydantic import ValidationError

from app import LOG, app, create_stories
from app.delete_stories import delete_story_file, reorder_stories
from app.models.canvas import ImageElements


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
            LOG.error("Stories creation failed.")
            return jsonify({"success": False, "error": f"Stories creation failed."}), 500
        
        # Store metadata into session so they can be later reused by another endpoint
        session["stories_metadata"] = stories_metadata
        
        # Show created images with metadata
        return jsonify({"success": True, "redirect_url": url_for("show_images", site=site)})
        
    except ValidationError as ve:
        LOG.error(f'ImageElements object cannot be validated: {str(ve)}')
        return jsonify({"success": False, "error": f"ImageElements object cannot be validated: {str(ve)}"}), 400
    
    except Exception as e:
        LOG.error( f"An unexpected error occurred: {e}")
        return jsonify({"success": False, "error": "An unexpected error occurred."}), 500
    
    
@app.route("/delete_story/<site>/<story_number>", methods=["DELETE"])
def delete_story(site: str, story_number: str):
    """Endpoint for deleting selected story"""
    
    story_number = int(story_number)
    
    metadata_key = "stories_metadata"
    metadata = session.get(metadata_key, {})
    
    # Delete png file
    if delete_story_file(metadata[story_number], site):
        LOG.info(f"File {story_number}.png was deleted.")
        # Delete entry in the metadata
        metadata.pop(story_number)
        # Reorder png files numbers and numbers in metadata
        metadata = reorder_stories(metadata, site)
        session[metadata_key] = metadata
        return jsonify({"success": True})
    else:
        LOG.error(f"File {story_number}.png was not deleted.")
        return jsonify({"success": False, "error": f"File {story_number}.png was not deleted"})