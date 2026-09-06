"""GitHub CLI transport and fixed Codex invocation for the opt-in IWANT pilot."""
import base64
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time
from urllib.parse import urlsplit

from workspace_handoff import HandoffError, atomic_json


class RateLimited(HandoffError):
    write_rejected = True

    def __init__(self, until):
        self.until = until
        super().__init__('GitHub richiede una pausa prima della prossima richiesta')


class RejectedRequest(HandoffError):
    write_rejected = True


class GitHub:
    """Use gh for credentials/HTTP; persist ETags and backoff, not a second queue."""
    def __init__(self, config, root):
        self.base = f"repos/{config['repository']}/issues/{config['thread']}/comments"
        self.repo = config['repository']
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.path = self.root / 'transport.json'
        self.meta = json.loads(self.path.read_text()) if self.path.exists() else {
            'pause_until': 0, 'failures': 0, 'requests': 0, 'cache': {}}
        self.metrics = self.meta
        self.gh = config.get('gh', 'gh')

    def request(self, method, endpoint, data=None, etag=None):
        now = time.time()
        if now < self.meta['pause_until']:
            raise RateLimited(self.meta['pause_until'])
        args = [self.gh, 'api', '--hostname', 'github.com', '--include', '--method', method,
                '-H', 'Accept: application/vnd.github+json', endpoint]
        if etag:
            args += ['-H', 'If-None-Match: ' + etag]
        if data is not None:
            args += ['--input', '-']
        if method != 'GET':
            time.sleep(max(0, 1 - (now - self.meta.get('last_write', 0))))
            self.meta['last_write'] = time.time()
        self.meta['requests'] += 1
        atomic_json(self.path, self.meta)
        env = dict(os.environ, GH_PROMPT_DISABLED='1', GH_PAGER='cat')
        try:
            proc = subprocess.run(args, input=json.dumps(data) if data is not None else None,
                                  text=True, capture_output=True, timeout=45, env=env)
        except subprocess.TimeoutExpired as error:
            raise TimeoutError('Risposta gh non ricevuta') from error
        raw = proc.stdout.replace('\r\n', '\n')
        if not raw.startswith('HTTP/'):
            raise HandoffError('gh non ha restituito una risposta HTTP verificabile')
        # gh may include redirect/proxy response headers before the final block.
        while raw.startswith('HTTP/'):
            header, separator, raw = raw.partition('\n\n')
            if not separator:
                raise HandoffError('Risposta HTTP incompleta')
            lines = header.splitlines()
            status = int(lines[0].split()[1])
            headers = {key.lower(): value.strip() for key, value in
                       (line.split(':', 1) for line in lines[1:] if ':' in line)}
        body = None if status == 304 else json.loads(raw or 'null')
        self.meta['last_quota'] = {k: v for k, v in headers.items() if k.startswith('x-ratelimit-')}
        if status in (403, 429) and (status == 429 or 'retry-after' in headers or
                headers.get('x-ratelimit-remaining') == '0' or
                'rate limit' in str(body).lower()):
            self.meta['failures'] += 1
            wait = max(60, 60 * (2 ** min(self.meta['failures'] - 1, 6)))
            wait = max(wait, float(headers.get('retry-after', 0)))
            until = max(time.time() + wait, float(headers.get('x-ratelimit-reset', 0))
                        if headers.get('x-ratelimit-remaining') == '0' else 0)
            self.meta['pause_until'] = until
            atomic_json(self.path, self.meta)
            if self.meta['failures'] > 5:
                raise HandoffError('Rate limit ripetuto: diagnosi necessaria, polling arrestato')
            raise RateLimited(until)
        if status >= 400:
            atomic_json(self.path, self.meta)
            # Do not publish raw upstream bodies, which may contain sensitive context.
            if status < 500:
                raise RejectedRequest(f'GitHub HTTP {status}; correggere accesso o richiesta')
            raise TimeoutError(f'GitHub HTTP {status}; esito della scrittura da riconciliare')
        self.meta['failures'] = 0
        if headers.get('x-ratelimit-remaining') == '0':
            self.meta['pause_until'] = max(time.time(), float(headers.get('x-ratelimit-reset', 0)))
        atomic_json(self.path, self.meta)
        return status, headers, body

    def list_comments(self):
        endpoint = self.base + '?per_page=100'
        comments, visited = [], set()
        while endpoint:
            if endpoint in visited or len(visited) >= 20:
                raise HandoffError('Paginazione ciclica o thread oltre il perimetro del POC')
            visited.add(endpoint)
            cached = self.meta['cache'].get(endpoint, {})
            status, headers, body = self.request('GET', endpoint, etag=cached.get('etag'))
            if status == 304:
                if not cached:
                    raise HandoffError('304 senza rappresentazione locale')
                body, link = cached['body'], cached['link']
            else:
                link = headers.get('link', '')
                self.meta['cache'][endpoint] = {'body': body, 'etag': headers.get('etag'), 'link': link}
                atomic_json(self.path, self.meta)
            if not isinstance(body, list):
                raise HandoffError('La lista commenti non è una lista JSON')
            comments.extend(body)
            match = re.search(r'<([^>]+)>;\s*rel="next"', link)
            endpoint = None
            if match:
                next_url = urlsplit(match.group(1))
                if (next_url.scheme != 'https' or next_url.netloc != 'api.github.com'
                        or next_url.path != '/' + self.base):
                    raise HandoffError('URL di paginazione fuori dal thread autorizzato')
                endpoint = next_url.path.lstrip('/') + '?' + next_url.query
        return comments

    def create_comment(self, body):
        return self.request('POST', self.base, {'body': body})[2]

    def update_comment(self, comment_id, body):
        return self.request('PATCH', f'repos/{self.repo}/issues/comments/{int(comment_id)}', {'body': body})[2]


