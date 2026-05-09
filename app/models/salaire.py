from datetime import datetime
from decimal import Decimal
from ..extensions import db


class Salaire(db.Model):
    __tablename__ = "salaire"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    nom_complet = db.Column(db.String(255), nullable=False)
    dept = db.Column(db.String(100), nullable=True)
    periode = db.Column(db.String(60), nullable=False)
    salaire_base = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    primes = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    deductions = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    net = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    status = db.Column(db.String(20), nullable=False, default="pending")
    paid_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    @classmethod
    def get_employee_primes_total(cls, employee_id):
        from .primes import Prime

        total = db.session.query(
            db.func.coalesce(db.func.sum(Prime.montant), 0)
        ).filter(Prime.employee_id == employee_id).scalar()

        return Decimal(str(total or 0))

    @classmethod
    def get_employee_deductions_total(cls, employee_id):
        from .deduction import Deduction

        total = db.session.query(
            db.func.coalesce(db.func.sum(Deduction.montant), 0)
        ).filter(Deduction.employee_id == employee_id).scalar()

        return Decimal(str(total or 0))