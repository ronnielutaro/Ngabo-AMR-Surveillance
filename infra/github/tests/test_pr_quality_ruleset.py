import copy
import json
import pathlib
import sys
import unittest

MODULE_DIR = pathlib.Path(__file__).parents[1]
sys.path.insert(0, str(MODULE_DIR))
import pr_quality_ruleset  # noqa: E402


class FakeRunner:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, args, input_text=None):
        self.calls.append((list(args), input_text))
        return self.responses.pop(0)


def result(payload, code=0):
    return pr_quality_ruleset.CommandResult(code, json.dumps(payload), "")


class RulesetTests(unittest.TestCase):
    def test_desired_contract(self):
        desired = pr_quality_ruleset.desired_ruleset(15368)
        self.assertEqual(
            desired["conditions"]["ref_name"]["include"],
            ["refs/heads/develop", "refs/heads/main"],
        )
        rules = {rule["type"]: rule for rule in desired["rules"]}
        self.assertEqual(
            rules["pull_request"]["parameters"]["allowed_merge_methods"], ["merge"]
        )
        self.assertTrue(
            rules["required_status_checks"]["parameters"][
                "strict_required_status_checks_policy"
            ]
        )
        checks = rules["required_status_checks"]["parameters"]["required_status_checks"]
        self.assertEqual(
            checks,
            [
                {"context": "PR Quality Gate", "integration_id": 15368},
                {"context": "CI Control Plane", "integration_id": 15368},
            ],
        )
        self.assertTrue(
            rules["pull_request"]["parameters"]["required_review_thread_resolution"]
        )
        self.assertEqual(
            rules["pull_request"]["parameters"]["required_approving_review_count"], 0
        )
        self.assertIn("non_fast_forward", rules)
        self.assertEqual(desired["bypass_actors"], [])

    def test_verify_check_run_integration_success(self):
        payload = {
            "check_runs": [
                {"name": "PR Quality Gate", "app": {"slug": "github-actions", "id": 15368}}
            ]
        }
        runner = FakeRunner([result(payload)])
        app_id = pr_quality_ruleset.verify_check_run_integration(
            "owner/repo", "sha123", runner=runner
        )
        self.assertEqual(app_id, 15368)

    def test_verify_check_run_integration_mismatch_fails(self):
        payload = {
            "check_runs": [
                {"name": "PR Quality Gate", "app": {"slug": "other-app", "id": 99999}}
            ]
        }
        runner = FakeRunner([result(payload)])
        with self.assertRaisesRegex(RuntimeError, "CHECK_INTEGRATION_MISMATCH"):
            pr_quality_ruleset.verify_check_run_integration(
                "owner/repo", "sha123", runner=runner
            )

    def test_verify_check_run_not_found_fails(self):
        payload = {"check_runs": []}
        runner = FakeRunner([result(payload)])
        with self.assertRaisesRegex(RuntimeError, "CHECK_RUN_NOT_FOUND"):
            pr_quality_ruleset.verify_check_run_integration(
                "owner/repo", "sha123", runner=runner
            )

    def test_absent_ruleset_plans_create(self):
        runner = FakeRunner([result([])])
        manager = pr_quality_ruleset.RulesetManager("owner/repo", runner=runner)
        plan = manager.plan()
        self.assertEqual(plan["action"], "CREATE")

    def test_converged_ruleset_plans_none(self):
        desired = pr_quality_ruleset.desired_ruleset()
        summary = {"id": 42, "name": pr_quality_ruleset.RULESET_NAME}
        detail = {"id": 42, **desired}
        runner = FakeRunner([result([summary]), result(detail)])
        manager = pr_quality_ruleset.RulesetManager("owner/repo", runner=runner)
        self.assertEqual(manager.plan()["action"], "NONE")

    def test_drift_plans_update(self):
        desired = pr_quality_ruleset.desired_ruleset()
        summary = {"id": 42, "name": pr_quality_ruleset.RULESET_NAME}
        detail = {"id": 42, **desired, "enforcement": "evaluate"}
        runner = FakeRunner([result([summary]), result(detail)])
        manager = pr_quality_ruleset.RulesetManager("owner/repo", runner=runner)
        self.assertEqual(manager.plan()["action"], "UPDATE")

    def test_apply_streams_json_and_post_validates(self):
        desired = pr_quality_ruleset.desired_ruleset()
        summary = {"id": 42, "name": pr_quality_ruleset.RULESET_NAME}
        drifted = {"id": 42, **desired, "enforcement": "evaluate"}
        converged = {"id": 42, **desired}
        runner = FakeRunner(
            [
                result([summary]),
                result(drifted),
                result({"id": 42}),
                result([summary]),
                result(converged),
            ]
        )
        manager = pr_quality_ruleset.RulesetManager("owner/repo", runner=runner)
        outcome = manager.apply()
        self.assertTrue(outcome["success"])
        mutation = runner.calls[2]
        self.assertIn("--input", mutation[0])
        self.assertEqual(json.loads(mutation[1]), desired)

    def test_inspection_failure_fails_closed(self):
        runner = FakeRunner(
            [pr_quality_ruleset.CommandResult(1, "", "permission denied")]
        )
        manager = pr_quality_ruleset.RulesetManager("owner/repo", runner=runner)
        with self.assertRaisesRegex(RuntimeError, "INSPECTION_FAILED"):
            manager.plan()

    def test_invalid_json_fails_closed(self):
        runner = FakeRunner([pr_quality_ruleset.CommandResult(0, "not json", "")])
        manager = pr_quality_ruleset.RulesetManager("owner/repo", runner=runner)
        with self.assertRaisesRegex(RuntimeError, "INSPECTION_FAILED"):
            manager.plan()

    def test_unknown_github_populated_params_do_not_break_validation(self):
        # GitHub may echo server-populated pull_request parameters that the
        # desired payload never declared; validation must compare only the
        # governed subset and still report convergence.
        desired = pr_quality_ruleset.desired_ruleset()
        summary = {"id": 42, "name": pr_quality_ruleset.RULESET_NAME}
        detail = {"id": 42, **copy.deepcopy(desired)}
        detail["rules"][0]["parameters"]["some_future_github_field"] = "x"
        runner = FakeRunner([result([summary]), result(detail)])
        manager = pr_quality_ruleset.RulesetManager("owner/repo", runner=runner)
        self.assertEqual(manager.plan()["action"], "NONE")

    def test_github_default_unattributed_approval_is_pinned_and_drifts_to_update(self):
        # The live GitHub API defaults require_extra_approval_for_unattributed_changes
        # to true when omitted; the contract pins it to false, so an observed
        # ruleset carrying the server default must be reported as drift (UPDATE).
        desired = pr_quality_ruleset.desired_ruleset()
        summary = {"id": 42, "name": pr_quality_ruleset.RULESET_NAME}
        detail = {"id": 42, **copy.deepcopy(desired)}
        detail["rules"][0]["parameters"][
            "require_extra_approval_for_unattributed_changes"
        ] = True
        runner = FakeRunner([result([summary]), result(detail)])
        manager = pr_quality_ruleset.RulesetManager("owner/repo", runner=runner)
        plan = manager.plan()
        self.assertEqual(plan["action"], "UPDATE")
        self.assertEqual(plan["ruleset_id"], 42)

    def test_desired_contract_pins_github_managed_defaults(self):
        desired = pr_quality_ruleset.desired_ruleset()
        pull_params = desired["rules"][0]["parameters"]
        self.assertFalse(pull_params["require_extra_approval_for_unattributed_changes"])
        self.assertEqual(pull_params["required_reviewers"], [])

    def test_teardown_rehearsal(self):
        desired = pr_quality_ruleset.desired_ruleset()
        summary = {"id": 42, "name": pr_quality_ruleset.RULESET_NAME}
        detail = {"id": 42, **desired}
        runner = FakeRunner([result([summary]), result(detail)])
        manager = pr_quality_ruleset.RulesetManager("owner/repo", runner=runner)
        outcome = manager.teardown_rehearsal()
        self.assertEqual(outcome["teardown_mode"], "PLAN_ONLY")
        self.assertFalse(outcome["destructive_actions_executed"])
        self.assertTrue(outcome["ruleset_present"])



if __name__ == "__main__":
    unittest.main()
