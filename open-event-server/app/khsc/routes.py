"""
KHSC integration routes — Flask blueprint mounted at /v1/khsc.

Endpoints:
    POST /v1/khsc/import          Import delegates from KHSC into Open Event
    POST /v1/khsc/sync-checkins   Reconcile check-in state for an event
    POST /v1/khsc/push-checkin    Push a single Open Event check-in to KHSC
    GET  /v1/khsc/stats           Live event stats proxied from KHSC

All endpoints require a valid JWT (organizer or admin).
"""

from flask import Blueprint, jsonify, request

from app.api.helpers.errors import ForbiddenError, UnprocessableEntityError
from app.api.helpers.permissions import jwt_required
from app.khsc.client import KHSCClient, KHSCError
from app.khsc.sync import import_delegates, push_checkin_to_khsc, sync_checkins

khsc_routes = Blueprint('khsc_routes', __name__, url_prefix='/v1/khsc')


def _require_json_field(body, field):
    value = body.get(field)
    if not value:
        raise UnprocessableEntityError({'source': field}, f"'{field}' is required.")
    return value


# ── POST /v1/khsc/import ──────────────────────────────────────────────────────

@khsc_routes.route('/import', methods=['POST'])
@jwt_required
def import_from_khsc():
    """
    Import a list of KHSC delegates into Open Event as attendees.

    Request body:
        {
            "event_id": 1,
            "uids": ["CONF-1001", "CONF-1002", ...]
        }

    Response:
        {
            "created": 2,
            "updated": 0,
            "failed": []
        }
    """
    body = request.get_json(silent=True) or {}
    event_id = _require_json_field(body, 'event_id')
    uids = _require_json_field(body, 'uids')

    if not isinstance(uids, list) or len(uids) == 0:
        raise UnprocessableEntityError({'source': 'uids'}, "'uids' must be a non-empty list.")

    try:
        result = import_delegates(event_id, uids)
    except KHSCError as e:
        return jsonify({'error': str(e)}), e.status_code or 502

    return jsonify(result), 200


# ── POST /v1/khsc/sync-checkins ───────────────────────────────────────────────

@khsc_routes.route('/sync-checkins', methods=['POST'])
@jwt_required
def sync_event_checkins():
    """
    Reconcile check-in state between KHSC and Open Event for all attendees in
    an event who were originally imported from KHSC.

    Request body:
        {"event_id": 1}

    Response:
        {
            "synced": 3,
            "already_in_sync": 8,
            "failed": []
        }
    """
    body = request.get_json(silent=True) or {}
    event_id = _require_json_field(body, 'event_id')

    try:
        result = sync_checkins(event_id)
    except KHSCError as e:
        return jsonify({'error': str(e)}), e.status_code or 502

    return jsonify(result), 200


# ── POST /v1/khsc/push-checkin ────────────────────────────────────────────────

@khsc_routes.route('/push-checkin', methods=['POST'])
@jwt_required
def push_checkin():
    """
    Push a check-in that was recorded in Open Event (e.g. via the Android app)
    back to KHSC so both systems stay in sync.

    Request body:
        {"uid": "CONF-1001"}

    Response on success:
        {"delegate_id": "CONF-1001", "name": "James Mwangi", "checked_in_at": "..."}

    Response on failure (already checked in, unpaid, not found):
        {"error": "<KHSC message>"}, 409 / 403 / 404
    """
    body = request.get_json(silent=True) or {}
    uid = _require_json_field(body, 'uid')

    try:
        result = push_checkin_to_khsc(uid)
    except KHSCError as e:
        return jsonify({'error': str(e)}), e.status_code or 502

    return jsonify(result), 200


# ── GET /v1/khsc/stats ────────────────────────────────────────────────────────

@khsc_routes.route('/stats', methods=['GET'])
@jwt_required
def khsc_stats():
    """
    Proxy KHSC live event stats directly to the caller.

    Response:
        {
            "total_registered": 12,
            "total_paid": 9,
            "total_checked_in": 2,
            "total_unpaid": 3,
            "total_revenue": 99000.0
        }
    """
    try:
        result = KHSCClient().event_stats()
    except KHSCError as e:
        return jsonify({'error': str(e)}), e.status_code or 502

    return jsonify(result), 200
