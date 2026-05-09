from flask import Blueprint, jsonify

bp = Blueprint("face", __name__)

@bp.get("/health")
def health():
    return jsonify({"ok": True, "module": "face"})
