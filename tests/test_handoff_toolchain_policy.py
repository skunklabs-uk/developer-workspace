"""Static contract for the path-scoped handoff Go mounts."""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / 'docs/workspace-handoff-candidates/apparmor-iwant.profile'


class HandoffToolchainPolicyTests(unittest.TestCase):
    def test_go_roots_have_only_path_specific_read_only_mounts(self):
        profile = PROFILE.read_text(encoding='utf-8')
        roots = (
            '/home/coder/.local/share/mise/installs/go/1.26.5/',
            '/home/coder/go/pkg/mod/',
        )
        for root in roots:
            self.assertIn(
                f'mount options=(rw,rbind) /oldroot{root} -> /newroot{root},', profile)
            self.assertIn(
                'remount options=(ro,bind,nosuid,nodev,relatime,silent) '
                f'/newroot{root},', profile)

        for forbidden in (
            '/oldroot/home/coder/.local/ ->',
            '/oldroot/home/coder/.local/share/mise/ ->',
            '/oldroot/home/coder/.local/share/mise/shims/',
            '/oldroot/home/coder/go/ ->',
        ):
            self.assertNotIn(forbidden, profile)

        state_checkout = ('/home/coder/.local/state/workspace-handoff/'
                          '@{handoff_state}/runs/@{hex64}/checkout/')
        self.assertIn(
            'remount options=(ro,bind,nosuid,nodev,relatime,silent) '
            f'/newroot{state_checkout}.git/,', profile)
        self.assertIn(
            'remount options=(ro,bind,nosuid,nodev,relatime,silent) '
            f'/newroot{state_checkout}.{{agents,codex}}/,', profile)


if __name__ == '__main__':
    unittest.main()
