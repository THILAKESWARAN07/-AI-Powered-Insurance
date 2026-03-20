# ShieldGig: AI-Powered Parametric Insurance for Gig Workers (India)

Phase 1 hackathon prototype for an AI-powered parametric insurance platform that protects gig delivery workers from **income loss only** due to external disruptions.

## Problem Statement

Gig workers can lose weekly income because of weather shocks, pollution spikes, and city restrictions. Traditional claims are slow and manual.

This prototype solves it with:

- Weekly pricing model
- AI risk scoring by location and disruption factors
- Parametric auto-triggers (no manual filing)
- Instant automatic claim processing
- Basic fraud detection

## Website Structure (Pages)

1. **Landing Page** (`/`)
- Purpose: Explain value proposition and how parametric insurance works.
- Content: Product pitch, key features, CTA buttons for registration and admin analytics.

2. **User Registration/Login Page** (`/auth`)
- Purpose: Onboard worker profile.
- Content: Name, location, platform selection (Swiggy/Zomato/etc.), register action.

3. **Dashboard Page** (`/dashboard?user_id=...`)
- Purpose: Main worker control center.
- Content: Active policy, weekly premium, risk card, claims history, total earnings protected, trigger buttons.

4. **Insurance Plan Page** (`/plans?user_id=...`)
- Purpose: Show weekly plan details and purchase action.
- Content: AI risk level, weekly premium, coverage amount, policy activation button.

5. **Claim Status Page** (`/claims?user_id=...`)
- Purpose: Show automatic claim outcomes.
- Content: Latest claim, status, payout, fraud flag, trigger simulation and refresh.

6. **Admin/Analytics Page** (`/admin`)
- Purpose: Portfolio-level monitoring.
- Content: All users, all claims, risk distribution, approved vs flagged claims, total payouts.

## Core Features Implemented

### A. User Onboarding
- Endpoint: `POST /register`
- Inputs: `name`, `location`, `platform`
- Stores user in in-memory data store.

### B. AI Risk Assessment
- Endpoint: `GET /calculate-risk?user_id=...`
- Uses mock location data: rainfall, temperature, AQI, curfew.
- Returns risk score and risk level (`Low`, `Medium`, `High`).

### C. Weekly Premium Calculation
- Based on risk level:
	- Low: INR 99 premium, INR 3000 coverage
	- Medium: INR 149 premium, INR 5000 coverage
	- High: INR 219 premium, INR 7000 coverage
- Displayed in dashboard and plan page.

### D. Parametric Trigger System
- Endpoint: `POST /trigger-event`
- Trigger simulation via dashboard buttons (`rain`, `heat`, `pollution`, `curfew`).
- Trigger rules:
	- Rainfall > 50mm
	- Temperature > 40C
	- AQI > 300
	- Curfew event true

### E. Automatic Claim Processing
- No manual claim form.
- When trigger is met and policy is active:
	- Claim generated automatically
	- Auto-approved unless fraud check flags it
	- Payout shown instantly

### F. Fraud Detection
- Duplicate claim prevention (same user + trigger + week).
- Mock GPS location validation (`gps_location` vs registered city).
- Flags suspicious high-frequency claim behavior.

### G. Worker Dashboard
- Shows:
	- Active policy status
	- Weekly premium
	- Claims history
	- Earnings protected (sum of approved payouts)

### H. Admin Panel
- Shows:
	- All users
	- All claims
	- Risk distribution
	- Approved/flagged claim counts

## Functional Flow (Step-by-Step)

1. User registers from `/auth`.
2. System calculates location risk through `/calculate-risk`.
3. Weekly premium and coverage are generated from risk level.
4. User buys plan (`POST /buy-plan`).
5. System monitors/simulates triggers via `/trigger-event`.
6. Disruption trigger occurs (rain/heat/pollution/curfew).
7. Claim is auto-generated.
8. Fraud checks run (duplicate/GPS/frequency).
9. Approved payout is displayed instantly (or flagged claim shown).

## Backend API Summary

- `POST /register`
- `GET /calculate-risk?user_id=...`
- `POST /trigger-event`
- `GET /claim?user_id=...`
- `POST /buy-plan`
- `GET /api/admin`

## UI Design Notes

- Clean dashboard layout with analytics cards.
- Cards include risk, premium, claims, and earnings-protected metrics.
- Action buttons:
	- `Simulate Rain`
	- `Simulate Heat`
	- `Simulate AQI Spike`
	- `View Claim`
- Mobile-responsive layout and lightweight animations.

## Tech Stack

- Backend: Python, Flask
- Frontend: HTML (Jinja templates), CSS, JavaScript
- Storage: In-memory dictionaries/lists (prototype)

## Run Locally

1. Create and activate virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Start app:

```powershell
python app.py
```

4. Open browser:
- `http://127.0.0.1:5000/`

## Hackathon Scope Constraints Met

- Income-loss coverage only
- Weekly pricing model
- Parametric automatic triggers
- Simple but functional end-to-end prototype

## Next Phase Ideas

- Replace mock weather with real APIs (IMD/OpenWeather/Air quality feeds)
- Persist users/policies/claims in PostgreSQL
- Add UPI payout integration
- Add model-based anomaly detection for fraud scoring