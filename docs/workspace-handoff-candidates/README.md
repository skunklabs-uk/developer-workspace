# Profili runtime del POC IWANT

**Stato: Active.** Sorgenti dei profili ridotti approvati e applicati nella
missione [#75](https://github.com/skunklabs-uk/developer-workspace/issues/75),
con il delta della continuazione [#79](https://github.com/skunklabs-uk/developer-workspace/issues/79) distribuito e ricaricato il 9 settembre 2026.
Il nome storico della directory non indica che siano ancora candidati.

| Sorgente | Destinazione sui worker K3s | SHA-256 |
| --- | --- | --- |
| [apparmor-iwant.profile](apparmor-iwant.profile) | `/etc/apparmor.d/workspace-handoff-poc-iwant` | `4581088a082c031dfea806127b1fcbcb926da6f740c0ccbd97ea35658538b672` |
| [seccomp.json](seccomp.json) | `/var/lib/kubelet/seccomp/profiles/workspace-handoff-poc-v1.json` | `8657dc596023b63a3501932caf19e55e416ff795d1724e68612812fd865f1d53` |

Homelab possiede distribuzione, caricamento e riferimenti GitOps; la procedura
è nel [disegno operativo](https://github.com/skunklabs-uk/homelab/blob/main/doc/35-Developer%20Workspace%20K3s%20GitOps%20design.md).
Il profilo #79 attualmente osservato sui worker resta la revisione precedente:
sorgente SHA-256 `4581088a082c031dfea806127b1fcbcb926da6f740c0ccbd97ea35658538b672`,
compilato `f04f6adf97faecd1883144701c46e4bc043ba62f804d262540428e30a87f162d`,
profilo in enforce sui tre worker. Il branch `fix/79-handoff-write-apparmor`
propone un delta successivo non ancora applicato al runtime: stato dedicato
`iwant` o `iwant-<thread>` e remount `rw` limitato al checkout per
`workspace-write`.

Le regole mount/remount del profilo mantengono il checkout diagnostico e i
checkout in `runs/<sha256>/checkout`, tramite `@{hex64}`. Il delta write non apre
la home né altre directory dello stato: restringe il nome della root a `iwant`
o `iwant-<thread>` e consente sia remount `ro` sia `rw` del solo checkout,
coerentemente con la modalità scelta dal permission profile Codex. Il profilo
non autentica il job e non autorizza da solo un incarico; request, thread,
branch, head, prompt e `publish_paths` restano verificati dal consumer.

Il delta deve essere compilato e revisionato nel workspace prima del reload.
Dopo applicazione va verificato sui tre worker con consumer fermo, quindi con
probe `read-only` e `workspace-write` su state path dedicato. Un fallimento non
autorizza wildcard più ampie, full access o bypass della sandbox.

Rollback: mantenere `execution_enabled=false`, ripristinare la sorgente runtime
precedente SHA-256 `4581088a082c031dfea806127b1fcbcb926da6f740c0ccbd97ea35658538b672`
e ricaricarla sui tre worker. Stato e risultati restano conservati; seccomp,
StatefulSet, RBAC, credenziali e CLI non fanno parte del rollback di questo delta.
La baseline storica pre-#79 `b28fec1792b33cb77cd0e9ae1dc4c4af269a9a8ad12ef786c23313b74f592cc2`
resta evidenza diagnostica, non il rollback immediato della continuazione write.

Confini, verifiche e lifecycle sono nel [runbook](../WORKSPACE-HANDOFF.md).
La [cronologia diagnostica](archive/README.md) è archiviata e non autorizza operazioni.
