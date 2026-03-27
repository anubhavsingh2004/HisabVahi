import os


class Config:
    """Central config for Flask app."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///database.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
