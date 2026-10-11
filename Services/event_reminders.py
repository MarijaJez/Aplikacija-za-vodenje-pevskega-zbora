"""Daily event reminders. Invoked by the production systemd timer."""
import argparse
import json
import logging
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from Data.repository import ChoirRepository
from Services.push_notifications import PushNotificationService

ZONE = ZoneInfo("Europe/Ljubljana")
LOG = logging.getLogger(__name__)


def run_reminders(repository, push, now=None, dry_run=False):
    frozen_now = now
    now = (now or datetime.now(ZONE)).astimezone(ZONE)
    if now.time() < time(8):
        return 0
    if not push.configured:
        if dry_run:
            LOG.info("Push is not configured")
            return 0
        raise RuntimeError("Push is not configured")
    tomorrow = datetime.combine(now.date() + timedelta(days=1), time.min, ZONE)
    with repository.db.cursor() as cur:
        cur.execute("""SELECT id,name,event_date FROM events
            WHERE event_date > %s AND event_date < %s ORDER BY event_date,id""", (now, tomorrow))
        events = cur.fetchall()
    for event in events:
        if not dry_run:
            when = event["event_date"].astimezone(ZONE)
            payload = json.dumps({
                "title": "Opomnik za današnji dogodek",
                "body": f"{event['name']} · danes ob {when:%H:%M}",
                "url": f"/dogodki/{event['id']}",
                "tag": f"event-reminder-{event['id']}-{now.date()}",
                "event_id": event["id"],
            }, ensure_ascii=False)
            push._deliver(payload, category="event", reminder_date=now.date(), now=frozen_now)
    LOG.info("Daily reminders: date=%s eligible_events=%s dry_run=%s", now.date(), len(events), dry_run)
    return len(events)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Inspect eligible events without claims or push delivery")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    repository = ChoirRepository()
    run_reminders(repository, PushNotificationService(repository), dry_run=args.dry_run)


if __name__ == "__main__":
    main()
