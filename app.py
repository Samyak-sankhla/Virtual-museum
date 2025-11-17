
from flask import Flask
from config import settings
from auth import bp as auth_bp
from main import bp as main_bp
import os

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["MAX_CONTENT_LENGTH"] = settings.MAX_CONTENT_LENGTH
    os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
    # register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
