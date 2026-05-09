from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from ...extensions import db
from ...models.employee import Position
from ...errors import ApiError
from ...utils.roles import role_required

bp = Blueprint("positions", __name__, url_prefix="/positions")


def serialize(pos: Position):
    return {
        "id": pos.id,
        "name": pos.name,
        "grade": pos.grade
    }


# =========================
# GET ALL
# =========================
@bp.get("/")

@jwt_required()
@role_required("RH")
def get_positions():

    positions = Position.query.all()

    return jsonify([serialize(p) for p in positions]), 200


# =========================
# GET ONE
# =========================
@bp.get("/<int:pos_id>")
@jwt_required()
@role_required("RH")
def get_position(pos_id):

    pos = Position.query.get(pos_id)

    if not pos:
        raise ApiError("Position not found", status=404)

    return jsonify(serialize(pos)), 200


# =========================
# CREATE
# =========================
@bp.post("/")
@jwt_required()
@role_required("RH")
def create_position():

    data = request.get_json() or {}

    if not data.get("name"):
        raise ApiError("name is required", status=400)

    pos = Position(
        name=data["name"],
        grade=data.get("grade")
    )

    db.session.add(pos)
    db.session.commit()

    return jsonify(serialize(pos)), 201


# =========================
# UPDATE
# =========================
@bp.put("/<int:pos_id>")
@jwt_required()
@role_required("RH")
def update_position(pos_id):

    pos = Position.query.get(pos_id)

    if not pos:
        raise ApiError("Position not found", status=404)

    data = request.get_json() or {}

    if "name" in data:
        pos.name = data["name"]

    if "grade" in data:
        pos.grade = data["grade"]

    db.session.commit()

    return jsonify(serialize(pos)), 200


# =========================
# DELETE
# =========================
@bp.delete("/<int:pos_id>")
@jwt_required()
@role_required("RH")
def delete_position(pos_id):

    pos = Position.query.get(pos_id)

    if not pos:
        raise ApiError("Position not found", status=404)

    db.session.delete(pos)
    db.session.commit()

    return jsonify({"message": "Position deleted"}), 200