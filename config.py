import os
from urllib.parse import quote_plus
from datetime import timedelta


class Config:
    # Prefer generic DB_* envs (Kubernetes), fallback to MYSQL_*.
    # Provide sane defaults so the app can run in development without envs.
    _host = os.environ.get("DB_HOST") or os.environ.get("MYSQL_HOST") or "127.0.0.1"
    _port = os.environ.get("DB_PORT") or os.environ.get("MYSQL_PORT") or "3306"
    _db = os.environ.get("DB_NAME") or os.environ.get("MYSQL_DATABASE") or "marriage_app"
    _user = os.environ.get("DB_USER") or os.environ.get("MYSQL_USER") or ""
    _password = os.environ.get("DB_PASSWORD") or os.environ.get("MYSQL_PASSWORD") or ""

    # Public attributes for introspection or other modules
    MYSQL_HOST = _host
    try:
        MYSQL_PORT = int(_port)
    except (TypeError, ValueError):
        MYSQL_PORT = 3306
    MYSQL_DB = _db
    MYSQL_USER = _user
    MYSQL_PASSWORD = _password

    # Allow full override via DATABASE_URL (12-factor style)
    _database_url = os.environ.get("DATABASE_URL") or None
    if _database_url:
        SQLALCHEMY_DATABASE_URI = _database_url
    else:
        _pwd = quote_plus(_password) if _password else ""
        if _user:
            _auth = f"{_user}:{_pwd}" if _pwd else _user
            auth_prefix = f"{_auth}@"
        else:
            auth_prefix = ""
        SQLALCHEMY_DATABASE_URI = (
            f"mysql+pymysql://{auth_prefix}{_host}:{MYSQL_PORT}/{_db}"
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Avoid hard-coded secrets; default is fine for dev, use k8s Secret in prod
    SECRET_KEY = os.environ.get("SECRET_KEY", "super-secret-key")
    # Root admin password for simple login. Provide via env/Secret in k8s.
    # Default intentionally empty to avoid leaking credentials in source.
    ROOT_PASSWORD = os.environ.get("ROOT_PASSWORD") or ""
    # Root admin username (configurable via env)
    ROOT_USER = os.environ.get("ROOT_USER", "root")
    # Session lifetime: expire login after 5 minutes
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=5)

    # Gallery configuration: Google Drive folder + optional image IDs
    # Set via env for production, with sensible defaults for dev.
    DRIVE_FOLDER_URL = os.environ.get(
        "DRIVE_FOLDER_URL",
        "https://drive.google.com/drive/folders/1AXkQ11ZDW2jlrXlv1C3Pse4eqYhDnG1e",
    )
    # Comma-separated list of file IDs; optional.
    DRIVE_IMAGE_IDS = os.environ.get("DRIVE_IMAGE_IDS", "")
