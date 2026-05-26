# SPDX-License-Identifier: LGPL-3.0-only
"""Loaner allocation + Odoo Sign integration.

This module is the EE-only overlay. It depends on `sign` (Odoo Enterprise)
and adds:
- `sign_request_id` Many2one + `sign_status` Selection fields
- `action_send_for_signature` — generates the sign.request from a configured
  template
- `_sync_sign_status` + `cron_sync_pending_signatures` — pulls live state
  from sign.request back into the allocation
- Override of `action_activate` to require sign_status == "signed" before
  letting the customer pick up the loaner
- Override of `action_cancel` to also cancel any pending sign.request

Configuration: see `data/sign_config.xml` (ir.config_parameter entries) and
the README.
"""

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AlfaLoanerAllocation(models.Model):
    _inherit = "alfa_core_loaner.allocation"

    sign_request_id = fields.Many2one(
        "sign.request",
        string="Signature Request",
        help="Odoo Sign request for the loaner agreement.",
    )
    sign_status = fields.Selection(
        [
            ("not_sent", "Not Sent"),
            ("sent", "Sent for Signature"),
            ("signed", "Signed"),
            ("expired", "Expired / Cancelled"),
        ],
        default="not_sent",
        tracking=True,
    )

    def action_send_for_signature(self):
        """Generate a sign.request from the configured loaner agreement template.

        Configuration: ir.config_parameter 'alfa_core_loaner.sign_template_id'
        must be set to the ID of a published sign.template. The template
        should have at least one role; if multiple, the role named in
        'alfa_core_loaner.sign_signer_role' (default: 'Customer') is used
        for the customer signer.

        Failure modes (all raise UserError with a clear message):
        - No template configured
        - Template ID doesn't resolve to a sign.template record
        - Template has no roles defined
        - Customer has no email address (Sign needs one to deliver)
        """
        ICP = self.env["ir.config_parameter"].sudo()
        template_id_str = ICP.get_param("alfa_core_loaner.sign_template_id")
        signer_role_name = ICP.get_param("alfa_core_loaner.sign_signer_role", default="Customer")

        if not template_id_str:
            raise UserError(
                _(
                    "Loaner agreement sign template is not configured. "
                    "Go to Settings → Technical → Parameters and set "
                    "'alfa_core_loaner.sign_template_id' to the ID of your "
                    "published loaner-agreement sign.template."
                )
            )
        try:
            template_id = int(template_id_str)
        except (TypeError, ValueError) as err:
            raise UserError(
                _("Configured sign template ID is not a valid integer: %r") % template_id_str
            ) from err

        Template = self.env["sign.template"].sudo()
        template = Template.browse(template_id).exists()
        if not template:
            raise UserError(
                _(
                    "Configured sign.template (id=%d) does not exist. "
                    "Verify alfa_core_loaner.sign_template_id."
                )
                % template_id
            )

        SignRequest = self.env["sign.request"].sudo()

        for a in self:
            if a.sign_status == "signed":
                a.message_post(body=_("Skipped send-for-signature: agreement already signed."))
                continue
            if not a.partner_id.email:
                raise UserError(
                    _(
                        "Customer %s has no email address. "
                        "Sign needs an email to deliver the agreement."
                    )
                    % a.partner_id.display_name
                )

            roles = template.sign_item_ids.mapped("responsible_id")
            if not roles:
                raise UserError(
                    _(
                        "Sign template %s has no roles defined. "
                        "Open the template in Sign and assign at least one role "
                        "(typically 'Customer') to a signature field."
                    )
                    % template.name
                )
            matching = roles.filtered(lambda r: r.name == signer_role_name)
            signer_role = matching[:1] if matching else roles[:1]

            sign_request_vals = {
                "template_id": template.id,
                "reference": a.name,
                "subject": _("Loaner Agreement — %s") % a.loaner_vehicle_id.name,
                "request_item_ids": [
                    (
                        0,
                        0,
                        {
                            "role_id": signer_role.id,
                            "partner_id": a.partner_id.id,
                        },
                    )
                ],
            }
            try:
                request_rec = SignRequest.create(sign_request_vals)
            except Exception as e:
                raise UserError(
                    _(
                        "Could not create sign.request: %s. "
                        "Verify the template is published and roles are wired "
                        "correctly."
                    )
                    % str(e)
                ) from e

            a.sign_request_id = request_rec.id
            a.sign_status = "sent"
            a.message_post(
                body=_("Loaner agreement sent for signature to %s (sign.request reference: %s).")
                % (a.partner_id.display_name, request_rec.reference or request_rec.id)
            )

    def _sync_sign_status(self):
        """Pull the latest state from the linked sign.request and map it to
        our sign_status."""
        changed = 0
        for a in self:
            if not a.sign_request_id:
                continue
            req_state = a.sign_request_id.state
            new_status = None
            if req_state == "signed":
                new_status = "signed"
            elif req_state in ("canceled", "cancelled", "expired"):
                new_status = "expired"
            if new_status and new_status != a.sign_status:
                old_status = a.sign_status
                a.sign_status = new_status
                a.message_post(
                    body=_("Signature status synced: %s → %s (sign.request.state = %s).")
                    % (old_status, new_status, req_state)
                )
                changed += 1
        return changed

    @api.model
    def cron_sync_pending_signatures(self):
        """Cron entry — sync all allocations currently waiting on signature."""
        pending = self.search(
            [
                ("sign_status", "=", "sent"),
                ("sign_request_id", "!=", False),
            ]
        )
        if not pending:
            return {"checked": 0, "changed": 0}
        changed = pending._sync_sign_status()
        return {"checked": len(pending), "changed": changed}

    def action_activate(self):
        """Override: require sign_status == 'signed' before pickup activation."""
        for a in self:
            if a.state == "scheduled" and a.sign_status != "signed":
                raise UserError(_("Loaner agreement must be signed before activation."))
        return super().action_activate()

    def action_cancel(self):
        """Override: also cancel any pending sign.request."""
        for a in self:
            if a.state in ("completed", "cancelled"):
                continue
            if a.sign_request_id and a.sign_status == "sent":
                try:
                    a.sign_request_id.sudo().cancel()
                    a.sign_status = "expired"
                except Exception as e:
                    a.message_post(
                        body=_("Allocation cancelled, but could not cancel sign.request: %s")
                        % str(e)
                    )
        return super().action_cancel()
