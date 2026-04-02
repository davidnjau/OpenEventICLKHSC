"""
KHSC Mock Server
Simulates https://khsc.site/api/index.php for local development.

Run:
    pip install flask
    python mock_server.py

Server starts at: http://localhost:9090/api/index.php
"""

import json
import os
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Load delegate data
# ---------------------------------------------------------------------------
DELEGATES_FILE = os.path.join(os.path.dirname(__file__), "delegates.json")

def load_delegates():
    with open(DELEGATES_FILE) as f:
        return json.load(f)

def save_delegates(delegates):
    with open(DELEGATES_FILE, "w") as f:
        json.dump(delegates, f, indent=2)

def find_delegate(delegates, uid):
    return next((d for d in delegates if d["unique_id"] == uid), None)

# ---------------------------------------------------------------------------
# Dummy credentials (all requests must include these headers)
# ---------------------------------------------------------------------------
VALID_CREDENTIALS = {
    "X-API-Username": "admin_desk_1",
    "Authorization":  "Bearer tok_test_khsc_mock_2026",
    "X-Pass-Key":     "pk_test_khsc_mock_2026",
    "X-Secret-Key":   "sk_test_khsc_mock_2026",
}

def check_auth():
    for header, expected in VALID_CREDENTIALS.items():
        if request.headers.get(header) != expected:
            return False
    return True

def auth_error():
    return jsonify({
        "status": "error",
        "message": f"Unauthorized. Ensure all 4 auth headers are present and correct. "
                   f"See khsc_mock/README_MOCK.md for dummy credentials."
    }), 401

# ---------------------------------------------------------------------------
# Main route
# ---------------------------------------------------------------------------
@app.route("/api/index.php", methods=["GET", "POST"])
def api():
    if not check_auth():
        return auth_error()

    endpoint = request.args.get("endpoint", "")

    if endpoint == "verify_delegate":
        return verify_delegate()
    elif endpoint == "check_in":
        return check_in()
    elif endpoint == "search_delegate":
        return search_delegate()
    elif endpoint == "offline_sync":
        return offline_sync()
    elif endpoint == "mark_paid_onsite":
        return mark_paid_onsite()
    elif endpoint == "event_stats":
        return event_stats()
    elif endpoint == "sandbox_test":
        return sandbox_test()
    else:
        return jsonify({
            "status": "error",
            "message": f"Unknown endpoint: '{endpoint}'"
        }), 404

# ---------------------------------------------------------------------------
# Endpoint handlers
# ---------------------------------------------------------------------------

def verify_delegate():
    """GET ?endpoint=verify_delegate&uid=CONF-XXXX"""
    uid = request.args.get("uid", "").strip()
    if not uid:
        return jsonify({"status": "error", "message": "Missing 'uid' parameter."}), 400

    delegates = load_delegates()
    delegate = find_delegate(delegates, uid)

    if not delegate:
        return jsonify({"status": "error", "message": f"Delegate '{uid}' not found."}), 404

    return jsonify({
        "status": "success",
        "message": "Delegate retrieved successfully.",
        "data": {
            "delegate_id":    delegate["unique_id"],
            "name":           f"{delegate['first_name']} {delegate['last_name']}",
            "email":          delegate.get("email"),
            "organization":   delegate["organization"],
            "category":       delegate.get("category"),
            "payment_status": delegate["payment_status"],
            "amount_paid":    delegate.get("amount_paid", 0),
            "payment_method": delegate.get("payment_method"),
            "is_checked_in":  delegate["is_checked_in"],
            "can_enter":      delegate["payment_status"] == "Paid" and not delegate["is_checked_in"],
        }
    })


def check_in():
    """POST ?endpoint=check_in  body: {"uid": "CONF-XXXX"}"""
    body = request.get_json(silent=True) or {}
    uid  = body.get("uid", "").strip()

    if not uid:
        return jsonify({"status": "error", "message": "Missing 'uid' in request body."}), 400

    delegates = load_delegates()
    delegate  = find_delegate(delegates, uid)

    if not delegate:
        return jsonify({"status": "error", "message": f"Delegate '{uid}' not found."}), 404

    if delegate["payment_status"] != "Paid":
        return jsonify({
            "status":  "error",
            "message": "Check-in denied. Delegate has not completed payment."
        }), 403

    if delegate["is_checked_in"]:
        return jsonify({
            "status":  "error",
            "message": "Delegate is already checked in."
        }), 409

    delegate["is_checked_in"] = True
    save_delegates(delegates)

    return jsonify({
        "status":  "success",
        "message": f"{delegate['first_name']} {delegate['last_name']} checked in successfully.",
        "data": {
            "delegate_id":  delegate["unique_id"],
            "name":         f"{delegate['first_name']} {delegate['last_name']}",
            "checked_in_at": datetime.utcnow().isoformat() + "Z",
        }
    })


