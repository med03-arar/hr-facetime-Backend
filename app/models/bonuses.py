from datetime import datetime
from ..extensions import db

class Bonus(db.Model):
    __tablename__ = "bonuses"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    type = db.Column(db.String(50), default="OTHER")
    description = db.Column(db.Text)
    date_awarded = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)