def git(directory, *args):
    command = ['git', '--literal-pathspecs', '-c', 'core.hooksPath=/dev/null']
    if directory is not None:
        command += ['-C', str(directory)]
    command += list(args)
    env = dict(os.environ, GIT_TERMINAL_PROMPT='0', GIT_LFS_SKIP_SMUDGE='1')
    return subprocess.check_output(command, text=True, stderr=subprocess.PIPE,
                                   timeout=180, env=env).strip()


def prepare_checkout(request, origin, target):
    """New isolated clone only. Never reset, clean or switch an existing checkout."""
    target = Path(target)
    if target.exists():
        raise HandoffError('Checkout esistente: riconciliare, non cancellare né resettare')
    git(None, 'check-ref-format', '--branch', request['branch'])
    git(None, 'clone', '--no-local', '--depth=1', '--single-branch', '--no-checkout',
        '--branch', request['branch'], '--', origin, str(target))
    head = git(target, 'rev-parse', 'HEAD')
    if head != request['head']:
        raise HandoffError('Branch remoto diverso dallo SHA autorizzato')
    git(target, 'checkout', '--detach', head)
    entry = git(target, 'ls-tree', 'HEAD', '--', request['prompt'])
    if not entry.startswith(('100644 blob ', '100755 blob ')):
        raise HandoffError('Il prompt non è un file Git regolare')
    prompt = target / request['prompt']
    if not prompt.resolve().is_relative_to(target.resolve()) or prompt.is_symlink():
        raise HandoffError('Il prompt esce dal checkout')
    if prompt.stat().st_size > 131072:
        raise HandoffError('Prompt oltre il perimetro del POC')
    # A repository-supplied configuration must not enable tools outside this profile.
    if (target / '.codex').exists():
        raise HandoffError('Configurazione Codex di progetto presente: richiede review esplicita')
    return prompt.read_text(encoding='utf-8')


def reference_context(github):
    """Read the two canonical sources per run; no vendored policy/skill copies."""
    if github is None:
        raise HandoffError('Accesso alle fonti canoniche non disponibile')
    text = []
    for repository, path in (
            ('skunklabs-uk/agent-os', 'rfcs/RFC-0001-principles.md'),
            ('skunklabs-uk/codex-skills', 'global/agent-loop/SKILL.md')):
        _, _, value = github.request('GET', f'repos/{repository}/contents/{path}?ref=main')
        if (not isinstance(value, dict) or value.get('encoding') != 'base64' or
                not re.fullmatch(r'[0-9a-f]{40}', str(value.get('sha', '')))):
            raise HandoffError('Fonte canonica senza contenuto o revisione verificabile')
        raw = base64.b64decode(''.join(value['content'].split()), validate=True)
        if len(raw) > 262144:
            raise HandoffError('Fonte oltre il perimetro del POC')
        text.append(f"Fonte corrente: {repository}/{path}; blob {value['sha']}\n" + raw.decode('utf-8'))
    return '\n\n'.join(text)


