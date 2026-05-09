from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity,
    create_access_token,
    get_jwt
)
from werkzeug.security import generate_password_hash, check_password_hash

from ...extensions import db, limiter
from ...models.user import User
from ...errors import ApiError

bp = Blueprint("auth", __name__)


# 🔐 LOGIN
@bp.post("/login")
@limiter.limit("10/minute")
def post_login():
    data = request.get_json(silent=True) or {}

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        raise ApiError("email and password required", status=422, code="validation_error")

    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid credentials"}), 401

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role}
    )

    return jsonify({
        "access_token": access_token,
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role
        }
    })


@bp.post("/register")
def post_register():
    data = request.get_json(silent=True) or {}

    email = data.get("email")
    password = data.get("password")
    nom_complet = data.get("nom_complet")
    nom_entreprise = data.get("nom_entreprise")

    # validation minimale
    if not email or not password or not nom_complet or not nom_entreprise:
        return jsonify({"error": "Champs obligatoires manquants"}), 400

    # email existant
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email déjà utilisé"}), 409

    try:
        user = User(
            email=email,
            nom_complet=nom_complet,
            nom_entreprise=nom_entreprise,

            # 🔒 FIXED VALUES
            role="RH",
            status="ACTIVE",

            # 🔓 tous les autres champs = NULL automatiquement
            tel=None,
            dept=None,
            contract_type=None,
            date_embauche=None
        )

        user.password_hash = generate_password_hash(password)

        db.session.add(user)
        db.session.commit()

        return jsonify({
            "message": "RH créé avec succès",
            "user": {
                "id": user.id,
                "email": user.email,
                "nom_complet": user.nom_complet,
                "nom_entreprise": user.nom_entreprise,
                "role": user.role,
                "status": user.status
            }
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# 🔄 REFRESH TOKEN
@bp.post("/refresh")
@jwt_required(refresh=True)
def post_refresh():
    uid = get_jwt_identity()
    role = (get_jwt() or {}).get("role")

    new_token = create_access_token(
        identity=str(uid),
        additional_claims={"role": role}
    )

    return jsonify({"access_token": new_token})


# 🚪 LOGOUT
@bp.post("/logout")
@jwt_required()
def post_logout():
    return jsonify({"message": "Logout successful"})