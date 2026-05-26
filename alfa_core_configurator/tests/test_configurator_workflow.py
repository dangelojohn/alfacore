# SPDX-License-Identifier: LGPL-3.0-only
"""Configurator workflow tests — session lifecycle, signal aggregation, benefit ledger."""

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "alfacore_sprint7_workflow")
class TestConfiguratorWorkflow(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Configurator Test Customer"})
        cls.vehicle = cls.env["alfa_fleet.vehicle"].create(
            {
                "vin": "ZASFAKBN3J7CCFGX1",
                "year": 2020,
                "model": "Stelvio",
            }
        )
        plan = cls.env.ref("alfa_core.plan_premium", raise_if_not_found=False)
        if plan:
            cls.subscription = cls.env["alfa_core.subscription"].create(
                {
                    "partner_id": cls.partner.id,
                    "plan_id": plan.id,
                    "state": "active",
                }
            )
        else:
            cls.subscription = None

    def test_session_sequence_assigned(self):
        session = self.env["alfa_core_configurator.session"].create(
            {
                "vehicle_id": self.vehicle.id,
                "blueprint_code": "spring_service",
            }
        )
        self.assertTrue(session.name)
        self.assertIn("AC-CFG-", session.name)

    def test_session_default_state_draft(self):
        session = self.env["alfa_core_configurator.session"].create(
            {
                "vehicle_id": self.vehicle.id,
                "blueprint_code": "spring_service",
            }
        )
        self.assertEqual(session.state, "draft")

    def test_signal_aggregation(self):
        """Multiple signals on a session should be queryable and weighted."""
        session = self.env["alfa_core_configurator.session"].create(
            {
                "vehicle_id": self.vehicle.id,
                "blueprint_code": "spring_service",
                "state": "active",
            }
        )
        self.env["alfa_core_configurator.recommendation_signal"].create(
            [
                {
                    "session_id": session.id,
                    "signal_type": "mileage_interval",
                    "weight": 0.8,
                    "confidence": 0.95,
                },
                {
                    "session_id": session.id,
                    "signal_type": "dtc",
                    "weight": 0.75,
                    "confidence": 0.78,
                },
            ]
        )
        self.assertEqual(len(session.signal_ids), 2)
        # Highest-weight signal should be the mileage one
        top = session.signal_ids.sorted("weight", reverse=True)[0]
        self.assertEqual(top.signal_type, "mileage_interval")

    def test_benefit_ledger_records_evaluation(self):
        """Ledger entries should record rule evaluations (Pattern 9)."""
        session = self.env["alfa_core_configurator.session"].create(
            {
                "vehicle_id": self.vehicle.id,
                "blueprint_code": "spring_service",
                "state": "active",
            }
        )
        rule = self.env.ref(
            "alfa_core_configurator.rule_loaner_premium_plus", raise_if_not_found=False
        )
        if not rule:
            self.skipTest("Demo rules not loaded")
        self.env["alfa_core_configurator.benefit_ledger"].create(
            {
                "session_id": session.id,
                "entry_type": "rule_evaluated",
                "name": rule.name,
                "explanation": "Test: rule evaluated against demo subscription",
                "rule_id": rule.id,
                "actor_user_id": self.env.user.id,
            }
        )
        self.assertEqual(len(session.ledger_ids), 1)
        self.assertEqual(session.ledger_ids[0].entry_type, "rule_evaluated")

    def test_demo_session_signals_present(self):
        """Demo: John's spring service session has the three signals seeded."""
        session = self.env.ref(
            "alfa_core_configurator.session_dangelo_spring", raise_if_not_found=False
        )
        if not session:
            self.skipTest("Demo session not loaded")
        self.assertEqual(session.state, "active")
        self.assertEqual(len(session.signal_ids), 3)
        signal_types = session.signal_ids.mapped("signal_type")
        self.assertIn("mileage_interval", signal_types)
        self.assertIn("dtc", signal_types)
        self.assertIn("season", signal_types)


@tagged("post_install", "-at_install", "alfacore_sprint7_cascade")
class TestConfiguratorCascade(TransactionCase):
    """Cascade orchestrator tests.

    Cascade is the heart of the configurator: it takes the session's
    blueprint + the catalog of eligibility rules + the captured signals,
    evaluates each rule against the session, applies precedence, and
    produces a final per-option resolution.

    These tests cover (1) the rule evaluation engine, (2) precedence
    resolution between conflicting actions, (3) idempotency, and (4)
    the ledger audit trail.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Cascade Test Customer"})
        cls.vehicle = cls.env["alfa_fleet.vehicle"].create(
            {
                "vin": "ZASFAKBN3J7CCAS01",
                "year": 2020,
                "model": "Stelvio",
            }
        )
        cls.plan_basic = cls.env.ref("alfa_core.plan_basic", raise_if_not_found=False)
        cls.plan_premium = cls.env.ref("alfa_core.plan_premium", raise_if_not_found=False)
        cls.plan_pro = cls.env.ref("alfa_core.plan_pro", raise_if_not_found=False)

    def _create_session(self, blueprint="test_blueprint", plan=None):
        sub = None
        if plan:
            sub = self.env["alfa_core.subscription"].create(
                {
                    "partner_id": self.partner.id,
                    "plan_id": plan.id,
                    "state": "active",
                }
            )
        return self.env["alfa_core_configurator.session"].create(
            {
                "vehicle_id": self.vehicle.id,
                "blueprint_code": blueprint,
                "subscription_id": sub.id if sub else False,
            }
        )

    def _create_rule(
        self, code, action, option, domain="[]", blueprint="test_blueprint", sequence=10
    ):
        return self.env["alfa_core_configurator.eligibility_rule"].create(
            {
                "name": code,
                "code": code,
                "blueprint_code": blueprint,
                "rule_action": action,
                "option_value": option,
                "domain_expression": domain,
                "sequence": sequence,
            }
        )

    # ------------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------------

    def test_cascade_moves_draft_to_active(self):
        session = self._create_session()
        self.assertEqual(session.state, "draft")
        session.run_cascade()
        self.assertEqual(session.state, "active")

    def test_cascade_rejected_in_terminal_state(self):
        session = self._create_session()
        session.state = "committed"
        with self.assertRaises(Exception):
            session.run_cascade()

    def test_cascade_with_no_rules_succeeds(self):
        """Empty rule set is a valid cascade — just produces an empty resolution."""
        session = self._create_session(blueprint="nonexistent_blueprint")
        result = session.run_cascade()
        self.assertEqual(result["summary"]["rules_evaluated"], 0)
        self.assertEqual(result["options"], {})

    # ------------------------------------------------------------------------
    # Rule evaluation engine
    # ------------------------------------------------------------------------

    def test_unconditional_rule_matches(self):
        """Empty domain expression = unconditional match."""
        session = self._create_session()
        self._create_rule("always_show", "show", "option_a", domain="[]")
        result = session.run_cascade()
        self.assertEqual(result["summary"]["rules_matched"], 1)
        self.assertEqual(result["options"]["option_a"]["state"], "show")

    def test_domain_filters_correctly(self):
        """Rule with a domain that fails doesn't apply its action."""
        session = self._create_session()
        # Domain that can never match this session
        self._create_rule("never_match", "hide", "option_x", domain="[('id', '=', -999)]")
        result = session.run_cascade()
        self.assertEqual(result["summary"]["rules_evaluated"], 1)
        self.assertEqual(result["summary"]["rules_matched"], 0)
        # Option is not in resolution because no rule applied
        self.assertNotIn("option_x", result["options"])

    def test_subscription_tier_gating(self):
        """Track-prep style rule: hide for non-pro subscriptions."""
        if not (self.plan_basic and self.plan_pro):
            self.skipTest("Plan demo records required")
        basic_session = self._create_session(plan=self.plan_basic)
        pro_session = self._create_session(plan=self.plan_pro)
        self._create_rule(
            "track_pro_only",
            "hide",
            "track_prep",
            domain="[('subscription_id.plan_id.code', '!=', 'pro')]",
        )

        basic_result = basic_session.run_cascade()
        pro_result = pro_session.run_cascade()

        # Basic: rule matches, option hidden
        self.assertEqual(basic_result["options"]["track_prep"]["state"], "hide")
        # Pro: rule does NOT match, no option entry created
        self.assertNotIn("track_prep", pro_result["options"])

    def test_malformed_domain_fails_closed(self):
        """A broken domain logs the error, doesn't crash, treats rule as non-match."""
        session = self._create_session()
        self._create_rule("broken", "hide", "option_b", domain="this is not valid python")
        result = session.run_cascade()
        self.assertEqual(result["summary"]["rules_errored"], 1)
        # Errored rule = treated as non-match = no resolution entry
        self.assertNotIn("option_b", result["options"])

    # ------------------------------------------------------------------------
    # Precedence resolution
    # ------------------------------------------------------------------------

    def test_require_dominates_show(self):
        session = self._create_session()
        self._create_rule("show_it", "show", "option_c", sequence=10)
        self._create_rule("require_it", "require", "option_c", sequence=20)
        result = session.run_cascade()
        self.assertEqual(result["options"]["option_c"]["state"], "require")
        self.assertEqual(result["options"]["option_c"]["rule_count"], 2)
        self.assertGreater(result["options"]["option_c"]["precedence_overrides_count"], 0)

    def test_hide_dominates_recommend(self):
        session = self._create_session()
        self._create_rule("recommend_it", "recommend", "option_d", sequence=10)
        self._create_rule("hide_it", "hide", "option_d", sequence=20)
        result = session.run_cascade()
        self.assertEqual(result["options"]["option_d"]["state"], "hide")

    def test_require_dominates_hide(self):
        """Require wins even over hide (most important: surface the option)."""
        session = self._create_session()
        self._create_rule("hide_it", "hide", "option_e", sequence=10)
        self._create_rule("require_it", "require", "option_e", sequence=20)
        result = session.run_cascade()
        self.assertEqual(result["options"]["option_e"]["state"], "require")

    def test_precedence_independent_of_rule_order(self):
        """Resolution should depend on action precedence, not rule sequence."""
        s1 = self._create_session()
        # Order A: show first, then require
        self._create_rule("a1_show", "show", "opt", sequence=10)
        self._create_rule("a1_require", "require", "opt", sequence=20)
        r1 = s1.run_cascade()

        s2 = self._create_session()
        # Order B: require first, then show — same blueprint different session
        # (different rules to keep test isolated)
        self._create_rule("a2_require", "require", "opt2", sequence=10)
        self._create_rule("a2_show", "show", "opt2", sequence=20)
        r2 = s2.run_cascade()

        self.assertEqual(r1["options"]["opt"]["state"], "require")
        self.assertEqual(r2["options"]["opt2"]["state"], "require")

    # ------------------------------------------------------------------------
    # selected_options_json mutation
    # ------------------------------------------------------------------------

    def test_require_sets_selected_true(self):
        import json

        session = self._create_session()
        self._create_rule("must_have", "require", "must_option")
        session.run_cascade()
        opts = json.loads(session.selected_options_json)
        self.assertTrue(opts["must_option"])

    def test_hide_sets_selected_false(self):
        import json

        session = self._create_session()
        session.selected_options_json = '{"hidden_option": true}'
        self._create_rule("nope", "hide", "hidden_option")
        session.run_cascade()
        opts = json.loads(session.selected_options_json)
        self.assertFalse(opts["hidden_option"])

    def test_recommend_does_not_mutate_selection(self):
        """Recommend is a soft signal — UI shows it, but selection stays user-driven."""
        import json

        session = self._create_session()
        session.selected_options_json = '{"soft_option": false}'
        self._create_rule("suggest", "recommend", "soft_option")
        session.run_cascade()
        opts = json.loads(session.selected_options_json)
        # Selection unchanged
        self.assertFalse(opts["soft_option"])
        # But the cascade result marks it recommended
        # (re-query the last cascade by replaying — for the test we check ledger)
        recs = session.ledger_ids.filtered(lambda l: l.entry_type == "recommendation_made")
        self.assertTrue(recs)

    # ------------------------------------------------------------------------
    # Audit trail
    # ------------------------------------------------------------------------

    def test_every_rule_evaluation_logged(self):
        session = self._create_session()
        self._create_rule("r1", "show", "opt1", domain="[]")  # matches
        self._create_rule("r2", "hide", "opt2", domain="[('id', '=', -1)]")  # doesn't match
        session.run_cascade()
        evaluated = session.ledger_ids.filtered(lambda l: l.entry_type == "rule_evaluated")
        self.assertEqual(len(evaluated), 2)

    def test_resolution_logged_per_option(self):
        session = self._create_session()
        self._create_rule("show_a", "show", "opt_a")
        self._create_rule("hide_b", "hide", "opt_b")
        session.run_cascade()
        option_entries = session.ledger_ids.filtered(
            lambda l: (
                l.entry_type
                in ("option_shown", "option_hidden", "option_selected", "recommendation_made")
            )
        )
        self.assertEqual(len(option_entries), 2)

    # ------------------------------------------------------------------------
    # Idempotency
    # ------------------------------------------------------------------------

    def test_cascade_is_idempotent_on_state(self):
        """Re-running cascade produces the same final selected_options_json."""
        session = self._create_session()
        self._create_rule("req", "require", "must")
        self._create_rule("hid", "hide", "no")
        session.run_cascade()
        after_first = session.selected_options_json
        session.run_cascade()
        after_second = session.selected_options_json
        self.assertEqual(after_first, after_second)

    def test_cascade_re_run_appends_ledger_entries(self):
        """The ledger is append-only — second run = more entries, not replaced ones."""
        session = self._create_session()
        self._create_rule("r1", "show", "opt")
        session.run_cascade()
        first_count = len(session.ledger_ids)
        session.run_cascade()
        second_count = len(session.ledger_ids)
        self.assertGreater(second_count, first_count)
