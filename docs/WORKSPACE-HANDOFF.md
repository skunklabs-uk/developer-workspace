# Collegamento ChatGPT → Codex: POC IWANT

**Stato: Active.** Owner: maintainer Developer Workspace.
Missione [#75](https://github.com/skunklabs-uk/developer-workspace/issues/75).
Il 7 settembre 2026 g1 e g2 sono stati eseguiti, consegnati e riletti dalla chat,
con HEAD, digest e checkout puliti verificati. Il consumer foreground è terminato
ed è nuovamente disabilitato; configurazione e risultati sono conservati.
Nessun servizio è avviato automaticamente.

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
[fonte delle policy](workspace-handoff-candidates/README.md). Il consumer resta
fermo e disabilitato. Nessun incarico write o modello è stato ancora avviato.

| Iterazione | HEAD eseguito | Report riletto dalla chat |
| --- | --- | --- |
| g1 | `9384c1808da6926e7eb222b974ac78f7661200fd` | [5570838436](https://github.com/skunklabs-uk/iwant/pull/524#issuecomment-5570838436) |
| g2 | `dd0ce7de6e517f235d7906ed71a1de4986d67d64` | [5571022274](https://github.com/skunklabs-uk/iwant/pull/524#issuecomment-5571022274) |

Entrambi exit 0: g1 verifica la subordinazione dei prompt alle fonti autorevoli;
g2 conferma g1 e distingue successo del processo da closeout. Le risposte e i
riferimenti sono stati confrontati con le fonti dello stesso commit.

## Perimetro

Il collegamento legge un solo thread GitHub di `skunklabs-uk/iwant`, prende una
richiesta esplicita, prepara un clone separato alla revisione indicata e invoca
`codex exec`. Pubblica prima una ricevuta e poi aggiorna **quello stesso
commento** con il risultato: un timeout del PATCH non richiede una seconda
esecuzione né un secondo commento.

La richiesta autorizzata e i criteri di accettazione restano posseduti dalla
missione; il prompt versionato resta subordinato ad AGENTS. Il collegamento non
pianifica wave, non decide merge/deploy e non risveglia questa conversazione.
Il coordinatore rilegge il report quando l'utente riprende il lavoro in chat.

Il connettore ChatGPT verificato permette commenti nelle conversazioni di PR.
Usare una PR pertinente al lavoro, non una PR fittizia creata soltanto come
trasporto. Gli endpoint REST usati dal processo locale funzionano anche per
issue ordinarie, ma ciò **non prova** che questo connettore possa scriverle.

## Avvio locale, solo dopo il riesame dei permessi

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
Il codice rifiuta altri repository e campi inattesi. `gh` e `codex` sono gli
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
thread fra più directory di stato: il lock impedisce due processi sullo stesso
stato, non coordina worker distribuiti.

Dopo il riesame dei prerequisiti, abilitare localmente `execution_enabled` e
usare `once` per il primo giro. `watch` ripete lo stesso ciclo seriale con
intervallo minimo di 60 secondi. Il processo può essere avviato nel tmux già
esistente; non viene aggiunto un autostart al Pod. Una ricreazione del Pod
interrompe i processi: leggere e riconciliare lo stato prima del riavvio.

## Richiesta

Il commento deve essere nuovo, non modificato, provenire da un ID abilitato e
iniziare esattamente con `/workspace run` seguito da un oggetto JSON:

```text
/workspace run
{"repository":"skunklabs-uk/iwant","assignment":"WORKSPACE-HANDOFF-POC","generation":1,"branch":"agent/workspace-75-prompt-authority","head":"SHA_COMPLETO_DEL_COMMIT_APPROVATO","prompt":"docs/agents/prompts/workspace-handoff-poc-g1.md"}
```

L'esempio va completato con uno SHA reale di 40 caratteri: non è eseguibile così
com'è. Il branch deve ancora puntare a quello SHA al momento del clone. Il
prompt deve essere un file Git regolare, non un symlink o un file archiviato.
Una nuova generation è una nuova iterazione esplicitamente autorizzata, non un
modo per aggirare un problema tecnico. Il POC #75 resta in sola lettura.
La sandbox di scrittura descritta sotto è collaudata nel workspace; restano da
verificare con un incarico IWANT reale il commit remoto, la ricevuta e la review
di ChatGPT.

Repository, assignment e generation identificano l'incarico. Ripubblicare lo
stesso incarico non lo riesegue; cambiarne il contenuto senza cambiare identità
è un conflitto registrato in `last_rejection`, senza impedire una consegna
pendente. Una generation inferiore a una già accettata per lo stesso assignment
viene rifiutata. Se era in attesa, riceve un risultato di mancato avvio perché
superata; risultati già prodotti vengono comunque consegnati. I comandi malformati vengono registrati come rifiutati senza
bloccare le successive richieste valide. Le modifiche a un comando non sono un
meccanismo di cancellazione di un processo già avviato.

## Consegna di modifiche — runtime verificato, incarico reale ancora da eseguire

La richiesta può aggiungere `publish_paths`, una lista non vuota di **file
esatti** relativi al repository. Non sono pattern o directory. Il campo è
ammesso solo con configurazione locale `sandbox: workspace-write` già
approvata. Ometterlo conserva la consegna del solo report, anche quando il
checkout è scrivibile: la scrittura locale non autorizza implicitamente il push.

La destinazione è il branch della PR IWANT aperta e Draft selezionata da
`thread`; deve appartenere allo stesso repository, non essere il default
branch e avere lo SHA autorizzato. Il collegamento non crea PR artificiali,
non pubblica su fork, non esegue merge né force-push. Prima di eseguire un
incarico il coordinatore verifica anche questi prerequisiti: il publisher li
ricontrolla al momento della consegna, non garantisce che restino invariati
mentre il modello lavora.

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
IWANT corrente, rispettare il lavoro UI attivo e risolvere con il Product Owner
solo le decisioni di prodotto realmente mancanti. Non riassegnare vecchi prompt.

Il nuovo thread richiede un enrollment esplicito distinto dopo la verifica
che il consumer precedente sia fermo e i risultati siano consegnati; conservare
lo stato storico, non cambiarne il binding. Non avviare due worker. Pubblicare
il payload completo realmente da ChatGPT soltanto dopo questo preflight,
quindi eseguire `once`, verificare commit e report, e reiterare se serve.
Il successo locale dei test non chiude la #79: manca il percorso write reale
con review del risultato e closeout. Il merge producer resta distinto
perché può attivare build/pubblicazione e il successivo rollout GitOps.

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

Il Pod usa user namespace, `procMount: Unmasked` nel solo code-server,
seccomp locale e AppArmor ridotto con compensazioni delle protezioni proc.
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
Una scrittura nel tmpfs privato può riuscire senza modificare il filesystem
persistente: il controllo esterno viene fatto dal padre. `read-only` protegge
i dati persistenti, non vieta file temporanei privati.
Gli strumenti figli possono richiedere percorsi assoluti, come
`/usr/bin/git` e `/usr/bin/sha256sum`, perché il PATH è ristretto.

Il runtime verificato usa l'immagine `2026.09.09-b000242`; il collaudo delle
policy non costituisce una nuova release applicativa.
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
| Consumer seriale e richiesta stretta | KEEP: il collegamento chat/processo non è coperto dai singoli tool; un repository/thread/attore, nessun scheduler. |
| Clone, head e prompt verificati | KEEP: impediscono esecuzione di una revisione diversa, symlink, prompt stale o configurazione progetto non riesaminata. |
| Lock, stato e ricevuta unica | KEEP: i test di interruzione e consegna incerta mostrano perché non rilanciare modello o POST; riuso di flock, file atomici e PATCH, nessun ledger distribuito. |
| Sandbox nativa, policy e compensazioni | KEEP: la baseline negava namespace/mount necessari; letture globali e privilegi personali non soddisfano il confine. Profili ridotti e probe proteggono dati persistenti e rete dei comandi. |
| Override app/plugin/hook e ambiente | KEEP: il config utente conteneva un plugin; exec e sandbox caricavano layer diversi. Override nativi, nessun nuovo checker. |
| Quote, paginazione e backoff | KEEP: rispettano gli header e limitano il trasporto seriale; i retry di consegna non rilanciano Codex. |
| Skill `agent-loop` come prerequisito del trasporto | DELETE nella #79: ritirata dall'upstream locale, causava 404 prima del modello. RFC resta obbligatoria; il prompt conserva la responsabilità delle istruzioni di esecuzione. |
| Consegna dei file nella #79 | Candidata KEEP: test comportamentali dimostrano commit esatto, rifiuto di file inattesi e recupero del push senza modello. Necessità e perimetro approvati nella #79; beneficio live ancora da dimostrare. Riuso result.json e Git nativo. |
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
