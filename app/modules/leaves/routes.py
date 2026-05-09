from flask import Blueprint, request, jsonify
from ...extensions import db
from ...models.leave import Leave

bp = Blueprint('leaves', __name__, url_prefix='/leaves')


def serialize_leave(leave):
    """Serialize a Leave object to a dictionary."""
    return {
        "id": leave.id,
        "employee_id": leave.employee_id,
        "type": leave.leave_type,
        "start_date": leave.start_date.isoformat() if leave.start_date else None,
        "end_date": leave.end_date.isoformat() if leave.end_date else None,
        "status": leave.status,
        "reason": leave.reason
    }


# get all leaves
@bp.route('/', methods=['GET'])
def get_leaves():
    leaves = Leave.query.all()
    return jsonify([serialize_leave(leave) for leave in leaves]), 200


# get leave by id
@bp.route('/<int:id>', methods=['GET'])
def get_leave(id):
    leave = Leave.query.get_or_404(id)
    return jsonify(serialize_leave(leave)), 200


# create leave
@bp.route('/', methods=['POST'])
def add_leave():
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    required_fields = ["employee_id", "leave_type", "start_date", "end_date"]
    missing = [field for field in required_fields if field not in data]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    try:
        leave = Leave(
            employee_id=data["employee_id"],
            leave_type=data["leave_type"],
            start_date=data["start_date"],
            end_date=data["end_date"],
            reason=data.get("reason")
        )

        db.session.add(leave)
        db.session.commit()

        return jsonify({"message": "Leave request created", "leave": serialize_leave(leave)}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to create leave request", "details": str(e)}), 500


# update leave status (approve or reject)
@bp.route('/<int:id>/status', methods=['PUT'])
def update_leave_status(id):
    leave = Leave.query.get_or_404(id)
    data = request.get_json()

    if not data or "status" not in data:
        return jsonify({"error": "Status is required"}), 400

    allowed_statuses = {"APPROVED", "REJECTED", "PENDING"}
    status = data["status"].upper()

    if status not in allowed_statuses:
        return jsonify({"error": f"Invalid status. Must be one of: {', '.join(allowed_statuses)}"}), 400

    try:
        leave.status = status
        db.session.commit()
        return jsonify({"message": f"Leave status updated to {status}", "leave": serialize_leave(leave)}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update leave status", "details": str(e)}), 500


# delete leave
@bp.route('/<int:id>', methods=['DELETE'])
def delete_leave(id):
    leave = Leave.query.get_or_404(id)

    try:
        db.session.delete(leave)
        db.session.commit()
        return jsonify({"message": "Leave deleted successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to delete leave", "details": str(e)}), 500