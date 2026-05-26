# SPDX-License-Identifier: LGPL-3.0-only
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "alfacore_smoke")
class TestInstall(TransactionCase):
    def test_installed(self):
        m = self.env["ir.module.module"].search([("name", "=", "alfa_tsb")])
        self.assertEqual(m.state, "installed")

    def test_default_collection_seeded(self):
        coll = self.env["alfa_tsb.qdrant_collection"].search([("name", "=", "alfa_tsb_v1")])
        self.assertEqual(len(coll), 1)


@tagged("post_install", "-at_install", "alfacore_sprint13")
class TestTsbChunking(TransactionCase):
    def test_chunking_creates_chunks(self):
        tsb = self.env["alfa_tsb.tsb"].create(
            {
                "name": "Test TSB Chunking",
                "bulletin_number": "TEST-CHUNK-001",
                "full_text": "Para one.\n\n"
                + ("Para two. " * 50)
                + "\n\n"
                + ("Para three. " * 50)
                + "\n\nPara four.",
                "state": "published",
            }
        )
        tsb.action_chunk()
        self.assertGreater(len(tsb.chunk_ids), 0)
        self.assertEqual(tsb.state, "chunked")
        for c in tsb.chunk_ids:
            self.assertLessEqual(len(c.text), 1500)

    def test_chunking_is_idempotent(self):
        tsb = self.env["alfa_tsb.tsb"].create(
            {
                "name": "Test TSB Re-chunk",
                "bulletin_number": "TEST-CHUNK-002",
                "full_text": "Some text.\n\nMore text.",
                "state": "published",
            }
        )
        tsb.action_chunk()
        first_count = len(tsb.chunk_ids)
        tsb.action_chunk()  # re-chunk
        self.assertEqual(len(tsb.chunk_ids), first_count)

    def test_index_stub_marks_chunks(self):
        tsb = self.env["alfa_tsb.tsb"].create(
            {
                "name": "Test TSB Index",
                "bulletin_number": "TEST-INDEX-001",
                "full_text": "Some text content.",
                "state": "published",
            }
        )
        tsb.action_chunk()
        tsb.action_index_to_qdrant()
        self.assertEqual(tsb.state, "indexed")
        for c in tsb.chunk_ids:
            self.assertTrue(c.qdrant_point_id)
            self.assertTrue(c.indexed_at)

    def test_bulletin_number_uniqueness(self):
        self.env["alfa_tsb.tsb"].create(
            {
                "name": "First",
                "bulletin_number": "TEST-UNIQ-100",
            }
        )
        with self.assertRaises(Exception):
            self.env["alfa_tsb.tsb"].create(
                {
                    "name": "Duplicate",
                    "bulletin_number": "TEST-UNIQ-100",
                }
            )