def search_delegate():
    """GET ?endpoint=search_delegate&q=SEARCH_TERM"""
    q = request.args.get("q", "").strip().lower()
    if not q:
        return jsonify({"status": "error", "message": "Missing 'q' search parameter."}), 400

    delegates = load_delegates()
    results = [
        d for d in delegates
        if q in d["first_name"].lower()
        or q in d["last_name"].lower()
        or q in d["email"].lower()
        or q in d["unique_id"].lower()
        or q in d["organization"].lower()
    ]

    return jsonify({
        "status":  "success",
        "message": f"{len(results)} delegate(s) found.",
        "data":    [
            {
                "unique_id":      d["unique_id"],
                "first_name":     d["first_name"],
                "last_name":      d["last_name"],
                "email":          d["email"],
                "organization":   d["organization"],
                "payment_status": d["payment_status"],
                "is_checked_in":  d["is_checked_in"],
            }
            for d in results
        ]
    })


def offline_sync():
    """POST ?endpoint=offline_sync  body: {"uids": ["CONF-XXX", ...]}"""
    body = request.get_json(silent=True) or {}
    uids = body.get("uids", [])

    if not uids or not isinstance(uids, list):
        return jsonify({"status": "error", "message": "Missing or invalid 'uids' array."}), 400

    delegates = load_delegates()
    successful = 0
    failed = []

    for uid in uids:
        delegate = find_delegate(delegates, uid)
        if not delegate:
            failed.append({"uid": uid, "reason": "Not found"})
        elif delegate["payment_status"] != "Paid":
            failed.append({"uid": uid, "reason": "Unpaid"})
        elif delegate["is_checked_in"]:
            failed.append({"uid": uid, "reason": "Already checked in"})
        else:
            delegate["is_checked_in"] = True
            successful += 1

    save_delegates(delegates)

    return jsonify({
        "status":  "success",
        "message": f"Offline Sync Complete: {successful} synced.",
        "data": {
            "successful": successful,
            "failed":     failed,
        }
    })


def mark_paid_onsite():
    """POST ?endpoint=mark_paid_onsite  body: {"uid": "CONF-XXXX", "payment_method": "On-Site Cash"}"""
    body           = request.get_json(silent=True) or {}
    uid            = body.get("uid", "").strip()
    payment_method = body.get("payment_method", "On-Site Cash")

    if not uid:
        return jsonify({"status": "error", "message": "Missing 'uid' in request body."}), 400

    delegates = load_delegates()
    delegate  = find_delegate(delegates, uid)

    if not delegate:
        return jsonify({"status": "error", "message": f"Delegate '{uid}' not found."}), 404

    if delegate["payment_status"] == "Paid":
        return jsonify({
            "status":  "error",
            "message": "Delegate has already paid. No action taken."
        }), 409

    delegate["payment_status"] = "Paid"
    delegate["payment_method"] = payment_method
    delegate["amount_paid"]    = 10000  # default on-site amount
    save_delegates(delegates)

    return jsonify({
        "status":  "success",
        "message": "Payment settled. Receipt emailed to delegate.",
        "data": {
            "delegate_id":    delegate["unique_id"],
            "name":           f"{delegate['first_name']} {delegate['last_name']}",
            "payment_status": "Paid",
            "payment_method": payment_method,
            "amount_paid":    delegate["amount_paid"],
            "receipt_sent_to": delegate["email"],
        }
    })


def event_stats():
    """GET ?endpoint=event_stats"""
    delegates      = load_delegates()
    total_reg      = len(delegates)
    total_paid     = sum(1 for d in delegates if d["payment_status"] == "Paid")
    total_checkin  = sum(1 for d in delegates if d["is_checked_in"])
    total_revenue  = sum(d.get("amount_paid", 0) for d in delegates)

    return jsonify({
        "status":  "success",
        "message": "Live Event Stats retrieved.",
        "data": {
            "total_registered": total_reg,
            "total_paid":       total_paid,
            "total_checked_in": total_checkin,
            "total_unpaid":     total_reg - total_paid,
            "total_revenue":    float(total_revenue),
        }
    })


def sandbox_test():
    """POST ?endpoint=sandbox_test"""
    return jsonify({
        "status":  "success",
        "message": "Sandbox test successful. Mock live keys generated below (not real).",
        "data": {
            "tok_live": "tok_live_MOCK_DO_NOT_USE_IN_PRODUCTION",
            "pk_live":  "pk_live_MOCK_DO_NOT_USE_IN_PRODUCTION",
            "sk_live":  "sk_live_MOCK_DO_NOT_USE_IN_PRODUCTION",
            "note":     "These are mock keys. Contact the KHSC admin for real production keys.",
        }
    })


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("\n  KHSC Mock Server")
    print("  Running at: http://localhost:9090/api/index.php")
    print("  Delegates file: khsc_mock/delegates.json")
    print("  Press Ctrl+C to stop\n")
    app.run(host="0.0.0.0", port=9090, debug=True)
