"""Contract tests for per-request Codex model selection."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))

import workspace_handoff as handoff
import workspace_handoff_io as io


def comment(**changes):
    request = {
        'repository': 'skunklabs-uk/developer-workspace',
        'assignment': 'MODEL-SELECTION',
        'generation': 1,
        'branch': 'feat/model-selection',
        'head': 'a' * 40,
        'prompt': 'docs/agents/prompts/model-selection.md',
    }
    request.update(changes)
    return {
        'id': 1,
        'user': {'id': 7},
        'created_at': '2026-09-17T00:00:00Z',
        'updated_at': '2026-09-17T00:00:00Z',
        'body': '/workspace run\n' + json.dumps(request),
    }


class ModelSelectionTests(unittest.TestCase):
    def setUp(self):
        self.config = {
            'repository': 'skunklabs-uk/developer-workspace',
            'thread': 105,
            'actor_ids': [7],
            'publisher_id': 7,
        }

    def test_intake_accepts_explicit_model_and_reasoning(self):
        request = handoff.parse_request(
            comment(model='gpt-6-astra', reasoning_effort='xhigh'), self.config)
        self.assertEqual(request['model'], 'gpt-6-astra')
        self.assertEqual(request['reasoning_effort'], 'xhigh')

    def test_intake_rejects_unsafe_model_or_reasoning_values(self):
        for changes in (
            {'model': '--config=evil'},
            {'model': 'model with spaces'},
            {'reasoning_effort': '-c'},
            {'reasoning_effort': 'high value'},
        ):
            with self.subTest(changes=changes):
                with self.assertRaises(handoff.HandoffError):
                    handoff.parse_request(comment(**changes), self.config)

    def test_command_passes_explicit_selection_without_shell_interpolation(self):
        runner = io.LocalCodex({'sandbox': 'read-only'})
        command = runner.command(
            Path('/tmp/checkout'), Path('/tmp/summary.md'),
            request={'model': 'gpt-6-astra', 'reasoning_effort': 'high'})
        model_index = command.index('--model')
        self.assertEqual(command[model_index + 1], 'gpt-6-astra')
        self.assertIn('model_reasoning_effort="high"', command)
        self.assertIn('--ignore-user-config', command)
        self.assertNotIn('--dangerously-bypass-approvals-and-sandbox', command)

    def test_command_without_selection_keeps_runtime_default(self):
        runner = io.LocalCodex({'sandbox': 'read-only'})
        command = runner.command(Path('/tmp/checkout'), Path('/tmp/summary.md'))
        self.assertNotIn('--model', command)
        self.assertFalse(any('model_reasoning_effort=' in arg for arg in command))

    def test_result_reports_the_requested_selection(self):
        with tempfile.TemporaryDirectory() as directory:
            consumer = handoff.Consumer(Path(directory), self.config, None, None)
            job = {
                'comment_id': 1,
                'request': {
                    'repository': self.config['repository'],
                    'assignment': 'MODEL-SELECTION',
                    'generation': 1,
                    'branch': 'feat/model-selection',
                    'head': 'a' * 40,
                    'prompt': 'docs/agents/prompts/model-selection.md',
                    'model': 'gpt-6-astra',
                    'reasoning_effort': 'high',
                },
            }
            report = consumer.report('run-key', job, {
                'exit_code': 0,
                'summary': 'ok',
                'head': 'a' * 40,
                'dirty': False,
            })
        self.assertIn('Modello richiesto: `gpt-6-astra`', report)
        self.assertIn('Reasoning richiesto: `high`', report)


if __name__ == '__main__':
    unittest.main()
