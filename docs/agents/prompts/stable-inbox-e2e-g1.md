# Stable Handoff Inbox E2E

**Stato: Active**

## Obiettivo

Eseguire un incarico **report-only** per verificare il percorso stabile ChatGPT → Handoff Inbox → Developer Workspace → Codex → RESULT sul thread autorevole.

## Contesto

Questa revisione contiene l'implementazione integrata della missione developer-workspace #103. Il thread autorevole del risultato è la issue #103; la Handoff Inbox #107 è soltanto trasporto.

## Incarico

Ispeziona esclusivamente il checkout ricevuto e le fonti obbligatorie fornite dal collegamento.

Verifica sinteticamente che il codice corrente:

- mantenga un solo consumer seriale;
- accetti in modalità inbox un repository target ammesso e un thread target esplicito;
- distingua la inbox dal thread autorevole di destinazione;
- pubblichi receipt/RESULT sul target tramite il parent, non dal processo Codex;
- conservi exact-head, sandbox e nessun retry automatico del modello.

## Consegna

Produci soltanto un breve report con:
- revisione osservata;
- esito delle verifiche sopra;
- eventuali limiti o incongruenze realmente osservati.

Non modificare file. Non creare commit. Non eseguire rete, merge, deploy o GitHub Actions.
