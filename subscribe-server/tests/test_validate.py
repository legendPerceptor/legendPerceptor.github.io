import unittest

from app.validate import clean_text, hash_ip, normalize_email
from app.ratelimit import RateLimiter


class NormalizeEmailTests(unittest.TestCase):
    def test_accepts_common_addresses(self):
        cases = {
            "someone@example.com": "someone@example.com",
            "  Someone@Example.COM  ": "someone@example.com",
            "<someone@example.com>": "someone@example.com",
            "first.last+tag@sub.example.co.uk": "first.last+tag@sub.example.co.uk",
            "a_b-c@my-domain.io": "a_b-c@my-domain.io",
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(normalize_email(raw), expected)

    def test_rejects_bad_addresses(self):
        cases = [
            None,
            42,
            "",
            "   ",
            "no-at-sign",
            "@example.com",
            "someone@",
            "someone@example",
            "someone@@example.com",
            "some..one@example.com",
            ".someone@example.com",
            "someone.@example.com",
            "someone@-example.com",
            "someone@example-.com",
            "someone@exa..mple.com",
            "someone@example.com trailing",
            "someone@exa mple.com",
            "a" * 65 + "@example.com",
            "someone@" + "a" * 250 + ".com",
        ]
        for raw in cases:
            with self.subTest(raw=raw):
                self.assertIsNone(normalize_email(raw))

    def test_clean_text(self):
        self.assertIsNone(clean_text(""))
        self.assertIsNone(clean_text("   "))
        self.assertIsNone(clean_text(None))
        self.assertEqual(clean_text("  /posts/hello-world\n"), "/posts/hello-world")
        self.assertEqual(len(clean_text("x" * 500, max_length=10)), 10)

    def test_hash_ip_is_salted_and_stable(self):
        first = hash_ip("203.0.113.7", "salt-a")
        self.assertEqual(first, hash_ip("203.0.113.7", "salt-a"))
        self.assertNotEqual(first, hash_ip("203.0.113.7", "salt-b"))
        self.assertNotEqual(first, hash_ip("203.0.113.8", "salt-a"))
        self.assertEqual(len(first), 32)
        self.assertNotIn("203.0.113.7", first)
        self.assertIsNone(hash_ip(None, "salt-a"))


class RateLimiterTests(unittest.TestCase):
    def test_allows_up_to_limit_then_blocks(self):
        now = [0.0]
        limiter = RateLimiter(3, 60, clock=lambda: now[0])

        for _ in range(3):
            allowed, retry_after = limiter.check("1.2.3.4")
            self.assertTrue(allowed)
            self.assertEqual(retry_after, 0)

        allowed, retry_after = limiter.check("1.2.3.4")
        self.assertFalse(allowed)
        self.assertGreaterEqual(retry_after, 1)

        # another key is unaffected
        self.assertTrue(limiter.check("5.6.7.8")[0])

        # window slides
        now[0] = 61.0
        self.assertTrue(limiter.check("1.2.3.4")[0])

    def test_evicts_stale_keys(self):
        now = [0.0]
        limiter = RateLimiter(1, 10, max_keys=5, clock=lambda: now[0])
        for index in range(10):
            limiter.check(f"key-{index}")
        now[0] = 100.0
        limiter.check("fresh")
        self.assertLessEqual(len(limiter._hits), 6)


if __name__ == "__main__":
    unittest.main()
