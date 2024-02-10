import json
from flask import jsonify, request

from app import LOG, app
from app.models.posts import PostData
from app.models.story import Template
from app.utils.get_posts_metadata import get_posts_metadata
from app.utils.stories_data import get_elements, get_story_template


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
    
    posts_from = request.args.get("from_date")
    if posts_from is None:
        LOG.error("Missing 'from_date' in the request.")
        return jsonify({"success": False, "error": "Missing 'from_date' in the request."}), 400
    
    posts_data = get_posts_metadata(site, links, int(posts_number), posts_from)
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