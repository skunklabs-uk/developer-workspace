"""Behavioral regressions for #79; real local Git, mocked external HTTP only."""
import base64
import importlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import workspace_handoff_io as io
from workspace_handoff import HandoffError, parse_request


def response(status, body):
    return subprocess.CompletedProcess([], 0 if status < 400 else 1,
        f'HTTP/2.0 {status} status\n\n' + json.dumps(body), '')


class ReferenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.api = io.GitHub({'repository': 'skunklabs-uk/iwant', 'thread': 1}, self.tmp.name)
        self.rfc = {'encoding': 'base64', 'content': base64.b64encode(
            b'Current authoritative RFC').decode(), 'sha': 'a' * 40}

    def test_preflight_works_after_execution_skill_is_retired(self):
        def upstream(args, **kwargs):
            endpoint = next(x for x in args if x.startswith('repos/'))
            if endpoint == 'repos/skunklabs-uk/agent-os/contents/rfcs/RFC-0001-principles.md?ref=main':
                return response(200, self.rfc)
            return response(404, {'message': 'Retired skill'})
        runner = io.LocalCodex({}, self.api)
        with patch.object(io.subprocess, 'run', side_effect=upstream):
            try:
                runner.prepare()
            except HandoffError as error:
                self.fail(f'A retired optional skill still prevents preflight: {error}')
        self.assertIn('Current authoritative RFC', runner.references)
        self.assertIn('a' * 40, runner.references)
        self.assertEqual(self.api.metrics['requests'], 1)

    def test_missing_rfc_still_blocks_preflight(self):
        with patch.object(io.subprocess, 'run', return_value=response(404, {})):
            with self.assertRaises(HandoffError):
                io.LocalCodex({}, self.api).prepare()

    def test_rfc_without_identifiable_revision_is_rejected(self):
        body = dict(self.rfc, sha='unknown')
        with patch.object(io.subprocess, 'run', return_value=response(200, body)):
            with self.assertRaises(HandoffError):
                io.LocalCodex({}, self.api).prepare()


