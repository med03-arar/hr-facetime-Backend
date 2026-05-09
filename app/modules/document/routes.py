import os
from io import BytesIO
from datetime import datetime

from flask import (
    request,
    jsonify,
    Blueprint,
    send_file
)

from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity
)

from ...extensions import db
from ...models.document import Document


document_bp = Blueprint("documents", __name__)


# ─────────────────────────────────────────────
# UPLOAD DOCUMENT
# USER → upload fichier dans la DB
# ─────────────────────────────────────────────
@document_bp.route("/upload", methods=["POST"])
@jwt_required()
def upload_document():

    user_id = get_jwt_identity()

    document_type = request.form.get("document_type")
    label = request.form.get("label")

    file = request.files.get("file")

    if not document_type or not file:
        return jsonify({
            "error": "document_type and file are required"
        }), 400

    # ✅ Lire contenu fichier
    file_data = file.read()

    if not file_data:
        return jsonify({
            "error": "Empty file"
        }), 400

    # ✅ Création document
    doc = Document(
        user_id=user_id,
        document_type=document_type,
        label=label,

        file_name=file.filename,
        mime_type=file.content_type,
        file_data=file_data,

        status="PENDING",
        created_at=datetime.utcnow()
    )

    db.session.add(doc)
    db.session.commit()

    return jsonify({
        "message": "Document uploaded successfully",
        "document": {
            "id": doc.id,
            "file_name": doc.file_name,
            "status": doc.status
        }
    }), 201


# ─────────────────────────────────────────────
# GET DOCUMENTS
# USER → ses documents
# ADMIN → tous les documents
# ─────────────────────────────────────────────
@document_bp.route("/", methods=["GET"])
@jwt_required()
def get_documents():

    user_id = get_jwt_identity()

    role = (
        request.args.get("role") or "USER"
    ).upper()

    query = Document.query

    # ✅ USER → uniquement ses docs
    if role != "ADMIN":
        query = query.filter_by(user_id=user_id)

    documents = query.order_by(
        Document.created_at.desc()
    ).all()

    return jsonify([
        {
            "id": doc.id,

            "user_id": doc.user_id,

            "employee_name": (
                doc.user.nom_complet
                if doc.user else None
            ),

            "document_type": doc.document_type,

            "label": doc.label,

            "file_name": doc.file_name,

            "mime_type": doc.mime_type,

            "status": doc.status,

            "comment": doc.comment,

            "created_at": (
                doc.created_at.isoformat()
                if doc.created_at else None
            ),

            "reviewed_at": (
                doc.reviewed_at.isoformat()
                if doc.reviewed_at else None
            )
        }
        for doc in documents
    ]), 200


# ─────────────────────────────────────────────
# GET ONE DOCUMENT
# ─────────────────────────────────────────────
@document_bp.route("/<int:doc_id>", methods=["GET"])
@jwt_required()
def get_document(doc_id):

    user_id = get_jwt_identity()

    role = (
        request.args.get("role") or "USER"
    ).upper()

    doc = Document.query.get_or_404(doc_id)

    # ✅ sécurité accès
    if role != "ADMIN" and doc.user_id != user_id:
        return jsonify({
            "error": "Unauthorized"
        }), 403

    return jsonify({
        "id": doc.id,

        "user_id": doc.user_id,

        "employee_name": (
            doc.user.nom_complet
            if doc.user else None
        ),

        "document_type": doc.document_type,

        "label": doc.label,

        "file_name": doc.file_name,

        "mime_type": doc.mime_type,

        "status": doc.status,

        "comment": doc.comment,

        "created_at": (
            doc.created_at.isoformat()
            if doc.created_at else None
        ),

        "reviewed_at": (
            doc.reviewed_at.isoformat()
            if doc.reviewed_at else None
        )
    }), 200


