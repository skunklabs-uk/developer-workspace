# Collegamento seriale ChatGPT → Codex

**Stato: Active.** Owner: maintainer Developer Workspace.
Il protocollo nasce dal POC [#75](https://github.com/skunklabs-uk/developer-workspace/issues/75)
e dalla continuazione [#79](https://github.com/skunklabs-uk/developer-workspace/issues/79).
La missione [Homelab #1143](https://github.com/skunklabs-uk/homelab/issues/1143)
ha promosso il consumer automatico IWANT isolato con la
[PR Homelab #1246](https://github.com/skunklabs-uk/homelab/pull/1246), dopo la
verifica browser attraverso Cloudflare Access. Il nuovo incarico report-only
ha verificato autostart, consegna e RETURN; le evidenze sono riportate sotto.
Il closeout infrastrutturale della missione resta di proprietà Homelab.

Il lifecycle operativo precedente a `/workspace run`, inclusa la qualification
del Coordinator e l'eventuale selezione per-incarico di modello/reasoning, è
posseduto da [WORKSPACE-HANDOFF-LIFECYCLE.md](WORKSPACE-HANDOFF-LIFECYCLE.md).
Questo runbook vi rimanda senza duplicarne il contratto.

La missione [#103](https://github.com/skunklabs-uk/developer-workspace/issues/103)
sostituisce il cambio di binding per-thread con la Handoff Inbox stabile
[#107](https://github.com/skunklabs-uk/developer-workspace/issues/107).
Il codice mantiene temporaneamente compatibilità con la configurazione storica
per non interrompere il runtime prima del cutover Homelab. La #107 resta
**non attiva** finché integrazione, promozione runtime ed E2E finale della #103
non sono completati.

## Collaudi storici #75 e #79

Il 7 settembre 2026 g1 e g2 sono stati eseguiti, consegnati e riletti dalla chat,
con HEAD, digest e checkout puliti verificati. Il consumer foreground è stato
terminato e disabilitato a fine collaudo, conservando configurazione e risultati.
Quel collaudo non comprendeva un avvio automatico.

La continuazione [#79](https://github.com/skunklabs-uk/developer-workspace/issues/79)
aggiunge la consegna dei file autorizzati e rimuove la dipendenza dalla skill
ritirata `agent-loop`. Il codice è stato rilasciato dalla #80. Il 10 settembre
2026 i probe nativi `read-only` e `workspace-write` sono passati nel Pod: il
checkout è scrivibile soltanto in modalità write, mentre `.git`, `.agents` e
`.codex`, filesystem esterno, rete e credenziali del padre restano protetti.

Homelab ha distribuito e ricaricato i profili AppArmor e seccomp della #83 su
`k3s-worker1`, `k3s-worker2` e `k3s-worker3`; soltanto
`developer-workspace-0` è stato ricreato per acquisire il nuovo seccomp. Hash,
enforce e rollback sono nella
[fonte delle policy](workspace-handoff-candidates/README.md). In quel checkpoint
il consumer era fermo e disabilitato e il percorso write reale non era ancora
stato verificato. Queste evidenze storiche non descrivono lo stato live della
#1143.

| Iterazione | HEAD eseguito | Report riletto dalla chat |
| --- | --- | --- |
| g1 | `9384c1808da6926e7eb222b974ac78f7661200fd` | [5570838436](https://github.com/skunklabs-uk/iwant/pull/524#issuecomment-5570838436) |
| g2 | `dd0ce7de6e517f235d7906ed71a1de4986d67d64` | [5571022274](https://github.com/skunklabs-uk/iwant/pull/524#issuecomment-5571022274) |

Entrambi exit 0: g1 verifica la subordinazione dei prompt alle fonti autorevoli;
g2 conferma g1 e distingue successo del processo da closeout. Le risposte e i
riferimenti sono stati confrontati con le fonti dello stesso commit.

### Accettazione write della #79

Il [closeout della #79](https://github.com/skunklabs-uk/developer-workspace/issues/79#issuecomment-5629528460)
registra la prova write su IWANT: generation 4 eseguita
una sola volta, commit `c22df05bddd8636448e4e250c87c5a12431f6f0f` pubblicato
dal parent sulla Draft PR #548 e diff remoto riletto dal coordinatore ChatGPT.
La CI naturale ha poi rilevato un problema nel generated templ; le correzioni
successive e i gate verdi sono registrati nello stesso closeout. La consegna
del commit non equivaleva all'accettazione applicativa della PR.

Il consumer era fermo e disabilitato al termine di quella prova, con storico
e risultati conservati. L'autostart e il nuovo incarico report-only della
#1143 sono verifiche successive e distinte. Queste evidenze riguardano IWANT:
non dimostrano l'estensione ad altri progetti della
[Homelab #1252](https://github.com/skunklabs-uk/homelab/issues/1252).

## Perimetro

Nel percorso stabile il collegamento legge un solo thread configurato: la
Handoff Inbox. Ogni richiesta esplicita identifica un repository target ammesso,
il thread autorevole della issue/PR, branch, head e prompt. Il consumer prepara
un clone separato alla revisione indicata e invoca `codex exec`.

Receipt e RESULT vengono pubblicati sul **thread autorevole target**, non nella
inbox. Il RESULT aggiorna la stessa receipt; un timeout del PATCH non richiede
una seconda esecuzione né un secondo commento. La inbox conserva soltanto
l'envelope originario e non diventa una seconda fonte dello stato del lavoro.

La richiesta autorizzata e i criteri di accettazione restano posseduti dalla
missione; il prompt versionato resta subordinato ad AGENTS. Il collegamento non
pianifica wave, non decide merge/deploy e non risveglia questa conversazione.
Il coordinatore rilegge il report e lo confronta con repository e revisione
reali prima di accettarlo; nella #1143 questo passaggio costituisce il RETURN.

Il connettore ChatGPT è stato verificato sia su conversazioni di PR sia su una
issue ordinaria: il commento
[5729228269](https://github.com/skunklabs-uk/developer-workspace/issues/103#issuecomment-5729228269)
ha confermato la scrittura sulla #103. La inbox può quindi essere una issue
dedicata e non richiede una PR fittizia. La issue/PR del repository target resta
comunque la fonte autorevole del lavoro.

## Consumer automatico seriale

Homelab possiede launcher, StatefulSet e promozione GitOps. Il
[disegno del Developer Workspace](https://github.com/skunklabs-uk/homelab/blob/main/doc/35-Developer%20Workspace%20K3s%20GitOps%20design.md#consumer-workspace-handoff)
è la fonte del confine runtime: container `workspace-handoff` non privilegiato,
stessa immagine immutabile del workspace, `hostUsers:false`, home persistente
e `/tmp` separato. Nessun mount `/workspaces`, kubeconfig, token ServiceAccount,
CA Proxmox o socket Docker/containerd. La sandbox dei comandi figli resta
quella descritta sotto; il padre riusa le autenticazioni già disponibili.

Il launcher richiede la configurazione persistente con
`execution_enabled=false` e prepara una copia runtime privata `0600` con
esecuzione abilitata, quindi avvia `workspace-handoff watch`. Non esegue
automaticamente `init` o `once`, non usa tmux e non crea un secondo worker o
ledger. I percorsi effettivi e il binario Codex fissato restano autorevoli nel
manifest Homelab.

Fino al cutover della #103 il manifest live conserva il binding storico
repository/thread. La configurazione stabile userà invece repository/thread
della inbox e una lista piatta `allowed_repositories` dei target ammessi.
Il cambio è unico per il runtime: un nuovo incarico non deve più richiedere
stop, enrollment e rollout GitOps per cambiare progetto.

Se un prerequisito manca o watch termina, il launcher conserva lo stato e
rimane fermo. Non rilancia automaticamente il processo modello. I retry bounded
del trasporto già implementati in watch restano distinti da una nuova
esecuzione Codex; il recupero segue la sezione dedicata sotto.

La #1143 ha verificato il browser reale attraverso Cloudflare Access prima
della promozione. Per gli incarichi successivi usare il thread già enrolled,
branch/head reali e un prompt corrente esplicitamente autorizzato. Preferire il
solo report quando non serve modificare IWANT. Osservare receipt e result dello
stesso incarico; il coordinatore verifica il risultato e, se presente,
`publication.head` remoto, quindi registra il RETURN. Pod Ready e test locali
non sostituiscono la prova del collegamento.

### Accettazione autostart, handoff e RETURN

Il rollout Homelab `f9c9489535aa3db5ef7aa840309f79d8e6b08d32` è stato
osservato `Synced / Healthy`, con entrambi i container Ready e watch avviato
automaticamente. La configurazione persistente è rimasta disabilitata, la
copia runtime privata `0600` abilitata; il consumer non montava `/workspaces`,
kubeconfig, token ServiceAccount o CA Proxmox.

La [richiesta](https://github.com/skunklabs-uk/iwant/pull/548#issuecomment-5670563289)
`HOMELAB-1143-HANDOFF-RETURN`, generation `1`, ha prodotto una sola esecuzione
e una [ricevuta aggiornata con il risultato](https://github.com/skunklabs-uk/iwant/pull/548#issuecomment-5670574049).
Il probe sandbox e il modello sono terminati con exit 0; lo stato è `delivered`,
HEAD `e4da88195fd11c7395b333903367359c59c5d16d` e checkout pulito. Il report-only
non prevedeva una publication. Non sono serviti avvio manuale, secondo worker,
reset dello stato o nuova generation per aggirare errori.

Nel [RETURN](https://github.com/skunklabs-uk/iwant/pull/548#issuecomment-5670602343)
il coordinatore ha confrontato il report con le fonti dello stesso head e
accettato il risultato. Questa prova dimostra il percorso automatico
richiesta → receipt → Codex → result → RETURN. Non dimostra una nuova
pubblicazione write della #79 e non autorizza altri incarichi. Prompt e branch
del collaudo sono temporanei; stato, ricevute e risultati restano conservati
per il recupero.

## Estensione autorizzata #1252

La [missione Homelab #1252](https://github.com/skunklabs-uk/homelab/issues/1252)
ammette IWANT e Skunklabs. Il consumer seleziona un solo repository/thread;
non ascolta l’organizzazione e non crea worker per progetto. Le prove IWANT
sopra restano storiche. Il 15 settembre 2026 il rollout Homelab ha selezionato
Skunklabs sul thread121, con watch automatico e stato separato. La
[richiesta via connettore](https://github.com/skunklabs-uk/skunklabs/pull/121#issuecomment-5672259424)
ha prodotto il commit README `e3bde001f5c945732542e434c823f9820b7e5603`;
[risultato e RETURN](https://github.com/skunklabs-uk/skunklabs/pull/121#issuecomment-5672297046)
attestano consegna e review del diff remoto. Il producer
[34909336589](https://github.com/skunklabs-uk/skunklabs/actions/runs/34909336589)
ha verificato lint/build e pubblicato il digest del medesimo head;
[runtime e browser](https://github.com/skunklabs-uk/homelab/issues/1252#issuecomment-5672474271)
sono stati verificati nella preview GitOps protetta da Access.

Il ritorno al binding IWANT548 tramite Homelab #1261 ha completato una nuova
[richiesta report-only e RETURN](https://github.com/skunklabs-uk/iwant/pull/548#issuecomment-5672485254),
con checkout pulito. Gli otto risultati IWANT precedenti e il risultato
Skunklabs sono conservati; non sono stati riaperti thread o azzerati stati.
Il browser IWANT #1143 resta una prova storica del percorso invariato, distinta
dalla nuova regressione del cambio seriale. Il perimetro terminale approvato
della #1252 era IWANT + Skunklabs; i 30 rimanenti appartengono alla
continuazione distinta #1265 descritta sotto.

Per cambiare progetto, attendere la consegna dei risultati e fermare watch
tramite GitOps. Conservare configurazioni, enrollment, receipt e risultati
IWANT. Il nuovo stato Skunklabs usa esattamente la root sorella `skunklabs`;
il profilo AppArmor aggiunge soltanto quel nome. Distribuzione e
reload sui worker appartengono a Homelab e precedono l’attivazione del nuovo
binding. Non modificare un binding esistente né riutilizzare il suo file di
stato. Eseguire `init` una sola volta per il thread reale approvato, con il
consumer fermo, poi selezionare il binding nel launcher GitOps. Il launcher
usa una copia privata runtime e non esegue enrollment automatico.

Il rollback torna all’immagine precedente e al binding IWANT tramite GitOps,
dopo aver fermato il consumer e conservato le consegne pendenti. La versione
precedente non possiede il lock comune: non avviarla insieme alla nuova.
Il formato dello stato non cambia e non richiede migrazione.

Il producer esegue la suite Python nelle PR e prima della build main; le PR
non pubblicano immagini. La build e la pubblicazione restano nel producer.

## Continuazione per tutti i repository

La [Homelab #1265](https://github.com/skunklabs-uk/homelab/issues/1265) prosegue
l'adozione sui 32 repository inventariati. Il Product Owner ha approvato i 30
nomi aggiuntivi della [sorgente AppArmor](workspace-handoff-candidates/apparmor-iwant.profile)
e il lifecycle seriale di enrollment e selezione GitOps. La #1252 conserva
le prove concluse IWANT + Skunklabs; non attestano i nuovi incarichi.

L'approvazione non estende dati, credenziali o preview. Il checkout corrente
materializza l'intero repository e rende leggibili anche gli oggetti Git;
`publish_paths` limita la pubblicazione, non gli input. Prima di incarichi su
repository con dati personali o cliente serve un confine effettivo degli input
oppure l'autorizzazione esplicita a dati e destinazione. Il solo prompt o sparse
checkout non dimostra l'esclusione. Una `.codex` presente continua a richiedere
review e viene rifiutata dal preflight corrente.

I referenti dei repository possono preparare e revisionare in parallelo i propri
worktree; il collegamento nel cluster esegue un solo incarico alla volta.
Il coordinatore mantiene selezione, autorizzazioni e integrazione condivise.
Ogni nuovo binding segue la stessa sequenza di arresto, conservazione dello
stato, enrollment, autostart, richiesta reale e RETURN. La configurazione di un
nome non sostituisce il collaudo; lo stato aggiornato dell'adozione resta nella
missione, fino al closeout delle fonti proprietarie.

### Report con input minimo senza cambiare il consumer

Per un report che non richiede il corpus del repository, il coordinatore può
preparare uno snapshot Git temporaneo senza parent, nello stesso repository.
Si riusano Git e il percorso report-only esistente; nessun nuovo campo della
richiesta, filtro runtime, publisher o credenziale.

1. Qualificare i byte e i mode dei soli file regolari necessari, comprese le
   istruzioni applicabili. Registrare head sorgente e blob ID nel prompt.
   Non omettere una policy obbligatoria per aggirare un gate; dati necessari
   non ammessi restano una decisione esplicita.
2. Creare un tree con soltanto quei blob e il prompt Active, poi un commit
   senza parent su un nuovo branch snapshot. Non copiare pack, storia o
   configurazioni dal repository sorgente. Le API Git native equivalenti
   usano tree senza `base_tree` e commit con `parents: []`.
3. Prima della richiesta, clonare il branch remoto esatto con il percorso
   del consumer e verificare tree, mode, head, assenza di parent e tutti gli
   oggetti locali, inclusi quelli non raggiungibili. Ammettere solo gli oggetti
   attesi e l'empty tree tecnico usato per neutralizzare gli attributi; nessun
   blob escluso, alternates o promisor. Questa qualificazione non sostituisce
   il probe nativo che il consumer esegue prima del modello.
4. Usare una PR documentale pertinente, discendente dal main, come thread.
   La richiesta indica branch/head snapshot e omette `publish_paths`: il
   risultato è solo un report. Il controllo della PR write non si applica;
   il coordinatore verifica anche la distinta provenienza sorgente.
5. Il parent può applicare la proposta revisionata sul normale branch della
   PR. Conservare i file esclusi senza leggerli o riscriverli: con le API Git,
   usare il tree sorgente come `base_tree` e modificare soltanto i file
   documentali autorizzati. Non integrare mai il branch senza parent.
6. Completare RETURN del report e verifiche della PR separatamente. Trasferire
   i fatti durevoli nel README, ritirare prompt e branch snapshot, conservare
   enrollment, risultato, clone dell'esecuzione e provenienza.

La preparazione [Bookmarks #2](https://github.com/skunklabs-uk/bookmarks/pull/2)
ha verificato il clone remoto dello snapshot
`e2505ca47e17c37afa95c5f8552d89280c8f8a52`, derivato da
`ca50f63449de7e0e3c0e682f93564794282b28f2`: tre file ammessi e nove oggetti
locali, senza il blob XBEL, commit sorgente, alternates o promisor. Il solo
oggetto non raggiungibile è l'empty tree tecnico. Handoff e probe Bookmarks
restano da eseguire; questa prova non attesta la sincronizzazione floccus.

## Enrollment e avvio manuale del collaudo

Servono Linux, Python 3.10 o successivo, Git, GitHub CLI autenticata e Codex CLI
con autenticazione valida. Non vengono installati runtime, credenziali, servizi
o nuove Actions. Il comando si usa dal checkout della PR; gli stessi script
sono inclusi dal `COPY scripts/` dell'immagine dopo il normale rilascio.

Prima dell'attivazione verificare il confine approvato nell'ADR 0007 di Homelab,
la versione CLI reale, i tool/MCP/plug-in effettivamente disponibili, il percorso
di autenticazione e il profilo di filesystem. Il flag `execution_enabled` è
una scelta dell'operatore **dopo** queste verifiche, non una loro attestazione.
Non usare lo step-up Proxmox o credenziali amministrative.

Configurazione locale senza segreti, per esempio in
`~/.config/workspace-handoff/iwant.json`:

```json
{
  "repository": "skunklabs-uk/iwant",
  "thread": 0,
  "actor_ids": [25493712],
  "publisher_id": 25493712,
  "execution_enabled": false,
  "poll_seconds": 60,
  "timeout_seconds": 1200,
  "sandbox": "read-only"
}
```

`thread: 0` è intenzionalmente invalido: sostituirlo con la PR concordata, dopo
averne verificato accesso e stato. Gli ID identificano l'account osservato nelle
scritture ChatGPT; verificare separatamente il publisher reale di `gh` nel Pod.
Il codice richiede il nome esatto di un repository `skunklabs-uk` e rifiuta
wildcard, altre organizzazioni e campi inattesi. La configurazione è ammissione
operativa esplicita, non scoperta automatica dei repository accessibili. `gh` e `codex` sono gli
unici percorsi di eseguibili eventualmente configurabili.

```bash
python3 -m unittest discover -s tests -v
python3 scripts/workspace-handoff --config ~/.config/workspace-handoff/iwant.json \
  --state ~/.local/state/workspace-handoff/iwant init
python3 scripts/workspace-handoff --config ~/.config/workspace-handoff/iwant.json \
  --state ~/.local/state/workspace-handoff/iwant status
```

`init` registra il limite dei commenti già presenti, che **non** verranno
eseguiti. Lo stato è privato e non va ricreato per forzare un retry. Pubblicare
la prima richiesta soltanto dopo l'enrollment. Non condividere lo stesso
thread fra più directory di stato. Tutte le root operative devono essere
sorelle sotto `~/.local/state/workspace-handoff/`: `consumer.lock` in questa
directory resta acquisito per tutta la durata di `init`, `once` o `watch`,
compresa l’attesa fra poll. Impedisce un secondo consumer anche su un altro
binding. Il lock `worker.lock` del singolo stato resta invariato; nessuno dei
due va eliminato per recuperare un incarico. Non coordina host o volumi distinti.

Nel collaudo manuale, dopo il riesame dei prerequisiti, si abilitava localmente
`execution_enabled` e si usava `once` per il primo giro. `watch` ripete lo stesso
ciclo seriale con intervallo minimo di 60 secondi. L'avvio in tmux appartiene
al percorso storico: non affiancarlo al consumer automatico della #1143.
La promozione riusa lo stato già enrolled e mantiene disabilitata la
configurazione persistente. Una ricreazione del Pod interrompe i processi;
le regole di recupero vietano il rilancio di un modello dall'esito incerto.

## Richiesta

Ogni nuovo prompt deve contenere una sola dichiarazione su riga autonoma
`**Stato: Active**`. Il preflight rifiuta dichiarazione assente, duplicata o
Archived anche se il file è ancora fuori da `archive/`. La dichiarazione non
sostituisce la verifica delle autorità, dell’head e dell’incarico corrente.
I prompt storici non vengono modificati né riattivati da questo requisito.


Il commento deve essere nuovo, non modificato, provenire da un ID abilitato e
iniziare esattamente con `/workspace run` seguito da un oggetto JSON:

```text
/workspace run
{"repository":"skunklabs-uk/iwant","assignment":"WORKSPACE-HANDOFF-POC","generation":1,"branch":"agent/workspace-75-prompt-authority","head":"SHA_COMPLETO_DEL_COMMIT_APPROVATO","prompt":"docs/agents/prompts/workspace-handoff-poc-g1.md"}
```

L'esempio va completato con uno SHA reale di 40 caratteri: non è eseguibile così
com'è. Il branch deve ancora puntare a quello SHA al momento del clone. Il
prompt deve essere un file Git regolare, non un symlink o un file archiviato.
Il percorso Markdown è relativo al repository e segue le sue istruzioni:
`docs/agents/prompts/` nell'esempio non è un prefisso obbligatorio. È ammesso,
per esempio, `data/homelab-1265-adoption-g1.md` quando il repository riserva
`docs/` ad altri usi. Restano esclusi percorsi assoluti, traversal, componenti
vuote, `archive`, `.git`, `.codex` e `.agents`, backslash e caratteri di controllo.
Il percorso non amplia gli input qualificati, i permessi della sandbox o i
file pubblicabili. L'head, il file regolare e lo stato Active sono verificati
prima del modello anche per i percorsi alternativi.
Una nuova generation è una nuova iterazione esplicitamente autorizzata, non un
modo per aggirare un problema tecnico. Il POC #75 resta in sola lettura.
Il collaudo della sandbox di scrittura resta distinto dalla prova della
pubblicazione reale; l'accettazione automatica della #1143 è report-only.

Repository, assignment e generation identificano l'incarico. Ripubblicare lo
stesso incarico non lo riesegue; cambiarne il contenuto senza cambiare identità
è un conflitto registrato in `last_rejection`, senza impedire una consegna
pendente. Una generation inferiore a una già accettata per lo stesso assignment
viene rifiutata. Se era in attesa, riceve un risultato di mancato avvio perché
superata; risultati già prodotti vengono comunque consegnati. I comandi malformati vengono registrati come rifiutati senza
bloccare le successive richieste valide. Le modifiche a un comando non sono un
meccanismo di cancellazione di un processo già avviato.

## Consegna di modifiche

La richiesta può aggiungere `publish_paths`, una lista non vuota di **file
esatti** relativi al repository. Non sono pattern o directory. Il campo è
ammesso solo con configurazione locale `sandbox: workspace-write` già
approvata. Ometterlo conserva la consegna del solo report, anche quando il
checkout è scrivibile: la scrittura locale non autorizza implicitamente il push.

La destinazione write è il branch della PR aperta e Draft selezionata da
`thread`; deve appartenere allo stesso repository, non essere il default
branch e avere lo SHA autorizzato. Il collegamento non crea PR artificiali,
non pubblica su fork, non esegue merge né force-push. Prima di eseguire un
incarico il coordinatore verifica anche questi prerequisiti: il publisher li
ricontrolla al momento della consegna, non garantisce che restino invariati
mentre il modello lavora.

La consegna report-only può usare il thread storico di una PR già integrata;
non richiede di riaprirla o ricreare il branch ritirato. Il nuovo incarico
indica comunque il branch e l'head esatto del checkout da leggere.

Il modello modifica i file e svolge le verifiche del prompt, senza commit o
push. Il padre, con identità Git e autenticazione già configurate, crea una
revisione tramite indice temporaneo e `git commit-tree`, con la base autorizzata
come unico parent. L'implementazione è verificata con Git 2.47.3 e usa il
supporto nativo `GIT_ATTR_SOURCE`; verificarlo prima di usarla con altre versioni.
Il clone usa un template vuoto controllato per non ereditare attributi locali
dal Git del padre. Lo snapshot ignora gli attributi del repository, non esegue
hook, fsmonitor o filtri clean, e conserva i byte e i permessi eseguibili dei
file regolari.
Il percorso write non è un publisher LFS o di submodule.

Tutte le modifiche rilevate da Git devono essere comprese in `publish_paths`;
un file inatteso o un symlink blocca la pubblicazione. L'autorizzazione dei
percorsi non è uno scanner di segreti: non includere credenziali, stato locale
oppure file che il prompt non deve modificare. La sandbox protegge separatamente
il filesystem e i metadati Git del checkout.

La revisione e lo stato `prepared` sono salvati nella sezione `publication`
del `result.json` esistente prima del push. Git pubblica senza force e il
publisher verifica lo SHA remoto. Se la risposta si perde ma quello SHA è già
sul branch, la consegna è riconosciuta senza un secondo push. Se il branch
avanza diversamente, non viene sovrascritto. Un timeout ancora incerto lascia
il risultato recuperabile; un push rifiutato con branch invariato produce
`blocked`, non un ciclo di retry. Un exit code del modello diverso da zero non
pubblica modifiche. Con working tree invariato non viene creato un commit vuoto.

Il report distingue `published`, `unchanged` e `blocked`. Per `published`
contiene il commit remoto esatto da revisionare. Il checkout e il suo indice
non vengono resettati: `Head locale` può ancora essere la base e `dirty` può
essere vero, pur esistendo il commit remoto. La revisione di consegna è
`publication.head`, non la prosa del modello. Un secondo incarico riparte
esplicitamente dalla nuova revisione remota, non dal vecchio clone.

Per i risultati bloccati conservare lo stato e riconciliare la sola consegna
con il coordinatore; non cancellare directory o creare una generation per
aggirare il fallimento tecnico. Un errore di trasporto del commit o del report
non può autorizzare un nuovo modello. La ricevuta usa il PATCH già esistente;
nessun altro ledger o stato globale è introdotto.

### Prerequisiti dell'incarico reale

Il profilo installato consente `runs/<sha256>/checkout` tramite `@{hex64}`:
evita aperture sull'intera home e policy per generation. `@{hex64}` ammette
anche A-F maiuscole e i pattern sorgente e destinazione sono indipendenti; non
è un controllo di identità del job. Nel lifecycle corrente bubblewrap espone al
comando soltanto il checkout selezionato. Non allargare la policy per questo
motivo. Nessun reboot di nodo/VM o operazione Proxmox, pruning, backup o registry
è parte della #79.

Prima dell'incarico reale, Codex nel workspace verifica i permessi effettivi,
la CLI, l'identità Git del padre e l'accesso alla PR, senza stampare segreti.
I gate di test del task devono poter funzionare nel perimetro approvato; non
aprire rete o directory personali per farli passare. Leggere il puntatore
corrente del repository selezionato; per IWANT rispettare il lavoro UI attivo.
Risolvere con il Product Owner
solo le decisioni di prodotto realmente mancanti. Non riassegnare vecchi prompt.

Un cambio di thread richiede un enrollment esplicito distinto dopo la verifica
che il consumer precedente sia fermo e i risultati siano consegnati; conservare
lo stato storico, non cambiarne il binding. La #1143 riusa invece il thread e
l'enrollment esistenti. Non avviare due worker. Pubblicare il payload completo
soltanto dopo il preflight e i gate della missione, poi osservare il consumer
automatico senza avviare `once` manualmente. Verificare report ed eventuale
commit, completando il RETURN. Il successo locale dei test non dimostra il
percorso write reale della #79. Il collaudo automatico della #1143 è invece
sostenuto dalla ricevuta e dal RETURN riportati sopra. Il merge producer resta
distinto perché può attivare build/pubblicazione e il successivo rollout GitOps.

## Permessi: cosa fa il codice e cosa resta da provare

Il processo padre usa `gh` per GitHub e Git per un clone nuovo, senza reset,
pulizia o cambio branch nel checkout interattivo. Recupera per ogni esecuzione
la RFC corrente dalla fonte canonica e la passa come contesto con il blob SHA,
senza copiarla nel repository. La RFC mancante resta bloccante. La skill
`agent-loop` è stata ritirata dal catalogo: non viene ripristinata, fissata a
una revisione storica o sostituita da un nuovo prerequisito di rete. Le skill
pertinenti sono scelte nel prompt e nel progetto secondo disponibilità reale;
la mancanza di subagenti non autorizza a fingere deleghe. Fornisce anche la
richiesta verificata e il suo head: il figlio non deve interrogare GitHub per
ricostruire questi dati.

L'invocazione Codex non carica la configurazione utente (`--ignore-user-config`),
non inoltra variabili come `GH_TOKEN`, `BW_SESSION`, `SSH_AUTH_SOCK` e
`OPENAI_API_KEY`, mantiene le regole applicabili e rifiuta una `.codex` di
progetto non riesaminata. Usa un profilo nativo con letture minime e del
checkout, scritture assenti o limitate al checkout e rete dei comandi disabilitata.
Non esiste fallback `danger-full-access` o bypass delle approvazioni.

I permission profile upstream sono **beta** e non si combinano con i vecchi
`sandbox_mode`. Prima del modello, `codex sandbox` prova il profilo su
file sentinella non segreti: lettura nel checkout, lettura esterna negata,
assenza di mutazioni persistenti esterne e scrittura nel checkout coerente
con la modalità scelta. Un esito negativo
ferma il tentativo. Non allargare il profilo automaticamente per farlo passare.

Questa prova **non certifica** tutti i tool gestiti, MCP, plug-in, gli effetti di
policy organizzative o la protezione dei processi esterni a Codex. Il relativo
riesame nel Pod e la compatibilità della versione installata restano necessari.
Il login salvato di Codex è distinto da una API key; non assumere quota o costi
senza verificarne l'identità e il percorso reale. Il POC non cambia login.

Fonti upstream: [esecuzione non interattiva](https://developers.openai.com/codex/noninteractive/),
[permission profile](https://developers.openai.com/codex/permissions),
[CLI sandbox](https://developers.openai.com/codex/cli/reference).

### Runtime corrente e lifecycle

Il collaudo del 7 settembre 2026 usa Codex CLI `0.153.4`, binario diretto
`/home/coder/.local/libexec/codex/codex`, SHA-256
`56ef98ab4032d317ab26e9b5e5a175650717351edb16ed9cde0cb6d1734d62da`.
Non usare il launcher `/usr/local/bin/codex` per verifiche riproducibili:
può aggiornare la CLI anche invocando `--version`.

Homelab possiede manifest, RBAC e distribuzione delle
[policy correnti](workspace-handoff-candidates/README.md) sui worker.
I permessi approvati rimangono installati anche a consumer fermo; ciò non
autorizza nuovi incarichi. AppArmor e seccomp della #83 sono distribuiti sui
tre worker; il profilo AppArmor è in enforce e il Pod è stato ricreato per
acquisire il filtro seccomp. La
[fonte delle policy](workspace-handoff-candidates/README.md) conserva hash e
rollback. Il profilo non costituisce una sandbox generica per altri task e non
abilita da solo il consumer.

Il Pod del collaudo storico usava user namespace, `procMount: Unmasked` nel
solo code-server, seccomp locale e AppArmor ridotto con compensazioni delle protezioni proc.
Proc è realmente montato; PID, mount e network namespace del comando figlio
sono distinti dal padre. Il collaudo ha verificato letture ristrette, checkout
non scrivibile, connessioni IPv4/IPv6 e Unix pathname/abstract negate,
socket UDP negati e apertura di `/proc/keys` negata anche attraverso alias proc.
AF_UNIX può creare socket: è la connessione a essere negata.
Le sentinelle non contengono segreti.

Il padre mantiene login ChatGPT e autenticazione GitHub per modello e trasporto.
L'isolamento dei comandi figli non rende la postazione interattiva priva di
segreti. Exec ignora il config utente e disabilita app, plugin, hook e web search
con override nativi condivisi col probe. La configurazione effettiva riesaminata
non presenta requisiti gestiti o MCP attivi. Il profilo nega
`/etc/developer-workspace` e rende leggibile il solo helper Codex fissato.
Prima di cambiare CLI, profilo, tool gestiti o checkout ammesso, verificare
nuovamente il confine pertinente. Non ampliare i permessi per far passare un test.

Il probe usa lo stesso profilo `handoff` di exec e richiede proc montato.
La lettura positiva usa `.git/HEAD`, presente nel checkout verificato: non
presume che il repository contenga `AGENTS.md`. Le istruzioni AGENTS presenti
restano vincolanti; questa verifica riguarda soltanto l’accesso al checkout.
La regressione locale su repository senza AGENTS è passata nel producer
[#97](https://github.com/skunklabs-uk/developer-workspace/pull/97).
Il nuovo artifact ha poi superato il probe nativo, con exit 0, nel
[risultato OutSystems](https://github.com/skunklabs-uk/outsystems-release-manager/pull/2#issuecomment-5679193183)
della continuazione #1265. Questa prova riguarda il confine del checkout,
non il collaudo applicativo; va ripetuta quando cambia il confine pertinente.
Una scrittura nel tmpfs privato può riuscire senza modificare il filesystem
persistente: il controllo esterno viene fatto dal padre. `read-only` protegge
i dati persistenti, non vieta file temporanei privati.
Gli strumenti figli possono richiedere percorsi assoluti, come
`/usr/bin/git` e `/usr/bin/sha256sum`, perché il PATH è ristretto.

Per gli incarichi Go della continuazione #79, il profilo espone in sola lettura
soltanto `~/.local/share/mise/installs/go/1.26.5` e il module cache effettivo
`~/go/pkg/mod`. Non espone `.local`, l'albero mise, gli shim o il GOPATH
completo. Il figlio riceve un PATH esplicito con il `bin` della release fissata,
`GOPROXY=off`, `GOTOOLCHAIN=local`, `GOENV=off` e `GOTELEMETRY=off`; build cache
e temporanei Go restano nel tmpfs privato sotto `/tmp`. Il module cache è input
read-only: le dipendenze devono essere presenti prima dell'incarico e nessuna
installazione o aggiornamento viene eseguito durante il modello.

Il collaudo storico delle policy usava l'immagine `2026.09.09-b000242`;
non costituisce una nuova release applicativa né identifica la release
selezionata oggi dai manifest Homelab.
Prima di rimuovere il collegamento conservare risultati e stato. Revocare i
riferimenti runtime tramite Homelab prima di scaricare policy non più in uso.
Le [prove diagnostiche archiviate](workspace-handoff-candidates/archive/README.md)
non sono istruzioni operative.

## Recupero ed evidenze

Lo stato separa presa in carico, avvio e consegna. `running` viene persistito
prima di invocare l'esecutore; `result.json` prima di pubblicare l'esito.
Un riavvio con risultato durevole riprende solo la consegna: eventuale commit
preparato, poi PATCH della ricevuta; non avvia di nuovo il modello. Un riavvio senza
risultato riporta l'incertezza sulla ricevuta e ferma nuove esecuzioni.
Un timeout del POST iniziale viene riconciliato cercando la ricevuta dello
stesso publisher: se non è univoca non viene effettuato un secondo POST.
Un rifiuto HTTP definitivo, invece, non è una consegna incerta.

Non promettiamo exactly-once distribuito. Non cancellare `state.json` o
`runs/` per sbloccare il consumer: verificare processo, checkout e risultato
conservati. L'assenza di un file di risultato non dimostra l'assenza di effetti.
Non inventare un `result.json` di successo e non creare una nuova generation
solo per forzare il rilancio. Se lo stato non è riconciliabile, lasciare
l'incarico bloccato e registrare il fatto nella missione.

I log, il summary integrale, eventuali errori sanitizzati e la prova dei permessi
restano nella directory privata del tentativo. Si pubblicano il report finale
e, soltanto quando esplicitamente autorizzato, il commit dei file previsti. `exit_code: 0` significa processo terminato, non accettazione della
missione; una PR/commit menzionati dal modello vanno verificati dal coordinatore.
Modifiche non pubblicate restano locali e non sono revisionabili da ChatGPT
tramite GitHub: non dichiarare completata una consegna che le richiede.

## Quote e limiti del collaudo

Il trasporto riusa `gh api`, richieste condizionali, paginazione seriale e
intervallo minimo. Il caso di prima pagina `304` con una pagina successiva
modificata è coperto dai test. Il POC si arresta oltre 20 pagine invece di
estendere la scansione. I limiti ricevuti fermano le chiamate secondo gli header;
errori ripetuti non generano un loop infinito. Un retry del trasporto non
riavvia Codex. Non vengono eseguiti dispatch o rerun di Actions.

`status` mostra il numero di chiamate del collegamento e l'ultima quota
osservata, non il consumo attribuito a tutti i client o un contatore dei limiti
secondari. Quota condivisa e chiamate del connettore ChatGPT sono distinti.
La lettura della RFC è conteggiata. La pubblicazione aggiunge le letture dei
metadati repository/PR; Git e Codex non sono strumentati con un proxy. Fonte: [GitHub REST best practices](https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api).

I test usano filesystem e repository Git locali reali, risposte HTTP controllate
ed esecutori finti. Non consumano token e non dimostrano un'esecuzione Codex live.
Il collaudo storico #75, precedente al ritiro di `agent-loop` e comprensivo
delle due letture di fonti allora richieste, ha registrato 19 chiamate del
consumer, da 5 dopo l'enrollment:
5 per il preflight iniziale fallito, 4 per la ripresa controllata g1 e 5 per g2.
Ultima quota osservata 4994/5000, senza errori trasporto o pausa pendente.
Non attribuire alla missione l'intera variazione della quota condivisa.
Entrambi i risultati sono `delivered`, exit 0, con checkout puliti e digest
confrontati dal coordinatore. Questo prova il POC circoscritto, non altri
incarichi, modalità write o un servizio permanente in background.


## Necessità e riesame cumulativo

La baseline non collegava i commenti della chat a un processo locale con
restituzione del risultato. Il POC approvato in #75 riusa connettore GitHub,
`gh api`, Git e sandbox Codex; il consumer copre soltanto il tratto mancante.
Eliminandolo manca quel passaggio; un runner, servizio pubblico, workflow CI
o proxy introdurrebbe più operatività senza un requisito aggiuntivo.
Le esecuzioni reali verificano il beneficio, non i soli test interni.

| Controlli collegati | Esito e necessità |
| --- | --- |
| Autostart del consumer nella #1143 | KEEP: il nuovo incarico e il RETURN documentati sopra dimostrano l'avvio e la consegna senza comando manuale dopo rollout. Riuso di consumer e StatefulSet, nessun nuovo protocollo, ledger o identità. Lifecycle e rollback appartengono al disegno Homelab. |
| Consumer seriale e richiesta stretta | KEEP: il collegamento chat/processo non è coperto dai singoli tool; un repository/thread/attore, nessun scheduler. |
| Clone, head e prompt verificati | KEEP: impediscono esecuzione di una revisione diversa, symlink, prompt stale o configurazione progetto non riesaminata. |
| Lock, stato e ricevuta unica | KEEP: i test di interruzione e consegna incerta mostrano perché non rilanciare modello o POST; riuso di flock, file atomici e PATCH, nessun ledger distribuito. |
| Sandbox nativa, policy e compensazioni | KEEP: la baseline negava namespace/mount necessari; letture globali e privilegi personali non soddisfano il confine. Profili ridotti e probe proteggono dati persistenti e rete dei comandi. |
| Override app/plugin/hook e ambiente | KEEP: il config utente conteneva un plugin; exec e sandbox caricavano layer diversi. Override nativi, nessun nuovo checker. |
| Quote, paginazione e backoff | KEEP: rispettano gli header e limitano il trasporto seriale; i retry di consegna non rilanciano Codex. |
| Skill `agent-loop` come prerequisito del trasporto | DELETE nella #79: ritirata dall'upstream locale, causava 404 prima del modello. RFC resta obbligatoria; il prompt conserva la responsabilità delle istruzioni di esecuzione. |
| Consegna dei file nella #79 | KEEP: il closeout write documentato sopra dimostra pubblicazione del commit e review ChatGPT su IWANT. I test proteggono file autorizzati e recupero del push senza modello. Riuso result.json e Git nativo; nessuna ammissione implicita di altri repository. |
| Aperture globali proc-v3/v4 e checkpoint preparatori | DELETE dal percorso operativo; REPLACE con profilo ristretto e fonti correnti. Prove conservate in archivio. |

Owner del codice: maintainer Developer Workspace; del runtime/RBAC: maintainer
Homelab. La continuazione #79 aggiunge un modulo di pubblicazione Git ai tre
componenti precedenti; mantiene test dei contratti, una
configurazione e uno stato privati, due policy native e documentazione nei
repository già coinvolti. Nessuna nuova identità, dipendenza, Action o servizio.
Prima di altri consumer o capacità riesaminare l'insieme; sostituire il custom
quando una capacità nativa copre lo stesso requisito.

Il recupero una tantum del preflight g1 ha conservato l'intera directory e
riconciliato la sola fase sotto il lock, dopo aver provato dal percorso
d'errore che il modello non era partito. Non aggiunge retry automatici.
