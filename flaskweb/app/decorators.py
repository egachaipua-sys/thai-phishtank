"""Auth decorators used by route handlers.

These guard state-changing endpoints. Without them, several routes were
callable by any unauthenticated visitor (delete_user, delete_report, etc.).
"""
from functools import wraps
from flask import session, jsonify, redirect, url_for, request


def _wants_json():
    """Heuristic: does the caller expect a JSON response?

    AJAX endpoints should get a JSON 401/403; full-page navigations should be
    redirected to the login page.
    """
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        return True
    if request.is_json:
        return True
    accept = request.headers.get("Accept") or ""
    if "application/json" in accept:
        return True
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return True
    return False


def login_required(f):
    """Reject unauthenticated callers."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            if _wants_json():
                return jsonify({"status": "error", "error": "Unauthorized"}), 401
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    """Reject anyone who isn't an authenticated admin."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session or session.get("user_role") != "admin":
            if _wants_json():
                return jsonify({"status": "error", "error": "Forbidden"}), 403
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return wrapper
