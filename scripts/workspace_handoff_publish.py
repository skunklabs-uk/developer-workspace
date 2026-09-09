"""Snapshot and fast-forward delivery using native Git, without child credentials."""
import os
from pathlib import Path
import subprocess
import tempfile

from workspace_handoff import HandoffError


def _git(directory, *args, extra_env=None, input_text=None):
    env = dict(os.environ, GIT_TERMINAL_PROMPT='0', GIT_LFS_SKIP_SMUDGE='1')
    for name in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_COMMON_DIR', 'GIT_INDEX_FILE',
                 'GIT_OBJECT_DIRECTORY', 'GIT_ALTERNATE_OBJECT_DIRECTORIES'):
        env.pop(name, None)
    env.update(extra_env or {})
    command = ['git', '--literal-pathspecs', '--no-replace-objects',
               '-c', 'core.hooksPath=/dev/null', '-c', 'core.fsmonitor=false',
               '-c', 'core.attributesFile=/dev/null', '-c', 'core.autocrlf=false',
               '-c', 'commit.gpgsign=false',
               '-C', str(directory), *args]
    return subprocess.check_output(command, input=input_text, text=True,
        stderr=subprocess.PIPE, timeout=180, env=env).strip()


def snapshot_commit(checkout, base, paths, message):
    """Commit only approved regular-file changes; preserve the checkout and index."""
    checkout = Path(checkout)
    if _git(checkout, 'rev-parse', 'HEAD') != base:
        raise HandoffError('HEAD locale diverso dalla base autorizzata')
    # Ignore repository attributes, so snapshotting does not run clean filters
    # or transform the bytes produced by the child. This does not affect auth.
    empty_tree = _git(checkout, 'hash-object', '-w', '-t', 'tree', '--stdin', input_text='')
    env = {'GIT_ATTR_SOURCE': empty_tree}
    changed = set(filter(None, _git(checkout, 'diff', '--no-ext-diff', '--no-textconv',
        '--name-only', '-z', base, '--', extra_env=env).split('\0')))
    changed.update(filter(None, _git(checkout, 'ls-files', '--others',
        '--exclude-standard', '-z', extra_env=env).split('\0')))
    if changed - set(paths):
        raise HandoffError('Modifiche fuori dai percorsi autorizzati alla pubblicazione')
    if not changed:
        return base
    for name in changed:
        path = checkout / name
        current = checkout
        for part in Path(name).parts:
            current /= part
            if current.is_symlink():
                raise HandoffError('La pubblicazione non ammette symlink')
        if path.exists() and not path.is_file():
            raise HandoffError('La pubblicazione ammette soltanto file regolari')
    with tempfile.TemporaryDirectory(prefix='.publish-', dir=checkout.parent) as temporary:
        env['GIT_INDEX_FILE'] = str(Path(temporary) / 'index')
        _git(checkout, 'read-tree', base, extra_env=env)
        _git(checkout, 'add', '--all', '--', *sorted(changed), extra_env=env)
        tree = _git(checkout, 'write-tree', extra_env=env)
        if tree == _git(checkout, 'rev-parse', base + '^{tree}'):
            return base
        return _git(checkout, 'commit-tree', tree, '-p', base, '-m', message, extra_env=env)


def push_commit(checkout, origin, branch, base, head):
    """Reconcile uncertain delivery; never force or overwrite an external advance."""
    ref = 'refs/heads/' + branch

    def remote_head():
        rows = _git(checkout, 'ls-remote', '--heads', origin, ref).splitlines()
        if len(rows) != 1 or rows[0].split()[1:] != [ref]:
            raise HandoffError('Branch remoto assente o non univoco')
        return rows[0].split()[0]

    observed = remote_head()
    if observed == head:
        return head  # A previous push may have succeeded without its response.
    if observed != base:
        raise HandoffError('Branch remoto avanzato: nessuna sovrascrittura autorizzata')
    # A snapshot has one exact authorized parent. No refspec can remove history.
    if _git(checkout, 'rev-list', '--parents', '-n', '1', head).split() != [head, base]:
        raise HandoffError('Il commit da pubblicare non discende direttamente dalla base')
    try:
        _git(checkout, 'push', '--porcelain', '--no-follow-tags', origin, head + ':' + ref)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
        observed = remote_head()
        if observed == head:
            return head
        if observed != base:
            raise HandoffError('Branch cambiato durante il push: riconciliazione necessaria')
        if isinstance(error, subprocess.CalledProcessError):
            raise HandoffError('Push rifiutato: verificare autorizzazioni e regole del branch') from error
        raise TimeoutError('Push non confermato: conservare commit e riprendere solo la consegna') from error
    if remote_head() != head:
        raise HandoffError('HEAD remoto cambiato dopo il push: riconciliazione necessaria')
    return head