class PublicationTests(unittest.TestCase):
    def setUp(self):
        source = Path(__file__).resolve().parents[1] / 'scripts/workspace_handoff_publish.py'
        self.assertTrue(source.exists(), 'Publication is not implemented')
        self.m = importlib.import_module('workspace_handoff_publish')
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.origin = self.root / 'origin.git'
        self.repo = self.root / 'work'
        self.git(None, 'init', '--bare', str(self.origin))
        self.git(None, 'init', '-b', 'agent/task', str(self.repo))
        self.git(self.repo, 'config', 'user.name', 'Fixture')
        self.git(self.repo, 'config', 'user.email', 'fixture@example.invalid')
        (self.repo / 'item.txt').write_text('before\n')
        (self.repo / 'keep.txt').write_text('untouched\n')
        self.git(self.repo, 'add', '.')
        self.git(self.repo, 'commit', '-m', 'fixture')
        self.base = self.git(self.repo, 'rev-parse', 'HEAD')
        self.git(self.repo, 'remote', 'add', 'origin', str(self.origin))
        self.git(self.repo, 'push', 'origin', 'agent/task')

    def git(self, directory, *args):
        cmd = ['git'] + (['-C', str(directory)] if directory else []) + list(args)
        return subprocess.check_output(cmd, text=True, stderr=subprocess.PIPE).strip()

    def snapshot(self, paths=None):
        return self.m.snapshot_commit(self.repo, self.base, paths or ['item.txt'], 'chore: test')

    def push(self, head):
        return self.m.push_commit(self.repo, str(self.origin), 'agent/task', self.base, head)

    def test_snapshot_contains_change_without_touching_head_or_index(self):
        old_index = (self.repo / '.git/index').read_bytes()
        (self.repo / 'item.txt').write_text('after\n')
        head = self.snapshot()
        self.assertEqual(self.git(self.repo, 'show', head + ':item.txt'), 'after')
        self.assertEqual(self.git(self.repo, 'show', head + ':keep.txt'), 'untouched')
        self.assertEqual(self.git(self.repo, 'rev-parse', head + '^'), self.base)
        self.assertEqual(self.git(self.repo, 'rev-parse', 'HEAD'), self.base)
        self.assertEqual((self.repo / '.git/index').read_bytes(), old_index)
        self.assertEqual((self.repo / 'item.txt').read_text(), 'after\n')

    def test_snapshot_preserves_bytes_with_operator_autocrlf_enabled(self):
        self.git(self.repo, 'config', 'core.autocrlf', 'true')
        content = b'after\r\n'
        (self.repo / 'item.txt').write_bytes(content)
        head = self.snapshot()
        actual = subprocess.check_output(['git', '-C', str(self.repo), 'show', head + ':item.txt'])
        self.assertEqual(actual, content)

    def test_no_change_returns_original_revision(self):
        self.assertEqual(self.snapshot(), self.base)

    def test_addition_and_deletion_are_preserved(self):
        (self.repo / 'item.txt').unlink()
        (self.repo / 'new.txt').write_text('new\n')
        head = self.snapshot(['item.txt', 'new.txt'])
        files = self.git(self.repo, 'ls-tree', '--name-only', head).splitlines()
        self.assertNotIn('item.txt', files)
        self.assertIn('new.txt', files)
        self.assertEqual(self.git(self.repo, 'show', head + ':new.txt'), 'new')

    def test_executable_mode_is_preserved(self):
        (self.repo / 'item.txt').chmod(0o755)
        head = self.snapshot()
        self.assertTrue(self.git(self.repo, 'ls-tree', head, 'item.txt').startswith('100755 '))

    def test_unapproved_tracked_or_untracked_files_are_not_published(self):
        for filename in ('keep.txt', 'secret.txt'):
            with self.subTest(filename=filename):
                path = self.repo / filename
                before = path.read_bytes() if path.exists() else None
                path.write_text('not authorized\n')
                with self.assertRaises(HandoffError):
                    self.snapshot()
                if before is None:
                    path.unlink()
                else:
                    path.write_bytes(before)
        self.assertEqual(self.git(self.origin, 'rev-parse', 'refs/heads/agent/task'), self.base)

    def test_symlink_output_cannot_export_file_outside_checkout(self):
        secret = self.root / 'secret'
        secret.write_text('not a real secret\n')
        (self.repo / 'item.txt').unlink()
        (self.repo / 'item.txt').symlink_to(secret)
        with self.assertRaises(HandoffError):
            self.snapshot()

    def test_wrong_base_is_rejected(self):
        (self.repo / 'item.txt').write_text('after\n')
        with self.assertRaises(HandoffError):
            self.m.snapshot_commit(self.repo, '0' * 40, ['item.txt'], 'test')

    def test_filters_and_hooks_are_not_executed_by_snapshot(self):
        marker = self.root / 'executed'
        (self.repo / '.gitattributes').write_text('item.txt filter=unsafe\n')
        self.git(self.repo, 'add', '.gitattributes')
        self.git(self.repo, 'commit', '-m', 'fixture attributes')
        self.base = self.git(self.repo, 'rev-parse', 'HEAD')
        self.git(self.repo, 'config', 'filter.unsafe.clean', f'touch {marker}; cat')
        self.git(self.repo, 'config', 'core.fsmonitor', f'touch {marker}')
        hook = self.repo / '.git/hooks/pre-commit'
        hook.write_text(f'#!/bin/sh\ntouch {marker}\n')
        hook.chmod(0o755)
        (self.repo / 'item.txt').write_text('after\n')
        head = self.snapshot()
        self.assertFalse(marker.exists())
        self.assertEqual(self.git(self.repo, 'show', head + ':item.txt'), 'after')

    def test_publish_moves_only_selected_branch(self):
        (self.repo / 'item.txt').write_text('after\n')
        head = self.snapshot()
        self.assertEqual(self.push(head), head)
        self.assertEqual(self.git(self.origin, 'rev-parse', 'refs/heads/agent/task'), head)
        self.assertEqual(self.git(self.origin, 'show', head + ':item.txt'), 'after')

    def test_publish_does_not_follow_unrequested_tags(self):
        self.git(self.repo, 'tag', '-a', 'outside-authorized-branch', '-m', 'fixture', self.base)
        self.git(self.repo, 'config', 'push.followTags', 'true')
        (self.repo / 'item.txt').write_text('after\n')
        self.push(self.snapshot())
        refs = self.git(self.origin, 'for-each-ref', '--format=%(refname)').splitlines()
        self.assertEqual(refs, ['refs/heads/agent/task'])

    def test_external_branch_advance_is_never_overwritten(self):
        (self.repo / 'item.txt').write_text('after\n')
        head = self.snapshot()
        (self.repo / 'keep.txt').write_text('external\n')
        self.git(self.repo, 'add', '.')
        self.git(self.repo, 'commit', '-m', 'external writer')
        external = self.git(self.repo, 'rev-parse', 'HEAD')
        self.git(self.repo, 'push', 'origin', 'agent/task')
        with self.assertRaises(HandoffError):
            self.push(head)
        self.assertEqual(self.git(self.origin, 'rev-parse', 'refs/heads/agent/task'), external)

    def test_definitively_rejected_push_is_not_an_automatic_retry(self):
        (self.repo / 'item.txt').write_text('after\n')
        head = self.snapshot()
        real_git = self.m._git
        def rejected(directory, *args, **kwargs):
            if args[0] == 'push':
                raise subprocess.CalledProcessError(1, 'git push', stderr='denied')
            return real_git(directory, *args, **kwargs)
        with patch.object(self.m, '_git', side_effect=rejected):
            with self.assertRaises(HandoffError):
                self.push(head)
        self.assertEqual(self.git(self.origin, 'rev-parse', 'refs/heads/agent/task'), self.base)

    def test_lost_push_response_and_repeated_delivery_do_not_repush(self):
        (self.repo / 'item.txt').write_text('after\n')
        head = self.snapshot()
        real_git = self.m._git
        pushes = []
        def lost_response(directory, *args, **kwargs):
            result = real_git(directory, *args, **kwargs)
            if args and args[0] == 'push':
                pushes.append(args)
                raise subprocess.TimeoutExpired('git push', 180)
            return result
        with patch.object(self.m, '_git', side_effect=lost_response):
            self.assertEqual(self.push(head), head)
            self.assertEqual(self.push(head), head)
        self.assertEqual(len(pushes), 1)

