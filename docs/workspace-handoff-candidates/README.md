# Candidati runtime per WORKSPACE-HANDOFF-POC

**Stato: Draft.** Missione [#75](https://github.com/skunklabs-uk/developer-workspace/issues/75).
Candidati completi come file di policy, derivati dalla baseline di
`f712903f5fac019058a4cd59d8314468a66c28e5`. Per lo stato operativo prevale il
checkpoint seguente; le sezioni successive conservano le prove precedenti.

## Checkpoint corrente — reality check del 7 settembre 2026

### Profilo ridotto applicato e collaudato

Homelab #1112 è merged nel commit `2b13bf4d1b7f00aeff658a09f7c6eb76c21ed42f`;
Argo lo ha applicato. Il Pod corrente è `ec539a0a-218d-4151-9e56-aed0fc64caf4`,
Ready, init exit 0, profilo `workspace-handoff-poc-iwant`. Gli hash sorgente
e compilato del profilo ridotto sono nella sezione di riesame sotto.
La riconciliazione ha richiesto un refresh nativo della sola Application;
nessuna modifica alla syncPolicy o ai permessi del service account.

Sul profilo ridotto, `LocalCodex.probe` del commit `3fff82f` passa con ambiente
del consumer: proc presente, checkout diagnostico leggibile, lettura/scrittura
esterne e scrittura nel checkout negate. Namespace del figlio:
PID `4026533325`, mount `4026533137`, network `4026533607`; quelli del padre
sono rispettivamente `4026532686`, `4026532685`, `4026532412`.
Mountinfo del figlio mostra filesystem proc montato su `/proc`.

Le prove delle connessioni IPv4/IPv6 e Unix pathname/abstract restituiscono
EPERM nel figlio, con controlli positivi raggiungibili dal padre. AF_UNIX può
creare il socket: è la connessione a essere negata. Le prove usano Perl
installato nell'immagine; `/usr/bin/python3` è assente e curl non esponeva
l'errno necessario. Questi errori del materiale diagnostico non sono deny
aggiuntivi del profilo e non hanno causato aperture.
Anche la creazione di socket UDP IPv4/IPv6 è negata EPERM. L'apertura in lettura
di `/proc/keys`, esistente, è negata EACCES anche attraverso l'alias
`/proc/self/root/proc/keys`; nessun contenuto è stato letto.

UID/GID mapping del Pod: `0 3765764096 65536`; home/workspaces mantengono
owner interno `1000:1000`, senza chown. Healthz risponde alive. Config e stato
restano agli hash attesi, `execution_enabled=false`, jobs vuoti. Il collaudo
non ha ancora avviato un incarico LLM: la prova completa di exec resta g1.
Il profilo proc-v4 è stato scaricato e il suo file rimosso dai tre worker
soltanto dopo la verifica di assenza di processi che lo usavano. Seccomp v1 e
il profilo IWANT restano installati e in uso.

### Evidenze del reality check precedente al rollout

Revisione esaminata: `3ccaa80bb33482cea2e540e455e8546a22ba8f9a`, con il delta
locale `handoff-inputs.diff` ora applicato a `scripts/workspace_handoff_io.py`.
Il Pod `23b20a02-8104-4ed3-bd50-ce6c51a726b7` usa ancora proc-v4,
`hostUsers: false`, `procMount: Unmasked`, seccomp v1, capability rimosse e
noNewPrivileges. Il profilo sul worker ha SHA-256
`1bcdd08732b4788b916ec39752ab5f1191c6882b5a38cadfea18540e136515b7`.
Non è una baseline ripristinata né un runtime accettato.

**Finding della diagnosi:** i probe proc-v2/v3/v4 con il solo
`codex sandbox -- /bin/true` non specificavano il profilo del POC. Il builder
della release distingue root globale readonly da root vuota con readable roots
ristrette. I deny sul bind `/oldroot/ -> /newroot/` e sui remount successivi
non dimostrano che quelle aperture siano necessarie al profilo `handoff`.
Il journal proc-v4 mostra un deny sul remount `/newroot/proc/`; il messaggio
bubblewrap indica `/newroot/dev`. Senza una traccia correlata non si identifica
quest'ultimo errore con il solo evento AppArmor.

**Nuova prova discriminante: SÌ, limitata al probe.** Il binario diretto
0.153.4, verificato SHA-256 `56ef98ab4032d317ab26e9b5e5a175650717351edb16ed9cde0cb6d1734d62da`,
con `--include-managed-config --permission-profile handoff`, gli override
del delta nativo e cwd `/workspaces/developer-workspace/.worktrees/handoff-75`
termina correttamente. Il checkout diagnostico è stato ricreato allo SHA sopra.
`AGENTS.md` è leggibile e ha SHA-256
`d5cd254e15da5bee89e283a0fe4197431ad693c4c344697e5b6b6f06fbd9e0b3`;
mountinfo del figlio mostra proc montato su `/proc`; namespace PID figlio
`4026533325`, padre `4026532684`. Il comando verifica soltanto la leggibilità,
senza aprirne i contenuti, del kubeconfig amministrativo e della configurazione
del consumer: entrambi non leggibili nel figlio. Nessuna nuova regola runtime
è stata aggiunta per questa prova. Il PASS su proc-v4 non dimostra ancora che
le aperture globali aggiunte in v3/v4 siano inutilizzate: verificarlo sul profilo
ridotto prima di qualificarne la rimozione come collaudata.

Config e stato conservano gli hash completi riportati sotto; consumer disabilitato,
`jobs={}`, cursor `5557127806`. Suite dopo il delta nativo: 42/42 OK.
Nessun incarico LLM avviato. Non è ancora accettazione della missione.

Prosecuzione determinata dal riesame, prima di altri rollout:

- Riesaminare insieme input, syscall, mount e tool di `sandbox` e `exec`;
  il PASS di una shell non certifica MCP, plugin o processo Codex padre.
- Classificare le due aperture globali v3/v4 come candidate alla rimozione:
  la loro prova di necessità usava un'invocazione diversa dal POC.
- Derivare i due checkout esatti da assignment/generation per g1 e g2;
  non ampliare a tutta la home o `runs/**`. Il profilo attuale copre solo g1.
  Non precreare i checkout dei job: il lifecycle ordinario rifiuta target esistenti.
- Verificare il set effettivo di tool, l'autenticazione e le differenze di
  configurazione gestita prima dell'attivazione; preservare il primo giro e
  la seconda iterazione con riletture, come richiesto da ADR 0007.
- Riallineare runbook e tracker allo stato live; conservare separatamente
  evidenze storiche e criteri ancora non soddisfatti.

## Riesame dei tool e candidato ridotto

L'ispezione sanitizzata rileva un plugin Figma abilitato nella configurazione
utente. `exec --ignore-user-config` esclude quel layer, ma il probe lo carica;
la sola esclusione non equivale a disabilitare plugin remoti e app. Per il
POC si usano i flag nativi `features.plugins=false`, `features.apps=false`
e `features.hooks=false` in entrambe le invocazioni. Sono una restrizione
del perimetro esistente, senza un nuovo gestore di tool o credenziali.
Il manager upstream della release verificata restituisce un insieme vuoto
di plugin quando `plugins_enabled` è falso, anche nei percorsi remoti.

Prova di necessità e proporzionalità del delta:

| Campo | Evidenza |
|---|---|
| Requisito | ADR 0007: il POC non eredita i poteri personali tramite tool/MCP/plugin. |
| Failure mode | Configurazione utente con plugin abilitato; differenza documentata tra loader di probe ed exec. |
| Copertura esistente | Filesystem/rete dei comandi e `--ignore-user-config`; non certificano gli strumenti esterni al figlio sandboxato. |
| Alternative e gap | Eliminare app/plugin/hook dal POC riusando i flag nativi; nessun proxy o inventario custom persistente necessario. Il solo filtro environment non disabilita i tool. |
| Beneficio e verifica | Risoluzione nativa della configurazione e inventario MCP senza turni LLM; successivo riscontro nell'esecuzione reale. |
| Costo e impatto cumulativo | Tre override nel punto già condiviso da probe/exec. Nessun servizio, identità o permesso nuovo; riduce il set operativo del POC. |
| Lifecycle | Owner missione #75; KEEP per il POC ristretto, riesame prima di nuove capacità. Revocabile insieme al profilo handoff. |

La lettura `config/read` di un app-server temporaneo con gli override sopra
conferma profilo handoff, approvazioni never e app/plugin/hook disabilitati.
I layer osservati sono sessionFlags, user e system; il layer system non
contiene MCP o plugin. `mcpServerStatus/list` mostra soltanto cloudflare-api,
disabilitato dalla configurazione utente e senza tool, senza pagina successiva.
Nessun thread o turno creato; processo diagnostico terminato. Questo inventario
è dell'app-server con layer utente: l'equivalenza completa con `exec` non è
affermata. Il login diretto riporta ChatGPT, senza esportare credenziali.

Il [candidato ridotto IWANT](apparmor-iwant.profile), SHA-256
`b28fec1792b33cb77cd0e9ae1dc4c4af269a9a8ad12ef786c23313b74f592cc2`,
riusa proc-v2 con nome/self-peer distinti e la sola coppia bind/remount g2.
Rispetto a proc-v4 elimina le due concessioni globali sulla root. Review
indipendente statica senza finding; compilazione sul worker con
`apparmor_parser -Q -K -S /dev/stdin` senza caricamento o cache, exit 0,
SHA-256 compilato `56f2927e628ceed16235be16e9ed21d5c97e281cd2b496cfccf0c09ab03815df`.
Il profilo ridotto non è ancora applicato. Mantiene le compensazioni Unmasked,
i due checkout esatti, il checkout diagnostico e la release verificata;
non aggiunge bind dell'intera home né della root. La restrizione delle letture
è applicata dalla sandbox nativa; AppArmor conserva la regola baseline `file,`.

Il probe deve inoltre verificare proc nel figlio: il precedente collaudo v1
ha dimostrato che l'exit 0 della shell può convivere con il fallback no-proc.
La verifica di `/proc/self/status` rende osservabile il requisito già approvato.

## Preparazione storica v1
**Proposta originaria v1:** i due profili richiedono anche il diff nativo handoff
preparato sotto per affrontare i due finding. Non applicare i soli profili
al POC invariato. Non sono un profilo
predefinito per altri repository, versioni o comandi interattivi.

## Proposta storica: proc obbligatorio, revisione proc-v2

L'utente ha scelto di mantenere `/proc` come requisito. Il ramo no-proc non è
accettato per il POC. La disponibilità a valutare nuovi diritti non è stata
usata per applicare privilegi non definiti. Il successivo «continua» approva
il delta concreto descritto sotto per il solo collaudo di sicurezza.
**proc-v2 non è applicata: il preflight è bloccato dall’accesso amministrativo.**

### Restrizione identificata e forza dell'evidenza

Le [letture mirate e verifiche](proc-v2-evidence.json) appartengono al Pod di
rollback corrente, UID `e14979d2-8b9b-4d7c-9e57-d14b0697b1cd`, container
`39b7d762529910130a524f8b9d9391b6dbd078c64b638480d044de70be6e4e20`.
Il kernel è Debian `6.12.101-1`; namespace.c e proc/root.c della sorgente Debian
sono byte-identici ai file del tag upstream v6.12.101 verificato.

**Deduzione sufficiente sulla baseline corrente:** esiste un solo mount proc
con root intera `/`; contiene figli su file come sysrq-trigger, kcore e keys,
oltre ai bind readonly. Al clone NEWUSER/NEWNS, `copy_mnt_ns()` chiama
`lock_mnt_tree()`: quei figli diventano MNT_LOCKED. Non sono directory
permanentemente vuote; `mnt_already_visible()` rifiuta quindi questo proc e
scarta gli altri perché hanno root parziale. `mount_too_revealing()` restituisce
true, che `do_new_mount_fc()` traduce in EPERM.

È una restrizione VFS indipendente, non una nuova regola seccomp da allargare.
La deduzione è coerente con la traccia del precedente collaudo, ma non è un
kretprobe del ramo attraversato dal vecchio processo: il suo OCI non è più
recuperabile con crictl. Non si attribuisce retroattivamente un'unica causa
esclusiva. Sono conservati mountpoint, parent/root, opzioni e liste OCI,
non contenuti proc sensibili né environment.

Fonti della versione installata:
[namespace.c](https://sources.debian.org/src/linux/6.12.101-1/fs/namespace.c/),
[proc/root.c](https://sources.debian.org/src/linux/6.12.101-1/fs/proc/root.c/),
[validazione Kubernetes 1.34.9](https://github.com/kubernetes/kubernetes/blob/v1.34.9/pkg/apis/core/validation/validation.go#L8078),
[conversione procMount](https://github.com/kubernetes/kubernetes/blob/v1.34.9/pkg/securitycontext/util.go#L232).

### Delta minimo nativo proposto

- [Riferimenti proc-v2](references-proc-v2.diff): `hostUsers: false` per il Pod;
  `procMount: Unmasked` solo per code-server, con seccomp v1 e AppArmor proc-v2.
  Kubernetes 1.34.9 richiede hostUsers false per Unmasked: non è un'opzione
  aggiunta arbitrariamente. Nessuna capability, privilegi, immagine o servizio nuovi.
- [AppArmor proc-v2 completo](apparmor-proc-v2.profile) e
  [diff rispetto a v1](apparmor-proc-v2.diff): cinque gruppi deny compensano
  i percorsi delle liste OCI rimosse da Unmasked. Nessun nuovo allow mount;
  nome/self-peer distinti per distribuzione e rollback senza sovrascrivere v1.
- [Seccomp v1](seccomp.json) e [input nativo handoff](handoff-inputs.diff)
  invariati, da applicare insieme al nuovo delta durante il solo collaudo.

- `apparmor-proc-v2.profile`: SHA-256 `3adf6c8b4b723d3a31289aa265c99fdcdcc82de54db66ca49d98a404dfaf8bf2`.
- `apparmor-proc-v2.diff`: SHA-256 `27509fdd1a31823feaa1d97cfe8a63dc1f8df332adc96b564b18355328304fff`.
- `references-proc-v2.diff`: SHA-256 `2481f4bfddab0f37b39795374e300a769ad5a43945c0ccb5c12e41b3d7ee55f9`.
- `seccomp.json`: SHA-256 `8657dc596023b63a3501932caf19e55e416ff795d1724e68612812fd865f1d53`.
- `handoff-inputs.diff`: SHA-256 `e681df788ea816563702efdc76ca24bf79dcdfade0a513c9e3befd27269b80ce`.

### Impatto e limiti delle compensazioni

Unmasked svuota entrambe le liste OCI, anche per i due percorsi /sys:
non significa soltanto rendere leggibile /proc. La proposta mantiene negate
le letture dei contenuti prima mascherati e le scritture prima impedite dai
bind readonly, mediante AppArmor sul container intero.

I gruppi coprono: tre directory e sette file proc mascherati, due directory
sys mascherate, quattro directory proc readonly e sysrq-trigger readonly.
Le regole proc includono `/proc`, `/oldroot/proc` e `/newroot/proc`, cioè gli
alias dei pivot osservati; quelle sys coprono `/sys` e `/oldroot/sys`. Il builder
non monta sys in newroot. I pattern sono limitati ai percorsi OCI elencati,
non a pathname arbitrari o descriptor casuali.

**Non è equivalenza semantica alle maschere:** un programma può ricevere EACCES
invece di vedere una directory vuota o leggere EOF da un file; nomi/stat possono
restare visibili. Le compensazioni proteggono l'accesso ai contenuti, non
promettono invisibilità dei metadati. Per questo la compatibilità di shell,
estensioni e comandi del workspace va collaudata.

`hostUsers: false` interessa tutti i container del Pod, incluso l'init.
Il runtime assegna UID/GID host distinti, mentre runAsUser/runAsGroup/fsGroup
restano 1000 dentro il Pod. Kubernetes usa mount idmapped per i volumi;
non si propone chown dei dati, modifica di credenziali o assegnazione manuale
di intervalli UID. L'init esistente esegue mkdir/chmod delle due directory:
va verificato con la rimappatura prima di procedere.

Tutti i worker dichiarano userNamespaces=true per i runtime default/runc;
kubelet è 1.34.9+k3s1 e containerd 2.2.5-k3s2. Filesystem osservati: ext4 per
kubelet e volumi ordinari, tmpfs per il volume projected. Sono tipi supportati,
ma ciò **non prova** l'effettivo montaggio idmapped dei PVC/subPath in questo Pod.
Nessuna scansione o modifica degli owner di tutti i file è stata effettuata.

Alternative valutate: aggiungere CAP_SYS_ADMIN non elimina da solo il controllo
VFS nel nuovo user namespace; non è proposto. Un bind del proc padre conserva
la vista PID del padre e non soddisfa il requisito. La documentazione kernel
più recente descrive un'eccezione subset=pid, ma il sorgente 6.12.101 esaminato
imposta SB_I_USERNS_VISIBLE senza quell'eccezione e il comando osservato passa
mount data NULL: non si importa quel comportamento da una main più nuova.
Non si propongono upgrade kernel, runtime custom o ricompilazione di Codex.

### Verifiche eseguite e decisione richiesta

AppArmor 4.1.0 compila con `-Q -K -S`, exit 0: 45489 byte,
SHA-256 `5a30179694a4894707b8cc898f70860be1ac6bc8e77bced28ad684141bc7963d`.
Nessun caricamento o modifica cache. I diff superano patch --dry-run;
il server Kubernetes accetta la patch in dry-run e conserva i campi proposti.
Il manifest live è stato riletto: hostUsers/procMount non sono applicati.
Review indipendente statica completata senza finding; nessun test del codice
invariato o nuovo probe sandbox eseguito in questa diagnosi.

**Collaudo approvato:** l’utente ha risposto «continua» dopo la descrizione del
namespace dedicato al Pod, nuovo proc e compensazioni AppArmor senza capability.
L’autorizzazione copre l’insieme agli hash sopra per la finestra di sicurezza;
non copre consumer, incarichi LLM o ulteriori aperture.

**Stop prima dell’applicazione, 7 settembre 2026, 06:46 UTC:** le letture di
Pod, StatefulSet e Application falliscono con TLS handshake timeout; una
rilettura limitata a 10 secondi termina con context deadline exceeded.
L’accesso amministrativo già autorizzato via pve1 fallisce prima del worker:
`ssh: connect to host 192.168.1.201 port 22: No route to host`.
Nessun profilo distribuito/caricato, patch, pausa Argo o rollout proc-v2.
Nessun probe nel Pod o modifica a configurazione/stato; il consumer resta
fermo nell’ultima verifica disponibile, non riconfermata dopo la perdita d’accesso.

Unica risorsa esterna necessaria: ripristino della raggiungibilità del canale
amministrativo esistente dal coordinatore (API Kubernetes e bastion pve1).
Non sono state cambiate rete, firewall, credenziali o policy per ripristinarlo.
Al ripristino: verificare nuovamente identità del Pod, processi interattivi,
hash di configurazione/stato e assenza di operazioni Argo, poi proseguire il
collaudo già approvato. Non occorre una nuova approvazione del medesimo delta.

Distribuzione Ansible sui tre worker prima dei riferimenti, profilo proc-v2
separato e immutable; eventuale sospensione temporanea della sola Application
Argo tramite skip-reconcile come nel precedente collaudo, parent/syncPolicy
invariati. Una ricreazione del Pod, previa conservazione delle sessioni.

Accettazione: OCI userns e mapping effettivi, init concluso, PVC/subPath leggibili
con identità corrette e stato invariato; proc realmente montato nel PID namespace
del figlio senza fallback; nuove regole AppArmor verificate anche lungo gli
alias dei pivot con sentinelle non segrete, senza leggere file sensibili;
probe filesystem, maschera amministrativa, rete/socket e tool coerenti.
Verificare il workspace interattivo. Consumer disabilitato, nessun incarico LLM.

Rollback: ripristinare input handoff e riferimenti, rimuovere anche hostUsers e
procMount aggiunti, ricreare il Pod e verificare baseline/owner/stato. Riprendere
Argo soltanto dopo la verifica; scaricare e rimuovere i profili quando inutilizzati.
Se servono nuove aperture, owner changes o modifiche ai nodi, fermarsi prima
senza adottare una variante non approvata. La missione rimane aperta.

## Collaudo approvato del 7 settembre 2026

**Esito complessivo: NO; rollback completato.** Le [evidenze runtime](runtime-test.json)
separano la suite simulata dalle prove native. I file di policy e i diff qui
conservati restano identici agli hash approvati; i commenti interni descrivono
la loro preparazione originaria, non lo stato operativo successivo.

I profili sono stati distribuiti con Ansible sui tre worker e referenziati
soltanto da code-server. OCI seccomp identico al candidato, AppArmor in enforce,
capability zero e noNewPrivileges verificati sul nuovo container. Il probe
filesystem del collegamento passa; maschera amministrativa EACCES, TCP IPv4/IPv6
e socket Unix negati EPERM con controlli positivi nel padre. Il controllo UDP
locale è raggiungibile dal padre, ma non riceve datagrammi dal resolver figlio.
Questi risultati non sono un incarico LLM né una prova dei tool alternativi.

La traccia mirata osserva `mount("proc", "/newroot/proc", "proc", 0xe, NULL)`
negato EPERM. La release usa quindi il fallback **nativo bubblewrap senza proc**,
in modo silenzioso; il comando termina correttamente ma /proc è assente.
Non è legacy/full access e non amplia le readable roots. Il criterio approvato
"proc montato, nessun fallback qualificato PASS" non è però soddisfatto.
Non attribuiamo il nuovo diniego a seccomp o AppArmor senza ulteriore evidenza:
il filtro OCI contiene l'allow dei flag 0xe e il journal letto non contiene
un evento AppArmor pertinente. Nessuna nuova apertura è stata applicata.

Rollback verificato: input handoff originale nel checkout locale e nel Pod,
RuntimeDefault e `cri-containerd.apparmor.d` effettivi, Pod Ready e healthz 200.
Profili scaricati e file rimossi dai tre worker solo dopo assenza di processi
che li usavano. Argo CD 3.5.2 è stato sospeso con l'annotazione nativa
skip-reconcile della sola Application durante la prova; annotazione rimossa,
riconciliazione ripresa e syncPolicy originale invariata. Nessun merge GitOps,
upgrade immagine, modifica del parent Argo o nuova PR Homelab.
Config/stato/enrollment conservati; consumer sempre disabilitato. Gli strumenti
strace temporanei sono rimossi; tracce ed evidenze restano nello stato esistente.

**Decisione successiva dell'utente:** mantenere proc obbligatorio. L'alternativa
no-proc non è stata adottata; la proposta corrente proc-v2 è descritta sopra.
Nessun nuovo delta è applicato e nessun incarico IWANT è abilitato.
Review indipendente delle evidenze completata; closeout della missione ancora
aperto finché mancano i due giri e le riletture ChatGPT.

### Aggiornamento proc-v2 — prova runtime del 7 settembre 2026

Il successivo trial proc-v2 è stato applicato via Homelab GitOps e poi ritirato
con rollback. Con `hostUsers: false`, `procMount: Unmasked` e i profili locali
referenziati soltanto da `code-server`, il probe nativo
`codex sandbox -- /bin/true` si è fermato su bubblewrap prima del mount della
sandbox. Il journal di `k3s-worker1` registra AppArmor `DENIED` su
`mount /oldroot/ -> /newroot/`, `info="failed srcname match"`, `error=-13`.
Il problema è quindi nel match AppArmor del candidato; non è stata introdotta
una nuova apertura per aggirarlo.

Il rollback è stato completato su GitOps con `b49bfabba4b9ba21d22cdfd376c95bd2d045e3d9`:
Argo è `Synced`, il Pod è stato ricreato con UID
`6a11b497-27be-45af-a129-858d42710e40`, e i riferimenti proc-v2 non sono più
presenti. Ansible ha scaricato e rimosso i profili temporanei dai tre worker.
Config e stato sono invariati (`4acb321e...d69` e `96a601a...025`),
`execution_enabled=false`, `jobs={}`; nessun consumer o incarico LLM è stato
avviato. I test del repository sono 42/42 OK.

Esito: **NO-GO** per il delta proc-v2 approvato. Una correzione del match
AppArmor richiede una nuova proposta e review; non è parte del closeout
operativo corrente.

## Preparazione originaria — 6 settembre 2026

Le sezioni seguenti descrivono gli input e la proposta prima dell'applicazione;
per lo stato attuale prevale il checkpoint di collaudo sopra.

## Artefatti e verifica

- [Seccomp completo](seccomp.json), [diff](seccomp.diff).
- [AppArmor completo](apparmor.profile), [diff](apparmor.diff).
- [Diff dei riferimenti Homelab](references.diff): solo `code-server`;
  Pod e init container conservano RuntimeDefault.
- [Diff del solo input handoff](handoff-inputs.diff), non applicato al codice.
- [Input osservati](inputs.json), [verifica offline](verification.json).
- [Baseline completa](../workspace-handoff-runtime-baseline.json).

| Artefatto | SHA-256 |
|---|---|
| seccomp.json | `8657dc596023b63a3501932caf19e55e416ff795d1724e68612812fd865f1d53` |
| apparmor.profile | `ff91f6bfaa2322e8c75047df1019adbf6540aa08c4e93a5b0810615f02ff1097` |

Il diff dell’input handoff ha SHA-256
`e681df788ea816563702efdc76ca24bf79dcdfade0a513c9e3befd27269b80ce`.

AppArmor 4.1.0: `apparmor_parser -Q -K -S`, exit 0, 39897 byte,
SHA-256 compilato `a43a317d26bc4ee08bb19ecb72ac64786260a55568190e1f6fae67b055a57e0a`.
Nessun caricamento kernel, accesso cache o file sul nodo.
Seccomp: libseccomp 2.6.0, tutte le architetture e tutte le regole compilate
tramite API standard, zero errori; export BPF su memfd, 8600 byte,
SHA-256 `3f7e13e2d82f4f02eba78a44443e826d4ede2ea159500fabb9fa178409f6ac4c`.
`seccomp_load` non è stato chiamato. La compilazione non prova il risultato
del matching AppArmor né l'isolamento runtime. Il diff dei riferimenti supera
`patch --dry-run` sulla fonte Homelab acquisita.

Il diff dei riferimenti ha SHA-256
`b1e623cf34d5bfbd43b702d50384d4d178cb6c2312d3b4da39adef1d5a2267e3`. Gli hash di tutti i diff e degli
input sono registrati in verification.json. Review statica indipendente
completata sui due candidati e sul diff nativo; nessun finding residuo.

## Osservato: identità e input

Nodo e container sono ancora quelli della baseline; UID/GID 1000, senza
modifiche di sicurezza. Gli hash config/stato sono invariati.
I binari operativi non sono stati eseguiti, sostituiti o ricompilati.

Il manifest installato `codex-package.json` dichiara layoutVersion 1,
versione 0.153.4, target x86_64-unknown-linux-musl, entrypoint bin/codex,
resourcesDir codex-resources. Gli asset ufficiali del tag
`rust-v0.153.4` sono stati scaricati solo nel checkout diagnostico:
gli archivi corrispondono ai digest della release e i binari estratti
corrispondono agli hash già acquisiti:

| Asset | Archivio SHA-256 | Binario SHA-256 |
|---|---|---|
| codex-x86_64-unknown-linux-musl.tar.gz | `f479424eca092484dc40d87ae28c44f4cc40234a60045d6131e493800d814a30` | `56ef98ab4032d317ab26e9b5e5a175650717351edb16ed9cde0cb6d1734d62da` |
| bwrap-x86_64-unknown-linux-musl.tar.gz | `e7d65c75e05637e42b93f6abf9222fa0d26b537648a7a34c122b75021d41756d` | `77360cb751ccedc5971391444ac86a8a33c15b04d6b4a6fe45f5d25496e62c4c` |

Il tag punta al commit `3d2ee51ca2d5db578f328aa75e20aa22c0197c9a`.
Questo identifica la release esaminata; non è una ricompilazione riproducibile
del binario. Lo zsh incluso è `codex-resources/zsh/bin/zsh`,
SHA-256 `67faaaa89242c4a332e16e508a1977cffc24bf7fca31d4411cdfd101f3831ef3`.

Mountinfo è stato ridotto a mountpoint, tipo, opzioni e propagazione dei
percorsi pertinenti. Non sono esportati sorgenti dei volumi o dati dei file.
`/bin,/sbin,/lib,/lib64` risolvono sotto `/usr`; Nix e current-system
sono assenti. Root overlay ro,relatime; checkout e home su ext4 rw,relatime;
i mount annidati di /etc sono elencati negli input.
Il PATH dell'init e le directory convenzionali già note non contengono bwrap.
Il PATH di una futura shell manuale non viene attestato retroattivamente:
la selezione deve essere ricontrollata nel collaudo senza usare il wrapper
che aggiorna Codex.

## Derivato: launcher e invocazione

Riferimenti al commit della release:
[builder](https://github.com/openai/codex/blob/3d2ee51ca2d5db578f328aa75e20aa22c0197c9a/codex-rs/linux-sandbox/src/bwrap.rs),
[launcher](https://github.com/openai/codex/blob/3d2ee51ca2d5db578f328aa75e20aa22c0197c9a/codex-rs/linux-sandbox/src/launcher.rs),
[bundled launcher](https://github.com/openai/codex/blob/3d2ee51ca2d5db578f328aa75e20aa22c0197c9a/codex-rs/linux-sandbox/src/bundled_bwrap.rs),
[stadi](https://github.com/openai/codex/blob/3d2ee51ca2d5db578f328aa75e20aa22c0197c9a/codex-rs/linux-sandbox/src/linux_run_main.rs).

Il launcher preferisce un bwrap su PATH se supporta le opzioni richieste;
altrimenti trova la risorsa del package/posizione legacy, verifica il digest
atteso quando incluso nella build ed esegue il file aperto tramite
`/proc/self/fd/B`. **B è un descriptor di esecuzione, non un mount**.
Il wrapper Rust del package chiama il bwrap_main vendorizzato. Non viene
usato un bubblewrap diverso o ricompilato.

Il primo stadio interno effettua un preflight proc con sole readable roots
`:minimal` e `/usr/bin/true`. Non è un incarico né un retry del collegamento.
Segue l'invocazione effettiva, con questo schema **derivato, non catturato**:

```text
bwrap --as-pid-1 --new-session --die-with-parent
  --tmpfs / --dev /dev
  --ro-bind /bin /bin
  --ro-bind /etc /etc
  --ro-bind RELEASE/codex-resources/zsh/bin/zsh RELEASE/codex-resources/zsh/bin/zsh
  --ro-bind /lib /lib
  --ro-bind /lib64 /lib64
  --ro-bind /sbin /sbin
  --ro-bind /usr /usr
  --ro-bind CWD CWD
  --unshare-user --unshare-pid --unshare-ipc --unshare-net
  --proc /proc --cap-drop ALL --argv0 codex-linux-sandbox
  -- RELEASE/bin/codex
     --sandbox-policy-cwd CWD --command-cwd CWD
     --permission-profile P --apply-seccomp-then-exec -- /bin/true
```

`RELEASE=/home/coder/.codex/packages/standalone/releases/0.153.4-x86_64-unknown-linux-musl`.
`CWD=/workspaces/developer-workspace/.worktrees/handoff-75` per il collaudo
sul checkout esistente. Le readable roots sono ordinate lessicograficamente:
nel checkout g1 sotto /home la coppia CWD compare prima di /lib.
P indica la serializzazione della policy effettiva, non un valore da copiare:
filesystem restricted, minimal read, workspace read, zsh read, rete restricted.
Il preflight omette CWD/zsh e lo stadio interno; termina direttamente in true.
Non vi sono writable roots, deny masks o registry sintetici negli input attuali.
Il diff nativo proposto aggiunge, nello stadio principale, il bind readonly
del solo RELEASE/bin/codex (prima dello zsh nell'ordine lessicografico) e,
dopo i bind, `--perms 000 --tmpfs /etc/developer-workspace --remount-ro
/etc/developer-workspace`. La directory esiste ed è verificata non symlink;
non serve bind-data. P comprende anche queste due regole native.
Il preflight interno resta quello hardcoded minimal e `/usr/bin/true`: non
applica la maschera, ma non esegue comandi o codice dell'incarico. Non va
qualificato come prova della maschera o del confine POC.

Per il distinto percorso `codex exec`, core aggiunge la directory del proprio
execve-wrapper, generata da arg0 con prefisso `codex-arg0` sotto
`/home/coder/.codex/tmp/arg0/`; exec-server aggiunge l'helper eseguibile.
La prima richiede una coppia ro-bind aggiuntiva ARG0DIR/ARG0DIR.
Il secondo è già coperto dal bind del solo RELEASE/bin/codex proposto.
Il suffisso ARG0DIR è futuro e non viene presentato come osservato; il parent
esistente è verificato non symlink e sul mount home ext4 rw,relatime.
Il cwd già canonico non richiede un ulteriore `--chdir`.

`--as-pid-1` è aggiunto dal launcher, `--argv0` dallo stadio interno.
Il sorgente contiene gestione di `--ro-bind-fd`, ma **nessun produttore nel
percorso qui ricostruito**. `--ro-bind-data` è prodotto per maschere di file
negati; il delta nega una directory esistente, quindi usa tmpfs. Non sono
state aggiunte concessioni per bind-data o ro-bind-fd.
I bind C vengono risolti prima del pivot; i descriptor usati per riaprire
destinazioni e leggere mountinfo non richiedono wildcard /proc/**/fd/**.

Il checkout futuro g1 ha la destinazione deterministica
`/home/coder/.local/state/workspace-handoff/iwant/runs/0048cc226d51c6d1daf9aa33cf5fb1f6f43b56d849c26dee079b21f132c81b21/checkout`,
derivata dalla chiave dell'identità già definita nel collegamento.
È ammesso come secondo target esatto, senza pattern per altre generation;
non è stato creato. Risoluzione, assenza di symlink e mount sottostante vanno
verificati dopo la preparazione autorizzata, prima del futuro utilizzo.

## Derivato: sole differenze necessarie

[Bubblewrap](https://github.com/openai/codex/blob/3d2ee51ca2d5db578f328aa75e20aa22c0197c9a/codex-rs/vendor/bubblewrap/bubblewrap.c),
[bind/remount](https://github.com/openai/codex/blob/3d2ee51ca2d5db578f328aa75e20aa22c0197c9a/codex-rs/vendor/bubblewrap/bind-mount.c).

| Regola seccomp aggiunta | Operazione raggiungibile e limite AppArmor |
|---|---|
| clone arg0 EQ 0x78020011 | Primo ingresso osservato: NEWNS/NEWIPC/NEWUSER/NEWPID/NEWNET e SIGCHLD. |
| unshare arg0 EQ 0x10000000 | --dev richiede devpts: mappatura temporanea a UID/GID 0, poi secondo user namespace per tornare UID/GID richiesti; C righe 3305–3320, 3501. |
| mount flags EQ 0x8c000 | Propagazione rslave ricorsiva e silent su / prima del setup. |
| mount flags EQ 0x6 | tmpfs nosuid,nodev: /tmp, /newroot, /newroot/dev e maschera amministrativa proposta. |
| mount flags EQ 0xc0edd000 | Bind ricorsivo di /tmp/newroot su sé stesso, include MS_MGC_VAL del sorgente. |
| mount flags EQ 0xd000 | Bind ricorsivi silent delle sole radici/devices elencati; eventuale copertura proc. |
| mount flags EQ 0xa | Devpts nosuid,noexec su /newroot/dev/pts. |
| mount flags EQ 0xe | Proc nosuid,nodev,noexec su /newroot/proc. |
| mount flags EQ 0x209027 | Remount bind readonly,nosuid,nodev,relatime,silent delle radici, degli helper, della maschera e dei mount annidati /etc osservati. |
| mount flags EQ 0x20902f | Stesso remount con noexec per le coperture proc condizionali. |
| mount flags EQ 0x4c000 | Propagazione private ricorsiva e silent su /oldroot. |
| pivot_root | Due chiamate; seccomp non può leggere pathname. AppArmor limita newroot/oldroot a /tmp e /newroot. |
| umount2 arg1 EQ 2 | MNT_DETACH della vecchia radice; AppArmor conserva la baseline umount già consentita. |

Nessuna aggiunta di setns, chroot, clone3, hostname, mqueue, overlay o nuove API
mount. I device della baseline sono rw,nosuid: bind_mount con BIND_DEVICES
non richiede un remount aggiuntivo. Stdout del collaudo è una pipe:
nessun /dev/console da terminale. Il profilo non si estende automaticamente
a una futura esecuzione con PTY.

Le coperture proc sono limitate ai quattro percorsi del sorgente:
sys, sysrq-trigger, irq, bus; avvengono soltanto se access(W_OK) le giudica
scrivibili nel nuovo proc. Si preserva il ramo, senza inventare l'esito di
quel controllo futuro. Il fallback nativo senza proc non vale come PASS
del collaudo proposto.

Il testo conserva anche gli spazi finali presenti nella baseline AppArmor;
i relativi avvisi di git diff --check sono attesi, così come quelli delle
righe di contesto nei diff distribuiti.
AppArmor conserva tutto il testo preprocessato della baseline, eccetto
nome/self-peer e sostituzione del deny mount. Nessun allow inefficace
accanto al deny. I target sono esatti salvo la directory arg0: `codex-arg0*` copre una sola
componente sotto il parent privato noto; `*` non attraversa slash.
Non si fissa un suffisso casuale. Codex monta la propria directory esatta,
mentre AppArmor non correla i due suffissi della regola: può ammettere bind
fra due directory arg0 di quel parent. È un limite esplicito della proposta,
non lettura dell'intera home. Non ci sono numeri FD codificati. Le modalità di corrispondenza dei pathname
dopo pivot e delle opzioni AppArmor restano da dimostrare nel runtime.
La [policy bubblewrap upstream AppArmor](https://gitlab.com/apparmor/apparmor/-/blob/master/profiles/apparmor.d/glycin.bwrap)
è stata usata solo per riscontro della sintassi; non è la baseline né
un'autorizzazione a copiarne mount/remount generici o capability.

## Finding degli input attuali e delta proposto

1. **Confine amministrativo sotto /etc.** Il builder monta /etc ricorsivamente.
   Gli antenati osservati sono attraversabili, il kubeconfig
   /etc/developer-workspace/kubeconfig/config è 0644 root:1000.
   La lettura è prevista dalla combinazione policy/DAC; nessun contenuto è
   stato letto. Non si afferma che il file contenga un token specifico.
   Il candidato AppArmor conserva la baseline file: la sola compilabilità
   dei mount non protegge questo dato. Negarlo nell'AppArmor dell'intero
   code-server potrebbe rompere il workspace amministrativo interattivo.
2. **Rientro del debug helper.** Nel tag verificato,
   [debug_sandbox](https://github.com/openai/codex/blob/3d2ee51ca2d5db578f328aa75e20aa22c0197c9a/codex-rs/cli/src/debug_sandbox.rs)
   non aggiunge bin/codex alle readable roots; lo stadio interno vi rientra
   tramite current_exe, che risiede fuori da minimal/CWD/zsh.
   È quindi previsto un errore di exec dopo il setup, non ancora osservato.
   Il percorso exec-server aggiunge helper roots ma non corregge il probe
   preliminare del collegamento. Un allow mount AppArmor non aggiunge
   automaticamente un mount all'argv Codex.

Il minimo delta nativo è preparato in [handoff-inputs.diff](handoff-inputs.diff):
aggiungere al solo handoff una negazione di
`/etc/developer-workspace` e la lettura del solo `RELEASE/bin/codex`.
Nella sintassi corrente i valori sono rispettivamente `deny` e `read`.
Il diff non è stato applicato: sorgente operativo, configurazione e stato
sono invariati. Le quattro regole AppArmor per i mount derivati dalla
maschera e dall'helper sono già comprese nei candidati e compilate offline.
Seccomp non richiede altre aperture: i flag erano già necessari.
Il diff risultante è stato verificato in memoria per sintassi Python e
valore TOML; non è stato importato o eseguito il consumer.
Il pathname dell'helper è intenzionalmente fissato alla release verificata;
un aggiornamento CLI richiede una nuova derivazione, non una wildcard
sull'intero package.
Non si concede lettura dell'intera home/package né si ricolloca il consumer.

## Impatto, decisione, collaudo e rollback

Il candidato amplia le syscall disponibili a tutti i processi code-server,
inclusi shell ed estensioni. I percorsi AppArmor limitano i mount ma non
attestano che il chiamante sia bwrap o sia già nella sua mount namespace.
La propagazione su / e i due pivot sono aperture reali; restano drop ALL,
noNewPrivileges, read-only root del container e gli altri deny.
Queste condizioni non certificano il confine del figlio Codex.

**Decisione richiesta prima dell'applicazione:** approvare congiuntamente
seccomp.json, apparmor.profile, handoff-inputs.diff e references.diff negli
hash pubblicati, con distribuzione sui worker eleggibili e una finestra
esplicita per ricreare il Pod. Il consumer deve rimanere disabilitato:
l'approvazione coprirebbe soltanto il collaudo di sicurezza descritto sotto,
non incarichi IWANT, merge del collegamento, build immagine o rollout ulteriori.
Non applicare i soli profili lasciando invariato l'input handoff.
Il costo resta due profili nativi versionati e distribuzione Ansible già
adottata; nessun nuovo gestore della sandbox. Se la mitigazione imponesse
regole generiche o un sottosistema custom, riesaminare la proporzionalità
prima di estendere le aperture.

La proposta di collaudo dopo approvazione dell'insieme è circoscritta:

- Baseline e hash del nuovo task/LSM coerenti; init ancora RuntimeDefault.
- Una sola prova nativa con binario diretto, profilo finale, cwd verificato
  e stdout su pipe; proc effettivamente montato, nessun fallback qualificato PASS.
- Sentinelle non segrete dimostrano lettura minima/checkout e divieti di
  lettura/scrittura esterne; anche una sentinella nel perimetro amministrativo
  mascherato, senza usare il kubeconfig reale come materiale di test.
- Rete IPv4/IPv6, DNS, loopback e socket pertinenti negati dai comandi;
  tool/MCP/plugin non devono aggirare il confine. Nessuna esecuzione LLM.
- Verifica delle funzioni essenziali del workspace interattivo.
  Consumer disabilitato e stato conservato durante tutto il collaudo.

Distribuzione: Ansible, profili immutabili su tutti i worker eleggibili prima
dei riferimenti; la directory seccomp deve essere ricavata dalla root kubelet
effettiva. Replica singola RollingUpdate: ricreazione solo nella finestra
approvata, previa conservazione delle sessioni interattive.
Rollback: ripristinare anche il solo input handoff proposto, se applicato,
senza toccare enrollment o stato; rimuovere entrambi gli override, ricreare il Pod nella stessa
finestra, verificare baseline e stato disabilitato; rimuovere i profili
distribuiti solo quando inutilizzati. Non servono merge/build immagine del
collegamento, né un rollout è avvenuto in questa preparazione.
