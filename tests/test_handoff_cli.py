"""Public CLI tests: subprocess boundaries, config validation and offline status."""
import json
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'workspace-handoff'
sys.path.insert(0, str(SCRIPT.parent))


class CLITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = self.root / 'config.json'
        self.config.write_text(json.dumps({'repository': 'skunklabs-uk/iwant', 'thread': 42,
            'actor_ids': [7], 'publisher_id': 7, 'execution_enabled': False,
            'poll_seconds': 60, 'timeout_seconds': 1200, 'sandbox': 'read-only'}))

    def run_cli(self, operation):
        self.assertTrue(SCRIPT.is_file(), 'CLI entrypoint missing')
        return subprocess.run([sys.executable, str(SCRIPT), '--config', str(self.config),
            '--state', str(self.root / 'state'), operation], capture_output=True, text=True)

    def test_explicit_second_repository_is_accepted_without_enrollment(self):
        value = json.loads(self.config.read_text())
        value['repository'] = 'skunklabs-uk/skunklabs'
        self.config.write_text(json.dumps(value))
        result = self.run_cli('status')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.root / 'state').exists())

    def test_repository_must_be_an_exact_organization_member_name(self):
        for repository in ('other/skunklabs', 'skunklabs-uk/*', 'skunklabs-uk/',
                           'skunklabs-uk/../iwant', 'skunklabs-uk/iwant.git/', None, True):
            with self.subTest(repository=repository):
                value = json.loads(self.config.read_text())
                value['repository'] = repository
                self.config.write_text(json.dumps(value))
                self.assertEqual(self.run_cli('status').returncode, 2)

    def test_watch_keeps_one_consumer_across_sibling_states_while_idle(self):
        fake = self.root / 'gh-fixture'
        fake.write_text('#!' + sys.executable + '\nprint("HTTP/2 200 OK\\n\\n[]")\n')
        fake.chmod(0o700)
        value = json.loads(self.config.read_text())
        value.update(gh=str(fake), execution_enabled=True)
        self.config.write_text(json.dumps(value))
        self.assertEqual(self.run_cli('init').returncode, 0)
        args = [sys.executable, str(SCRIPT), '--config', str(self.config),
                '--state', str(self.root / 'state'), 'watch']
        watcher = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        def stop():
            if watcher.poll() is None:
                watcher.terminate()
            watcher.communicate(timeout=5)
        self.addCleanup(stop)
        deadline = time.monotonic() + 5
        transport = self.root / 'state' / 'transport.json'
        while time.monotonic() < deadline:
            if json.loads(transport.read_text())['requests'] >= 2:
                break
            time.sleep(0.02)
        else:
            self.fail('watch non ha completato il primo polling')
        original = (self.root / 'state' / 'state.json').read_bytes()
        result = subprocess.run(args[:-2] + [str(self.root / 'second'), 'init'],
                                capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertFalse((self.root / 'second' / 'transport.json').exists())
        self.assertEqual((self.root / 'state' / 'state.json').read_bytes(), original)
        stop()
        # Process exit releases the lock without deleting it or resetting state.
        result = subprocess.run(args[:-2] + [str(self.root / 'second'), 'init'],
                                capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_once_disabled_fails_before_network_or_process_launch(self):
        result = self.run_cli('once')
        self.assertEqual(result.returncode, 2)
        self.assertIn('Esecuzione disabilitata', result.stderr)
        self.assertNotIn('gh', result.stderr)
        self.assertFalse((self.root / 'state' / 'transport.json').exists())

    def test_status_works_offline_without_creating_state(self):
        result = self.run_cli('status')
        self.assertEqual(result.returncode, 0)
        self.assertIn('non inizializzato', result.stdout)
        self.assertFalse((self.root / 'state').exists())

    def test_invalid_actor_ids_cannot_authorize_boolean_id(self):
        value = json.loads(self.config.read_text())
        value['actor_ids'] = [True]
        self.config.write_text(json.dumps(value))
        result = self.run_cli('once')
        self.assertEqual(result.returncode, 2)
        self.assertIn('actor_ids', result.stderr)

    def test_polling_below_one_minute_is_rejected(self):
        value = json.loads(self.config.read_text())
        value['poll_seconds'] = 1
        self.config.write_text(json.dumps(value))
        result = self.run_cli('once')
        self.assertEqual(result.returncode, 2)
        self.assertIn('poll_seconds', result.stderr)

    def test_watch_stops_after_repeated_rate_limits_even_with_intervening_reads(self):
        value = json.loads(self.config.read_text())
        value['execution_enabled'] = True
        self.config.write_text(json.dumps(value))
        main = runpy.run_path(str(SCRIPT))['main']
        scope = main.__globals__
        error_type = scope['RateLimited']
        class Limited:
            calls = 0
            def tick(inner):
                inner.calls += 1
                if inner.calls > 5:
                    raise AssertionError('Repeated rate limits did not stop polling')
                raise error_type(0)
        limited = Limited()
        arguments = [str(SCRIPT), '--config', str(self.config), '--state', str(self.root / 'state'), 'watch']
        with patch.object(sys, 'argv', arguments), patch.dict(scope, {'Consumer': lambda *a: limited}), \
                patch.object(scope['time'], 'sleep'), patch.object(sys, 'stderr'):
            self.assertEqual(main(), 2)
        self.assertEqual(limited.calls, 5)
