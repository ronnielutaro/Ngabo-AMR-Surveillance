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
        self.assertTrue(
            rules["required_status_checks"]["parameters"][
                "strict_required_status_checks_policy"
            ]
        )
        self.assertTrue(
            rules["pull_request"]["parameters"]["required_review_thread_resolution"]
        )
        self.assertEqual(
            rules["pull_request"]["parameters"]["required_approving_review_count"], 0
        )
        self.assertIn("non_fast_forward", rules)

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


if __name__ == "__main__":
    unittest.main()
