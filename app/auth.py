from functools import wraps
from flask import session, redirect, url_for, request

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("uid"):
            return redirect(url_for("meta.login", next=request.path))
        return fn(*args, **kwargs)
    return wrapper
