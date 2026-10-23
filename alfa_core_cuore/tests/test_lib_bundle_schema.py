# SPDX-License-Identifier: LGPL-3.0-only
"""Pure-Python validator test (no Odoo needed).

python -m pytest alfa_core_cuore/tests/test_lib_bundle_schema.py
python alfa_core_cuore/tests/test_lib_bundle_schema.py
"""

import importlib.util
import sys
import unittest
from pathlib import Path

_HERE = Path(__file__).resolve().parent


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


bundle_schema = _load("cuore_bundle_schema_under_test", _HERE.parent / "lib" / "bundle_schema.py")
synth = _load("cuore_synthetic_bundle_under_test", _HERE / "synthetic_bundle.py")


class TestValidator(unittest.TestCase):
    def test_valid_passes_and_tampered_sha256_fails(self):
        for kind in ("scan", "job"):
            good = synth.build_bundle(kind)
            self.assertEqual(bundle_schema.validate_bundle(good), [])
            member = "dtcs.json" if kind == "scan" else "job.json"
            errors = bundle_schema.validate_bundle(synth.tamper_member(good, member))
            self.assertTrue(any("sha256 mismatch" in e for e in errors), errors)


if __name__ == "__main__":
    unittest.main()
