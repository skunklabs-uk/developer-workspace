"""Observable contract tests for the stable GitHub handoff inbox."""
import copy
import json
from pathlib import Path
import runpy
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))

import workspace_handoff as handoff
import workspace_handoff_io as io


class InboxAPI:
    def __init__(self, publisher_id=7):
        self.publisher_id = publisher_id
        self.inbox = []
        self.targets = {}
        self.posts = 0
        self.patches = 0
        self.lose_post = False

    def list_comments(self, repository=None, thread=None):
        if repository is None:
            return copy.deepcopy(self.inbox)
        return copy.deepcopy(self.targets.get((repository, thread), []))

    def create_comment(self, body, repository=None, thread=None):
        self.posts += 1
        item = {
            'id': 1000 + self.posts,
            'body': body,
            'user': {'id': self.publisher_id},
            'created_at': '2026-09-18T12:00:00Z',
            'updated_at': '2026-09-18T12:00:00Z',
        }
        self.targets.setdefault((repository, thread), []).append(item)
        if self.lose_post:
            self.lose_post = False
            raise TimeoutError('POST response lost')
        return copy.deepcopy(item)

    def update_comment(self, comment_id, body, repository=None):
        self.patches += 1
        for (repo, _), comments in self.targets.items():
            if repo != repository:
                continue
            for item in comments:
                if item['id'] == comment_id:
                    item['body'] = body
                    return copy.deepcopy(item)
        raise RuntimeError('target comment missing')


class Runner:
    def __init__(self):
        self.calls = 0

    def __call__(self, request, run_dir):
        self.calls += 1
        return {
            'exit_code': 0,
            'summary': 'Target verificato.',
            'head': request['head'],
            'dirty': False,
        }


class StableInboxTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.api = InboxAPI()
        self.runner = Runner()
        self.config = {
            'repository': 'skunklabs-uk/developer-workspace',
            'thread': 107,
            'actor_ids': [7],
            'publisher_id': 7,
            'allowed_repositories': ['skunklabs-uk/iwant', 'skunklabs-uk/skunklabs'],
        }
        self.consumer = handoff.Consumer(self.root, self.config, self.api, self.runner)
        self.consumer.enroll()

    def request(self, cid=1, repository='skunklabs-uk/iwant', thread=603,
                assignment='TASK', generation=1):
        value = {
            'repository': repository,
            'thread': thread,
            'assignment': assignment,
            'generation': generation,
            'branch': 'agent/task',
            'head': 'a' * 40,
            'prompt': 'docs/agents/prompts/task.md',
        }
        return {
            'id': cid,
            'body': '/workspace run\n' + json.dumps(value),
            'user': {'id': 7},
            'created_at': '2026-09-18T12:00:00Z',
            'updated_at': '2026-09-18T12:00:00Z',
        }

    def test_inbox_routes_receipt_and_result_only_to_authoritative_target(self):
        self.api.inbox.append(self.request())
        self.consumer.tick()
        target = self.api.targets[('skunklabs-uk/iwant', 603)]
        self.assertEqual(self.runner.calls, 1)
        self.assertEqual(len(target), 1)
        self.assertIn('## Risultato workspace', target[0]['body'])
        self.assertIn('Thread: `603`', target[0]['body'])
        self.assertNotIn('workspace-handoff:', self.api.inbox[0]['body'])

    def test_repository_allowlist_and_target_thread_are_fail_closed(self):
        for changes in (
            {'repository': 'skunklabs-uk/other', 'thread': 1},
            {'repository': 'skunklabs-uk/iwant', 'thread': 0},
            {'repository': 'skunklabs-uk/developer-workspace', 'thread': 107},
        ):
            value = self.request()
            data = json.loads(value['body'].split('\n', 1)[1])
            data.update(changes)
            value['body'] = '/workspace run\n' + json.dumps(data)
            with self.subTest(changes=changes), self.assertRaises(handoff.HandoffError):
                handoff.parse_request(value, self.config)

        value = self.request()
        data = json.loads(value['body'].split('\n', 1)[1])
        data.pop('thread')
        value['body'] = '/workspace run\n' + json.dumps(data)
        with self.assertRaises(handoff.HandoffError):
            handoff.parse_request(value, self.config)

    def test_same_assignment_generation_on_two_target_threads_are_independent(self):
        self.api.inbox.extend([self.request(1, thread=603), self.request(2, thread=604)])
        self.consumer.tick()
        self.consumer.tick()
        self.assertEqual(self.runner.calls, 2)
        self.assertEqual(len(self.api.targets[('skunklabs-uk/iwant', 603)]), 1)
        self.assertEqual(len(self.api.targets[('skunklabs-uk/iwant', 604)]), 1)

    def test_lost_target_receipt_is_reconciled_without_second_post_or_rerun(self):
        self.api.inbox.append(self.request())
        self.api.lose_post = True
        with self.assertRaises(TimeoutError):
            self.consumer.tick()
        restarted = handoff.Consumer(self.root, self.config, self.api, self.runner)
        restarted.tick()
        self.assertEqual(self.api.posts, 1)
        self.assertEqual(self.runner.calls, 1)
        self.assertEqual(self.api.patches, 1)


class InboxConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.configuration = runpy.run_path(str(SCRIPTS / 'workspace-handoff'))['configuration']

    def config(self, allowed):
        path = self.root / 'config.json'
        path.write_text(json.dumps({
            'repository': 'skunklabs-uk/developer-workspace',
            'thread': 107,
            'actor_ids': [7],
            'publisher_id': 7,
            'allowed_repositories': allowed,
        }))
        return path

    def test_flat_exact_repository_allowlist_is_accepted(self):
        value = self.configuration(self.config(['skunklabs-uk/iwant', 'skunklabs-uk/skunklabs']))
        self.assertEqual(value['allowed_repositories'], ['skunklabs-uk/iwant', 'skunklabs-uk/skunklabs'])

    def test_wildcards_duplicates_and_foreign_repositories_are_rejected(self):
        for allowed in (
            ['skunklabs-uk/*'],
            ['other/iwant'],
            ['skunklabs-uk/iwant', 'skunklabs-uk/iwant'],
            [],
        ):
            with self.subTest(allowed=allowed), self.assertRaises(handoff.HandoffError):
                self.configuration(self.config(allowed))


class PublicationTargetTests(unittest.TestCase):
    def test_publication_uses_target_pr_not_inbox_thread(self):
        base = 'a' * 40
        request = {
            'repository': 'skunklabs-uk/iwant',
            'thread': 603,
            'assignment': 'TASK',
            'generation': 1,
            'branch': 'agent/task',
            'head': base,
            'prompt': 'docs/agents/prompts/task.md',
            'publish_paths': ['item.txt'],
        }
        endpoints = []

        class API:
            def request(self, method, endpoint):
                endpoints.append(endpoint)
                if endpoint == 'repos/skunklabs-uk/iwant':
                    return 200, {}, {'default_branch': 'main'}
                if endpoint == 'repos/skunklabs-uk/iwant/pulls/603':
                    return 200, {}, {
                        'state': 'open',
                        'draft': True,
                        'head': {
                            'ref': 'agent/task',
                            'sha': base,
                            'repo': {'full_name': 'skunklabs-uk/iwant'},
                        },
                    }
                raise AssertionError(endpoint)

        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory)
            (run_dir / 'checkout').mkdir()
            runner = io.LocalCodex(
                {'sandbox': 'workspace-write', 'thread': 107}, API())
            result = {'exit_code': 0, 'summary': 'unchanged', 'head': base, 'dirty': False}
            with patch('workspace_handoff_publish.snapshot_commit', return_value=base):
                result = runner.publish(request, run_dir, result)
        self.assertEqual(result['publication']['state'], 'unchanged')
        self.assertIn('repos/skunklabs-uk/iwant/pulls/603', endpoints)
        self.assertNotIn('repos/skunklabs-uk/iwant/pulls/107', endpoints)


if __name__ == '__main__':
    unittest.main()
