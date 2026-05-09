from functools import wraps
from flask_jwt_extended import get_jwt_identity
from flask import jsonify
from ..models.user import User


def role_required(role):

    def decorator(fn):

        @wraps(fn)
        def wrapper(*args, **kwargs):

            user_id = get_jwt_identity()
            user = User.query.get(user_id)

            if not user or user.role != role:
                return jsonify({
                    "error": "Access denied"
                }), 403

            return fn(*args, **kwargs)

        return wrapper

    return decorator