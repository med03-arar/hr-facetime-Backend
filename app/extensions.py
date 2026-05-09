from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

# Note: if RATELIMIT_STORAGE_URI is not set, it will use in-memory storage (dev only)
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])