# ─────────────────────────────────────────────
# DOWNLOAD DOCUMENT
# USER propriétaire ou ADMIN
# ─────────────────────────────────────────────
@document_bp.route("/<int:doc_id>/download", methods=["GET"])
@jwt_required()
def download_document(doc_id):

    user_id = get_jwt_identity()

    role = (
        request.args.get("role") or "USER"
    ).upper()

    doc = Document.query.get_or_404(doc_id)

    # ✅ sécurité accès
    if role != "ADMIN" and doc.user_id != user_id:
        return jsonify({
            "error": "Unauthorized"
        }), 403

    return send_file(
        BytesIO(doc.file_data),

        mimetype=doc.mime_type,

        as_attachment=True,

        download_name=doc.file_name
    )


# ─────────────────────────────────────────────
# APPROVE DOCUMENT
# ADMIN ONLY
# ─────────────────────────────────────────────
@document_bp.route("/<int:doc_id>/approve", methods=["PUT"])
@jwt_required()
def approve_document(doc_id):

    role = (
        request.args.get("role") or "USER"
    ).upper()

    if role != "ADMIN":
        return jsonify({
            "error": "Forbidden"
        }), 403

    doc = Document.query.get_or_404(doc_id)

    doc.status = "APPROVED"

    doc.reviewed_at = datetime.utcnow()

    db.session.commit()

    return jsonify({
        "message": "Document approved"
    }), 200


# ─────────────────────────────────────────────
# REJECT DOCUMENT
# ADMIN ONLY
# ─────────────────────────────────────────────
@document_bp.route("/<int:doc_id>/reject", methods=["PUT"])
@jwt_required()
def reject_document(doc_id):

    role = (
        request.args.get("role") or "USER"
    ).upper()

    if role != "ADMIN":
        return jsonify({
            "error": "Forbidden"
        }), 403

    doc = Document.query.get_or_404(doc_id)

    doc.status = "REJECTED"

    doc.reviewed_at = datetime.utcnow()

    db.session.commit()

    return jsonify({
        "message": "Document rejected"
    }), 200


# ─────────────────────────────────────────────
# ADD COMMENT
# ADMIN ONLY
# ─────────────────────────────────────────────
@document_bp.route("/<int:doc_id>/comment", methods=["PUT"])
@jwt_required()
def add_comment(doc_id):

    role = (
        request.args.get("role") or "USER"
    ).upper()

    if role != "ADMIN":
        return jsonify({
            "error": "Forbidden"
        }), 403

    doc = Document.query.get_or_404(doc_id)

    data = request.get_json()

    comment = data.get("comment")

    doc.comment = comment

    db.session.commit()

    return jsonify({
        "message": "Comment added"
    }), 200


# ─────────────────────────────────────────────
# DELETE DOCUMENT
# USER propriétaire ou ADMIN
# ─────────────────────────────────────────────
@document_bp.route("/<int:doc_id>", methods=["DELETE"])
@jwt_required()
def delete_document(doc_id):

    user_id = get_jwt_identity()

    role = (
        request.args.get("role") or "USER"
    ).upper()

    doc = Document.query.get_or_404(doc_id)

    # ✅ sécurité suppression
    if role != "ADMIN" and doc.user_id != user_id:
        return jsonify({
            "error": "Unauthorized"
        }), 403

    db.session.delete(doc)

    db.session.commit()

    return jsonify({
        "message": "Document deleted"
    }), 200
@document_bp.route("/<int:doc_id>/view", methods=["GET"])
@jwt_required()
def view_document(doc_id):

    user_id = get_jwt_identity()

    role = (
        request.args.get("role") or "USER"
    ).upper()

    doc = Document.query.get_or_404(doc_id)

    # sécurité
    if role != "ADMIN" and doc.user_id != user_id:
        return jsonify({
            "error": "Unauthorized"
        }), 403

    return send_file(
        BytesIO(doc.file_data),

        mimetype=doc.mime_type,

        as_attachment=False,

        download_name=doc.file_name
    )