from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from ...extensions import db
from ...errors import ApiError
from ...models.primes import Prime

bp = Blueprint("primes", __name__)

VALID_STATUSES = ["pending", "approved", "rejected"]


@bp.get("/")
@jwt_required()
def get_primes():
    primes = Prime.query.all()
    return jsonify([
        {
            "id": p.id,
            "employee_id": p.employee_id,
            "nom_complet": p.nom_complet,
            "montant": float(p.montant),
            "type": p.type,
            "date_insere": p.date_insere.isoformat(),
            "status": p.status,
        }
        for p in primes
    ])


@bp.get("/<int:id>")
@jwt_required()
def get_prime(id):
    p = Prime.query.get(id)
    if not p:
        raise ApiError("prime_not_found", status=404)

    return jsonify({
        "id": p.id,
        "employee_id": p.employee_id,
        "nom_complet": p.nom_complet,
        "montant": float(p.montant),
        "type": p.type,
        "description": p.description,
        "date_insere": p.date_insere.isoformat(),
        "status": p.status,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    })


@bp.get("/employee/<int:employee_id>")
@jwt_required()
def get_employee_primes(employee_id):
    primes = Prime.query.filter_by(employee_id=employee_id).all()
    return jsonify([
        {
            "id": p.id,
            "nom_complet": p.nom_complet,
            "montant": float(p.montant),
            "type": p.type,
            "description": p.description,
            "date_insere": p.date_insere.isoformat(),
            "status": p.status,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in primes
    ])


@bp.post("/")
@jwt_required()
def create_prime():
    data = request.get_json() or {}

    employee_id = data.get("employee_id")
    nom_complet = data.get("nom_complet")
    montant     = data.get("montant")

    if not employee_id or not nom_complet or montant is None:
        raise ApiError("missing_fields", status=400)

    try:
        montant = float(montant)
    except (TypeError, ValueError):
        raise ApiError("invalid_montant", status=400)

    if montant <= 0:
        raise ApiError("montant_must_be_positive", status=400)

    try:
        employee_id = int(employee_id)
    except (TypeError, ValueError):
        raise ApiError("invalid_employee_id", status=400)

    # ✅ Vérifier dans la table users
    from ...models.user import User  # adaptez le chemin selon votre projet
    user = User.query.get(employee_id)
    if not user:
        raise ApiError("user_not_found", status=404)

    prime = Prime(
        employee_id=employee_id,
        nom_complet=nom_complet,
        montant=montant,
        type=data.get("type"),
        description=data.get("description"),
        date_insere=data.get("date_insere"),
        status=data.get("status") or "pending",
    )

    db.session.add(prime)
    db.session.commit()

    return jsonify({"message": "Prime created", "id": prime.id}), 201

@bp.put("/<int:id>")
@jwt_required()
def update_prime(id):
    p = Prime.query.get(id)
    if not p:
        raise ApiError("prime_not_found", status=404)

    data = request.get_json() or {}

    if "montant" in data:
        p.montant = data["montant"]
    if "type" in data:
        p.type = data["type"]
    if "date_insere" in data:
        p.date_insere = data["date_insere"]
    if "description" in data:
        p.description = data["description"]
    if "status" in data:
        s = data["status"].lower()
        if s not in VALID_STATUSES:
            raise ApiError("invalid_status", status=400)
        p.status = s

    db.session.commit()
    return jsonify({"ok": True})


@bp.delete("/<int:id>")
@jwt_required()
def delete_prime(id):
    p = Prime.query.get(id)
    if not p:
        raise ApiError("prime_not_found", status=404)

    db.session.delete(p)
    db.session.commit()

    return jsonify({"ok": True})