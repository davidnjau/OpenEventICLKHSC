"""
KHSC ↔ Open Event sync logic.

Three operations:
    import_delegates(event_id, uids)  — pull KHSC delegates into Open Event as attendees
    sync_checkins(event_id)           — reconcile is_checked_in between both systems
    push_checkin_to_khsc(uid)         — push a check-in recorded in Open Event to KHSC
"""

import logging
from datetime import datetime, timezone

from app.khsc.client import KHSCClient, KHSCError
from app.models import db
from app.models.order import Order
from app.models.ticket import Ticket
from app.models.ticket_holder import TicketHolder

logger = logging.getLogger(__name__)

KHSC_DEVICE_LABEL = 'KHSC-Sync'


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_or_create_khsc_ticket(event_id):
    """
    Return the first available ticket for the event.
    If none exist, create a free 'KHSC Delegate' ticket so imports are never blocked.
    """
    ticket = Ticket.query.filter_by(event_id=event_id, deleted_at=None).first()
    if ticket:
        return ticket

    now = datetime.now(timezone.utc)
    far_future = now.replace(year=now.year + 10)
    ticket = Ticket(
        name='KHSC Delegate',
        event_id=event_id,
        price=0,
        quantity=10000,
        type='free',
        description='Auto-created for KHSC delegate imports.',
        sales_starts_at=now,
        sales_ends_at=far_future,
    )
    db.session.add(ticket)
    db.session.flush()  # get ticket.id without committing
    return ticket


def _create_order_for_delegate(delegate, event_id, ticket):
    """Create one Open Event Order for a single KHSC delegate."""
    is_paid = delegate['payment_status'] == 'Paid'
    order = Order(
        event_id=event_id,
        amount=float(delegate.get('amount_paid') or 0),
        status='completed' if is_paid else 'pending',
        paid_via=delegate.get('payment_method') or ('KHSC' if is_paid else None),
        completed_at=datetime.now(timezone.utc) if is_paid else None,
    )
    db.session.add(order)
    db.session.flush()
    return order


def _checkin_timestamp():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')


# ── Public sync functions ─────────────────────────────────────────────────────

def import_delegates(event_id, uids):
    """
    For each UID in the list, fetch the delegate from KHSC and create or update
    the corresponding TicketHolder (attendee) in Open Event.

    Returns a summary dict:
        {
            'created': int,
            'updated': int,
            'failed':  [{'uid': str, 'reason': str}],
        }
    """
    client = KHSCClient()
    ticket = _get_or_create_khsc_ticket(event_id)

    created = 0
    updated = 0
    failed = []

    for uid in uids:
        try:
            delegate = client.verify_delegate(uid)
        except KHSCError as e:
            failed.append({'uid': uid, 'reason': str(e)})
            continue

        existing = TicketHolder.query.filter_by(khsc_uid=uid, event_id=event_id).first()

        if existing:
            # Update all fields from KHSC
            existing.firstname = delegate['name'].split(' ')[0]
            existing.lastname = ' '.join(delegate['name'].split(' ')[1:])
            existing.email = delegate.get('email') or existing.email
            existing.company = delegate.get('organization') or None
            existing.job_title = delegate.get('category') or None
            existing.gender = delegate.get('gender') or None
            existing.phone = delegate.get('phone') or None
            existing.address = delegate.get('address') or None
            existing.city = delegate.get('city') or None
            existing.state = delegate.get('state') or None
            existing.country = delegate.get('country') or None
            existing.is_checked_in = delegate['is_checked_in']
            if delegate['is_checked_in'] and not existing.checkin_times:
                existing.checkin_times = _checkin_timestamp()
                existing.device_name_checkin = KHSC_DEVICE_LABEL
            if existing.order:
                existing.order.status = 'completed' if delegate['payment_status'] == 'Paid' else existing.order.status
            updated += 1
            logger.info('KHSC import: updated attendee for %s', uid)
        else:
            order = _create_order_for_delegate(delegate, event_id, ticket)
            attendee = TicketHolder(
                firstname=delegate['name'].split(' ')[0],
                lastname=' '.join(delegate['name'].split(' ')[1:]),
                email=delegate.get('email') or None,
                company=delegate.get('organization') or None,
                job_title=delegate.get('category') or None,
                gender=delegate.get('gender') or None,
                phone=delegate.get('phone') or None,
                address=delegate.get('address') or None,
                city=delegate.get('city') or None,
                state=delegate.get('state') or None,
                country=delegate.get('country') or None,
                event_id=event_id,
                ticket_id=ticket.id,
                order_id=order.id,
                khsc_uid=uid,
                is_checked_in=delegate['is_checked_in'],
                checkin_times=_checkin_timestamp() if delegate['is_checked_in'] else None,
                device_name_checkin=KHSC_DEVICE_LABEL if delegate['is_checked_in'] else None,
            )
            db.session.add(attendee)
            created += 1
            logger.info('KHSC import: created attendee for %s', uid)

    db.session.commit()
    return {'created': created, 'updated': updated, 'failed': failed}


def sync_checkins(event_id):
    """
    For every attendee in Open Event that has a khsc_uid, call KHSC verify_delegate
    and reconcile is_checked_in.

    KHSC is treated as the source of truth for check-in state — if KHSC says
    checked in, Open Event is updated to match (not the other way around).

    Returns:
        {
            'synced':  int,   # attendees whose state was updated
            'already_in_sync': int,
            'failed':  [{'uid': str, 'reason': str}],
        }
    """
    client = KHSCClient()
    attendees = TicketHolder.query.filter(
        TicketHolder.event_id == event_id,
        TicketHolder.khsc_uid.isnot(None),
    ).all()

    synced = 0
    in_sync = 0
    failed = []

    for attendee in attendees:
        try:
            delegate = client.verify_delegate(attendee.khsc_uid)
        except KHSCError as e:
            failed.append({'uid': attendee.khsc_uid, 'reason': str(e)})
            continue

        if delegate['is_checked_in'] != attendee.is_checked_in:
            attendee.is_checked_in = delegate['is_checked_in']
            if delegate['is_checked_in']:
                attendee.checkin_times = _checkin_timestamp()
                attendee.device_name_checkin = KHSC_DEVICE_LABEL
            synced += 1
        else:
            in_sync += 1

    db.session.commit()
    return {'synced': synced, 'already_in_sync': in_sync, 'failed': failed}


def push_checkin_to_khsc(uid):
    """
    Called when a check-in is recorded in Open Event (e.g. via the Android app).
    Pushes the check-in to KHSC so both systems stay in sync.

    Returns the KHSC response data dict on success.
    Raises KHSCError on failure (caller decides how to handle).
    """
    client = KHSCClient()
    return client.check_in(uid)
