import json
from flask import jsonify, request

from app import LOG, app
from app.utils.create_stories import adjust_elements

from app.utils.get_posts_metadata import modify_posts_metadata
from app.models.canvas import ImageElements


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
    
    LOG.info("Adjusting of img elements started...")
    
    # Get current images elements
    try:
        elements_value = request.args.get("elements")
        if elements_value is None:
            raise ValueError("Missing 'elements' in the request.")
        
        elements_json = json.loads(elements_value)
        
        elements = [ImageElements.model_validate(x) for x in elements_json]
        
    except ValueError as ve:
        LOG.exception("Error in 'elements' parameter")
        return jsonify({"success": False, "error": str(ve)}), 400
    except Exception as e:
        LOG.exception("Unexpected error occurred")
        return jsonify({"success": False, "error": "Unexpected error occurred"}), 400
    
    # Get changed parameters by user
    try:
        metadata_value = request.args.get("metadata")
        if metadata_value is None:
            raise ValueError("Missing 'metadata' in the request.") 
        
        metadata = json.loads(metadata_value)
        
    except ValueError as ve:
        LOG.exception("Error in 'metadata' parameter")
        return jsonify({"success": False, "error": str(ve)}), 400
    except Exception as e:
        LOG.exception("Unexpected error occurred")
        return jsonify({"success": False, "error": "Unexpected error occurred"}), 400
    
    # Replace parameters of image elements by the changed ones
    adjusted_elements = []
    for image_elements, image_metadata in zip(elements, metadata):
        adjusted_elements.append(adjust_elements(image_elements, image_metadata))
        
    if all(val is None for val in adjusted_elements):
        LOG.error("Image elements were not adjusted.")
        return jsonify({"success": False, "error": "Image elements were not adjusted."}), 500
    else:
        return jsonify({"success": True, "data": adjusted_elements})    