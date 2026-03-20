from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any
from uuid import uuid4

from flask import Flask, jsonify, redirect, render_template, request, url_for

app = Flask(__name__)


@dataclass
class User:
    id: str
    name: str
    location: str
    platform: str
    created_at: str


USERS: dict[str, User] = {}
POLICIES: dict[str, dict[str, Any]] = {}
CLAIMS: list[dict[str, Any]] = []
WEEKLY_EVENT_CLAIM_KEYS: set[tuple[str, str, int, int]] = set()

MOCK_LOCATION_DATA = {
    "Mumbai": {"rainfall_mm": 78, "temperature_c": 31, "aqi": 185, "curfew": False},
    "Delhi": {"rainfall_mm": 18, "temperature_c": 42, "aqi": 342, "curfew": False},
    "Bengaluru": {"rainfall_mm": 42, "temperature_c": 29, "aqi": 112, "curfew": False},
    "Chennai": {"rainfall_mm": 54, "temperature_c": 39, "aqi": 168, "curfew": False},
    "Kolkata": {"rainfall_mm": 65, "temperature_c": 35, "aqi": 210, "curfew": False},
    "Hyderabad": {"rainfall_mm": 30, "temperature_c": 37, "aqi": 176, "curfew": False},
    "Pune": {"rainfall_mm": 24, "temperature_c": 33, "aqi": 140, "curfew": False},
}


def now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def get_location_snapshot(location: str) -> dict[str, Any]:
    return MOCK_LOCATION_DATA.get(location, {"rainfall_mm": 28, "temperature_c": 34, "aqi": 160, "curfew": False})


def evaluate_risk(location: str) -> dict[str, Any]:
    snapshot = get_location_snapshot(location)
    score = 0

    if snapshot["rainfall_mm"] > 50:
        score += 35
    if snapshot["temperature_c"] > 40:
        score += 30
    if snapshot["aqi"] > 300:
        score += 25
    elif snapshot["aqi"] > 180:
        score += 15
    if snapshot["curfew"]:
        score += 20

    if score >= 60:
        level = "High"
    elif score >= 30:
        level = "Medium"
    else:
        level = "Low"

    return {
        "risk_score": score,
        "risk_level": level,
        "snapshot": snapshot,
    }


def calculate_weekly_premium(risk_level: str) -> dict[str, int]:
    model = {
        "Low": {"weekly_premium_inr": 99, "coverage_inr": 3000},
        "Medium": {"weekly_premium_inr": 149, "coverage_inr": 5000},
        "High": {"weekly_premium_inr": 219, "coverage_inr": 7000},
    }
    return model.get(risk_level, model["Medium"])


def should_trigger(snapshot: dict[str, Any]) -> tuple[bool, list[str]]:
    reasons = []
    if snapshot["rainfall_mm"] > 50:
        reasons.append("Rainfall > 50mm")
    if snapshot["temperature_c"] > 40:
        reasons.append("Temperature > 40C")
    if snapshot["aqi"] > 300:
        reasons.append("AQI > 300")
    if snapshot["curfew"]:
        reasons.append("Government curfew")
    return len(reasons) > 0, reasons


def fraud_check(user: User, event_type: str, user_gps: str | None) -> dict[str, Any]:
    week_year = datetime.utcnow().isocalendar()
    claim_key = (user.id, event_type, week_year.year, week_year.week)

    flags = []
    if claim_key in WEEKLY_EVENT_CLAIM_KEYS:
        flags.append("Duplicate weekly claim for same trigger")

    if user_gps and user_gps.strip().lower() != user.location.strip().lower():
        flags.append("GPS mismatch with registered location")

    recent_claims = [c for c in CLAIMS if c["user_id"] == user.id and c["week"] == week_year.week and c["year"] == week_year.year]
    if len(recent_claims) >= 2:
        flags.append("High claim frequency in same week")

    return {
        "fraud_flag": len(flags) > 0,
        "reasons": flags,
        "claim_key": claim_key,
    }


def auto_process_claim(user: User, event_type: str, reasons: list[str], user_gps: str | None = None) -> dict[str, Any]:
    policy = POLICIES.get(user.id)
    if not policy or not policy.get("active"):
        return {
            "status": "rejected",
            "message": "No active policy",
        }

    fraud = fraud_check(user, event_type, user_gps)
    week_year = datetime.utcnow().isocalendar()
    approved = not fraud["fraud_flag"]

    claim = {
        "claim_id": str(uuid4()),
        "user_id": user.id,
        "user_name": user.name,
        "location": user.location,
        "platform": user.platform,
        "event_type": event_type,
        "trigger_reasons": reasons,
        "status": "approved" if approved else "flagged",
        "payout_inr": policy["coverage_inr"] if approved else 0,
        "fraud_flag": fraud["fraud_flag"],
        "fraud_reasons": fraud["reasons"],
        "week": week_year.week,
        "year": week_year.year,
        "created_at": now_iso(),
    }
    CLAIMS.append(claim)

    if approved:
        WEEKLY_EVENT_CLAIM_KEYS.add(fraud["claim_key"])

    return {
        "status": claim["status"],
        "claim": claim,
        "message": "Claim auto-approved and payout released." if approved else "Claim flagged for fraud review.",
    }


