# AGENTS.md

## Fonte normativa e lifecycle delle skill

- Prima di analizzare, pianificare, modificare o creare issue o pull request, si DEVE leggere integralmente la versione corrente di [RFC-0001 – Principi fondanti della Software Factory](https://github.com/skunklabs-uk/agent-os/blob/main/rfcs/RFC-0001-principles.md).
- Se la fonte non è accessibile, il lavoro DEVE fermarsi.
- Le regole locali possono restringere la RFC, ma non indebolirla; conflitti o deroghe richiedono l'autorizzazione esplicita dell'utente o di una fonte attiva approvata di autorità superiore.
- Il contenuto della RFC non DEVE essere duplicato in questo repository.
- Le skill riusabili hanno una sola sorgente nel [repository codex-skills](https://github.com/skunklabs-uk/codex-skills); nei progetti vanno installate tramite symlink con `scripts/install-project.sh`, senza copiarne versioni locali.

## Arresto e prosecuzione

Fermarsi solo quando il lavoro richiede una decisione non documentata, supera lo scope approvato, viola una fonte `Active`, comporta conseguenze rilevanti non valutate oppure richiede una verifica obbligatoria che resta ineseguibile dopo ragionevoli tentativi.

Prima di fermarsi, indicare la condizione applicabile, il fatto osservato e la decisione o informazione necessaria.

Una condizione di stop si applica al solo perimetro che la richiede. Il blocco di un task, una fase o un'operazione non blocca automaticamente l'intera missione: il lavoro già autorizzato e determinato che non dipende da quella condizione deve proseguire.

Quando la fonte attiva o il task corrente identifica già il lavoro successivo necessario nella stessa missione, proseguire senza chiedere una conferma meccanica, salvo che si applichi una condizione di stop reale.

Non fermarsi per passaggi già approvati, errori locali correggibili, verifiche risolvibili entro lo scope, stato documentale correggibile in modo univoco o fallback già autorizzati.

## Governo, review e qualità editoriale

- Le istruzioni di questo file sono vincolanti; ogni deroga richiede autorizzazione esplicita.
- Ogni review deve indicare la revisione esaminata; se modifiche successive cambiano materialmente la superficie valutata, ripetere review e verifiche pertinenti.
- I testi rivolti a persone devono essere in italiano e sottoposti a revisione tecnica; applicare `humanize-writing` quando disponibile e proporzionato. La sua indisponibilità non è una condizione di stop; codice, identificatori, comandi, percorsi e termini tecnici restano nella forma più precisa.
- Il template Agent OS è uno scheletro, non una fonte autorevole: non copiarlo né introdurre percorsi, documenti o regole senza un requisito concreto.

### Closeout terminale RFC-0001

Prima del merge terminale, del commit o push che conclude la missione oppure della chiusura dell'issue, completare il closeout previsto da RFC-0001.

Verificare tutte le fonti autorevoli e i documenti `Active` interessati. Aggiornare quelli che mantengono la stessa funzione; archiviare nella stessa modifica quelli conclusi, superati, sostituiti, obsoleti o non più operativi. Prima dell'archiviazione trasferire fatti, decisioni, limiti, requisiti e obblighi di verifica ancora durevoli nella fonte corrente; rimuovere poi il documento da puntatori, indici, tracker, code di lavoro, sezioni sullo stato corrente e istruzioni operative.

I commenti GitHub forniscono tracciabilità, ma non sostituiscono la documentazione autorevole. Quando un'evidenza runtime è un criterio di accettazione, mantenere la missione aperta e non usare `Closes #N` finché tale evidenza manca. `NON APPLICABILE` richiede una motivazione concreta e verificabile.

Commit e push intermedi restano consentiti; quello terminale deve includere il closeout completato.
