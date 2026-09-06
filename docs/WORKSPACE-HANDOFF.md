# Collegamento ChatGPT → Codex: POC IWANT

**Stato: Draft.** Codice e verifiche locali della missione
[developer-workspace #75](https://github.com/skunklabs-uk/developer-workspace/issues/75).
I test sono stati rieseguiti nel Pod. L’attivazione resta bloccata dalla
creazione dei namespace richiesta dalla sandbox nativa; il giro completo con
Codex non è collaudato. Questo documento non dichiara il servizio attivo.

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
modo per aggirare un problema tecnico. Per il primo POC mantenere il task in
sola lettura; la pubblicazione automatica di branch modificati non è inclusa.

Repository, assignment e generation identificano l'incarico. Ripubblicare lo
stesso incarico non lo riesegue; cambiarne il contenuto senza cambiare identità
è un conflitto registrato in `last_rejection`, senza impedire una consegna
pendente. Una generation inferiore a una già accettata per lo stesso assignment
viene rifiutata. Se era in attesa, riceve un risultato di mancato avvio perché
superata; risultati già prodotti vengono comunque consegnati. I comandi malformati vengono registrati come rifiutati senza
bloccare le successive richieste valide. Le modifiche a un comando non sono un
meccanismo di cancellazione di un processo già avviato.

## Permessi: cosa fa il codice e cosa resta da provare

Il processo padre usa `gh` per GitHub e Git per un clone nuovo, senza reset,
pulizia o cambio branch nel checkout interattivo. Recupera per ogni esecuzione
la RFC corrente e la skill `agent-loop` dalle fonti canoniche e le passa come
contesto con il blob SHA, senza copiarle nel repository.

L'invocazione Codex non carica la configurazione utente (`--ignore-user-config`),
non inoltra variabili come `GH_TOKEN`, `BW_SESSION`, `SSH_AUTH_SOCK` e
`OPENAI_API_KEY`, mantiene le regole applicabili e rifiuta una `.codex` di
progetto non riesaminata. Usa un profilo nativo con letture minime e del
checkout, scritture assenti o limitate al checkout e rete dei comandi disabilitata.
Non esiste fallback `danger-full-access` o bypass delle approvazioni.

I permission profile upstream sono **beta** e non si combinano con i vecchi
`sandbox_mode`. Prima del modello, `codex sandbox` prova il profilo su
file sentinella non segreti: lettura nel checkout, lettura/scrittura negate
fuori, scrittura nel checkout coerente con la modalità scelta. Un esito negativo
ferma il tentativo. Non allargare il profilo automaticamente per farlo passare.

Questa prova **non certifica** tutti i tool gestiti, MCP, plug-in, gli effetti di
policy organizzative o la protezione dei processi esterni a Codex. Il relativo
riesame nel Pod e la compatibilità della versione installata restano necessari.
Il login salvato di Codex è distinto da una API key; non assumere quota o costi
senza verificarne l'identità e il percorso reale. Il POC non cambia login.

Fonti upstream: [esecuzione non interattiva](https://developers.openai.com/codex/noninteractive/),
[permission profile](https://developers.openai.com/codex/permissions),
[CLI sandbox](https://developers.openai.com/codex/cli/reference).

### Compatibilità verificata il 6 settembre 2026

Nel Pod `developer-workspace-0`, Codex CLI 0.153.4 espone il comando sandbox
senza sottocomando `linux`. Usare il binario già verificato
`/home/coder/.local/libexec/codex/codex` nel campo `codex`: il wrapper
`/usr/local/bin/codex` può aggiornare automaticamente la CLI anche per `--version`.
La verifica iniziale ha attivato quel comportamento preesistente e installato
0.153.4; le prove successive hanno usato direttamente il binario.

Il profilo `handoff` viene accettato dal parser, ma l’esecuzione di `/bin/true`
fallisce con `bwrap: No permissions to create a new namespace`. Anche
`unshare -Ur true` fallisce con `Operation not permitted`, pur con
`kernel.unprivileged_userns_clone=1` e `user.max_user_namespaces=96054`.
Non è ancora identificato quale controllo del runtime neghi la syscall.
Il Pod mantiene `RuntimeDefault`, capability rimosse e
`allowPrivilegeEscalation=false`; nessuno di questi confini è stato modificato.

L’attivazione richiede quindi una soluzione approvata dal proprietario del
runtime che renda eseguibile la sandbox nativa mantenendo il confine richiesto.
Non usare sandbox legacy con lettura globale, full access, disabilitazione di
seccomp o privilegi aggiuntivi come fallback. Login ChatGPT e identità GitHub
sono verificati, ma non sostituiscono la prova del filesystem e dei tool effettivi.
Lo stato operativo, gli head e i payload di ripartenza restano nella issue #75.

### Diagnosi del diniego e prossimo accertamento

La ripresa del 6 settembre distingue la shell del coordinatore in WSL2 dal
consumer su Linux Debian nel Pod. Nel consumer sono stati osservati
`Seccomp: 2`, un filtro, `NoNewPrivs: 1`, capability tutte a zero e AppArmor
`cri-containerd.apparmor.d (enforce)`. Il runtime del nodo è
`containerd://2.2.5-k3s2`. Senza cambiare queste condizioni:

- `unshare(0)` e `unshare(CLONE_NEWUSER)` restituiscono `EPERM`;
- `clone(SIGCHLD)` crea un figlio che termina subito;
  `clone(CLONE_NEWUSER | SIGCHLD)` restituisce `EPERM`;
- il probe del codice, riusando `runtime-probe` nello stato esistente,
  termina con exit 1; anche il comando nativo `/bin/true` fallisce in bwrap.

Il [profilo sorgente della stessa versione containerd](https://github.com/k3s-io/containerd/blob/v2.2.5-k3s2/contrib/seccomp/seccomp_default.go)
ammette `unshare` con `CAP_SYS_ADMIN` e, senza tale capability, ammette `clone`
solo senza i flag di namespace. È un'evidenza coerente con un diniego seccomp,
non la lettura del filtro OCI effettivamente caricato. AppArmor resta un
ulteriore confine da verificare. Non aggiungere capability per verificare
l'ipotesi. `strace` non è presente, `dmesg` è negato e securityfs non espone i
profili dal Pod; i sysctl già positivi non rimuovono questi limiti.

Una traccia successiva del binario installato 0.153.4, raccolta il 6 settembre
alle 19:17 UTC con `strace` temporaneo e senza avviare il consumer, identifica
il primo diniego nel percorso nativo:
`clone(CLONE_NEWNS|CLONE_NEWIPC|CLONE_NEWUSER|CLONE_NEWPID|CLONE_NEWNET|SIGCHLD)`
restituisce `EPERM`, prima dei mount. Consentire soltanto `unshare` non risolve
questo ingresso. Il template AppArmor della stessa versione upstream contiene
anche `deny mount`: occorre acquisire il profilo caricato, senza assumere che
coincida con il template o che una modifica solo seccomp basti. Traccia,
hash e proposta condizionata con impatto/rollback sono nella issue #75.

Il prossimo accertamento richiede al proprietario del runtime **solo un
estratto diagnostico dal nodo**, riferito al container corrente: sezione
`linux.seccomp` della specifica OCI, `process.apparmorProfile`,
`process.noNewPrivileges`, `process.capabilities` ed eventuali eventi kernel
`SECCOMP`/`apparmor="DENIED"` correlati alla prova. Escludere environment,
credenziali e l'output integrale di inspect. L'assenza di eventi audit non
dimostra assenza del filtro. ID e istante della prova sono nella issue #75.

Questa raccolta non richiede rollout o modifica del consumer. Se conferma la
necessità di cambiare policy, preparare un diff Homelab sul profilo effettivo
con le sole syscall/condizioni necessarie alla sandbox, impatto sull'intero
Pod, rollback e prova prevista, e ottenere l'autorizzazione **prima** di
applicarlo. Non proporre un profilo permissivo generico né presumere che una
sola eccezione risolva anche AppArmor. Spostare il consumer è un'alternativa
con conseguenze diverse, anch'essa da approvare; non clonare lo stato per
provarla. Nessuna di queste modifiche è autorizzata da questo runbook.

Dopo un rimedio approvato, ripetere il probe filesystem e verificare
separatamente rete e tool/MCP/plugin effettivi del figlio con la stessa
configurazione. Login ChatGPT, assenza dei file gestiti locali e filtro delle
variabili sono verifiche preliminari: non certificano da soli quel confine.

## Recupero ed evidenze

Lo stato separa presa in carico, avvio e consegna. `running` viene persistito
prima di invocare l'esecutore; `result.json` prima di pubblicare l'esito.
Un riavvio con risultato durevole riprende solo il PATCH. Un riavvio senza
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
restano nella directory privata del tentativo. Solo il report finale viene
pubblicato. `exit_code: 0` significa processo terminato, non accettazione della
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
Le due letture delle fonti canoniche sono conteggiate; Git e Codex non sono
strumentati con un proxy. Fonte: [GitHub REST best practices](https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api).

I test usano filesystem e repository Git locali reali, risposte HTTP controllate
ed esecutori finti. Non consumano token e non dimostrano un'esecuzione Codex live.
Per chiudere #75 servono ancora: profilo verificato nel workspace, un incarico
reale e una successiva iterazione, entrambi ricevuti e riletti da ChatGPT,
misura del trasporto e closeout delle fonti Homelab/IWANT interessate.
