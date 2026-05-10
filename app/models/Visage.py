from ..extensions import db
from datetime import datetime

class Face(db.Model):
    __tablename__ = "Visage"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
   

    image = db.Column(db.LargeBinary, nullable=False)  # image en BLOB

    created_at = db.Column(db.DateTime, default=datetime.utcnow)