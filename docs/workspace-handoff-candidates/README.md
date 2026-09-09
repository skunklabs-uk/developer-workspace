# Profili runtime del POC IWANT

**Stato: Active.** Questa directory conserva i candidati seccomp e AppArmor
della continuazione #79. I profili originano dalla missione
[#75](https://github.com/skunklabs-uk/developer-workspace/issues/75) e dalla
continuazione [#79](https://github.com/skunklabs-uk/developer-workspace/issues/79);
la tabella distingue ciò che è già applicato dal nuovo delta ancora da
distribuire.

| Stato | Sorgente | Destinazione sui worker K3s | SHA-256 sorgente |
| --- | --- | --- | --- |
| Candidato AppArmor #82, integrato ma non distribuito | [apparmor-iwant.profile](apparmor-iwant.profile) | `/etc/apparmor.d/workspace-handoff-poc-iwant` | `ec0abc6b7729743825d0be469d7b5559a06a48c51a18f776d6688c0e36f0e5e6` |
| Candidato seccomp #83, non ancora distribuito | [seccomp.json](seccomp.json) | `/var/lib/kubelet/seccomp/profiles/workspace-handoff-poc-v1.json` | `65bc289fe949214aae251e4adb265523a07d55d91108c163e8843a98cb0a24b2` |

Homelab possiede distribuzione, caricamento e riferimenti GitOps; la procedura
è nel [disegno operativo](https://github.com/skunklabs-uk/homelab/blob/main/doc/35-Developer%20Workspace%20K3s%20GitOps%20design.md).
Il profilo #79 attualmente osservato sui worker resta la revisione precedente:
sorgente SHA-256 `4581088a082c031dfea806127b1fcbcb926da6f740c0ccbd97ea35658538b672`,
compilato `f04f6adf97faecd1883144701c46e4bc043ba62f804d262540428e30a87f162d`,
profilo in enforce sui tre worker. La PR #82 ha integrato un delta successivo
non ancora applicato al runtime: stato dedicato
`iwant` o `iwant-<thread>` e remount `rw` limitato al checkout per
`workspace-write`. Il candidato è stato compilato offline con
`apparmor_parser 4.0.1`; il raw locale ha SHA-256
`9a0f79b5f61f7c0ca480238f7dc84d3f5ab6f76cc43f5054466ab98402d42873`.
L'ambiente locale non espone l'interfaccia kernel AppArmor: questo dato non
sostituisce l'hash compilato nativamente che va prodotto sui worker prima del
reload.

Le regole mount/remount del profilo mantengono il checkout diagnostico e i
checkout in `runs/<sha256>/checkout`, tramite `@{hex64}`. Il delta write non apre
la home né altre directory dello stato: restringe il nome della root a `iwant`
o `iwant-<thread>` e consente sia remount `ro` sia `rw` del solo checkout,
coerentemente con la modalità scelta dal permission profile Codex. Il profilo
non autentica il job e non autorizza da solo un incarico; request, thread,
branch, head, prompt e `publish_paths` restano verificati dal consumer.

Il delta deve essere compilato e revisionato nel workspace prima del reload.
Dopo applicazione va verificato sui tre worker con consumer fermo, quindi con
probe `read-only` e `workspace-write` su state path dedicato. Il candidato
seccomp #83 aggiunge esclusivamente l'allow `mount` con confronto
`SCMP_CMP_EQ` sui flag all'indice 3 e valore `2134054` (`0x209026`). Le due
varianti read-only `2134055` e `2134063` restano invariate. Un fallimento non
autorizza altre regole, wildcard più ampie, full access o bypass della sandbox.

Rollback: mantenere `execution_enabled=false`, ripristinare la sorgente runtime
precedente SHA-256 `4581088a082c031dfea806127b1fcbcb926da6f740c0ccbd97ea35658538b672`
e ricaricarla sui tre worker; ripristinare il seccomp precedente SHA-256
`8657dc596023b63a3501932caf19e55e416ff795d1724e68612812fd865f1d53` e
ricreare soltanto il Pod `developer-workspace-0`. Stato e risultati restano
conservati; StatefulSet, RBAC, credenziali e CLI non cambiano.
La baseline storica pre-#79 `b28fec1792b33cb77cd0e9ae1dc4c4af269a9a8ad12ef786c23313b74f592cc2`
resta evidenza diagnostica, non il rollback immediato della continuazione write.

Confini, verifiche e lifecycle sono nel [runbook](../WORKSPACE-HANDOFF.md).
La [cronologia diagnostica](archive/README.md) è archiviata e non autorizza operazioni.
