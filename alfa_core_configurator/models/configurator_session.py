# SPDX-License-Identifier: LGPL-3.0-only
"""Configurator session — 30-day TTL state, vehicle-anchored.

Configurator audit §2.2 — Sessions live for 30 days, durable across
customer drop-off and return. Includes the cascade orchestrator hook.
"""

from datetime import timedelta

from odoo import _, api, fields, models


class AlfaConfiguratorSession(models.Model):
    _name = "alfa_core_configurator.session"
    _description = "Configurator Session"
    _inherit = ["mail.thread"]
    _order = "create_date desc, id desc"
    _rec_name = "name"

    name = fields.Char(required=True, copy=False, readonly=True, default=lambda s: _("New"))
    vehicle_id = fields.Many2one("alfa_fleet.vehicle", required=True, tracking=True, index=True)
    partner_id = fields.Many2one(related="vehicle_id.primary_owner_id", store=True)
    subscription_id = fields.Many2one(
        "alfa_core.subscription",
        string="Subscription",
        help="Anchored subscription — drives tier-gated options.",
    )
    blueprint_code = fields.Char(string="Service Blueprint", required=True, index=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("committed", "Committed (became SO)"),
            ("abandoned", "Abandoned"),
            ("expired", "Expired"),
        ],
        default="draft",
        required=True,
        tracking=True,
    )
    started_at = fields.Datetime(default=fields.Datetime.now)
    last_touch_at = fields.Datetime(default=fields.Datetime.now)
    expires_at = fields.Datetime(compute="_compute_expires_at", store=True)
    sale_order_id = fields.Many2one("sale.order", string="Resulting SO", readonly=True, copy=False)
    signal_ids = fields.One2many("alfa_core_configurator.signal", "session_id", string="Signals")
    ledger_ids = fields.One2many(
        "alfa_core_configurator.benefit_ledger", "session_id", string="Benefit Audit Trail"
    )
    selected_options_json = fields.Text(
        string="Selected Options (JSON)", help="Serialized selection state. Schema by blueprint."
    )

    @api.depends("last_touch_at")
    def _compute_expires_at(self):
        for s in self:
            if s.last_touch_at:
                s.expires_at = s.last_touch_at + timedelta(days=30)
            else:
                s.expires_at = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "alfa_core_configurator.session"
                ) or _("New")
        return super().create(vals_list)

    def touch(self):
        """Refresh last_touch — extends TTL."""
        self.last_touch_at = fields.Datetime.now()

    # =========================================================================
    # Cascade implementation
    # =========================================================================
    # Pattern 6 — configuration as data. Rules live in
    # alfa_core_configurator.eligibility_rule records; the cascade engine is
    # pure: same rules + same session = same outcome.
    #
    # Pattern 9 — logging as UI. Every rule evaluation logs a benefit_ledger
    # entry. The ledger IS the audit trail; the "explanation" of the cascade
    # is reading the ledger back to the customer or advisor.
    #
    # Pattern 10 — honest boundaries. A malformed domain_expression doesn't
    # crash; it logs a 'rule_evaluated' entry with the error and is treated
    # as "rule did not match" for safety (fail-closed for hide/require,
    # fail-open for recommend/show).

    # Precedence ordering — higher number wins on the same option.
    # require dominates everything: it's a hard inclusion (e.g. safety recall).
    # hide dominates recommend/show: hard exclusion (e.g. tier-locked option).
    # recommend dominates show: soft preference with score.
    # show is the default (visible, no preference).
    _ACTION_PRECEDENCE = {"show": 1, "recommend": 2, "hide": 3, "require": 4}

    def run_cascade(self):
        """Evaluate all eligibility rules + signals against this session.

        Mutates: selected_options_json (require → selected; hide → deselected);
                 writes one benefit_ledger entry per rule evaluated, plus
                 one summary entry per resolved option.
        Returns: structured result dict (see _build_cascade_result for shape).

        Idempotent: re-running on the same session produces the same option
        states. The ledger gets new entries each run (it's an append-only
        audit log), but selected_options_json is convergent.
        """
        self.ensure_one()
        if self.state not in ("draft", "active"):
            from odoo.exceptions import UserError

            raise UserError(
                _(
                    "Cannot run cascade on a session in state %r. "
                    "Only draft and active sessions accept cascade."
                )
                % self.state
            )

        # Move to active on first cascade
        if self.state == "draft":
            self.state = "active"

        Rule = self.env["alfa_core_configurator.eligibility_rule"]
        Ledger = self.env["alfa_core_configurator.benefit_ledger"]

        # ---------------------------------------------------------------------
        # Stage 1 — collect applicable rules for this blueprint
        # ---------------------------------------------------------------------
        rules = Rule.search(
            [
                ("blueprint_code", "=", self.blueprint_code),
                ("active", "=", True),
            ],
            order="sequence, id",
        )

        # ---------------------------------------------------------------------
        # Stage 2 — evaluate each rule; log every evaluation regardless
        # ---------------------------------------------------------------------
        applied_actions = {}  # option -> list of (rule, action) tuples
        rule_log = []

        for rule in rules:
            matched, error = self._evaluate_rule(rule)
            rule_log.append(
                {
                    "rule_id": rule.id,
                    "rule_code": rule.code,
                    "matched": matched,
                    "action": rule.rule_action,
                    "option": rule.option_value,
                    "error": error,
                }
            )

            ledger_explanation = rule.explanation or rule.name
            if error:
                ledger_explanation = _("Rule %s evaluation failed: %s. Treated as non-match.") % (
                    rule.code,
                    error,
                )
            elif matched:
                ledger_explanation = _("Rule %s matched: %s") % (rule.code, ledger_explanation)
            else:
                ledger_explanation = _("Rule %s did not match.") % rule.code

            Ledger.create(
                {
                    "session_id": self.id,
                    "entry_type": "rule_evaluated",
                    "name": rule.name,
                    "explanation": ledger_explanation,
                    "rule_id": rule.id,
                }
            )

            if matched and not error:
                applied_actions.setdefault(rule.option_value, []).append((rule, rule.rule_action))

        # ---------------------------------------------------------------------
        # Stage 3 — aggregate signals into per-option scores
        # ---------------------------------------------------------------------
        signal_scores = self._aggregate_signal_scores()

        # ---------------------------------------------------------------------
        # Stage 4 — resolve final option states via precedence
        # ---------------------------------------------------------------------
        resolution = self._resolve_option_states(applied_actions, signal_scores)

        # ---------------------------------------------------------------------
        # Stage 5 — apply resolution to selected_options_json
        # ---------------------------------------------------------------------
        self._apply_resolution(resolution)

        # ---------------------------------------------------------------------
        # Stage 6 — log per-option resolution outcomes to the ledger
        # ---------------------------------------------------------------------
        for option, state in resolution.items():
            entry_type_map = {
                "show": "option_shown",
                "recommend": "recommendation_made",
                "hide": "option_hidden",
                "require": "option_selected",  # require auto-selects
            }
            score_note = ""
            if state["state"] == "recommend":
                score_note = _(" (score %.2f)") % state["score"]
            Ledger.create(
                {
                    "session_id": self.id,
                    "entry_type": entry_type_map.get(state["state"], "option_shown"),
                    "name": option,
                    "explanation": _("Resolved to '%s'%s. Conflicts: %d.")
                    % (state["state"], score_note, state["precedence_overrides_count"]),
                    "related_value": option,
                }
            )

        # ---------------------------------------------------------------------
        # Stage 7 — summary chatter post
        # ---------------------------------------------------------------------
        rules_matched = sum(1 for r in rule_log if r["matched"])
        rules_errored = sum(1 for r in rule_log if r["error"])
        self.message_post(
            body=_(
                "Cascade complete. %d rule(s) evaluated, %d matched, %d errored. "
                "%d option(s) resolved."
            )
            % (len(rule_log), rules_matched, rules_errored, len(resolution))
        )

        self.touch()
        return self._build_cascade_result(rule_log, resolution)

    def _evaluate_rule(self, rule):
        """Evaluate a single rule's domain_expression against this session.

        Returns (matched: bool, error: str | None).
        On any evaluation error, returns (False, error_message) — fail-closed.
        """
        self.ensure_one()
        if not rule.domain_expression:
            # No expression = unconditional match
            return True, None
        try:
            from odoo.tools.safe_eval import safe_eval

            domain = safe_eval(rule.domain_expression)
        except Exception as e:
            return False, _("domain parse: %s") % str(e)

        if not isinstance(domain, list):
            return False, _("domain_expression must be a list, got %s") % type(domain).__name__

        try:
            # Test if THIS session matches the domain
            matches = self.search(domain + [("id", "=", self.id)], limit=1)
        except Exception as e:
            return False, _("domain evaluation: %s") % str(e)

        return bool(matches), None

    def _aggregate_signal_scores(self):
        """Aggregate per-option recommendation scores from active signals.

        For now, this is a flat sum of weight * confidence across all
        non-expired signals. A future refinement would route signals to
        specific options via signal.value matching option keys.

        Returns dict: {option: aggregate_score (0.0–1.0+)}.
        For v1, every option gets the same aggregate (a global "demand
        score"); recommend-action rules then multiply by their own weight.
        """
        self.ensure_one()
        now = fields.Datetime.now()
        active_signals = self.signal_ids.filtered(lambda s: not s.expires_at or s.expires_at > now)
        if not active_signals:
            return {}
        # Global score = mean of weight * confidence
        scores = [s.weight * s.confidence for s in active_signals]
        global_score = sum(scores) / len(scores) if scores else 0.0
        # Return a dict keyed on signal value so option-specific routing
        # can replace this in a future iteration.
        return {"__global__": global_score}

    def _resolve_option_states(self, applied_actions, signal_scores):
        """Apply precedence to resolve final state per option.

        applied_actions: {option: [(rule, action), ...]}
        signal_scores:   {option_or_'__global__': score}

        Returns: {option: {"state": str, "score": float, "rules": list,
                           "precedence_overrides_count": int}}
        """
        resolution = {}
        global_score = signal_scores.get("__global__", 0.0)

        for option, rule_actions in applied_actions.items():
            best_action = "show"
            best_precedence = 0
            precedence_overrides_count = 0
            contributing_rules = []

            for rule, action in rule_actions:
                contributing_rules.append(rule.id)
                p = self._ACTION_PRECEDENCE.get(action, 0)
                if p > best_precedence:
                    if best_precedence > 0:
                        precedence_overrides_count += 1
                    best_action = action
                    best_precedence = p
                elif p == best_precedence and action != best_action:
                    # Tied precedence but different action — that's a conflict
                    # (impossible given our precedence table, since each level
                    # has a unique action, but defensive for future actions)
                    precedence_overrides_count += 1
                elif p < best_precedence:
                    precedence_overrides_count += 1

            # Score is only meaningful for 'recommend' state
            score = 0.0
            if best_action == "recommend":
                # Combine the global signal score with the rule's implicit weight (1.0)
                score = min(1.0, global_score)

            resolution[option] = {
                "state": best_action,
                "score": score,
                "rules": contributing_rules,
                "precedence_overrides_count": precedence_overrides_count,
            }

        return resolution

    def _apply_resolution(self, resolution):
        """Mutate selected_options_json based on the resolution.

        - 'require' → force option to True
        - 'hide'    → force option to False
        - 'recommend' → do not change current selection; the UI reads
          the state separately and renders a recommendation badge
        - 'show'    → no change to selection

        Preserves all options not touched by any rule.
        """
        self.ensure_one()
        import json

        current = {}
        if self.selected_options_json:
            try:
                current = json.loads(self.selected_options_json) or {}
            except (ValueError, TypeError):
                current = {}

        for option, state in resolution.items():
            if state["state"] == "require":
                current[option] = True
            elif state["state"] == "hide":
                current[option] = False
            # 'recommend' and 'show' do not mutate selection

        self.selected_options_json = json.dumps(current, sort_keys=True)

    def _build_cascade_result(self, rule_log, resolution):
        """Compose the structured result returned to the caller.

        Useful for API consumers and the future configurator UI — they
        get the full per-option state without re-querying the ledger.
        """
        options = {}
        for opt, state in resolution.items():
            options[opt] = {
                "state": state["state"],
                "score": round(state["score"], 4),
                "rule_count": len(state["rules"]),
                "precedence_overrides_count": state["precedence_overrides_count"],
            }

        return {
            "session_id": self.id,
            "session_name": self.name,
            "blueprint_code": self.blueprint_code,
            "options": options,
            "summary": {
                "rules_evaluated": len(rule_log),
                "rules_matched": sum(1 for r in rule_log if r["matched"]),
                "rules_errored": sum(1 for r in rule_log if r["error"]),
                "options_visible": sum(1 for o in options.values() if o["state"] != "hide"),
                "options_hidden": sum(1 for o in options.values() if o["state"] == "hide"),
                "options_required": sum(1 for o in options.values() if o["state"] == "require"),
                "options_recommended": sum(
                    1 for o in options.values() if o["state"] == "recommend"
                ),
            },
            "rule_log": rule_log,
        }
