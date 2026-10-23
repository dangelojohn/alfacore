# SPDX-License-Identifier: LGPL-3.0-only
try:
    import odoo
except ImportError:  # pure-Python tooling (lib/ tests) runs without an Odoo install
    pass
else:
    from . import models, wizard
