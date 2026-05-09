from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from ..extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(190), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    role = db.Column(
        db.Enum("ADMIN", "RH", "EMPLOYEE"),
        nullable=False,
        default="EMPLOYEE"
    )

    status = db.Column(
        db.Enum("ACTIVE", "SUSPENDED"),
        nullable=False,
        default="ACTIVE"
    )

    # 🔹 Nouveaux champs
    cin = db.Column(db.String(20), unique=True, nullable=True)
    nom_complet = db.Column(db.String(255), nullable=False)
    tel = db.Column(db.String(20), nullable=True)
    dept = db.Column(db.String(100), nullable=True)
    nom_entreprise = db.Column(db.String(255), nullable=True)
    salaire = db.Column(db.Numeric(10, 2), nullable=True)
    poste = db.Column(db.String(150), nullable=True)

    contract_type = db.Column(
        db.Enum("CDI", "CDD", "STAGE", "FREELANCE"),
        nullable=True
    )

    date_embauche = db.Column(db.Date, nullable=True)

    # 🔹 Champs existants
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # 🔐 Gestion mot de passe
    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)
    documents = db.relationship(
    "Document",
    back_populates="user",
    cascade="all, delete-orphan"
)