class RequestPublicationTests(unittest.TestCase):
    def request(self, paths, sandbox='workspace-write'):
        value = {'repository': 'skunklabs-uk/iwant', 'assignment': 'TASK', 'generation': 1,
                 'branch': 'agent/task', 'head': 'a' * 40, 'prompt': 'docs/agents/prompts/task.md',
                 'publish_paths': paths}
        comment = {'user': {'id': 1}, 'created_at': 't', 'updated_at': 't',
                   'body': '/workspace run\n' + json.dumps(value)}
        return parse_request(comment, {'actor_ids': [1], 'repository': value['repository'],
                                       'sandbox': sandbox})

    def test_publication_requires_explicit_valid_file_paths(self):
        try:
            request = self.request(['internal/value.go'])
        except HandoffError as error:
            self.fail(f'Authorized publication is unavailable: {error}')
        self.assertEqual(request['publish_paths'], ['internal/value.go'])

    def test_read_only_cannot_request_publication(self):
        with self.assertRaises(HandoffError):
            self.request(['item.txt'], 'read-only')

    def test_unsafe_or_ambiguous_path_lists_are_rejected(self):
        for paths in ([], 'item.txt', ['../secret'], ['/etc/passwd'], ['.git/config'],
                      ['dir//item'], ['./item'], ['item', 'item'], ['x\nname'], ['x\\y']):
            with self.subTest(paths=paths), self.assertRaises(HandoffError):
                self.request(paths)


