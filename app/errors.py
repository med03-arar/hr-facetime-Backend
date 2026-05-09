from flask import jsonify

class ApiError(Exception):
    def __init__(self, message, status=400, code="bad_request", details=None):
        super().__init__(message)
        self.message = message
        self.status = status
        self.code = code
        self.details = details

def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def handle_api_error(e):
        return jsonify({"error": {"code": e.code, "message": e.message, "details": e.details}}), e.status

    @app.errorhandler(404)
    def not_found(_):
        return jsonify({"error": {"code": "not_found", "message": "Not found"}}), 404
