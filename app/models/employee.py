from datetime import datetime
from ..extensions import db

class Department(db.Model):
    __tablename__ = "departments"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)

class Position(db.Model):
    __tablename__ = "positions"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    grade = db.Column(db.String(60), nullable=True)

class Employee(db.Model):
    __tablename__ = "employees"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)

    matricule = db.Column(db.String(60), unique=True, nullable=False)
    cin = db.Column(db.String(60), unique=True, nullable=False)
    nom = db.Column(db.String(120), nullable=False)
    prenom = db.Column(db.String(120), nullable=False)
    tel = db.Column(db.String(40), nullable=True)

    dept_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=True)
    position_id = db.Column(db.Integer, db.ForeignKey("positions.id"), nullable=True)
    manager_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=True)

    contract_type = db.Column(db.String(60), nullable=True)
    hire_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.Enum("ACTIVE", "SUSPENDED", "LEFT"), nullable=False, default="ACTIVE")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
