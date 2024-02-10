import os

from flask import redirect, request, session, url_for
from oauthlib.oauth2 import WebApplicationClient
import requests

from app import app


FACEBOOK_CLIENT_ID = os.getenv("FACEBOOK_CLIENT_ID")
FACEBOOK_CLIENT_SECRET = os.getenv("FACEBOOK_CLIENT_SECRET")

@app.route('/login/facebook/')
def login_facebook():
    
    fb_client = WebApplicationClient(FACEBOOK_CLIENT_ID)
    auth_base_url = "https://www.facebook.com/dialog/oauth"
    
    auth_url, state, _ = fb_client.prepare_authorization_request(
        auth_base_url,
        redirect_url = request.base_url + "auth",
        scope = ["pages_show_list", "instagram_basic", "business_management", "instagram_content_publish"],
    )
    return redirect(auth_url)
 
@app.route('/login/facebook/auth')
def facebook_callback():
    fb_client = WebApplicationClient(FACEBOOK_CLIENT_ID)
    token_endpoint = 'https://graph.facebook.com/oauth/access_token'
    
    # Avoid denying of authorization due to missing SSL
    # just a workaround while SSL is not activated and should be removed
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    
    token_url, headers, body = fb_client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        client_secret=FACEBOOK_CLIENT_SECRET 
    )
    
    token_response = requests.post(token_url, headers=headers, data=body, auth=(FACEBOOK_CLIENT_ID, FACEBOOK_CLIENT_SECRET))
    fb_client.parse_request_body_response(token_response.text)
    session["facebook_token"] = fb_client.token["access_token"]
    return redirect(url_for("instagram_profile_data"))


@app.route("/instagram_profile_data", methods=["GET"])
def instagram_profile_data():
    headers = {"Authorization": f"Bearer {session['facebook_token']}"}
    response = requests.get("https://graph.facebook.com/v19.0/me/accounts", headers=headers)
    results = response.json()
    
    page_id = results["data"][0].get("id")
    
    response = requests.get(f"https://graph.facebook.com/v19.0/{page_id}?fields=instagram_business_account", headers=headers)
    results = response.json()
    
    ig_business_id = results["instagram_business_account"].get("id")


