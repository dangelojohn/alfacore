# alfa_core_loaner — Sign integration setup

After installing this module, complete the Sign template configuration
before any allocation can be sent for signature.

## One-time setup

### 1. Create or import the loaner agreement template

In Odoo: **Sign → Templates → New**

Upload a PDF of your standard loaner agreement. Add at least one
signature field and assign it to a role. The role name should match
`alfa_core_loaner.sign_signer_role` (default `Customer`) — either set
the role to `Customer` in the template, or override the config param
to match whatever you named it.

If the template uses field placeholders ( `{partner_name}`, `{loaner_vehicle}`,
`{pickup_date}`, etc.), wire them via Sign's template-variable feature.
The allocation passes `name`, `reference`, `subject`, and signer
`partner_id` — additional context variables are TODO and tracked in
the Sprint 9 hand-off notes.

### 2. Note the template's record ID

Open the template in Sign and note its database ID (visible in the URL,
or via Developer Mode → Technical → Database Structure).

### 3. Set the config parameter

**Settings → Technical → Parameters → System Parameters**

| Key | Value |
|---|---|
| `alfa_core_loaner.sign_template_id` | the integer ID from step 2 |
| `alfa_core_loaner.sign_signer_role` | `Customer` (or match your template's role name) |

That's it. The next time an advisor clicks **Send for Signature** on an
allocation in `scheduled` state, the loaner-agreement Sign request will
be generated and emailed to the customer.

## Operational behavior

- **Status sync**: a cron job `cron_sync_signatures` runs every 5 minutes
  and pulls the current state of pending sign requests into the
  allocation's `sign_status` field. Manual sync via the **Sync Sig
  Status** button on the allocation form.
- **Activation gate**: `action_activate` (the "Pickup" button) requires
  `sign_status = signed`. The advisor cannot mark the loaner picked up
  until the customer has signed.
- **Cancel propagation**: cancelling an allocation also cancels the
  pending sign.request. Failures to cancel the sign.request are logged
  to chatter but don't block the allocation cancel.

## What's still hand-off

- **Template variable substitution** — the allocation passes basic
  context (`name`, `reference`, `subject`, signer `partner_id`) but does
  not yet inject vehicle-specific or date-specific variables into the
  Sign template's field substitution. Wire this up in Claude Code by
  extending `action_send_for_signature` with a `sign_template_value_ids`
  list-of-tuples in the `sign_request` create vals.
- **Email template** — Sign uses its default email template. To customize
  branding, copy the `sign.request_email` template and reference your
  copy via the Sign module's settings.
- **End-to-end UI test** — only meaningful against a running Odoo with
  Sign installed. Use Playwright or Odoo's tour testing framework to
  drive the full flow from allocation creation → signature → activation.
