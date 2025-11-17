import os
from dotenv import load_dotenv
load_dotenv()

class Settings:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-key")
    MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_DB = os.getenv("MYSQL_DB", "virtual_museum")
    MYSQL_USER = os.getenv("MYSQL_USER", "museum_admin")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "admin123")
    MYSQL_USER_READ = os.getenv("MYSQL_USER_READ", "museum_user")
    MYSQL_PASSWORD_READ = os.getenv("MYSQL_PASSWORD_READ", "user123")
    MYSQL_USER_ADMIN = os.getenv("MYSQL_USER_ADMIN", "museum_admin")
    MYSQL_PASSWORD_ADMIN = os.getenv("MYSQL_PASSWORD_ADMIN", "admin123")

    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    STATIC_DIR = os.path.join(BASE_DIR, "static")
    UPLOAD_FOLDER = os.path.join(STATIC_DIR, "uploads")
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8 MB
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

settings = Settings()
