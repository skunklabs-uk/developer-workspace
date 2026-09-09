#!/usr/bin/env python3
"""Single-thread handoff consumer. No scheduler, model calls or automatic reruns."""
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import tempfile


class HandoffError(RuntimeError):
    """A contract conflict requires inspection, not an automatic retry."""


def atomic_json(path, value):
    """Persist before side effects; replace and fsync within the same filesystem."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, name = tempfile.mkstemp(prefix='.handoff-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as output:
            json.dump(value, output, ensure_ascii=False, sort_keys=True)
            output.write('\n')
            output.flush()
            os.fsync(output.fileno())
        os.replace(name, path)
        parent = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(parent)
        finally:
            os.close(parent)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise HandoffError('Campo JSON duplicato')
        result[key] = value
    return result


def parse_request(comment, config):
    """Only authenticated metadata and a strict, unedited command authorize intake."""
    if comment.get('user', {}).get('id') not in config['actor_ids']:
        return None
    if not comment.get('created_at') or comment.get('updated_at') != comment['created_at']:
        return None
    body = comment.get('body', '')
    if not isinstance(body, str) or not body.startswith('/workspace run\n'):
        return None
    if len(body) > 4096:
        raise HandoffError('Comando troppo lungo')
    try:
        request = json.loads(body.split('\n', 1)[1], object_pairs_hook=unique_object)
    except (ValueError, TypeError) as error:
        raise HandoffError('Comando JSON non valido') from error
    fields = {'repository', 'assignment', 'generation', 'branch', 'head', 'prompt'}
    if (not isinstance(request, dict) or not fields.issubset(request)
            or set(request) - fields - {'publish_paths'}):
        raise HandoffError('Campi del comando non validi')
    if request['repository'] != config['repository']:
        raise HandoffError('Repository non autorizzato')
    if not isinstance(request['assignment'], str) or not re.fullmatch(
            r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', request['assignment']):
        raise HandoffError('Assignment non valido')
    if type(request['generation']) is not int or request['generation'] < 1:
        raise HandoffError('Generation non valida')
    if not isinstance(request['head'], str) or not re.fullmatch(r'[0-9a-f]{40}', request['head']):
        raise HandoffError('Richiesto un commit SHA completo')
    branch = request['branch']
    if (not isinstance(branch, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._/-]{0,199}', branch)
            or '..' in branch or '//' in branch or branch.endswith(('/', '.', '.lock'))):
        raise HandoffError('Branch non valido')
    prompt = request['prompt']
    if not isinstance(prompt, str):
        raise HandoffError('Percorso prompt non valido')
    parts = PurePosixPath(prompt).parts
    if (not prompt.startswith('docs/agents/prompts/') or not prompt.endswith('.md')
            or any(part in {'.', '..', 'archive'} for part in prompt.split('/'))
            or '\\' in prompt or len(parts) < 4 or '\x00' in prompt):
        raise HandoffError('Prompt fuori dal percorso corrente autorizzato')
    if 'publish_paths' in request:
        paths = request['publish_paths']
        if config.get('sandbox', 'read-only') != 'workspace-write':
            raise HandoffError('La pubblicazione richiede il profilo workspace-write autorizzato')
        if not isinstance(paths, list) or not paths:
            raise HandoffError('publish_paths deve elencare i file autorizzati')
        for path in paths:
            if (not isinstance(path, str) or not path or path != path.strip()
                    or path.startswith('/') or '\\' in path or any(ord(c) < 32 for c in path)
                    or any(part in {'', '.', '..', '.git', '.codex', '.agents'}
                           for part in path.split('/'))):
                raise HandoffError('Percorso di pubblicazione non valido')
        if len(set(paths)) != len(paths):
            raise HandoffError('Percorsi di pubblicazione duplicati')
    return request


class Consumer:
    """The persisted job identity is independent of comment delivery identity."""
    def __init__(self, root, config, github, runner):
        self.root = Path(root)
        if self.root.is_symlink():
            raise HandoffError('Lo stato non può essere un symlink')
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.root.stat().st_mode & 0o077:
            raise HandoffError('La directory di stato deve essere privata (0700)')
        self.config, self.github, self.runner = config, github, runner
        self.binding = {name: config[name] for name in
                        ('repository', 'thread', 'actor_ids', 'publisher_id')}
        self.path = self.root / 'state.json'

    @contextmanager
    def locked(self):
        fd = os.open(self.root / 'worker.lock', os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        try:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise HandoffError('Un altro consumer possiede questo stato') from error
            yield
        finally:
            os.close(fd)

    def enroll(self):
        with self.locked():
            if self.path.exists():
                raise HandoffError('Enrollment già presente: non azzerare lo stato')
            comments = self.github.list_comments()
            self.state = {'binding': self.binding, 'cursor': max(
                (item['id'] for item in comments), default=0), 'jobs': {}}
            self.save()

    def save(self):
        atomic_json(self.path, self.state)

    def marker(self, key):
        return '<!-- workspace-handoff:' + key + ' -->'

    def report(self, key, job, result):
        request = job['request']
        outcome = 'terminata — da revisionare' if result.get('exit_code') == 0 else 'fallita'
        summary = result.get('summary') or 'Nessun summary prodotto. Non considerare il lavoro completato.'
        if len(summary) > 45000:
            summary = summary[:45000] + '\n[Summary troncato; copia completa nello stato locale.]'
        publication = result.get('publication', {})
        delivery = ''
        if publication.get('state') == 'published':
            head = publication['head']
            delivery = (f"Commit pubblicato: `{head}` sul branch `{request['branch']}`.\n"
                        f"https://github.com/{request['repository']}/commit/{head}\n")
        elif publication.get('state') == 'unchanged':
            delivery = 'Pubblicazione: nessuna modifica prodotta; nessun nuovo commit.\n'
        elif publication.get('state') == 'blocked':
            delivery = 'Pubblicazione bloccata: ' + publication['reason'] + '\n'
        return (self.marker(key) + '\n## Risultato workspace\n\n'
                f"Incarico: `{request['assignment']}` / generation `{request['generation']}`.\n"
                f"Richiesta: commento `{job['comment_id']}`. Esecuzione: `{key}`.\n"
                f"Esito processo: **{outcome}**; exit code `{result.get('exit_code')}`.\n"
                f"Base: `{request['head']}`. Head locale: `{result.get('head', 'non rilevato')}`.\n"
                f"Modifiche locali non committate: `{result.get('dirty', 'non rilevato')}`.\n\n"
                + delivery + '\n' + summary + '\n\nIl successo del processo non equivale ad accettazione o merge.\n')

    def superseded(self, request):
        return any(job['request']['assignment'] == request['assignment'] and
                   job['request']['generation'] > request['generation']
                   for job in self.state['jobs'].values())

    def tick(self):
        with self.locked():
            if not self.path.is_file() or self.path.is_symlink():
                raise HandoffError('Enrollment mancante o stato non regolare')
            self.state = json.loads(self.path.read_text(encoding='utf-8'))
            if self.state['binding'] != self.binding:
                raise HandoffError('Stato associato a un altro thread o insieme di attori')
            comments = self.github.list_comments()
            # Reconcile uncertain execution before taking any new assignment.
            for key, job in self.state['jobs'].items():
                if job['phase'] == 'running':
                    if (self.root / 'runs' / key / 'result.json').is_file():
                        job['phase'] = 'result'
                        self.save()
                    else:
                        if not job.get('interruption_reported'):
                            self.github.update_comment(job['receipt'], self.marker(key) +
                                '\n## Esito non determinato\n\nProcesso interrotto prima della '
                                'registrazione del risultato. Verificare processo e checkout. '
                                'Nessuna nuova esecuzione automatica; non è una dichiarazione '
                                'di completamento né prova che tutti gli effetti siano annullati.')
                            job['interruption_reported'] = True
                            self.save()
                        raise HandoffError('Esecuzione incerta: verificare processo e checkout; nessun rilancio')
            for comment in sorted(comments, key=lambda item: item['id']):
                if comment['id'] <= self.state['cursor']:
                    continue
                try:
                    request = parse_request(comment, self.config)
                except HandoffError as error:
                    # Reject this message, not all subsequent authorized work.
                    self.state['last_rejection'] = {'comment_id': comment['id'], 'reason': str(error)}
                    request = None
                if request:
                    identity = [request['repository'], request['assignment'], request['generation']]
                    key = digest(identity)
                    existing = self.state['jobs'].get(key)
                    if existing and existing['request'] != request:
                        self.state['last_rejection'] = {'comment_id': comment['id'],
                            'reason': 'Stesso incarico con istruzioni o revisione differenti'}
                    if not existing and self.superseded(request):
                        self.state['last_rejection'] = {'comment_id': comment['id'],
                            'reason': 'Generation superata da un incarico già accettato'}
                    elif not existing:
                        self.state['jobs'][key] = {'request': request, 'comment_id': comment['id'],
                                                  'phase': 'pending', 'receipt': None}
                self.state['cursor'] = comment['id']
                self.save()
            for key, job in self.state['jobs'].items():
                if job['phase'] == 'delivered':
                    continue
                if job['phase'] == 'posting':
                    matches = [item for item in comments if
                               item.get('user', {}).get('id') == self.config['publisher_id']
                               and item.get('body', '').startswith(self.marker(key) + '\n')]
                    if len(matches) != 1:
                        raise HandoffError('Ricevuta incerta: riconciliare; nessun secondo POST automatico')
                    job['receipt'], job['phase'] = matches[0]['id'], 'ready'
                    self.save()
                if job['phase'] == 'pending':
                    job['phase'] = 'posting'
                    self.save()
                    try:
                        receipt = self.github.create_comment(self.marker(key) +
                            '\nIncarico ricevuto. Verifica dei prerequisiti prima di Codex.')
                    except Exception as error:
                        # A definitive rejection is different from a lost response.
                        if getattr(error, 'write_rejected', False):
                            job['phase'] = 'pending'
                            self.save()
                        raise
                    if receipt.get('user', {}).get('id') != self.config['publisher_id']:
                        raise HandoffError('Identità del publisher diversa da quella approvata')
                    job['receipt'], job['phase'] = receipt['id'], 'ready'
                    self.save()
                run_dir = self.root / 'runs' / key
                if job['phase'] == 'ready':
                    current = next((item for item in comments if item['id'] == job['comment_id']), None)
                    if current is None or parse_request(current, self.config) != job['request']:
                        raise HandoffError('Comando rimosso, modificato o non più autorizzato')
                    if self.superseded(job['request']):
                        atomic_json(run_dir / 'result.json', {'exit_code': 1,
                            'summary': 'Generation superata prima dell’avvio; Codex non eseguito.'})
                        job['phase'] = 'result'
                        self.save()
                if job['phase'] == 'ready':
                    # Read-only network prerequisites may wait without consuming an execution.
                    prepare = getattr(self.runner, 'prepare', None)
                    if prepare is not None:
                        prepare()
                    run_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
                    job['phase'] = 'running'
                    self.save()
                    try:
                        result = self.runner(job['request'], run_dir)
                    except Exception as error:
                        atomic_json(run_dir / 'failure.json', {'type': type(error).__name__,
                            'reason': str(error) if isinstance(error, HandoffError) else 'Consultare i log privati'})
                        # Do not publish raw exceptions, process logs or credential-bearing output.
                        result = {'exit_code': 1, 'summary': 'Esecuzione fallita: ' + type(error).__name__ +
                                  '. Consultare le evidenze locali; nessun retry automatico.'}
                    atomic_json(run_dir / 'result.json', result)
                    job['phase'] = 'result'
                    self.save()
                if job['phase'] == 'result':
                    result = json.loads((run_dir / 'result.json').read_text(encoding='utf-8'))
                    publish = getattr(self.runner, 'publish', None)
                    if publish is not None and job['request'].get('publish_paths'):
                        result = publish(job['request'], run_dir, result)
                        atomic_json(run_dir / 'result.json', result)
                    self.github.update_comment(job['receipt'], self.report(key, job, result))
                    job['phase'] = 'delivered'
                    self.save()
                return  # One execution/delivery per poll, not an unbounded drain.
