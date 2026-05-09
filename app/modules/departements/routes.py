from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from ...extensions import db
from ...models.employee import Department
from ...errors import ApiError
from ...utils.roles import role_required

bp = Blueprint("departments", __name__, url_prefix="/departments")


def serialize(dep: Department):
    return {
        "id": dep.id,
        "name": dep.name
    }


# =========================
# GET ALL
# =========================
@bp.get("/")
@jwt_required()
@role_required("RH")
def get_departments():
    deps = Department.query.all()
    return jsonify([serialize(d) for d in deps]), 200


# =========================
# GET ONE
# =========================
@bp.get("/<int:dep_id>")
@jwt_required()
@role_required("RH")
def get_department(dep_id):

    dep = Department.query.get(dep_id)

    if not dep:
        raise ApiError("Department not found", status=404)

    return jsonify(serialize(dep)), 200


# =========================
# CREATE
# =========================
@bp.post("/")
@jwt_required()
@role_required("RH")
def create_department():

    data = request.get_json() or {}

    if not data.get("name"):
        raise ApiError("name is required", status=400)

    dep = Department(name=data["name"])

    db.session.add(dep)
    db.session.commit()

    return jsonify(serialize(dep)), 201


# =========================
# UPDATE
# =========================
@bp.put("/<int:dep_id>")
@jwt_required()
@role_required("RH")
def update_department(dep_id):

    dep = Department.query.get(dep_id)

    if not dep:
        raise ApiError("Department not found", status=404)

    data = request.get_json() or {}

    if "name" in data:
        dep.name = data["name"]

    db.session.commit()

    return jsonify(serialize(dep)), 200


# =========================
# DELETE
# =========================
@bp.delete("/<int:dep_id>")
@jwt_required()
@role_required("RH")
def delete_department(dep_id):

    dep = Department.query.get(dep_id)

    if not dep:
        raise ApiError("Department not found", status=404)

    db.session.delete(dep)
    db.session.commit()

    return jsonify({"message": "Department deleted"}), 200