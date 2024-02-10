from urllib.parse import unquote

from flask import jsonify, render_template, request
from flask_mail import Message

from app import LOG, app, mail
from app.utils.file_paths import project_folder
from app.utils.credentials import get_mail_credentials


@app.route("/send_by_email", methods=["POST"])
def send_by_email():
    """Send generated images along with posts links to the email"""
    
    LOG.info("Sending created stories by mail...")
    
    # Get site name, posts liks and recipient email from request
    data = request.get_json()
    if data is None:
        LOG.error("Missing body in the request.")
        return jsonify({"success": False, "error": "Missing body in the request."}), 400 
    
    try:
        site = data["site"]
        links_encoded = data["links"]
        links = [unquote(x) for x in links_encoded]
        recipient_mail = data["mail"]
    except KeyError as e:
        LOG.exception("Missing key in request")
        return jsonify({"success": False, "error": "Missing key in request"}), 400 
    
    LOG.info(f"Recipient: '{recipient_mail}'")
    
    # Generate email with subject, body and attachments 
    try:    
        msg = Message(f"Storkoprístroj 3000", sender=get_mail_credentials()["mail_addr"], recipients=[recipient_mail])
        msg.html = render_template("stories_email.html", site=site, links=links)
        
        stories_path = project_folder() / "stories" / site
        
        if not stories_path.exists():
            LOG.error(f"Stories folder does not exists: '{str(stories_path)}'")
            return jsonify({"success": False, "error": f"Stories folder does not exists: '{str(stories_path)}'"})
        
        # Attach png files from stories dir to the email          
        png_files = stories_path.glob("*.png")
        
        if not png_files:
            LOG.error(f"No PNG file in the stories folder: '{str(stories_path)}'")
            return jsonify({"success": False, "error": f"No PNG file in the stories folder: '{str(stories_path)}'"})
        
        for story_file in png_files:
            with app.open_resource(stories_path / story_file) as png_f:
                msg.attach(str(story_file), "application/png", png_f.read())
        
        mail.send(message=msg)
        return jsonify({"success": True})
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return jsonify({"success": False, "error": f"Error sending email: {str(e)}"})
    finally:
        LOG.info("Email sent successfully")