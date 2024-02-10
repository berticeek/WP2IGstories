import logging
import os
import secrets
import sys

from flask import Flask
from flask_mail import Mail
from werkzeug.middleware.proxy_fix import ProxyFix

from app.j2_filters import url_decode
from app.utils.credentials import get_mail_credentials


script_dir = os.getcwd()

app = Flask(__name__)
app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
)
app.secret_key = os.environ.get('FLASK_APP_SECRET', secrets.token_hex(16))

app.config["UPLOAD_FOLDER"] = os.path.join(script_dir, "stories")

logging.basicConfig(level=logging.INFO, filename=os.path.join(script_dir, "app.log"), filemode="w", format='%(name)s - %(asctime)s - %(levelname)s - %(message)s')
LOG = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stdout)
LOG.addHandler(handler)

app.jinja_env.filters['url_decode'] = url_decode
    
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = get_mail_credentials()["mail_addr"]
app.config['MAIL_PASSWORD'] = get_mail_credentials()["mail_passwd"]
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
     
mail = Mail(app)

from app.models import canvas, posts, story

from app.routes import auth, download, email, images, main, posts_data, recreate
