# SPDX-License-Identifier: LGPL-3.0-only
try:
    import odoo
except ImportError:  # pure-Python test (test_lib_bundle_schema.py) runs without Odoo
    pass
else:
    from . import test_import, test_install
