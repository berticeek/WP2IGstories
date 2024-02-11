import os

from flask import redirect, request, session, url_for
from oauthlib.oauth2 import WebApplicationClient
import requests

from app import app


FACEBOOK_CLIENT_ID = os.getenv("FACEBOOK_CLIENT_ID")
FACEBOOK_CLIENT_SECRET = os.getenv("FACEBOOK_CLIENT_SECRET")

client = WebApplicationClient(FACEBOOK_CLIENT_ID)

@app.route('/login/facebook/')
def login_facebook():
    
    auth_base_url = "https://www.facebook.com/dialog/oauth"
    
    auth_url, _, _ = client.prepare_authorization_request(
        auth_base_url,
        redirect_url = url_for("facebook_callback", _external=True),
        scope = ["pages_show_list", "instagram_basic", "business_management", "instagram_content_publish"],
    )
    return redirect(auth_url)
 
@app.route('/login/facebook/callback')
def facebook_callback():
    token_endpoint = 'https://graph.facebook.com/oauth/access_token'
    
    # Avoid denying of authorization due to missing SSL
    # just a workaround while SSL is not activated and should be removed
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url = url_for("facebook_callback", _external=True),
        client_secret = FACEBOOK_CLIENT_SECRET 
    )
    
    token_response = requests.post(token_url, headers=headers, data=body, auth=(FACEBOOK_CLIENT_ID, FACEBOOK_CLIENT_SECRET))
    client.parse_request_body_response(token_response.text)
    session["facebook_token"] = client.token["access_token"]
    return redirect(url_for("instagram_profile_id"))


@app.route("/instagram_profile_id", methods=["GET"])
def instagram_profile_id():
    headers = {"Authorization": f"Bearer {session['facebook_token']}"}
    response = requests.get("https://graph.facebook.com/v19.0/me/accounts", headers=headers)
    results = response.json()
    
    page_id = results["data"][0].get("id")
    
    response = requests.get(f"https://graph.facebook.com/v19.0/{page_id}?fields=instagram_business_account", headers=headers)
    results = response.json()
    
    instagram_account_id = results["instagram_business_account"].get("id")
    
    return redirect(url_for("instagram_profile_details", account_id = instagram_account_id))


@app.route("/instagram_profile_details/<account_id>", methods=["GET"])
def instagram_profile_details(account_id):
    headers = {"Authorization": f"Bearer {session['facebook_token']}"}
    parameters = {"fields": ["name", "username"]}
    
    response = requests.get(f"https://graph.facebook.com/v19.0/{account_id}", headers=headers, params=parameters)
    results = response.json()
    print()