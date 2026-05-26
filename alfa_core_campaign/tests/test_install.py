# SPDX-License-Identifier: LGPL-3.0-only
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "alfacore_smoke")
class TestInstall(TransactionCase):
    def test_installed(self):
        m = self.env["ir.module.module"].search([("name", "=", "alfa_core_campaign")])
        self.assertEqual(m.state, "installed")


@tagged("post_install", "-at_install", "alfacore_sprint12")
class TestCampaignTargeting(TransactionCase):
    def test_targeting_picks_affected_vehicles(self):
        # Create a vehicle that should match the Giorgio coil campaign
        veh = self.env["alfa_fleet.vehicle"].create(
            {
                "vin": "ZASFAKBN3J7CCAMP1",
                "year": 2018,
                "model": "Stelvio",
                "platform_id": self.env.ref("alfa_fleet.platform_giorgio").id,
                "engine_id": self.env.ref("alfa_fleet.engine_gme_2_0t").id,
            }
        )
        camp = self.env.ref(
            "alfa_core_campaign.campaign_giorgio_coil_tsb", raise_if_not_found=False
        )
        if not camp:
            self.skipTest("Demo campaign not loaded")
        camp.action_target_vehicles()
        targets = self.env["alfa_core_campaign.target"].search(
            [
                ("campaign_id", "=", camp.id),
                ("vehicle_id", "=", veh.id),
            ]
        )
        self.assertEqual(len(targets), 1)

    def test_target_uniqueness_constraint(self):
        veh = self.env["alfa_fleet.vehicle"].create(
            {
                "vin": "ZASFAKBN3J7CCAMP2",
                "year": 2018,
                "model": "Stelvio",
                "platform_id": self.env.ref("alfa_fleet.platform_giorgio").id,
            }
        )
        camp = self.env["alfa_core_campaign.campaign"].create(
            {
                "name": "Test Camp",
                "campaign_type": "safety_recall",
                "source": "manufacturer",
                "source_id": "TEST-UNIQ-001",
                "severity": "medium",
            }
        )
        self.env["alfa_core_campaign.target"].create(
            {
                "campaign_id": camp.id,
                "vehicle_id": veh.id,
            }
        )
        with self.assertRaises(Exception):
            self.env["alfa_core_campaign.target"].create(
                {
                    "campaign_id": camp.id,
                    "vehicle_id": veh.id,
                }
            )

    def test_nhtsa_upsert_creates_campaign(self):
        record = {
            "NHTSACampaignNumber": "TEST-23V999000",
            "Manufacturer": "FCA US LLC",
            "Component": "BRAKES",
            "Summary": "Test summary for upsert",
            "Consequence": "Test consequence",
            "Remedy": "Test remedy",
        }
        client = self.env["alfa_core_campaign.nhtsa_client"]
        camp = client.upsert_campaign_from_nhtsa_record(record)
        self.assertTrue(camp)
        self.assertEqual(camp.source_id, "TEST-23V999000")
        # Idempotent — second call updates, doesn't duplicate
        camp2 = client.upsert_campaign_from_nhtsa_record(record)
        self.assertEqual(camp2.id, camp.id)
