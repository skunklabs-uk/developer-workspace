"""Contract tests: real state/filesystem, fake external GitHub and Codex boundaries."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'scripts' / 'workspace_handoff.py'


def load(test):
    test.assertTrue(SOURCE.exists(), 'The handoff implementation is missing')
    spec = importlib.util.spec_from_file_location('workspace_handoff', SOURCE)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


class GitHubFake:
    """Faults occur at the external boundary; durable state uses real files."""
    def __init__(self):
        self.comments = []
        self.posts = 0
        self.patches = 0
        self.lose_post = False
        self.lose_patch = False
        self.hide_post = False

    def list_comments(self):
        return copy.deepcopy(self.comments)

    def create_comment(self, body):
        self.posts += 1
        item = {'id': 1000 + self.posts, 'body': body, 'user': {'id': 7},
                'created_at': '2026-09-06T01:00:00Z',
                'updated_at': '2026-09-06T01:00:00Z'}
        if not self.hide_post:
            self.comments.append(item)
        if self.lose_post:
            self.lose_post = False
            raise TimeoutError('POST response lost')
        return copy.deepcopy(item)

    def update_comment(self, comment_id, body):
        self.patches += 1
        for item in self.comments:
            if item['id'] == comment_id:
                item['body'] = body
                if self.lose_patch:
                    self.lose_patch = False
                    raise TimeoutError('PATCH response lost')
                return copy.deepcopy(item)
        raise RuntimeError('comment missing')


class RunnerFake:
    def __init__(self):
        self.calls = 0
        self.crash = False
        self.reject = False
        self.on_run = None

    def __call__(self, request, run_dir):
        self.calls += 1
        if self.on_run:
            self.on_run()
        if self.crash:
            raise KeyboardInterrupt('simulated process interruption')
        if self.reject:
            raise ValueError('head is no longer current')
        return {'exit_code': 0, 'summary': 'Verifica locale completata.',
                'head': request['head'], 'dirty': False}


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.m = load(self)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.api = GitHubFake()
        self.runner = RunnerFake()
        self.config = {'repository': 'skunklabs-uk/iwant', 'thread': 42,
                       'actor_ids': [7], 'publisher_id': 7}
        self.consumer = self.m.Consumer(self.root, self.config, self.api, self.runner)
        self.consumer.enroll()

    def request(self, cid=1, assignment='POC', generation=1, **changes):
        data = {'repository': 'skunklabs-uk/iwant', 'assignment': assignment,
                'generation': generation, 'branch': 'agent/poc',
                'head': 'a' * 40, 'prompt': 'docs/agents/prompts/poc-g1.md'}
        data.update(changes)
        return {'id': cid, 'body': '/workspace run\n' + json.dumps(data),
                'user': {'id': 7}, 'created_at': '2026-09-06T01:00:00Z',
                'updated_at': '2026-09-06T01:00:00Z'}

    def restart(self):
        self.consumer = self.m.Consumer(self.root, self.config, self.api, self.runner)

    def test_one_request_delivers_result_in_same_receipt_comment(self):
        self.api.comments.append(self.request())
        self.consumer.tick()
        self.assertEqual(self.runner.calls, 1)
        self.assertEqual(self.api.posts, 1)
        self.assertEqual(self.api.patches, 1)
        self.assertIn('Verifica locale completata.', self.api.comments[-1]['body'])
        self.assertIn('a' * 40, self.api.comments[-1]['body'])
        self.assertEqual(len(list(self.root.glob('runs/*/result.json'))), 1)

    def test_reposted_same_assignment_does_not_execute_again_after_restart(self):
        self.api.comments.append(self.request())
        self.consumer.tick()
        self.api.comments.append(self.request(2))
        self.restart()
        self.consumer.tick()
        self.assertEqual(self.runner.calls, 1)
        self.assertEqual(self.api.posts, 1)

    def test_same_assignment_with_changed_head_is_a_conflict(self):
        self.api.comments.append(self.request())
        self.consumer.tick()
        self.api.comments.append(self.request(2000, head='b' * 40))
        self.restart()
        with self.assertRaises(self.m.HandoffError):
            self.consumer.tick()
        self.assertEqual(self.runner.calls, 1)

    def test_new_generation_is_a_new_explicit_iteration(self):
        self.api.comments.append(self.request())
        self.consumer.tick()
        self.api.comments.append(self.request(2000, generation=2, head='b' * 40))
        self.consumer.tick()
        self.assertEqual(self.runner.calls, 2)

    def test_enrollment_does_not_reactivate_history(self):
        other = self.root / 'second'
        self.api.comments.append(self.request())
        consumer = self.m.Consumer(other, self.config, self.api, self.runner)
        consumer.enroll()
        consumer.tick()
        self.assertEqual(self.runner.calls, 0)

    def test_unauthorized_and_edited_commands_do_not_execute(self):
        bad = self.request()
        bad['user']['id'] = 999
        edited = self.request(2)
        edited['updated_at'] = '2026-09-06T02:00:00Z'
        self.api.comments.extend([bad, edited])
        self.consumer.tick()
        self.assertEqual(self.runner.calls, 0)
        self.assertEqual(self.api.posts, 0)

    def test_archive_traversal_and_command_options_are_rejected(self):
        for changes in ({'prompt': 'docs/agents/prompts/archive/old.md'},
                        {'prompt': 'docs/agents/prompts/../../secret.md'},
                        {'branch': '--upload-pack=evil'},
                        {'repository': 'other/repo'}, {'generation': True},
                        {'head': 'main'}):
            with self.subTest(changes=changes):
                with self.assertRaises(self.m.HandoffError):
                    self.m.parse_request(self.request(**changes), self.config)

    def test_running_state_is_persisted_before_calling_executor(self):
        def inspect():
            state = json.loads((self.root / 'state.json').read_text())
            self.assertEqual(next(iter(state['jobs'].values()))['phase'], 'running')
        self.runner.on_run = inspect
        self.api.comments.append(self.request())
        self.consumer.tick()

    def test_restart_after_crash_never_reruns_and_blocks_new_work(self):
        self.runner.crash = True
        self.api.comments.append(self.request())
        with self.assertRaises(KeyboardInterrupt):
            self.consumer.tick()
        self.runner.crash = False
        self.restart()
        self.api.comments.append(self.request(2000, generation=2))
        with self.assertRaises(self.m.HandoffError):
            self.consumer.tick()
        self.assertEqual(self.runner.calls, 1)

    def test_persisted_result_is_recovered_without_reexecution(self):
        self.runner.crash = True
        self.api.comments.append(self.request())
        with self.assertRaises(KeyboardInterrupt):
            self.consumer.tick()
        run_dir = next((self.root / 'runs').iterdir())
        self.m.atomic_json(run_dir / 'result.json', {'exit_code': 0,
            'summary': 'Persistito prima del crash.', 'head': 'a' * 40, 'dirty': False})
        self.restart()
        self.consumer.tick()
        self.assertEqual(self.runner.calls, 1)
        self.assertIn('Persistito prima del crash.', self.api.comments[-1]['body'])

    def test_uncertain_post_is_reconciled_before_execution(self):
        self.api.lose_post = True
        self.api.comments.append(self.request())
        with self.assertRaises(TimeoutError):
            self.consumer.tick()
        self.assertEqual(self.runner.calls, 0)
        self.restart()
        self.consumer.tick()
        self.assertEqual(self.api.posts, 1)
        self.assertEqual(self.runner.calls, 1)

    def test_missing_uncertain_receipt_never_creates_another_post(self):
        self.api.lose_post = self.api.hide_post = True
        self.api.comments.append(self.request())
        with self.assertRaises(TimeoutError):
            self.consumer.tick()
        self.restart()
        with self.assertRaises(self.m.HandoffError):
            self.consumer.tick()
        self.assertEqual(self.api.posts, 1)
        self.assertEqual(self.runner.calls, 0)

    def test_patch_retry_only_redelivers_same_durable_report(self):
        self.api.lose_patch = True
        self.api.comments.append(self.request())
        with self.assertRaises(TimeoutError):
            self.consumer.tick()
        self.restart()
        self.consumer.tick()
        self.assertEqual(self.runner.calls, 1)
        self.assertEqual(self.api.posts, 1)
        self.assertEqual(self.api.patches, 2)

    def test_failure_is_reported_not_claimed_as_success(self):
        self.runner.reject = True
        self.api.comments.append(self.request())
        self.consumer.tick()
        self.assertIn('fallita', self.api.comments[-1]['body'])
        self.assertNotIn('Verifica locale completata', self.api.comments[-1]['body'])
        self.restart()
        self.consumer.tick()
        self.assertEqual(self.runner.calls, 1)

    def test_state_cannot_be_rebound_to_another_thread(self):
        changed = dict(self.config, thread=99)
        consumer = self.m.Consumer(self.root, changed, self.api, self.runner)
        with self.assertRaises(self.m.HandoffError):
            consumer.tick()


    def test_preflight_transport_failure_does_not_consume_the_execution(self):
        def unavailable():
            raise TimeoutError('canonical source unavailable')
        self.runner.prepare = unavailable
        self.api.comments.append(self.request())
        with self.assertRaises(TimeoutError):
            self.consumer.tick()
        self.assertEqual(self.runner.calls, 0)
        self.runner.prepare = lambda: None
        self.restart()
        self.consumer.tick()
        self.assertEqual(self.runner.calls, 1)
        self.assertEqual(self.api.posts, 1)

    def test_definitive_post_rejection_can_retry_without_uncertain_delivery(self):
        class Rejected(RuntimeError):
            write_rejected = True
        original = self.api.create_comment
        self.api.comments.append(self.request())
        self.api.create_comment = lambda body: (_ for _ in ()).throw(Rejected())
        with self.assertRaises(Rejected):
            self.consumer.tick()
        self.api.create_comment = original
        self.restart()
        self.consumer.tick()
        self.assertEqual(self.runner.calls, 1)
        self.assertEqual(self.api.posts, 1)

    def test_command_edited_while_receipt_is_pending_never_executes(self):
        self.api.lose_post = True
        self.api.comments.append(self.request())
        with self.assertRaises(TimeoutError):
            self.consumer.tick()
        self.api.comments[0]['updated_at'] = '2026-09-06T02:00:00Z'
        self.restart()
        with self.assertRaises(self.m.HandoffError):
            self.consumer.tick()
        self.assertEqual(self.runner.calls, 0)

    def test_interrupted_execution_is_reported_without_claiming_completion(self):
        self.runner.crash = True
        self.api.comments.append(self.request())
        with self.assertRaises(KeyboardInterrupt):
            self.consumer.tick()
        self.restart()
        with self.assertRaises(self.m.HandoffError):
            self.consumer.tick()
        self.assertIn('Esito non determinato', self.api.comments[-1]['body'])
        patches = self.api.patches
        with self.assertRaises(self.m.HandoffError):
            self.consumer.tick()
        self.assertEqual(self.api.patches, patches)
        self.assertEqual(self.runner.calls, 1)

    def test_malformed_request_does_not_starve_later_valid_work(self):
        bad = self.request()
        bad['body'] = '/workspace run\nnot JSON'
        self.api.comments.extend([bad, self.request(2)])
        self.consumer.tick()
        self.assertEqual(self.runner.calls, 1)
        state = json.loads((self.root / 'state.json').read_text())
        self.assertEqual(state['last_rejection']['comment_id'], 1)

    def test_second_instance_cannot_execute_while_first_holds_lock(self):
        with self.consumer.locked():
            with self.assertRaises(self.m.HandoffError):
                with self.m.Consumer(self.root, self.config, self.api, self.runner).locked():
                    self.fail('Second writer entered')


if __name__ == '__main__':
    unittest.main()
