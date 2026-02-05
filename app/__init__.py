import os
from flask import Flask
from .db import init_db, ensure_admin
from .routes import bp

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    # DB path: prefer /data when present
    db_env = os.environ.get("DB_PATH")
    if db_env:
        db_path = db_env
    else:
        db_path = "/data/metagame.db" if os.path.isdir("/data") else "metagame.db"
    app.config["DB_PATH"] = db_path

    init_db(app.config["DB_PATH"])
    ensure_admin(app.config["DB_PATH"])

    app.register_blueprint(bp)
    return app
