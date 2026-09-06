# Collegamento ChatGPT → Codex: POC IWANT

**Stato: Draft.** Codice e verifiche locali della missione
[developer-workspace #75](https://github.com/skunklabs-uk/developer-workspace/issues/75).
L'esecuzione nel Pod, i permessi effettivi e il giro completo con Codex non sono
ancora collaudati. Questo documento non dichiara il servizio attivo.

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
{"repository":"skunklabs-uk/iwant","assignment":"WORKSPACE-HANDOFF-POC","generation":1,"branch":"agent/workspace-handoff-poc","head":"SHA_COMPLETO_DEL_COMMIT_APPROVATO","prompt":"docs/agents/prompts/workspace-handoff-poc-g1.md"}
```

L'esempio va completato con uno SHA reale di 40 caratteri: non è eseguibile così
com'è. Il branch deve ancora puntare a quello SHA al momento del clone. Il
prompt deve essere un file Git regolare, non un symlink o un file archiviato.
Una nuova generation è una nuova iterazione esplicitamente autorizzata, non un
modo per aggirare un problema tecnico. Per il primo POC mantenere il task in
sola lettura; la pubblicazione automatica di branch modificati non è inclusa.

Repository, assignment e generation identificano l'incarico. Ripubblicare lo
stesso incarico non lo riesegue; cambiarne il contenuto senza cambiare identità
è un conflitto. I comandi malformati vengono registrati come rifiutati senza
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
`sandbox_mode`. Prima del modello, `codex sandbox linux` prova il profilo su
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
