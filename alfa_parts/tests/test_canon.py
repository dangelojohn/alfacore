# SPDX-License-Identifier: LGPL-3.0-only
"""Pattern 7 canonicalization tests."""

from odoo.addons.alfa_parts.models.part import canonicalize_part_number
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "alfacore_sprint3")
class TestCanonicalization(TransactionCase):
    def test_uppercase(self):
        self.assertEqual(canonicalize_part_number("abc123"), "ABC123")

    def test_strip_dashes(self):
        self.assertEqual(canonicalize_part_number("68377611-AA"), "68377611AA")

    def test_strip_underscores(self):
        self.assertEqual(canonicalize_part_number("68377611_AA"), "68377611AA")

    def test_strip_dots(self):
        self.assertEqual(canonicalize_part_number("68.377.611.AA"), "68377611AA")

    def test_strip_whitespace(self):
        self.assertEqual(canonicalize_part_number("  68377611AA  "), "68377611AA")

    def test_strip_quotes(self):
        self.assertEqual(canonicalize_part_number('"68377611AA"'), "68377611AA")

    def test_all_combined(self):
        self.assertEqual(canonicalize_part_number(" 68-377_611.AA "), "68377611AA")

    def test_dedup_on_create(self):
        part1 = self.env["alfa_parts.part"].create(
            {
                "part_number": "55214664",
                "name": "Coil",
            }
        )
        with self.assertRaises(Exception):
            self.env["alfa_parts.part"].create(
                {
                    "part_number": "55-214-664",  # canonicalizes to same value
                    "name": "Coil duplicate",
                }
            )

    def test_find_by_part_number(self):
        part = self.env["alfa_parts.part"].create(
            {
                "part_number": "55214664",
                "name": "Coil",
            }
        )
        # All variants find the same part
        for variant in ("55214664", "55-214-664", "55_214_664", "55214664", "55214664"):
            found = self.env["alfa_parts.part"].find_by_part_number(variant)
            self.assertEqual(found, part, f"Variant {variant} should find the canonical part")
