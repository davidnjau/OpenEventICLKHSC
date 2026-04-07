#!/usr/bin/env python3
"""
generate_qr.py — Generate QR code images for test KHSC delegates.

QR format used by Android/iOS app: {order_identifier}-{attendee_id}

Usage:
    python3 tools/generate_qr.py                  # all attendees in the event
    python3 tools/generate_qr.py --event-id 2     # specific event
    python3 tools/generate_qr.py --output ./qrcodes

Requirements:
    pip install requests qrcode[pil] python-dotenv
"""

import argparse
import os
import sys

try:
    import qrcode
    import requests
    from dotenv import load_dotenv
except ImportError:
    sys.exit("Install dependencies first:\n  pip install requests qrcode[pil] python-dotenv")

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

BASE_URL = f"http://localhost:8080"
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', '')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', '')


def get_token() -> str:
    resp = requests.post(f"{BASE_URL}/auth/session",
                         json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
                         timeout=10)
    resp.raise_for_status()
    return resp.json()['access_token']


def get_events(token: str) -> list:
    resp = requests.get(f"{BASE_URL}/v1/events?page[size]=50",
                        headers={"Authorization": f"JWT {token}"}, timeout=10)
    resp.raise_for_status()
    return resp.json().get('data', [])


def get_attendees(token: str, event_id: str) -> list:
    resp = requests.get(f"{BASE_URL}/v1/events/{event_id}/attendees?page[size]=200",
                        headers={"Authorization": f"JWT {token}"}, timeout=10)
    resp.raise_for_status()
    return resp.json().get('data', [])


def get_order_identifier(token: str, attendee_id: str) -> str:
    resp = requests.get(f"{BASE_URL}/v1/attendees/{attendee_id}/order",
                        headers={"Authorization": f"JWT {token}"}, timeout=10)
    if resp.status_code == 200:
        attrs = resp.json().get('data', {}).get('attributes', {})
        return attrs.get('identifier', attendee_id)
    return attendee_id  # fallback: use attendee id as order part


def generate_qr(content: str, output_path: str) -> None:
    img = qrcode.make(content)
    img.save(output_path)


def main():
    parser = argparse.ArgumentParser(description='Generate QR codes for event attendees')
    parser.add_argument('--event-id', type=str, help='Open Event event ID (default: first event)')
    parser.add_argument('--output', type=str, default='./qrcodes', help='Output directory')
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    print("Authenticating...")
    token = get_token()

    if args.event_id:
        event_id = args.event_id
    else:
        events = get_events(token)
        if not events:
            sys.exit("No events found.")
        event_id = events[0]['id']
        print(f"Using event ID {event_id}: {events[0]['attributes'].get('name', '')}")

    print(f"Fetching attendees for event {event_id}...")
    attendees = get_attendees(token, event_id)
    print(f"Found {len(attendees)} attendees")

    for attendee in attendees:
        attendee_id = attendee['id']
        attrs = attendee.get('attributes', {})
        firstname = attrs.get('firstname', '')
        lastname = attrs.get('lastname', '')
        name = f"{firstname}_{lastname}".replace(' ', '_')

        order_id = get_order_identifier(token, attendee_id)
        qr_content = f"{order_id}-{attendee_id}"

        filename = f"{args.output}/{attendee_id}_{name}.png"
        generate_qr(qr_content, filename)
        print(f"  ✓ {qr_content}  →  {filename}")

    print(f"\nGenerated {len(attendees)} QR codes in {args.output}/")


if __name__ == '__main__':
    main()
