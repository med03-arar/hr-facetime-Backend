from flask import Blueprint, request, jsonify
from datetime import datetime
from decimal import Decimal
import re

from ...extensions import db
from ...models.salaire import Salaire
from ...models.user import User

bp = Blueprint("salaires", __name__)


def serialize_salaire(salaire, user=None):
    if user is None and salaire.employee_id:
        user = User.query.get(salaire.employee_id)

    primes_total = Salaire.get_employee_primes_total(salaire.employee_id) if salaire.employee_id else 0
    deductions_total = Salaire.get_employee_deductions_total(salaire.employee_id) if salaire.employee_id else 0
    net_total = (salaire.salaire_base or 0) + primes_total - deductions_total

    return {
        "id": salaire.id,
        "employee_id": salaire.employee_id,

        # These come from User, not from Salaire table.
        "nom_complet": user.nom_complet if user else None,
        "dept": user.dept if user else None,
        "email": user.email if user else None,
        "poste": user.poste if user else None,

        "employee": {
            "id": user.id if user else None,
            "nom_complet": user.nom_complet if user else None,
            "dept": user.dept if user else None,
            "email": user.email if user else None,
            "poste": user.poste if user else None,
        } if user else None,

        "periode": salaire.periode,
        "salaire_base": float(salaire.salaire_base or 0),
        "primes": float(primes_total),
        "deductions": float(deductions_total),
        "net": float(net_total),
        "status": salaire.status,
        "paid_at": salaire.paid_at.isoformat() if salaire.paid_at else None,
        "created_at": salaire.created_at.isoformat() if salaire.created_at else None,
    }


def coerce_decimal(value, fallback=0):
    if value is None or value == "":
        return Decimal(str(fallback or 0))
    return Decimal(str(value))


def resolve_value(data, *keys, default=None):
    for key in keys:
        if key in data and data[key] is not None:
            return data[key]
    return default


# 📊 GET ALL SALAIRES
@bp.route("/", methods=["GET"])
def get_salaires():
    salaires = Salaire.query.all()

    employee_ids = [s.employee_id for s in salaires if s.employee_id]
    users = User.query.filter(User.id.in_(employee_ids)).all() if employee_ids else []
    users_map = {u.id: u for u in users}

    return jsonify([
        serialize_salaire(s, users_map.get(s.employee_id))
        for s in salaires
    ])


# 🔍 GET ONE SALAIRE
@bp.route("/<int:salaire_id>", methods=["GET"])
def get_salaire(salaire_id):
    salaire = Salaire.query.get_or_404(salaire_id)
    user = User.query.get(salaire.employee_id)

    return jsonify(serialize_salaire(salaire, user))


# ✏️ UPDATE SALAIRE
@bp.route("/<int:salaire_id>", methods=["PATCH"])
def update_salaire(salaire_id):
    salaire = Salaire.query.get_or_404(salaire_id)
    data = request.get_json(silent=True) or {}

    try:
        employee_id = resolve_value(data, "employee_id")

        if employee_id is not None:
            employee_id_text = str(employee_id).strip()
            numeric_match = re.search(r"(\d+)$", employee_id_text)

            if employee_id_text.isdigit():
                new_employee_id = int(employee_id_text)
            elif numeric_match:
                new_employee_id = int(numeric_match.group(1))
            else:
                return jsonify({"error": "employee_id invalide"}), 400

            user_exists = User.query.get(new_employee_id)

            if not user_exists:
                return jsonify({
                    "error": f"Aucun utilisateur trouvé avec employee_id={new_employee_id}"
                }), 404

            salaire.employee_id = new_employee_id

        periode = resolve_value(data, "periode", "period")
        if periode is not None:
            salaire.periode = str(periode)

        salaire.salaire_base = coerce_decimal(
            resolve_value(data, "salaire_base", "base_salary"),
            salaire.salaire_base
        )

        salaire.primes = Salaire.get_employee_primes_total(salaire.employee_id)

        salaire.deductions = Salaire.get_employee_deductions_total(salaire.employee_id)

        status = resolve_value(data, "status")
        if status is not None:
            salaire.status = str(status)

            if str(status).lower() == "paid":
                paid_at_value = resolve_value(data, "paid_at", "payment_date")

                if paid_at_value:
                    salaire.paid_at = datetime.fromisoformat(str(paid_at_value))
                elif not salaire.paid_at:
                    salaire.paid_at = datetime.utcnow()

            else:
                paid_at_value = resolve_value(data, "paid_at", "payment_date")

                if paid_at_value == "" or paid_at_value is None:
                    salaire.paid_at = None

        paid_at_value = resolve_value(data, "paid_at", "payment_date")
        if paid_at_value is not None:
            salaire.paid_at = datetime.fromisoformat(str(paid_at_value)) if paid_at_value else None

        salaire.net = salaire.salaire_base + salaire.primes - salaire.deductions

        db.session.commit()

        user = User.query.get(salaire.employee_id)
        return jsonify(serialize_salaire(salaire, user))

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


# ❌ DELETE SALAIRE
@bp.route("/<int:salaire_id>", methods=["DELETE"])
def delete_salaire(salaire_id):
    salaire = Salaire.query.get_or_404(salaire_id)

    try:
        db.session.delete(salaire)
        db.session.commit()
        return jsonify({"message": "Salaire supprimé"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


# 📈 GET SALAIRES BY EMPLOYEE
@bp.route("/employee/<int:employee_id>", methods=["GET"])
def get_salaires_by_employee(employee_id):
    user = User.query.get_or_404(employee_id)
    salaires = Salaire.query.filter_by(employee_id=employee_id).all()

    return jsonify([
        serialize_salaire(s, user)
        for s in salaires
    ])