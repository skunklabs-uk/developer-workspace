# Workspace Handoff Lifecycle Contract

**Stato: Active**  
**Owner: Developer Workspace**

## Scopo

Questo documento definisce il contratto operativo tra Coordinator e Workspace consumer nel flusso ChatGPT → Codex.

Il documento completa il protocollo `workspace-handoff` definendo la fase precedente all'esecuzione: quando un incarico è pronto per essere consegnato, quali artefatti sono necessari e quali responsabilità appartengono ai diversi attori.

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

## READY_FOR_HANDOFF

Un incarico può essere consegnato al Workspace consumer solo quando esistono:

- repository configurato;
- branch e head verificabili;
- richiesta GitHub pertinente;
- prompt versionato quando richiesto dal protocollo;
- publish paths espliciti se è prevista pubblicazione.

Una issue senza una superficie GitHub pertinente non viene trasformata automaticamente in un handoff. La fase di preparazione del lavoro appartiene al Coordinator.

## WORKSPACE_RUN

Il consumer esegue esclusivamente l'incarico ricevuto.

Il consumer:

- non modifica lo scope;
- non crea nuove missioni;
- non decide merge o deploy;
- non sostituisce l'autorità delle fonti del repository.

La richiesta `/workspace run` deve contenere il contesto necessario all'esecuzione secondo il protocollo attivo.

## RESULT

Il consumer restituisce evidenza dell'esecuzione:

- identificativo dell'esecuzione;
- incarico e generation;
- base/head verificati;
- esito processo;
- eventuali modifiche o pubblicazioni prodotte.

Il risultato tecnico non equivale ad accettazione.

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
- assicurare scope e autorizzazione;
- preparare PR/thread pertinenti;
- creare o aggiornare prompt versionati quando richiesto;
- valutare RETURN.

### Workspace consumer

Responsabile di:

- eseguire l'incarico ricevuto;
- rispettare repository, branch e prompt assegnati;
- produrre evidenza verificabile;
- non ampliare il perimetro.

## Compatibilità

Questo contratto mantiene compatibilità con i flussi già verificati:

- richiesta `/workspace run` su thread GitHub pertinente;
- receipt/result nello stesso thread;
- RETURN del Coordinator.

Non modifica il runtime consumer e non modifica il modello di sicurezza del workspace.