class PublicationIntegrationTests(unittest.TestCase):
    git = PublicationTests.git

    def setUp(self):
        PublicationTests.setUp(self)
        self.run = self.root / 'attempt'
        self.run.mkdir()
        self.repo = self.repo.rename(self.run / 'checkout')
        self.request = {'repository': 'skunklabs-uk/iwant', 'assignment': 'TASK', 'generation': 1,
            'branch': 'agent/task', 'head': self.base, 'prompt': 'docs/agents/prompts/task.md',
            'publish_paths': ['item.txt']}
        self.pr = {'state': 'open', 'draft': True,
                   'head': {'ref': 'agent/task', 'sha': self.base,
                            'repo': {'full_name': 'skunklabs-uk/iwant'}}}
        test = self
        class API:
            def request(self, method, endpoint):
                test.assertEqual(method, 'GET')
                if endpoint == 'repos/skunklabs-uk/iwant':
                    return 200, {}, {'default_branch': 'main'}
                test.assertEqual(endpoint, 'repos/skunklabs-uk/iwant/pulls/42')
                return 200, {}, test.pr
        self.runner = io.LocalCodex({'sandbox': 'workspace-write', 'thread': 42}, API())
        self.result = {'exit_code': 0, 'summary': 'changed', 'head': self.base, 'dirty': True}
        (self.repo / 'item.txt').write_text('after\n')
        self.assertTrue(hasattr(self.runner, 'publish'), 'Publication is not wired to the executor')

    def publish(self):
        real = self.m.push_commit
        def local_push(checkout, origin, branch, base, head):
            self.assertEqual(origin, 'https://github.com/skunklabs-uk/iwant.git')
            saved = json.loads((self.run / 'result.json').read_text())
            self.assertEqual(saved['publication']['head'], head)
            self.assertEqual(saved['publication']['state'], 'prepared')
            return real(checkout, str(self.origin), branch, base, head)
        with patch.object(self.m, 'push_commit', side_effect=local_push):
            return self.runner.publish(self.request, self.run, self.result)

    def test_publication_is_durable_before_push_and_report_has_commit(self):
        result = self.publish()
        self.assertEqual(result['publication']['state'], 'published')
        head = result['publication']['head']
        self.assertEqual(self.git(self.origin, 'show', head + ':item.txt'), 'after')
        self.assertEqual(json.loads((self.run / 'result.json').read_text()), result)

    def test_closed_non_draft_fork_and_wrong_branch_are_blocked(self):
        for field, value in [('state', 'closed'), ('draft', False),
                ('head', {'ref': 'agent/other', 'sha': self.base,
                          'repo': {'full_name': 'skunklabs-uk/iwant'}}),
                ('head', {'ref': 'agent/task', 'sha': self.base,
                          'repo': {'full_name': 'other/iwant'}})]:
            with self.subTest(field=field, value=value):
                original = self.pr[field]
                self.pr[field] = value
                result = self.publish()
                self.assertEqual(result['publication']['state'], 'blocked')
                self.pr[field] = original
                self.result.pop('publication', None)
        self.assertEqual(self.git(self.origin, 'rev-parse', 'refs/heads/agent/task'), self.base)

    def test_missing_or_default_branch_metadata_is_not_assumed_safe(self):
        for repository in ({}, {'default_branch': 'agent/task'}):
            with self.subTest(repository=repository), patch.object(
                    self.runner.github, 'request', return_value=(200, {}, repository)):
                result = self.runner.publish(self.request, self.run, self.result)
                self.assertEqual(result['publication']['state'], 'blocked')
                self.result.pop('publication', None)

    def test_missing_pr_head_cannot_authorize_publication(self):
        self.pr['head']['sha'] = None
        result = self.publish()
        self.assertEqual(result['publication']['state'], 'blocked')
        self.assertEqual(self.git(self.origin, 'rev-parse', 'refs/heads/agent/task'), self.base)

    def test_failed_execution_never_pushes(self):
        self.result['exit_code'] = 1
        result = self.publish()
        self.assertNotIn('publication', result)
        self.assertEqual(self.git(self.origin, 'rev-parse', 'refs/heads/agent/task'), self.base)

    def test_lost_push_response_resumes_same_snapshot(self):
        real = self.m.push_commit
        def lost_response(checkout, origin, branch, base, head):
            real(checkout, str(self.origin), branch, base, head)
            raise TimeoutError('Response lost')
        with patch.object(self.m, 'push_commit', side_effect=lost_response):
            with self.assertRaises(TimeoutError):
                self.runner.publish(self.request, self.run, self.result)
        self.result = json.loads((self.run / 'result.json').read_text())
        head = self.result['publication']['head']
        self.pr['head']['sha'] = head
        # Do not resnapshot even if the original checkout has since changed.
        (self.repo / 'item.txt').write_text('changed after interrupted delivery\n')
        result = self.publish()
        self.assertEqual(result['publication']['head'], head)
        self.assertEqual(result['publication']['state'], 'published')
        self.assertEqual(self.git(self.origin, 'show', head + ':item.txt'), 'after')


class ConsumerDeliveryTests(unittest.TestCase):
    def test_delivery_retry_never_runs_model_again(self):
        from workspace_handoff import Consumer
        with tempfile.TemporaryDirectory() as root:
            config = {'repository': 'skunklabs-uk/iwant', 'thread': 42, 'actor_ids': [1],
                      'publisher_id': 1, 'sandbox': 'workspace-write'}
            request = {'repository': config['repository'], 'assignment': 'TASK', 'generation': 1,
                       'branch': 'agent/task', 'head': 'a' * 40,
                       'prompt': 'docs/agents/prompts/task.md', 'publish_paths': ['item.txt']}
            class API:
                comments = []
                reports = []
                def list_comments(self): return self.comments
                def create_comment(self, body): return {'id': 2, 'user': {'id': 1}}
                def update_comment(self, comment, body): self.reports.append(body)
            class Runner:
                calls = 0
                deliveries = 0
                def __call__(self, request, directory):
                    self.calls += 1
                    return {'exit_code': 0, 'summary': 'done', 'head': request['head'], 'dirty': True}
                def publish(self, request, directory, result):
                    self.deliveries += 1
                    if self.deliveries == 1:
                        raise TimeoutError('uncertain delivery')
                    result['publication'] = {'state': 'published', 'head': 'b' * 40}
                    return result
            api, runner = API(), Runner()
            consumer = Consumer(root, config, api, runner)
            consumer.enroll()
            api.comments = [{'id': 1, 'user': {'id': 1}, 'created_at': 't', 'updated_at': 't',
                             'body': '/workspace run\n' + json.dumps(request)}]
            with self.assertRaises(TimeoutError):
                consumer.tick()
            restarted = Consumer(root, config, api, runner)
            restarted.tick()
            self.assertEqual(runner.calls, 1)
            self.assertEqual(runner.deliveries, 2)
            self.assertEqual(len(api.reports), 1)
            self.assertIn('b' * 40, api.reports[0])
            self.assertEqual(next(iter(restarted.state['jobs'].values()))['phase'], 'delivered')


if __name__ == '__main__':
    unittest.main()
