from flask import Blueprint, jsonify

bp = Blueprint("audit", __name__)

@bp.get("/health")
def health():
    return jsonify({"ok": True, "module": "audit"})
