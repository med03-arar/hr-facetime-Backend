from datetime import date, datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from ...errors import ApiError
from ...extensions import db
from ...models.deduction import Deduction
from ...models.user import User

bp = Blueprint("deductions", __name__)

VALID_STATUSES = ["pending", "approved", "rejected"]


def parse_date_value(value):
    if value in (None, ""):
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise ApiError("invalid_date", status=400) from exc


def serialize_deduction(deduction):
    return {
        "id": deduction.id,
        "employee_id": deduction.employee_id,
        "nom_complet": deduction.nom_complet,
        "montant": float(deduction.montant),
        "motif": deduction.motif,
        "type": deduction.motif,
        "description": deduction.description,
        "date_insere": deduction.date_insere.isoformat() if deduction.date_insere else None,
        "status": deduction.status,
        "created_at": deduction.created_at.isoformat() if deduction.created_at else None,
    }


@bp.get("/")
@jwt_required()
def get_deductions():
    deductions = Deduction.query.all()
    return jsonify([serialize_deduction(deduction) for deduction in deductions])


@bp.get("/<int:id>")
@jwt_required()
def get_deduction(id):
    deduction = Deduction.query.get(id)
    if not deduction:
        raise ApiError("deduction_not_found", status=404)

    return jsonify(serialize_deduction(deduction))


@bp.get("/employee/<int:employee_id>")
@jwt_required()
def get_employee_deductions(employee_id):
    deductions = Deduction.query.filter_by(employee_id=employee_id).all()
    return jsonify([serialize_deduction(deduction) for deduction in deductions])


@bp.post("/")
@jwt_required()
def create_deduction():
    data = request.get_json() or {}

    employee_id = data.get("employee_id")
    nom_complet = data.get("nom_complet")
    montant = data.get("montant")
    motif = data.get("motif") or data.get("type")

    if not employee_id or not nom_complet or montant is None:
        raise ApiError("missing_fields", status=400)

    try:
        employee_id = int(employee_id)
    except (TypeError, ValueError):
        raise ApiError("invalid_employee_id", status=400)

    try:
        montant = float(montant)
    except (TypeError, ValueError):
        raise ApiError("invalid_montant", status=400)

    if montant <= 0:
        raise ApiError("montant_must_be_positive", status=400)

    user = User.query.get(employee_id)
    if not user:
        raise ApiError("user_not_found", status=404)

    deduction = Deduction(
        employee_id=employee_id,
        nom_complet=nom_complet,
        montant=montant,
        motif=motif,
        description=data.get("description"),
        date_insere=parse_date_value(data.get("date_insere")) or date.today(),
        status=(data.get("status") or "pending").lower(),
    )

    if deduction.status not in VALID_STATUSES:
        raise ApiError("invalid_status", status=400)

    db.session.add(deduction)
    db.session.commit()

    return jsonify({"message": "Deduction created", "id": deduction.id}), 201


@bp.put("/<int:id>")
@jwt_required()
def update_deduction(id):
    deduction = Deduction.query.get(id)
    if not deduction:
        raise ApiError("deduction_not_found", status=404)

    data = request.get_json() or {}

    if "montant" in data:
        try:
            amount = float(data["montant"])
        except (TypeError, ValueError):
            raise ApiError("invalid_montant", status=400)
        if amount <= 0:
            raise ApiError("montant_must_be_positive", status=400)
        deduction.montant = amount

    if "motif" in data or "type" in data:
        deduction.motif = data.get("motif") or data.get("type")

    if "description" in data:
        deduction.description = data["description"]

    if "date_insere" in data:
        deduction.date_insere = parse_date_value(data.get("date_insere"))

    if "status" in data:
        status = str(data["status"]).lower()
        if status not in VALID_STATUSES:
            raise ApiError("invalid_status", status=400)
        deduction.status = status

    db.session.commit()
    return jsonify({"ok": True})


@bp.delete("/<int:id>")
@jwt_required()
def delete_deduction(id):
    deduction = Deduction.query.get(id)
    if not deduction:
        raise ApiError("deduction_not_found", status=404)

    db.session.delete(deduction)
    db.session.commit()

    return jsonify({"ok": True})