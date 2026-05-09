from datetime import datetime, date
from ..extensions import db


class Prime(db.Model):
    __tablename__ = "primes"

    id          = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)  # ✅ users
    nom_complet = db.Column(db.String(255), nullable=False)
    montant     = db.Column(db.Numeric(12, 2), nullable=False)
    type        = db.Column(db.String(64))
    description = db.Column(db.Text)
    date_insere = db.Column(db.Date, nullable=False, default=date.today)
    status      = db.Column(db.String(20), nullable=False, default="pending")
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)