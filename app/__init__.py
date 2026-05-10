from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

from .config import Config
from .extensions import db, migrate, jwt, limiter
from .errors import register_error_handlers
from dotenv import load_dotenv
load_dotenv()
def create_app():
    load_dotenv()
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app, resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", "*")}})

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    limiter.init_app(app)

    register_error_handlers(app)

    # Blueprints
    from .modules.auth.routes import bp as auth_bp
    from .modules.user.routes import bp as user_bp
    from .modules.leaves.routes import bp as leaves_bp
    from .modules.bonuses.routes import bp as bonuses_bp
    from .modules.primes.routes import bp as primes_bp
    from .modules.deductions.routes import bp as deductions_bp
    
    from .modules.audit.routes import bp as audit_bp
    from .modules.departements.routes import bp as departments_bp
    from .modules.positions.routes import bp as positions_bp
    from .modules.salaires.routes import bp as salaires_bp
    from .modules.document.routes import document_bp   
    from .modules.Visage.routes import bp as Visage_bp
    

    app.register_blueprint(departments_bp, url_prefix="/api/v1/departements")
    app.register_blueprint(positions_bp, url_prefix="/api/v1/positions")
    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(user_bp, url_prefix="/api/v1/users")
    app.register_blueprint(leaves_bp, url_prefix="/api/v1/leaves")
    app.register_blueprint(bonuses_bp, url_prefix="/api/v1/bonuses")
    
    app.register_blueprint(primes_bp, url_prefix="/api/v1/primes")
    app.register_blueprint(deductions_bp, url_prefix="/api/v1/deductions")
    app.register_blueprint(audit_bp, url_prefix="/api/v1/audit")
    app.register_blueprint(salaires_bp, url_prefix="/api/v1/salaires")
    app.register_blueprint(document_bp, url_prefix="/api/v1/documents")
    app.register_blueprint(Visage_bp, url_prefix="/api/v1/visage")

    return app
