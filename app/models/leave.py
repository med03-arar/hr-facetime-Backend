from ..extensions import db
from datetime import datetime

class Leave(db.Model):
    __tablename__ = "leaves"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)

    leave_type = db.Column(
        db.Enum('ANNUAL', 'SICK', 'UNPAID', 'MATERNITY', 'OTHER'),
        nullable=False
    )

    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)

    reason = db.Column(db.Text)

    status = db.Column(
        db.Enum('PENDING', 'APPROVED', 'REJECTED'),
        default='PENDING'
    )

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    employee = db.relationship("Employee", backref="leaves")