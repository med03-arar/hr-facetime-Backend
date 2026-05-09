import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:@localhost/hrdb"  # ← valeur par défaut
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt")
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", None)