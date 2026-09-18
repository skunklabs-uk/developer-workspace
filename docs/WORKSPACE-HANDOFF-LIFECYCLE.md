# Workspace Handoff Lifecycle Contract

**Stato: Active**  
**Owner: Developer Workspace**

## Scopo

Questo documento definisce il contratto operativo tra Coordinator e Workspace consumer nel flusso ChatGPT → Codex.

Il documento completa il protocollo `workspace-handoff` definendo la fase precedente all'esecuzione: quando un incarico è pronto per essere consegnato, quali artefatti sono necessari e quali responsabilità appartengono ai diversi attori.

Il trasporto ordinario usa una Handoff Inbox GitHub stabile. La issue o PR del repository target resta la fonte autorevole del lavoro; la inbox contiene soltanto l'envelope necessario al routing.

## Lifecycle

```text
PLANNED
  |
  v
READY_FOR_HANDOFF
  |
  v
WORKSPACE_RUN
  |
  v
RESULT
  |
  v
RETURN
  |
  v
CLOSED
```

## PLANNED

Un lavoro è identificato ma non ancora pronto per il consumer.

Richiede:

- missione o obiettivo autorizzato;
- scope definito;
- criteri di accettazione identificati.

### Qualification del Coordinator

Il Coordinator deve portare il lavoro da `PLANNED` a `READY_FOR_HANDOFF` senza trasformare in domande manuali informazioni già verificabili.

Prima di interrogare l'autore deve usare il contesto disponibile e le fonti collegate per ricostruire ciò che può determinare direttamente, per esempio repository, issue o PR pertinenti, branch/head, stato corrente, prompt esistente e altri prerequisiti tecnici.

Quando restano informazioni necessarie che non possono essere determinate con sufficiente certezza, il Coordinator deve chiederle all'autore prima di assumere una decisione che ne dipende. Sono esempi:

- repository o destinazione realmente ambigui;
- comportamento desiderato o scope non definiti;
- criteri di accettazione che ammettono più interpretazioni rilevanti;
- decisioni di prodotto o autorizzazioni non ricavabili dalle fonti;
- scelta esplicita di modello o reasoning quando l'autore vuole controllarli.

L'intervista deve essere mirata e proporzionata; può procedere una domanda alla volta quando serve chiarire una decisione. Il lavoro resta `PLANNED` finché i gap bloccanti non sono risolti. Informazioni non necessarie all'incarico non devono bloccare l'handoff.

## READY_FOR_HANDOFF

Un incarico può essere consegnato al Workspace consumer solo quando esistono:

- repository target presente nella allowlist della inbox;
- issue o PR target identificata da un thread GitHub positivo e verificabile;
- branch e head verificabili;
- richiesta GitHub pertinente nel repository target;
- prompt versionato quando richiesto dal protocollo;
- publish paths espliciti se è prevista pubblicazione;
- eventuale selezione di modello/reasoning già qualificata dal Coordinator.

Una issue senza una superficie GitHub pertinente non viene trasformata automaticamente in un handoff. La fase di preparazione del lavoro appartiene al Coordinator. La Handoff Inbox non possiede scope, criteri di accettazione o stato di prodotto e non sostituisce la superficie target.

La selezione del modello è opzionale. Se il Coordinator non specifica `model` o `reasoning_effort`, il consumer conserva il default del runtime Codex. Se li specifica, il consumer deve validarli come valori sicuri per il trasporto e applicarli soltanto a quell'incarico.

## WORKSPACE_RUN

Il consumer esegue esclusivamente l'incarico ricevuto.

Il consumer:

- non modifica lo scope;
- non crea nuove missioni;
- non decide merge o deploy;
- non sostituisce l'autorità delle fonti del repository;
- non conduce interviste con l'autore: riceve un incarico già qualificato.

La richiesta `/workspace run` viene pubblicata nella Handoff Inbox e deve contenere il contesto necessario all'esecuzione secondo il protocollo attivo. In modalità inbox include esplicitamente:

- `repository`: repository target ammesso;
- `thread`: numero della issue o PR autorevole del repository target;
- assignment, generation, branch, head e prompt già qualificati.

La inbox stessa non può essere indicata come destinazione autorevole.

Campi opzionali supportati per l'esecuzione Codex:

- `model`: identificatore del modello richiesto per quella singola esecuzione;
- `reasoning_effort`: valore di reasoning richiesto per quella singola esecuzione.

Il consumer valida la forma dei due valori prima dell'esecuzione e li passa esplicitamente a `codex exec`. La compatibilità effettiva tra modello, reasoning e account/runtime resta posseduta da Codex: una combinazione sintatticamente valida ma non disponibile deve fallire esplicitamente, senza fallback silenzioso verso un modello o un reasoning diverso.

## RESULT

Il consumer restituisce evidenza dell'esecuzione:

- identificativo dell'esecuzione;
- incarico e generation;
- base/head verificati;
- esito processo;
- modello e reasoning richiesti, quando espliciti;
- eventuali modifiche o pubblicazioni prodotte.

Receipt e RESULT vengono pubblicati sul thread autorevole del repository target; il comando nella inbox non viene trasformato in una seconda fonte di stato. Il risultato tecnico non equivale ad accettazione.

## RETURN

Il Coordinator verifica il risultato confrontandolo con:

- repository reale;
- revisione eseguita;
- criteri di accettazione;
- fonti autorevoli applicabili.

Solo il Coordinator registra l'accettazione finale.

## Responsabilità

### Coordinator

Responsabile di:

- qualificare il lavoro;
- recuperare dalle fonti le informazioni tecniche già determinabili;
- intervistare l'autore soltanto sui gap reali o sulle decisioni che richiedono autorità umana;
- assicurare scope e autorizzazione;
- preparare issue/PR target pertinenti e l'envelope della inbox;
- creare o aggiornare prompt versionati quando richiesto;
- selezionare opzionalmente modello e reasoning per incarico;
- valutare RETURN.

### Workspace consumer

Responsabile di:

- eseguire l'incarico ricevuto;
- rispettare repository, branch, prompt e selezione modello assegnati;
- produrre evidenza verificabile;
- non ampliare il perimetro;
- non colmare autonomamente gap di prodotto o di autorità che avrebbero dovuto bloccare `READY_FOR_HANDOFF`.

## Compatibilità

Il routing stabile riusa i comportamenti già verificati: richiesta stretta, exact head, sandbox, publication, recovery e RETURN. Durante la transizione il codice accetta ancora la configurazione storica senza `allowed_repositories`, nella quale trasporto e target coincidono; questo percorso serve soltanto a non interrompere il runtime prima del cutover Homelab.

Dopo il cutover, il percorso ordinario è:

- `/workspace run` nella Handoff Inbox stabile;
- receipt/result sul thread autorevole target;
- RETURN del Coordinator sul repository target.

La qualification e il routing non aggiungono scheduler, queue o un secondo worker. La selezione modello aggiunge soltanto parametri opzionali per singolo incarico e non modifica il modello di sicurezza del workspace.