# Profili runtime del POC IWANT

**Stato: Active.** Questa directory conserva i profili seccomp e AppArmor
della continuazione #79. I profili originano dalla missione
[#75](https://github.com/skunklabs-uk/developer-workspace/issues/75) e dalla
continuazione [#79](https://github.com/skunklabs-uk/developer-workspace/issues/79);
la tabella identifica la revisione sorgente verificata nel runtime.

| Stato | Sorgente | Destinazione sui worker K3s | SHA-256 sorgente |
| --- | --- | --- | --- |
| Candidato toolchain #79, non ancora distribuito | [apparmor-iwant.profile](apparmor-iwant.profile) | `/etc/apparmor.d/workspace-handoff-poc-iwant` | `3f6254472d9489a51ba3b345340951505068a8a51ff3a2a006b5397a398d0a6f` |
| Verificato e distribuito sui tre worker | [seccomp.json](seccomp.json) | `/var/lib/kubelet/seccomp/profiles/workspace-handoff-poc-v1.json` | `65bc289fe949214aae251e4adb265523a07d55d91108c163e8843a98cb0a24b2` |

Homelab possiede distribuzione, caricamento e riferimenti GitOps; la procedura
è nel [disegno operativo](https://github.com/skunklabs-uk/homelab/blob/main/doc/35-Developer%20Workspace%20K3s%20GitOps%20design.md).
Nel trial controllato del 10 settembre 2026, i tre worker usano il seccomp
SHA-256 `65bc289fe949214aae251e4adb265523a07d55d91108c163e8843a98cb0a24b2`
e AppArmor sorgente
`8130d61d4405fc495609497be3ab7eef72f61108f47bb826ac66a46be9378c1f`,
raw `5d55a2bb19dee4a3e6f91c8c6b04f220bea57a96cd08708cd8dd14d296e158b7`,
profilo in enforce sui tre worker. La revisione include lo stato dedicato
`iwant` o `iwant-<thread>` e remount `rw` limitato al checkout per
`workspace-write`. La PR #83 aggiunge il bind ricorsivo e il remount read-only del solo
`checkout/.git/` che Codex usa per proteggere i metadati Git dopo il remount
scrivibile del checkout. Protegge inoltre la creazione degli omonimi mancanti
`checkout/.agents/` e `checkout/.codex/` con tmpfs e remount read-only sugli
stessi path esatti. `apparmor_parser 4.1.0` ha prodotto lo stesso raw sui tre
worker prima del replace-mode.

Le regole mount/remount del profilo mantengono il checkout diagnostico e i
checkout in `runs/<sha256>/checkout`, tramite `@{hex64}`. Il delta write non apre
la home né altre directory dello stato: restringe il nome della root a `iwant`
o `iwant-<thread>` e consente sia remount `ro` sia `rw` del solo checkout,
coerentemente con la modalità scelta dal permission profile Codex. Il profilo
non autentica il job e non autorizza da solo un incarico; request, thread,
branch, head, prompt e `publish_paths` restano verificati dal consumer.

La remediation toolchain della #79 aggiunge soltanto due read root esatti:
`/home/coder/.local/share/mise/installs/go/1.26.5` e il `GOMODCACHE` osservato
`/home/coder/go/pkg/mod`. Per ciascuno il profilo ammette il bind ricorsivo e il
successivo remount read-only; non apre `.local`, mise, i suoi shim, GOPATH o home.
I flag mount sono quelli già coperti dal seccomp corrente (`53248` per `rbind` e
`2134055` per il remount read-only), quindi il seccomp non cambia.

Il delta è stato compilato e revisionato prima del reload, con consumer fermo.
I probe `read-only` e `workspace-write` sono passati sullo state path dedicato;
il secondo ha verificato checkout scrivibile, metadati protetti e assenza di
scritture persistenti esterne. Il seccomp #83 aggiunge esclusivamente l'allow `mount` con confronto
`SCMP_CMP_EQ` sui flag all'indice 3 e valore `2134054` (`0x209026`). Le due
varianti read-only `2134055` e `2134063` restano invariate. Un fallimento non
autorizza altre regole, wildcard più ampie, full access o bypass della sandbox.

Rollback del candidato toolchain: mantenere `execution_enabled=false`,
ripristinare la sorgente runtime distribuita dalla #83 SHA-256
`8130d61d4405fc495609497be3ab7eef72f61108f47bb826ac66a46be9378c1f`
e ricaricarla sui tre worker. Il seccomp resta invariato e non richiede rollback
o ricreazione del Pod per questa remediation. Stato e risultati restano
conservati; StatefulSet, RBAC, credenziali e CLI non cambiano.
La baseline storica pre-#79 `b28fec1792b33cb77cd0e9ae1dc4c4af269a9a8ad12ef786c23313b74f592cc2`
resta evidenza diagnostica, non il rollback immediato della continuazione write.

Confini, verifiche e lifecycle sono nel [runbook](../WORKSPACE-HANDOFF.md).
La [cronologia diagnostica](archive/README.md) è archiviata e non autorizza operazioni.
