# SPDX-License-Identifier: LGPL-3.0-only
"""Import tests, driven by SYNTHETIC bundles (fake VIN, test station), never a real export."""

from odoo.tests.common import TransactionCase, tagged

from . import synthetic_bundle as synth


@tagged("post_install", "-at_install", "alfacore_sprint14")
class TestCuoreImport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Bundle = cls.env["alfa.cuore.bundle"]
        cls.vehicle = cls.env["alfa_fleet.vehicle"].create(
            {"vin": synth.SYNTH_VIN, "year": 2018, "model": "Stelvio"}
        )

    def _counts(self):
        return [
            self.env[m].search_count([])
            for m in (
                "alfa.cuore.bundle",
                "alfa_core_scanner.scan_session",
                "alfa_core_scanner.scan_dtc",
                "alfa_core_diagnosis.report",
                "alfa.cuore.hypothesis",
                "alfa_core_inspection.inspection",
            )
        ]

    def test_reimport_same_bundle_creates_nothing(self):
        data = synth.build_bundle("scan")
        first = self.Bundle._import(data, "synthetic.cuore.zip")
        self.assertEqual(first["outcome"], "imported", first["errors"])
        self.assertEqual(len(first["bundle"].scan_session_id.dtc_ids), 3)
        before = self._counts()
        second = self.Bundle._import(data, "synthetic.cuore.zip")
        self.assertEqual(second["outcome"], "already")
        self.assertEqual(second["bundle"], first["bundle"])
        self.assertEqual(self._counts(), before)

    def test_evidence_class_and_status_preserved(self):
        out = self.Bundle._import(synth.build_bundle("job"), "synthetic.cuore.zip")
        self.assertEqual(out["outcome"], "imported", out["errors"])
        report = out["bundle"].report_id
        hyps = {h.hyp_id: h for h in report.hypothesis_ids}
        self.assertEqual(
            (hyps["hyp00001"].evidence_class, hyps["hyp00001"].status), ("inference", "open")
        )
        self.assertEqual(hyps["hyp00002"].evidence_class, "owner_attested")
        self.assertNotIn("reading", report.hypothesis_ids.mapped("evidence_class"))
        self.assertEqual(report.state, "draft")
        self.assertEqual(report.confidence, 0.0)

        # A hypothesis claiming to be a reading is refused.
        def lie(parts):
            parts["job.json"]["job"]["hypotheses"][0]["evidence_class"] = "reading"

        bad = self.Bundle._import(
            synth.build_bundle("job", salt="x", mutate_parts=lie), "bad.cuore.zip"
        )
        self.assertEqual(bad["outcome"], "rejected")
