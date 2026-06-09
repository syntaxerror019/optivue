from functools import wraps
from flask import request, Response
from dotenv import load_dotenv
import os

load_dotenv()
REALM = "OptiVue"
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

def check_auth(username, password):
    return username == USERNAME and password == PASSWORD

def auth_required():
    return Response(
        "Authentication required",
        401,
        {"WWW-Authenticate": f'Basic realm="{REALM}"'}
    )

def require_basic_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return auth_required()
        return f(*args, **kwargs)
    return decorated