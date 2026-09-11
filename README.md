# Developer Workspace

Private image and workstation tooling for the K3s-hosted iPad Developer Workspace.

## Scope

This repository owns the versioned container image, shared CLI baseline,
code-server defaults, smoke tests, and dependency automation. Personal
configuration is applied explicitly from a private chezmoi repository and
persists in the mounted home. Kubernetes, Cloudflare, storage, RBAC, backup,
and observability live in `skunklabs-uk/homelab`.

Source issues: `skunklabs-uk/homelab#297` and
`skunklabs-uk/homelab#300`.

## Build

```bash
make build
make smoke
```

The operator bootstrap, credential boundaries, tmux recovery flow, and live
acceptance checks are documented in `docs/OPERATOR-BOOTSTRAP.md`.

Most command-line tools are installed in the persistent, writable home through
`mise`. Use `mise ls` for inventory, `mise doctor` for diagnostics,
`mise install` for the declared baseline and `mise upgrade` for updates.
Codex keeps its small availability-first launcher and updates with
`codex update`. The practical guide is in `docs/TOOL-LIFECYCLE.md`.

Personal SSH agent sharing is managed by chezmoi, not by project repositories
or this image repository. The expected layout, Bash snippet, checks, and manual
post-Pod-recreation step are documented in `docs/SSH-AGENT.md`.

## POC ChatGPT → Codex su IWANT

La [missione #75](https://github.com/skunklabs-uk/developer-workspace/issues/75)
aggiunge il collegamento opt-in `scripts/workspace-handoff`, con test locali
eseguibili tramite `python3 -m unittest discover -s tests -v`.
Il [runbook del POC](docs/WORKSPACE-HANDOFF.md) è **Active**: due iterazioni
read-only sono state eseguite nel Pod e i report riletti dalla chat. Il consumer
resta opt-in, disabilitato a fine collaudo; i permessi approvati rimangono. Il codice non
installa servizi, non parte automaticamente e non introduce Actions di orchestrazione.

## Work on two repositories at the same time

Keep each repository in its own browser tab and tmux session. The example below
uses `repo-a` for the project already open and `repo-b` for the second
project. Replace `OWNER` and `repo-b` with the real GitHub owner and
repository name.

### 1. Leave the current project running

If Codex is already working in `repo-a`, leave that browser tab and its
terminal unchanged. Do not use **File > Open Folder** in that tab.

Open a new browser tab:

```text
https://dev.skunklabs.uk/?folder=/workspaces
```

In the new tab, choose **Terminal > New Terminal**.

### 2. Clone the second repository

Run these commands in the new terminal:

```bash
git clone git@github.com:OWNER/repo-b.git /workspaces/repo-b
tmux new-session -d -s repo-b -c /workspaces/repo-b
```

The first project continues running in the original tab.

### 3. Open the second project

In the second browser tab, open:

```text
https://dev.skunklabs.uk/?folder=/workspaces/repo-b
```

Open a terminal in that tab and attach to the new tmux session:

```bash
tmux attach -t repo-b
```

Then start Codex inside tmux:

```bash
codex
```

You can now work on both repositories without mixing their terminals or Codex
sessions.

### Return to a session later

List the available tmux sessions:

```bash
tmux ls
```

Reconnect to the second project:

```bash
tmux attach -t repo-b
```

To leave tmux without stopping Codex, press `Ctrl+B`, release the keys, and
then press `D`.

### Project development ports

Development services use code-server's native path proxy. Each project receives
a stable TCP port automatically; the generated assignment is stored in the
persistent workspace home and is not maintained by hand.

From a project repository:

```bash
workspace-port allocate
```

The command discovers the project from Git, reuses its existing assignment or
selects the first unassigned and currently unused port starting at `3000`, then
prints the corresponding preview URL, for example:

```text
Project: baialupo.com
Port:    3000
Preview: https://dev.skunklabs.uk/proxy/3000/
```

Useful commands:

```bash
workspace-port list
workspace-port check
workspace-port forget
```

`list` distinguishes a reserved port from a service that is currently
listening. `forget` removes only the persistent assignment; if a process is
still listening on that port, the allocator still treats the port as busy and
does not reuse it.

The port allocator owns only local project-to-port assignments. It does not
create Kubernetes resources, Cloudflare routes, DNS records or background
services. Friendly project hostnames remain outside this contract.

## Release flow

1. GitHub Actions builds, tests and scans one immutable image artifact.
2. The same verified artifact is published to GHCR with immutable CalVer/SHA tags.
3. Homelab references the accepted immutable tag through the authenticated Harbor Proxy Cache path `private-ghcr/skunklabs-uk/developer-workspace`.
4. Harbor fetches the artifact from GHCR on cache miss and performs registry scanning/rescanning; no manual GHCR-to-Harbor promotion or replication step is required.

No credentials belong in this repository or image.
