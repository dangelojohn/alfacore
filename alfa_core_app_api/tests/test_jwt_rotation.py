# SPDX-License-Identifier: LGPL-3.0-only
"""JWT secret rotation tests — both secrets accepted in grace window."""

from datetime import datetime, timedelta

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "alfacore_sprint11_jwt_rotation")
class TestJwtRotation(TransactionCase):
    def setUp(self):
        super().setUp()
        # Use the sudo manager throughout
        self.Manager = self.env["alfa_core_app_api.jwt_secret_manager"].sudo()
        self.ICP = self.env["ir.config_parameter"].sudo()
        # Start each test with a known-good current secret, no previous
        self.ICP.set_param("alfa_core_app_api.jwt_secret", "test-secret-original")
        self.ICP.set_param("alfa_core_app_api.jwt_secret_previous", "")
        self.ICP.set_param("alfa_core_app_api.jwt_secret_rotated_at", "")

    def _sign(self, secret, payload=None):
        import jwt

        payload = payload or {
            "sub": "1",
            "jti": "test-jti",
            "iat": int(datetime.utcnow().timestamp()),
            "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
        }
        return jwt.encode(payload, secret, algorithm="HS256")

    def test_verify_with_current_secret_succeeds(self):
        token = self._sign("test-secret-original")
        payload = self.Manager.verify_token(token)
        self.assertEqual(payload["jti"], "test-jti")

    def test_verify_with_wrong_secret_fails(self):
        import jwt

        token = self._sign("wrong-secret")
        with self.assertRaises(jwt.InvalidTokenError):
            self.Manager.verify_token(token)

    def test_rotation_moves_current_to_previous(self):
        result = self.Manager.action_rotate_secret()
        self.assertEqual(result["status"], "rotated")
        self.assertEqual(
            self.ICP.get_param("alfa_core_app_api.jwt_secret_previous"),
            "test-secret-original",
        )
        # Current is a fresh random value
        new_current = self.ICP.get_param("alfa_core_app_api.jwt_secret")
        self.assertNotEqual(new_current, "test-secret-original")
        self.assertGreater(len(new_current), 20)

    def test_token_signed_with_previous_secret_still_verifies(self):
        """After rotation, tokens signed with the old secret should still
        verify during the grace window."""
        # Sign before rotation
        old_token = self._sign("test-secret-original")
        # Rotate
        self.Manager.action_rotate_secret()
        # Old token should still verify (via previous-secret fallback)
        payload = self.Manager.verify_token(old_token)
        self.assertEqual(payload["jti"], "test-jti")

    def test_token_signed_with_new_secret_also_verifies(self):
        self.Manager.action_rotate_secret()
        new_secret = self.ICP.get_param("alfa_core_app_api.jwt_secret")
        new_token = self._sign(new_secret)
        payload = self.Manager.verify_token(new_token)
        self.assertEqual(payload["jti"], "test-jti")

    def test_token_signed_with_unrelated_secret_still_fails(self):
        import jwt

        self.Manager.action_rotate_secret()
        # A third, unknown secret
        rogue_token = self._sign("not-current-not-previous")
        with self.assertRaises(jwt.InvalidTokenError):
            self.Manager.verify_token(rogue_token)

    def test_clear_previous_blocks_old_tokens(self):
        old_token = self._sign("test-secret-original")
        self.Manager.action_rotate_secret()
        # Confirm it works before clear
        self.Manager.verify_token(old_token)
        # Clear
        self.Manager.action_clear_previous_secret()
        # Now it should fail
        import jwt

        with self.assertRaises(jwt.InvalidTokenError):
            self.Manager.verify_token(old_token)

    def test_cron_keeps_previous_during_grace(self):
        self.Manager.action_rotate_secret()
        # rotated_at just set to now — well within grace
        result = self.Manager.cron_clear_stale_previous()
        self.assertEqual(result["status"], "still_in_grace")
        # Previous still set
        self.assertTrue(self.ICP.get_param("alfa_core_app_api.jwt_secret_previous"))

    def test_cron_clears_previous_after_grace(self):
        self.Manager.action_rotate_secret()
        # Backdate the rotation timestamp to 31 days ago
        old_date = (datetime.utcnow() - timedelta(days=31)).isoformat()
        self.ICP.set_param("alfa_core_app_api.jwt_secret_rotated_at", old_date)
        result = self.Manager.cron_clear_stale_previous()
        self.assertEqual(result["status"], "cleared")
        self.assertFalse(self.ICP.get_param("alfa_core_app_api.jwt_secret_previous"))

    def test_first_time_setup_does_not_create_previous(self):
        """If the current secret is a placeholder, rotation is
        "initialization" — no previous slot populated."""
        self.ICP.set_param(
            "alfa_core_app_api.jwt_secret", "CHANGE_ME_IN_PRODUCTION_USE_OPENSSL_RAND"
        )
        result = self.Manager.action_rotate_secret()
        self.assertEqual(result["status"], "initialized")
        # Previous should still be empty
        self.assertFalse(self.ICP.get_param("alfa_core_app_api.jwt_secret_previous"))
