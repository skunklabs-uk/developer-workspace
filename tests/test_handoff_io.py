"""External adapters: HTTP fixtures and local Git; no live service or LLM calls."""
import base64
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))


def load(test):
    source = SCRIPTS / 'workspace_handoff_io.py'
    test.assertTrue(source.exists(), 'GitHub and Codex adapters are missing')
    spec = importlib.util.spec_from_file_location('workspace_handoff_io', source)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def response(status, body, **headers):
    text = f'HTTP/2.0 {status} status\r\n' + ''.join(f'{k}: {v}\r\n' for k,v in headers.items())
    return subprocess.CompletedProcess([], 0 if status < 400 else 1,
                                      text + '\r\n' + json.dumps(body), '')


class GitHubTests(unittest.TestCase):
    def setUp(self):
        self.m = load(self)
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.config = {'repository': 'skunklabs-uk/iwant', 'thread': 42}
        self.api = self.m.GitHub(self.config, Path(self.tmp.name))

    def test_conditional_pages_do_not_hide_new_comments_on_later_pages(self):
        second = 'https://api.github.com/repos/skunklabs-uk/iwant/issues/42/comments?per_page=100&page=2'
        responses = [response(200, [{'id': 1}], ETag='one', Link=f'<{second}>; rel="next"'),
                     response(200, [{'id': 2}], ETag='two'),
                     response(304, None), response(200, [{'id': 2}, {'id': 3}], ETag='three')]
        with patch.object(self.m.subprocess, 'run', side_effect=responses) as run:
            self.assertEqual([x['id'] for x in self.api.list_comments()], [1, 2])
            self.assertEqual([x['id'] for x in self.api.list_comments()], [1, 2, 3])
            self.assertIn('If-None-Match: one', run.call_args_list[2].args[0])
            self.assertIn('If-None-Match: two', run.call_args_list[3].args[0])
        self.assertEqual(self.api.metrics['requests'], 4)

    def test_rate_limit_is_persisted_and_no_request_occurs_before_reset(self):
        with patch.object(self.m.time, 'time', return_value=100), patch.object(
                self.m.subprocess, 'run', return_value=response(429, {'message': 'limited'}, **{'Retry-After': '120'})) as run:
            with self.assertRaises(self.m.RateLimited):
                self.api.list_comments()
            restarted = self.m.GitHub(self.config, Path(self.tmp.name))
            with self.assertRaises(self.m.RateLimited):
                restarted.list_comments()
            self.assertEqual(run.call_count, 1)

    def test_auth_failure_is_not_retried_as_rate_limit(self):
        with patch.object(self.m.subprocess, 'run', return_value=response(401, {'message': 'no'})):
            with self.assertRaises(self.m.HandoffError):
                self.api.list_comments()

    def test_foreign_pagination_url_is_not_followed(self):
        with patch.object(self.m.subprocess, 'run', return_value=response(200, [],
                Link='<https://evil.invalid/path>; rel="next"')) as run:
            with self.assertRaises(self.m.HandoffError):
                self.api.list_comments()
            self.assertEqual(run.call_count, 1)

    def test_required_rfc_is_read_once_and_identified_by_blob(self):
        encoded = base64.b64encode('Fonte verificata'.encode()).decode()
        body = {'encoding': 'base64', 'content': encoded, 'sha': 'a' * 40}
        self.assertTrue(hasattr(self.m, 'reference_context'), 'Canonical source loader missing')
        with patch.object(self.m.subprocess, 'run', return_value=response(200, body)):
            text = self.m.reference_context(self.api)
        self.assertIn('RFC-0001-principles.md', text)
        self.assertEqual(text.count('Fonte verificata'), 1)
        self.assertIn('a' * 40, text)
        self.assertEqual(self.api.metrics['requests'], 1)

    def test_missing_canonical_source_cannot_be_silently_ignored(self):
        self.assertTrue(hasattr(self.m, 'reference_context'), 'Canonical source loader missing')
        with patch.object(self.m.subprocess, 'run', return_value=response(404, {'message': 'Not Found'})):
            with self.assertRaises(self.m.HandoffError):
                self.m.reference_context(self.api)

    def test_mutations_send_json_stdin_never_shell_interpolation(self):
        body = "hello $(touch /tmp/should-not-exist) ' \""
        with patch.object(self.m.subprocess, 'run', return_value=response(201, {'id': 4})) as run:
            self.api.create_comment(body)
            self.assertEqual(json.loads(run.call_args.kwargs['input']), {'body': body})
            self.assertNotIn(body, run.call_args.args[0])
            self.assertFalse(run.call_args.kwargs.get('shell', False))


