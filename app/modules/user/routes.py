from flask import Blueprint, request, jsonify
from datetime import datetime
from decimal import Decimal

from ...extensions import db
from ...models.user import User
from ...models.salaire import Salaire

bp = Blueprint("users", __name__, url_prefix="/users")


# ➕ CREATE USER
@bp.route("/", methods=["POST"])
def add_user():
    data = request.get_json(silent=True) or {}

    try:
        salaire_base = Decimal(str(data.get("salaire", 0) or 0))
        current_period = datetime.now().strftime("%B %Y")

        user = User(
            email=data["email"],
            role=data.get("role", "EMPLOYEE"),
            status=data.get("status", "ACTIVE"),
            cin=data.get("cin"),
            nom_complet=data["nom_complet"],
            tel=data.get("tel"),
            dept=data.get("dept"),
            nom_entreprise=data.get("nom_entreprise"),
            salaire=salaire_base,
            poste=data.get("poste"),
            contract_type=data.get("contract_type"),
            date_embauche=datetime.fromisoformat(data["date_embauche"]).date()
            if data.get("date_embauche") else None
        )

        user.set_password(data["password"])

        db.session.add(user)
        db.session.flush()

        # IMPORTANT:
        # Salaire does NOT store nom_complet or dept anymore.
        # It only stores employee_id and salary data.
        salaire = Salaire(
            employee_id=user.id,
            periode=current_period,
            salaire_base=salaire_base,
            primes=Salaire.get_employee_primes_total(user.id),
            deductions=Salaire.get_employee_deductions_total(user.id),
            net=salaire_base + Salaire.get_employee_primes_total(user.id) - Salaire.get_employee_deductions_total(user.id),
            status="pending",
            paid_at=None,
        )

        db.session.add(salaire)
        db.session.commit()

        return jsonify({
            "message": "Utilisateur ajouté",
            "user_id": user.id
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


# 📄 GET ALL USERS
@bp.route("/", methods=["GET"])
def get_users():
    users = User.query.all()

    return jsonify([
        {
            "id": u.id,
            "email": u.email,
            "role": u.role,
            "status": u.status,
            "cin": u.cin,
            "nom_complet": u.nom_complet,
            "tel": u.tel,
            "dept": u.dept,
            "nom_entreprise": u.nom_entreprise,
            "salaire": str(u.salaire) if u.salaire is not None else None,
            "poste": u.poste,
            "contract_type": u.contract_type,
            "date_embauche": u.date_embauche.isoformat() if u.date_embauche else None,
            "created_at": u.created_at.isoformat() if u.created_at else None
        }
        for u in users
    ])


# 🔍 GET ONE USER
@bp.route("/<int:user_id>", methods=["GET"])
def get_user(user_id):
    user = User.query.get_or_404(user_id)

    return jsonify({
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "status": user.status,
        "cin": user.cin,
        "nom_complet": user.nom_complet,
        "tel": user.tel,
        "dept": user.dept,
        "nom_entreprise": user.nom_entreprise,
        "salaire": str(user.salaire) if user.salaire is not None else None,
        "poste": user.poste,
        "contract_type": user.contract_type,
        "date_embauche": user.date_embauche.isoformat() if user.date_embauche else None,
        "created_at": user.created_at.isoformat() if user.created_at else None
    })


# ✏️ UPDATE USER
@bp.route("/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json(silent=True) or {}

    try:
        user.email = data.get("email", user.email)
        user.role = data.get("role", user.role)
        user.status = data.get("status", user.status)

        user.cin = data.get("cin", user.cin)
        user.nom_complet = data.get("nom_complet", user.nom_complet)
        user.tel = data.get("tel", user.tel)
        user.dept = data.get("dept", user.dept)
        user.nom_entreprise = data.get("nom_entreprise", user.nom_entreprise)
        user.poste = data.get("poste", user.poste)
        user.contract_type = data.get("contract_type", user.contract_type)

        if data.get("salaire") is not None:
            user.salaire = Decimal(str(data.get("salaire") or 0))

        if data.get("date_embauche"):
            user.date_embauche = datetime.fromisoformat(
                data["date_embauche"]
            ).date()

        if data.get("password"):
            user.set_password(data["password"])

        db.session.commit()

        return jsonify({"message": "Utilisateur modifié"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


# ❌ DELETE USER
@bp.route("/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)

    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": "Utilisateur supprimé"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400