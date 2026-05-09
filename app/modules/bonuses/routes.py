from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from ...extensions import db
from ...errors import ApiError
from ...models.bonuses import Bonus  
from ...models.employee import Employee

bp = Blueprint("bonuses", __name__)

VALID_TYPES = ["PERFORMANCE", "ANNUAL", "EXCEPTIONAL", "OTHER"]

# 🔹 Get all bonuses
@bp.get("/")
@jwt_required()
def get_bonuses():
    bonuses = Bonus.query.all()
    return jsonify([
        {
            "id": b.id,
            "employee_id": b.employee_id,
            "amount": float(b.amount),
            "type": b.type,
            "date_awarded": b.date_awarded.isoformat()
        }
        for b in bonuses
    ])
@bp.get("/<int:id>")
@jwt_required()
def get_bonus(id):
    bonus = Bonus.query.get(id)
    if not bonus:
        raise ApiError("bonus_not_found", status=404)

    return jsonify({
        "id": bonus.id,
        "employee_id": bonus.employee_id,
        "amount": float(bonus.amount),
        "type": bonus.type,
        "description": bonus.description,
        "date_awarded": bonus.date_awarded.isoformat()
    })
# 🔹 Get bonuses by employee
@bp.get("/employee/<int:employee_id>")
@jwt_required()
def get_employee_bonuses(employee_id):
    bonuses = Bonus.query.filter_by(employee_id=employee_id).all()
    return jsonify([
        {
            "id": b.id,
            "amount": float(b.amount),
            "type": b.type,
            "date_awarded": b.date_awarded.isoformat()
        }
        for b in bonuses
    ])

# 🔹 Create bonus
@bp.post("/")
@jwt_required()
def create_bonus():
    data = request.get_json() or {}

    employee_id = data.get("employee_id")
    amount = data.get("amount")
    bonus_type = (data.get("type") or "OTHER").upper()
    date_awarded = data.get("date_awarded")

    if not employee_id or not amount or not date_awarded:
        raise ApiError("missing_fields", status=400)

    if bonus_type not in VALID_TYPES:
        raise ApiError("invalid_type", status=400)

    employee = Employee.query.get(employee_id)
    if not employee:
        raise ApiError("employee_not_found", status=404)

    bonus = Bonus(
        employee_id=employee_id,
        amount=amount,
        type=bonus_type,
        date_awarded=date_awarded,
        description=data.get("description")
    )

    db.session.add(bonus)
    db.session.commit()

    return  jsonify({"message": "Bonus created"}), 201


# 🔹 Update bonus
@bp.put("/<int:id>")
@jwt_required()
def update_bonus(id):
    bonus = Bonus.query.get(id)
    if not bonus:
        raise ApiError("bonus_not_found", status=404)

    data = request.get_json() or {}

    if "amount" in data:
        bonus.amount = data["amount"]

    if "type" in data:
        t = data["type"].upper()
        if t not in VALID_TYPES:
            raise ApiError("invalid_type", status=400)
        bonus.type = t

    if "date_awarded" in data:
        bonus.date_awarded = data["date_awarded"]

    if "description" in data:
        bonus.description = data["description"]

    db.session.commit()

    return jsonify({"ok": True})

# 🔹 Delete bonus
@bp.delete("/<int:id>")
@jwt_required()
def delete_bonus(id):
    bonus = Bonus.query.get(id)
    if not bonus:
        raise ApiError("bonus_not_found", status=404)

    db.session.delete(bonus)
    db.session.commit()

    return jsonify({"ok": True})