class CheckoutTests(unittest.TestCase):
    def setUp(self):
        self.m = load(self)
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.origin = self.root / 'origin'
        self.origin.mkdir()
        self.git('init', '-b', 'agent/poc')
        self.git('config', 'user.name', 'Fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        path = self.origin / 'docs/agents/prompts/poc.md'
        path.parent.mkdir(parents=True)
        path.write_text('Verifica questo repository, senza modifiche.\n')
        self.git('add', '.')
        self.git('commit', '-m', 'fixture')
        self.request = {'repository': 'skunklabs-uk/iwant', 'branch': 'agent/poc',
                        'head': self.git('rev-parse', 'HEAD'), 'prompt': 'docs/agents/prompts/poc.md'}

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.origin), *args], text=True,
                                       stderr=subprocess.DEVNULL).strip()

    def test_pinned_checkout_does_not_change_original_worktree(self):
        (self.origin / 'personal.txt').write_text('unfinished')
        target = self.root / 'task'
        prompt = self.m.prepare_checkout(self.request, str(self.origin), target)
        self.assertIn('Verifica questo repository', prompt)
        self.assertEqual((self.origin / 'personal.txt').read_text(), 'unfinished')
        self.assertFalse((target / 'personal.txt').exists())

    def test_moved_remote_branch_does_not_run_an_old_prompt(self):
        (self.origin / 'new.txt').write_text('new')
        self.git('add', '.')
        self.git('commit', '-m', 'move branch')
        with self.assertRaises(self.m.HandoffError):
            self.m.prepare_checkout(self.request, str(self.origin), self.root / 'task')

    def test_tracked_symlink_cannot_supply_prompt(self):
        path = self.origin / self.request['prompt']
        path.unlink()
        path.symlink_to('/etc/passwd')
        self.git('add', '.')
        self.git('commit', '-m', 'symlink')
        self.request['head'] = self.git('rev-parse', 'HEAD')
        with self.assertRaises(self.m.HandoffError):
            self.m.prepare_checkout(self.request, str(self.origin), self.root / 'task')

    def test_probe_invokes_flat_native_sandbox_and_propagates_denial(self):
        runner = self.m.LocalCodex({'sandbox': 'read-only'})
        def native_cli(args, **kwargs):
            # CLI 0.153.4 parses everything after an unrecognized positional
            # argument as the executable, including the historical "linux".
            if args[1:3] == ['sandbox', 'linux']:
                return subprocess.CompletedProcess(args, 101)
            return subprocess.CompletedProcess(args, 0)
        with patch.object(self.m.subprocess, 'run', side_effect=native_cli):
            runner.probe(self.origin, self.root, {})
        with patch.object(self.m.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1)):
            with self.assertRaises(self.m.HandoffError):
                runner.probe(self.origin, self.root, {})

    def test_execution_is_disabled_without_explicit_activation(self):
        runner = self.m.LocalCodex({'execution_enabled': False})
        with self.assertRaises(self.m.HandoffError):
            runner(self.request, self.root / 'run')

    def test_probe_rejects_host_write_despite_successful_child(self):
        runner = self.m.LocalCodex({'sandbox': 'read-only'})

        def host_mutation(args, **kwargs):
            (self.root / 'outside-write.txt').write_text('unexpected host mutation')
            return subprocess.CompletedProcess(args, 0)

        with patch.object(self.m.subprocess, 'run', side_effect=host_mutation):
            with self.assertRaises(self.m.HandoffError):
                runner.probe(self.origin, self.root, {})

    def test_executor_receives_verified_head_without_remote_lookup(self):
        runner = self.m.LocalCodex({'execution_enabled': True, 'sandbox': 'read-only'})
        runner.references = 'Fonti canoniche verificate'
        run_dir = self.root / 'run'
        captured = []
        prepare = self.m.prepare_checkout
        popen = subprocess.Popen

        class Child:
            returncode = 0

            def communicate(self, payload, timeout):
                captured.append(payload.decode())
                (run_dir / 'summary.md').write_text('Verifica completata')

        with patch.object(self.m, 'prepare_checkout', side_effect=lambda request, origin, target:
                          prepare(request, str(self.origin), target)), \
                patch.object(runner, 'probe'), \
                patch.object(self.m.subprocess, 'Popen', side_effect=lambda args, **kwargs:
                             Child() if args[0] == 'codex' else popen(args, **kwargs)):
            result = runner(self.request, run_dir)
        self.assertEqual(result['exit_code'], 0)
        self.assertIn(self.request['head'], captured[0])
        self.assertIn(self.request['repository'], captured[0])

    def test_final_checkout_status_does_not_run_parent_configured_filter(self):
        item = self.origin / 'item.txt'
        item.write_text('before\n')
        self.git('add', 'item.txt')
        self.git('commit', '-m', 'add item')
        self.request['head'] = self.git('rev-parse', 'HEAD')
        runner = self.m.LocalCodex({'execution_enabled': True, 'sandbox': 'read-only'})
        runner.references = 'Fonti canoniche verificate'
        run_dir = self.root / 'run'
        marker = self.root / 'parent-filter-ran'
        config = self.root / 'parent.gitconfig'
        config.write_text('[filter "review"]\n\tclean = touch ' + str(marker) + '; cat\n')

        class Child:
            returncode = 0

            def communicate(self, payload, timeout):
                target = run_dir / 'checkout'
                (target / '.gitattributes').write_text('item.txt filter=review\n')
                (target / 'item.txt').write_text('after!\n')
                (run_dir / 'summary.md').write_text('Verifica completata')

        prepare = self.m.prepare_checkout
        popen = subprocess.Popen
        with patch.dict(os.environ, {'GIT_CONFIG_GLOBAL': str(config)}), \
                patch.object(self.m, 'prepare_checkout', side_effect=lambda request, origin, target:
                             prepare(request, str(self.origin), target)), \
                patch.object(runner, 'probe'), \
                patch.object(self.m.subprocess, 'Popen', side_effect=lambda args, **kwargs:
                             Child() if args[0] == 'codex' else popen(args, **kwargs)):
            result = runner(self.request, run_dir)
        self.assertTrue(result['dirty'])
        self.assertFalse(marker.exists())

    def test_process_configuration_does_not_inherit_personal_tool_credentials(self):
        config = {'execution_enabled': True, 'sandbox': 'read-only'}
        runner = self.m.LocalCodex(config)
        with patch.dict(os.environ, {'GH_TOKEN': 'secret', 'BW_SESSION': 'secret',
                                    'SSH_AUTH_SOCK': '/tmp/agent', 'OPENAI_API_KEY': 'secret'}):
            env = runner.environment(self.root)
        for name in ('GH_TOKEN', 'BW_SESSION', 'SSH_AUTH_SOCK', 'OPENAI_API_KEY'):
            self.assertNotIn(name, env)
        command = runner.command(self.root, self.root / 'summary.md')
        self.assertIn('--ignore-user-config', command)
        self.assertIn('--output-last-message', command)
        self.assertNotIn('--dangerously-bypass-approvals-and-sandbox', command)
        self.assertTrue(any('default_permissions=' in arg for arg in command))


if __name__ == '__main__':
    unittest.main()