class LocalCodex:
    """Opt-in native permissions; the effective managed tool set still needs live review."""
    def __init__(self, config, github=None):
        self.github = github
        self.config = config
        self.codex = config.get('codex', 'codex')
        self.references = None

    def prepare(self):
        self.references = reference_context(self.github)

    def environment(self, run_dir):
        env = {key: os.environ[key] for key in ('HOME', 'PATH', 'LANG', 'CODEX_HOME') if key in os.environ}
        env['TMPDIR'] = str(run_dir / 'tmp')
        env['NO_COLOR'] = '1'
        return env

    def overrides(self):
        mode = self.config.get('sandbox', 'read-only')
        if mode not in ('read-only', 'workspace-write'):
            raise HandoffError('Il POC non supporta bypass o full access')
        access = 'read' if mode == 'read-only' else 'write'
        values = [
            'default_permissions="handoff"',
            'permissions.handoff={filesystem={":minimal"="read",":workspace_roots"="' + access +
                '"},network={enabled=false}}',
            'approval_policy="never"', 'web_search="disabled"',
            'shell_environment_policy.inherit="none"',
        ]
        return [part for value in values for part in ('-c', value)]

    def command(self, checkout, summary):
        return [self.codex, 'exec', '--ignore-user-config', *self.overrides(),
                '--cd', str(checkout), '--output-last-message', str(summary), '-']

    def probe(self, checkout, run_dir, env):
        """Probe native permissions without model usage or reading real secrets."""
        hidden = run_dir / 'outside-canary.txt'
        hidden.write_text('non-secret filesystem boundary probe\n')
        outside_write = run_dir / 'outside-write.txt'
        inside_write = checkout / '.handoff-probe'
        script = ('test -r "$1" || exit 11; '
                  'if cat "$2" >/dev/null 2>&1; then exit 12; fi; '
                  'if (printf probe >"$3") 2>/dev/null; then exit 13; fi; '
                  'if [ "$5" = write ]; then printf probe >"$4" || exit 14; '
                  'else if (printf probe >"$4") 2>/dev/null; then exit 15; fi; fi')
        access = 'read' if self.config.get('sandbox', 'read-only') == 'read-only' else 'write'
        args = [self.codex, 'sandbox', '--include-managed-config', '--permission-profile',
                'handoff', '--cd', str(checkout), *self.overrides(), '--', '/bin/sh', '-c', script,
                'probe', str(checkout / 'AGENTS.md'), str(hidden), str(outside_write),
                str(inside_write), access]
        result = subprocess.run(args, capture_output=True, timeout=30, env=env)
        atomic_json(run_dir / 'permissions-probe.json', {'exit_code': result.returncode})
        if inside_write.exists():
            inside_write.unlink()
        if result.returncode:
            raise HandoffError('Sandbox nativa non verificata: nessun fallback permissivo')

    def __call__(self, request, run_dir):
        if self.config.get('execution_enabled') is not True:
            raise HandoffError('Esecuzione disabilitata: attivazione locale esplicita richiesta')
        run_dir = Path(run_dir)
        run_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        (run_dir / 'tmp').mkdir(exist_ok=True, mode=0o700)
        checkout = run_dir / 'checkout'
        origin = 'https://github.com/' + request['repository'] + '.git'
        prompt = prepare_checkout(request, origin, checkout)
        if self.references is None:
            raise HandoffError('Preflight delle fonti non eseguito')
        env = self.environment(run_dir)
        self.probe(checkout, run_dir, env)
        summary = run_dir / 'summary.md'
        instructions = (self.references + '\n\nIncarico versionato:\n' + prompt + '\n\nConsegna: riepilogo italiano con risultato effettivo, verifiche, '
                        'limiti e documentazione. Usa agent-loop entro lo scope autorizzato. '
                        'Non inviare commenti, non rilanciare CI, non eseguire merge/deploy. '
                        'La pubblicazione del report è del collegamento, non dell\'agente.\n')
        with (run_dir / 'codex.log').open('wb') as log:
            child = subprocess.Popen(self.command(checkout, summary), stdin=subprocess.PIPE,
                                     stdout=log, stderr=log, env=env, start_new_session=True)
            try:
                child.communicate(instructions.encode(), timeout=self.config.get('timeout_seconds', 1200))
            except BaseException:
                try:
                    os.killpg(child.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                child.wait()
                raise
        text = summary.read_text(encoding='utf-8') if summary.is_file() else ''
        return {'exit_code': child.returncode if text else 1, 'summary': text,
                'head': git(checkout, 'rev-parse', 'HEAD'),
                'dirty': bool(git(checkout, 'status', '--porcelain'))}
