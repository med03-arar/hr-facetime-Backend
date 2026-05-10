import os
import smtplib
from email.message import EmailMessage

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity,
    create_access_token,
    get_jwt
)
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from werkzeug.security import generate_password_hash, check_password_hash

from ...extensions import db, limiter
from ...models.user import User
from ...errors import ApiError

bp = Blueprint("auth", __name__)


def _reset_serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])


def _build_reset_token(email: str) -> str:
    return _reset_serializer().dumps(email, salt="password-reset")


def _verify_reset_token(token: str, max_age_seconds: int = 3600) -> str | None:
    try:
        return _reset_serializer().loads(token, salt="password-reset", max_age=max_age_seconds)
    except (BadSignature, SignatureExpired):
        return None


def _send_reset_email(recipient_email: str, reset_url: str) -> bool:
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    mail_from = os.getenv("MAIL_FROM", smtp_username or "no-reply@localhost")
    use_tls = os.getenv("SMTP_USE_TLS", "true").lower() not in {"0", "false", "no"}

    if not smtp_host or not smtp_username or not smtp_password:
        return False

    message = EmailMessage()
    message["Subject"] = "Réinitialisation de votre mot de passe"
    message["From"] = mail_from
    message["To"] = recipient_email
    message.set_content(
        f"Bonjour,\n\nCliquez sur ce lien pour réinitialiser votre mot de passe : {reset_url}\n\nCe lien expire dans 1 heure.\n"
    )

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as smtp:
            if use_tls:
                smtp.starttls()
            smtp.login(smtp_username, smtp_password)
            smtp.send_message(message)
        return True
    except smtplib.SMTPAuthenticationError as exc:
        current_app.logger.warning(
            "SMTP authentication failed for password reset email: %s", exc
        )
        return False
    except smtplib.SMTPException as exc:
        current_app.logger.warning(
            "SMTP error while sending password reset email: %s", exc
        )
        return False


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


@bp.post("/forgot-password")
@limiter.limit("5/minute")
def post_forgot_password():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()

    if not email:
        return jsonify({"error": "email required"}), 422

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"message": "Si le compte existe, un email de réinitialisation a été envoyé."}), 200

    token = _build_reset_token(user.email)
    frontend_base = os.getenv("FRONTEND_URL", "http://localhost:3000")
    reset_url = f"{frontend_base}/connexion?reset_token={token}&email={user.email}"

    email_sent = _send_reset_email(user.email, reset_url)

    response_payload = {
        "message": "Si le compte existe, un email de réinitialisation a été envoyé.",
        "email_sent": email_sent,
    }

    if not email_sent:
        response_payload["reset_url"] = reset_url
        response_payload["token"] = token
        response_payload["delivery_note"] = (
            "SMTP non configuré ou identifiants Gmail refusés. "
            "Utilisez un mot de passe d'application Gmail ou un autre service SMTP."
        )

    return jsonify(response_payload), 200


@bp.post("/reset-password")
@limiter.limit("10/minute")
def post_reset_password():
    data = request.get_json(silent=True) or {}
    token = data.get("token") or ""
    password = data.get("password") or ""

    if not token or not password:
        return jsonify({"error": "token and password required"}), 422

    email = _verify_reset_token(token)
    if not email:
        return jsonify({"error": "invalid or expired token"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "user not found"}), 404

    user.password_hash = generate_password_hash(password)
    db.session.commit()

    return jsonify({"message": "Password updated successfully"}), 200
    
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