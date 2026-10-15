import csv
import io
import tempfile
import unittest
from pathlib import Path

from app.store import STATUS_ACTIVE, STATUS_UNSUBSCRIBED, SubscriberStore

from datetime import datetime, timedelta, timezone


class SubscriberStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "data" / "subscribers.db"
        self.store = SubscriberStore(self.db)

    def tearDown(self):
        self.tmp.cleanup()

    def test_creates_db_file_and_parent_directory(self):
        self.assertTrue(self.db.exists())
        self.assertEqual(self.store.count(), 0)

    def test_add_is_idempotent_and_normalises(self):
        subscriber, created = self.store.add("  Someone@Example.com ", source="/")
        self.assertTrue(created)
        self.assertEqual(subscriber.email, "someone@example.com")
        self.assertEqual(subscriber.status, STATUS_ACTIVE)
        self.assertTrue(subscriber.token)
        self.assertEqual(subscriber.source, "/")

        again, created_again = self.store.add("someone@example.com", source="/other")
        self.assertFalse(created_again)
        self.assertEqual(again.id, subscriber.id)
        self.assertEqual(self.store.count(), 1)

    def test_add_rejects_invalid_email(self):
        subscriber, created = self.store.add("not-an-email")
        self.assertIsNone(subscriber)
        self.assertFalse(created)
        self.assertEqual(self.store.count(), 0)

    def test_resubscribing_reactivates_but_keeps_the_token(self):
        subscriber, _ = self.store.add("someone@example.com")
        self.store.unsubscribe("someone@example.com")
        self.assertEqual(self.store.get("someone@example.com").status, STATUS_UNSUBSCRIBED)

        reactivated, created = self.store.add("someone@example.com")
        self.assertFalse(created)
        self.assertEqual(reactivated.id, subscriber.id)
        self.assertEqual(reactivated.token, subscriber.token)
        self.assertEqual(reactivated.status, STATUS_ACTIVE)
        self.assertIsNone(reactivated.unsubscribed_at)

    def test_unsubscribe_by_token(self):
        subscriber, _ = self.store.add("someone@example.com")
        updated = self.store.unsubscribe_by_token(subscriber.token)
        self.assertIsNotNone(updated)
        self.assertEqual(updated.status, STATUS_UNSUBSCRIBED)
        self.assertIsNotNone(updated.unsubscribed_at)

        self.assertIsNone(self.store.unsubscribe_by_token("nope"))
        self.assertIsNone(self.store.unsubscribe_by_token(""))

    def test_delete(self):
        self.store.add("someone@example.com")
        self.assertTrue(self.store.delete("SOMEONE@example.com"))
        self.assertFalse(self.store.delete("someone@example.com"))
        self.assertEqual(self.store.count(), 0)

    def test_list_filters_and_paginates(self):
        for index in range(5):
            self.store.add(f"user{index}@example.com", source="/")
        self.store.add("gone@example.com", source="/posts/x")
        self.store.unsubscribe("gone@example.com")

        self.assertEqual(self.store.count(), 6)
        self.assertEqual(self.store.count(STATUS_ACTIVE), 5)
        self.assertEqual(self.store.count(STATUS_UNSUBSCRIBED), 1)

        page = self.store.list(status=STATUS_ACTIVE, limit=2, offset=0)
        self.assertEqual(len(page), 2)
        self.assertEqual([item.email for item in page], ["user4@example.com", "user3@example.com"])

    def test_stats_reports_recent_signups_and_sources(self):
        self.store.add("a@example.com", source="/")
        self.store.add("b@example.com", source="/")
        self.store.add("c@example.com", source="/posts/hello")

        stats = self.store.stats()
        self.assertEqual(stats["total"], 3)
        self.assertEqual(stats["active"], 3)
        self.assertEqual(stats["last_7_days"], 3)
        self.assertEqual(
            stats["sources"],
            [{"source": "/", "count": 2}, {"source": "/posts/hello", "count": 1}],
        )

    def test_count_since_honours_timestamps(self):
        self.store.add("old@example.com")
        with self.store._connect() as conn:
            old = (datetime.now(timezone.utc) - timedelta(days=40)).isoformat(timespec="seconds")
            conn.execute("UPDATE subscribers SET created_at = ?", (old,))

        self.assertEqual(self.store.count_since(7), 0)
        self.assertEqual(self.store.count_since(30), 0)
        self.assertEqual(self.store.count_since(90), 1)

    def test_export_csv(self):
        self.store.add("someone@example.com", source="/")
        self.store.add("other@example.com", source="/posts/x")
        self.store.unsubscribe("other@example.com")

        text = self.store.export_csv()
        rows = list(csv.DictReader(io.StringIO(text)))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["email"], "someone@example.com")
        self.assertEqual(rows[0]["status"], STATUS_ACTIVE)
        self.assertEqual(rows[0]["source"], "/")
        self.assertTrue(rows[0]["unsubscribe_url_token"])

        active_only = list(csv.DictReader(io.StringIO(self.store.export_csv(status=STATUS_ACTIVE))))
        self.assertEqual([row["email"] for row in active_only], ["someone@example.com"])

    def test_reopening_the_same_file_keeps_data(self):
        self.store.add("someone@example.com")
        reopened = SubscriberStore(self.db)
        self.assertEqual(reopened.count(), 1)
        self.assertEqual(reopened.get("someone@example.com").email, "someone@example.com")


if __name__ == "__main__":
    unittest.main()
