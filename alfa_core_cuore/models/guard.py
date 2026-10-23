# SPDX-License-Identifier: LGPL-3.0-only
"""Write / unlink guard for CUORE-sourced rows (integration spec 6.5).

AlfaCore's own models enforce no immutability (MODEL_MAP 15.4). Rows that came from a
CUORE bundle are readings and ledger entries; only the importer may change them. The
importer sets ``cuore_import=True`` in the context (and runs as the importing user's
elevated environment, see ``alfa.cuore.bundle``). Correcting a reading means a new scan
and a new bundle; a bad import is deleted by a manager, never edited.
"""

from odoo import _
from odoo.exceptions import UserError

#: Fields mail.thread writes on its own; never a change to the reading itself.
MAIL_FIELDS = frozenset(
    {"message_main_attachment_id", "message_follower_ids", "message_ids", "activity_ids"}
)


def guard_write(records, vals, *, locked_fields=None, free_fields=MAIL_FIELDS):
    """Raise unless the importer is writing.

    ``locked_fields`` limits the guard to those field names (for models an advisor
    may still edit elsewhere, such as the report summary); ``None`` locks every
    field except ``free_fields``.
    """
    if records.env.context.get("cuore_import") or not records:
        return
    touched = set(vals) - set(free_fields)
    if locked_fields is not None:
        touched &= set(locked_fields)
    if touched:
        raise UserError(
            _(
                "This record comes from a CUORE bundle and cannot be edited (%(fields)s). "
                "To correct a reading, make a new scan and import its bundle; a bad import "
                "is deleted by a manager.",
                fields=", ".join(sorted(touched)),
            )
        )


def guard_unlink(records):
    if records.env.context.get("cuore_import") or not records:
        return
    raise UserError(
        _(
            "Records imported from a CUORE bundle cannot be deleted one by one. "
            "A manager deletes the whole bundle if the import was wrong."
        )
    )
