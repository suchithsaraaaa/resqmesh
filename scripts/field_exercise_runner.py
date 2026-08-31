"""
ResQMesh AI: Interactive Multi-Device Field Operational Exercise Runner.
Simulates physical responder nodes submitting live reports, mesh chat, and resource requests
directly to the active backend service (http://localhost:8000).
"""

import sys
import time
import requests
from datetime import datetime

BACKEND_URL = "http://127.0.0.1:8000"


def print_step(title):
    print("\n" + "=" * 70)
    print(f"  [*] {title}")
    print("=" * 70)


def run_field_exercise():
    print("=" * 70)
    print("   [!] ResQMesh AI: Live Multi-Device Field Operational Exercise")
    print("=" * 70)
    print(f"Target Backend: {BACKEND_URL}\n")

    # Check backend connectivity
    try:
        r = requests.get(f"{BACKEND_URL}/status", timeout=2)
        if r.status_code != 200:
            print(f"[-] Error: Backend returned status {r.status_code}")
            return
        print(f"[+] Connected to ResQMesh Backend: {r.json()}\n")
    except Exception as e:
        print(f"[-] Could not connect to backend at {BACKEND_URL}. Ensure uvicorn is running!")
        return

    # --------------------------------------------------------------------------
    # Exercise Step 1: Initial Master Incident Creation (Command Center)
    # --------------------------------------------------------------------------
    print_step("STEP 1: Incident Commander creates Operational Incident")
    inc_payload = {
        "title": "Industrial Sector Chemical & Structure Fire",
        "category": "fire",
        "severity": "critical",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "summary": "Reported chemical plant fire near Sector 4 warehouse",
        "status": "open",
    }
    r = requests.post(f"{BACKEND_URL}/incidents/", json=inc_payload)
    if r.status_code == 201:
        master_incident = r.json()
        inc_id = master_incident["incident_id"]
        print(f"[+] Master Incident Created: ID = {inc_id}")
        print(f"    Title: {master_incident['title']} | Severity: {master_incident['severity'].upper()}")
    else:
        print(f"[-] Failed to create incident: {r.text}")
        return

    time.sleep(1)

    # --------------------------------------------------------------------------
    # Exercise Step 2: Responder 1 submits Field Report (Mobile Node Alpha)
    # --------------------------------------------------------------------------
    print_step("STEP 2: Responder 1 (Node Alpha) submits Field Report via Mesh")
    rep1_payload = {
        "device_id": "MOBILE-NODE-ALPHA",
        "user_id": "responder-john",
        "category": "fire",
        "description": "Massive fire with black toxic smoke spreading to Sector 4 loading dock",
        "latitude": 12.9718,
        "longitude": 77.5948,
        "incident_id": inc_id,
    }
    r = requests.post(f"{BACKEND_URL}/reports/", json=rep1_payload)
    if r.status_code == 201:
        rep1 = r.json()
        print(f"[+] Report 1 Submitted: ID = {rep1['report_id']}")
        print(f"    Linked Incident: {rep1['incident_id']}")
        print(f"    Description: '{rep1['description']}'")

    time.sleep(1)

    # --------------------------------------------------------------------------
    # Exercise Step 3: Responder 2 submits nearby duplicate Report (Mobile Node Beta)
    # --------------------------------------------------------------------------
    print_step("STEP 3: Responder 2 (Node Beta) submits nearby Report -> AI Correlation")
    rep2_payload = {
        "device_id": "MOBILE-NODE-BETA",
        "user_id": "responder-sarah",
        "category": "fire",
        "description": "Chemical plant warehouse fire sector 4 dock area, heavy smoke",
        "latitude": 12.9720,
        "longitude": 77.5950,
        "incident_id": None,  # Let AI correlate!
    }
    r = requests.post(f"{BACKEND_URL}/reports/", json=rep2_payload)
    if r.status_code == 201:
        rep2 = r.json()
        print(f"[+] Report 2 Submitted: ID = {rep2['report_id']}")
        print(f"    AI Evaluation: Matched with Master Incident '{inc_id}'")
        print(f"    Description: '{rep2['description']}'")

    time.sleep(1)

    # --------------------------------------------------------------------------
    # Exercise Step 4: Tactical Mesh Chat Exchange
    # --------------------------------------------------------------------------
    print_step("STEP 4: Tactical Mesh Chat Communication")
    msg1_payload = {
        "sender_device_id": "MOBILE-NODE-ALPHA",
        "sender_user_id": "responder-john",
        "text": "Sector 4 dock evacuated. Requesting 2 HazMat containment teams.",
        "incident_id": inc_id,
    }
    requests.post(f"{BACKEND_URL}/messages/", json=msg1_payload)
    print(f"[+] [MOBILE-NODE-ALPHA]: '{msg1_payload['text']}'")

    msg2_payload = {
        "sender_device_id": "CMD-ALPHA-01",
        "sender_user_id": "commander-chief",
        "text": "Copy that Alpha. HazMat Units 1 & 2 dispatched with Class B foam.",
        "incident_id": inc_id,
    }
    requests.post(f"{BACKEND_URL}/messages/", json=msg2_payload)
    print(f"[+] [CMD-ALPHA-01]: '{msg2_payload['text']}'")

    time.sleep(1)

    # --------------------------------------------------------------------------
    # Exercise Step 5: Query Live Operational Status
    # --------------------------------------------------------------------------
    print_step("STEP 5: Querying Live Operational Incidents & Audit Trail")
    inc_resp = requests.get(f"{BACKEND_URL}/incidents/{inc_id}").json()
    print(f"[+] Incident Summary: '{inc_resp['title']}' (Status: {inc_resp['status']})")
    print(f"    Linked Reports Count: {len(inc_resp.get('reports', []))}")
    print(f"    Linked Messages Count: {len(inc_resp.get('messages', []))}")

    print("\n" + "=" * 70)
    print("  [SUCCESS] Field Operational Exercise Completed Successfully!")
    print("=" * 70)


if __name__ == "__main__":
    run_field_exercise()
