# SPDX-License-Identifier: LGPL-3.0-only
"""Token-bucket rate limiter tests — pure unit tests, no Odoo env needed."""

import time

from odoo.addons.alfa_core_app_api.models.rate_limiter import RateLimiter, TokenBucket
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "alfacore_sprint11_rate_limit")
class TestTokenBucket(TransactionCase):
    def test_fresh_bucket_allows_burst_up_to_capacity(self):
        bucket = TokenBucket(capacity=5, refill_rate_per_sec=1.0)
        for _ in range(5):
            allowed, _ = bucket.consume()
            self.assertTrue(allowed)
        # Sixth consume in same instant fails
        allowed, retry_after = bucket.consume()
        self.assertFalse(allowed)
        self.assertGreater(retry_after, 0)

    def test_bucket_refills_over_time(self):
        bucket = TokenBucket(capacity=5, refill_rate_per_sec=10.0)  # 10/sec
        # Drain
        for _ in range(5):
            bucket.consume()
        # Wait ~150ms — should accumulate ~1.5 tokens
        time.sleep(0.15)
        allowed, _ = bucket.consume()
        self.assertTrue(allowed)

    def test_bucket_caps_at_capacity(self):
        bucket = TokenBucket(capacity=3, refill_rate_per_sec=100.0)
        # Drain
        for _ in range(3):
            bucket.consume()
        # Wait long enough to overfill if uncapped
        time.sleep(0.5)
        # Should still be at capacity (3), not 50
        for _ in range(3):
            allowed, _ = bucket.consume()
            self.assertTrue(allowed)
        allowed, _ = bucket.consume()
        self.assertFalse(allowed)


@tagged("post_install", "-at_install", "alfacore_sprint11_rate_limit")
class TestRateLimiter(TransactionCase):
    def setUp(self):
        super().setUp()
        self.rl = RateLimiter()

    def test_unknown_profile_fails_open(self):
        """Misconfiguration must not break the API."""
        allowed, _ = self.rl.check("nonexistent", "any_key")
        self.assertTrue(allowed)

    def test_isolated_keys_dont_share_buckets(self):
        """user_a using their budget shouldn't affect user_b."""
        # Drain auth bucket for user_a (capacity 5)
        for _ in range(5):
            self.rl.check("auth", "user_a")
        # user_a should be limited now
        allowed_a, _ = self.rl.check("auth", "user_a")
        self.assertFalse(allowed_a)
        # user_b should still have a full bucket
        allowed_b, _ = self.rl.check("auth", "user_b")
        self.assertTrue(allowed_b)

    def test_isolated_profiles_dont_share_buckets(self):
        """Same key on two different profiles = two buckets."""
        # Drain auth profile
        for _ in range(5):
            self.rl.check("auth", "key1")
        # api_read for the same key should be untouched
        allowed, _ = self.rl.check("api_read", "key1")
        self.assertTrue(allowed)

    def test_reset_clears_buckets(self):
        for _ in range(5):
            self.rl.check("auth", "key1")
        # Should be limited
        allowed, _ = self.rl.check("auth", "key1")
        self.assertFalse(allowed)
        # Reset and try again
        self.rl.reset()
        allowed, _ = self.rl.check("auth", "key1")
        self.assertTrue(allowed)

    def test_reset_with_profile_and_key_targets_one_bucket(self):
        for _ in range(5):
            self.rl.check("auth", "user_a")
        for _ in range(5):
            self.rl.check("auth", "user_b")
        # Both limited
        self.assertFalse(self.rl.check("auth", "user_a")[0])
        self.assertFalse(self.rl.check("auth", "user_b")[0])
        # Reset only user_a
        self.rl.reset(profile="auth", key="user_a")
        self.assertTrue(self.rl.check("auth", "user_a")[0])
        # user_b still limited (minus the one we just spent on user_a check)
        # Drain user_a back down and check user_b is still limited.
        # Actually, simpler test: check user_b directly with cost > 0.
        allowed_b, _ = self.rl.check("auth", "user_b", cost=5)
        self.assertFalse(allowed_b)

    def test_retry_after_is_finite_and_positive_when_denied(self):
        for _ in range(5):
            self.rl.check("auth", "key1")
        allowed, retry_after = self.rl.check("auth", "key1")
        self.assertFalse(allowed)
        self.assertGreater(retry_after, 0)
        self.assertLess(retry_after, 60)  # auth refills at 10/min, so < 60s