def get_user_summary(user_id: str) -> dict[str, Any] | None:
    user = USERS.get(user_id)
    if not user:
        return None

    policy = POLICIES.get(user_id)
    user_claims = [c for c in CLAIMS if c["user_id"] == user_id]
    protected_income = sum(c["payout_inr"] for c in user_claims if c["status"] == "approved")

    risk_data = evaluate_risk(user.location)
    premium_data = calculate_weekly_premium(risk_data["risk_level"])

    return {
        "user": asdict(user),
        "risk": risk_data,
        "pricing": premium_data,
        "policy": policy,
        "claims": user_claims,
        "earnings_protected": protected_income,
    }


@app.get("/")
def landing_page():
    return render_template("landing.html")


@app.get("/auth")
def auth_page():
    return render_template("auth.html")


@app.get("/dashboard")
def dashboard_page():
    user_id = request.args.get("user_id", "")
    summary = get_user_summary(user_id) if user_id else None
    return render_template("dashboard.html", summary=summary, user_id=user_id)


@app.get("/plans")
def plans_page():
    user_id = request.args.get("user_id", "")
    summary = get_user_summary(user_id) if user_id else None
    return render_template("plans.html", summary=summary, user_id=user_id)


@app.get("/claims")
def claims_page():
    user_id = request.args.get("user_id", "")
    summary = get_user_summary(user_id) if user_id else None
    return render_template("claims.html", summary=summary, user_id=user_id)


@app.get("/admin")
def admin_page():
    risk_buckets = defaultdict(int)
    for user in USERS.values():
        risk_buckets[evaluate_risk(user.location)["risk_level"]] += 1

    payouts = sum(c["payout_inr"] for c in CLAIMS if c["status"] == "approved")

    data = {
        "users": [asdict(u) for u in USERS.values()],
        "claims": CLAIMS,
        "risk_distribution": dict(risk_buckets),
        "summary": {
            "total_users": len(USERS),
            "total_claims": len(CLAIMS),
            "approved_claims": sum(1 for c in CLAIMS if c["status"] == "approved"),
            "flagged_claims": sum(1 for c in CLAIMS if c["status"] == "flagged"),
            "total_payouts_inr": payouts,
        },
    }
    return render_template("admin.html", data=data)


@app.post("/register")
def register_user():
    data = request.get_json(silent=True) or request.form
    name = data.get("name", "").strip()
    location = data.get("location", "").strip()
    platform = data.get("platform", "").strip()

    if not name or not location or not platform:
        return jsonify({"error": "name, location, and platform are required"}), 400

    user_id = str(uuid4())
    user = User(
        id=user_id,
        name=name,
        location=location,
        platform=platform,
        created_at=now_iso(),
    )
    USERS[user_id] = user

    return jsonify({
        "message": "User registered successfully",
        "user": asdict(user),
        "next": {
            "calculate_risk": f"/calculate-risk?user_id={user_id}",
            "dashboard": f"/dashboard?user_id={user_id}",
        },
    })


@app.get("/calculate-risk")
def calculate_risk_route():
    user_id = request.args.get("user_id", "").strip()
    user = USERS.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    risk_data = evaluate_risk(user.location)
    premium = calculate_weekly_premium(risk_data["risk_level"])

    return jsonify({
        "user_id": user.id,
        "location": user.location,
        "risk": risk_data,
        "weekly_pricing": premium,
    })


@app.post("/buy-plan")
def buy_plan():
    data = request.get_json(silent=True) or request.form
    user_id = data.get("user_id", "").strip()
    user = USERS.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    risk_data = evaluate_risk(user.location)
    pricing = calculate_weekly_premium(risk_data["risk_level"])

    policy = {
        "policy_id": str(uuid4()),
        "active": True,
        "risk_level": risk_data["risk_level"],
        "weekly_premium_inr": pricing["weekly_premium_inr"],
        "coverage_inr": pricing["coverage_inr"],
        "started_at": now_iso(),
    }
    POLICIES[user_id] = policy

    return jsonify({
        "message": "Weekly income protection activated",
        "policy": policy,
    })


@app.post("/trigger-event")
def trigger_event():
    data = request.get_json(silent=True) or request.form
    user_id = data.get("user_id", "").strip()
    event_type = data.get("event_type", "rain")
    user_gps = data.get("gps_location", None)

    user = USERS.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    snapshot = get_location_snapshot(user.location)

    if event_type == "rain":
        snapshot["rainfall_mm"] = 75
    elif event_type == "heat":
        snapshot["temperature_c"] = 43
    elif event_type == "pollution":
        snapshot["aqi"] = 350
    elif event_type == "curfew":
        snapshot["curfew"] = True

    trigger_hit, reasons = should_trigger(snapshot)
    if not trigger_hit:
        return jsonify({"message": "No parametric trigger met", "snapshot": snapshot})

    result = auto_process_claim(user, event_type, reasons, user_gps=user_gps)
    return jsonify({
        "message": "Trigger detected",
        "snapshot": snapshot,
        "trigger_reasons": reasons,
        "claim_result": result,
    })


@app.get("/claim")
def claim_status():
    user_id = request.args.get("user_id", "").strip()
    user = USERS.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    user_claims = [c for c in CLAIMS if c["user_id"] == user_id]
    return jsonify({
        "user_id": user_id,
        "claims": user_claims,
        "latest_claim": user_claims[-1] if user_claims else None,
    })


@app.get("/api/admin")
def admin_api():
    risk_levels = [evaluate_risk(u.location)["risk_level"] for u in USERS.values()]
    return jsonify({
        "users": [asdict(u) for u in USERS.values()],
        "claims": CLAIMS,
        "risk_distribution": dict(Counter(risk_levels)),
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
