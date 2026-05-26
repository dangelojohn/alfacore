# SPDX-License-Identifier: LGPL-3.0-only
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "alfacore_smoke")
class TestInstall(TransactionCase):
    def test_installed(self):
        m = self.env["ir.module.module"].search([("name", "=", "alfa_core_app_api")])
        self.assertEqual(m.state, "installed")

    def test_jwt_secret_seeded(self):
        secret = self.env["ir.config_parameter"].sudo().get_param("alfa_core_app_api.jwt_secret")
        self.assertTrue(secret)


@tagged("post_install", "-at_install", "alfacore_sprint11")
class TestTokenLifecycle(TransactionCase):
    def test_issue_creates_record(self):
        partner = self.env["res.partner"].create({"name": "Token User"})
        Token = self.env["alfa_core_app_api.token"]
        rec = Token.issue_for_partner(partner.id, scope="pwa", ttl_days=7)
        self.assertEqual(rec.state, "active")
        self.assertEqual(rec.partner_id, partner)
        self.assertTrue(rec.jti)

    def test_revoke_flips_state(self):
        partner = self.env["res.partner"].create({"name": "Revoke User"})
        rec = self.env["alfa_core_app_api.token"].issue_for_partner(partner.id)
        rec.action_revoke()
        self.assertEqual(rec.state, "revoked")

    def test_expire_stale_sweeps(self):
        from datetime import datetime, timedelta

        partner = self.env["res.partner"].create({"name": "Stale User"})
        rec = self.env["alfa_core_app_api.token"].issue_for_partner(partner.id)
        # Force expiry into the past
        rec.expires_at = datetime.now() - timedelta(days=1)
        count = self.env["alfa_core_app_api.token"].expire_stale()
        self.assertGreaterEqual(count, 1)
        self.assertEqual(rec.state, "expired")
