from flask import Blueprint, request, jsonify
from datetime import datetime
from decimal import Decimal

from ...extensions import db
from ...models.user import User
from ...models.salaire import Salaire
# Ajoute ces imports aux imports existants
import smtplib
import secrets
import string
import bcrypt
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
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
    # ── Helpers ─────────────────────────────────────────────────

def generate_temp_password(length=10):
    characters = string.ascii_letters + string.digits + "!@#$"
    return ''.join(secrets.choice(characters) for _ in range(length))


import os

def send_reset_email(to_email, nom_complet, temp_password):

    MAIL_SERVER = os.getenv("MAIL_SERVER")
    MAIL_PORT = int(os.getenv("MAIL_PORT"))
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")

    msg = MIMEMultipart("alternative")

    msg["Subject"] = "Réinitialisation de votre mot de passe"
    msg["From"] = MAIL_USERNAME
    msg["To"] = to_email

    html = f"""
    <html>
    <body>

        <h2>Bonjour {nom_complet},</h2>

        <p>Votre mot de passe temporaire est :</p>

        <h3 style="color:#2d6cdf;">
            {temp_password}
        </h3>

        <p>
            Veuillez changer votre mot de passe après connexion.
        </p>

    </body>
    </html>
    """

    msg.attach(MIMEText(html, "html"))

    server = smtplib.SMTP(MAIL_SERVER, MAIL_PORT)

    server.starttls()

    server.login(MAIL_USERNAME, MAIL_PASSWORD)

    server.sendmail(
        MAIL_USERNAME,
        to_email,
        msg.as_string()
    )

    server.quit()

# 🔑 FORGOT PASSWORD
@bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip()

    if not email:
        return jsonify({"error": "Email requis"}), 400

    # 1. Chercher l'email dans la BD via SQLAlchemy (comme ton code existant)
    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"error": "Email introuvable"}), 404

    if user.status == "SUSPENDED":
        return jsonify({"error": "Compte suspendu"}), 403

    try:
        # 2. Générer mot de passe temporaire
        temp_password = generate_temp_password()

        # 3. Hasher et sauvegarder (utilise set_password() qui existe déjà dans ton modèle User)
        user.set_password(temp_password)
        db.session.commit()

        # 4. Envoyer l'email
        send_reset_email(user.email, user.nom_complet, temp_password)

        return jsonify({
            "message": f"Mot de passe temporaire envoyé à {email}"
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500