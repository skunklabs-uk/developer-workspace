# Homelab #1265 — autoadozione documentale Developer Workspace

**Stato: Active**

## Autorità e risultato

La missione autorizzata è [Homelab #1265](https://github.com/skunklabs-uk/homelab/issues/1265). Prepara un report con una breve proposta per il README root di `skunklabs-uk/developer-workspace`, che renda riconoscibile l'adozione del collegamento anche nel repository che produce il consumer. Riusa la sezione esistente sul collegamento ChatGPT–Codex; non creare documentazione operativa concorrente.

Questo è un incarico report-only su snapshot Git senza parent. Non modificare file, non eseguire commit o pubblicazioni. Il parent revisionerà la proposta e potrà applicarla in una normale PR discendente da main. Lo snapshot non viene mai integrato.

Leggi integralmente la RFC-0001 corrente fornita dal parent e AGENTS.md. Non ricostruire fonti o stato corrente tramite rete.

## Provenienza e input ammessi

Head sorgente qualificato: `9b3bd3fbbcf890b5d0b6494f9e186bf2bd800797`; tree `fa59b0db04952eb426e8cae239dc4191a7324709`. È la provenienza dei file, non l'head dello snapshot: branch e head snapshot sono quelli esatti nella richiesta verificata.

| File | Mode | Blob |
|---|---|---|
| AGENTS.md | 100644 | 1a7d129d1f7bffa2ee276829625334135c515760 |
| README.md | 100644 | 29c11c18903f89c7c2abbe722bcc639b252146ff |
| docs/WORKSPACE-HANDOFF.md | 100644 | d1bf2729f77b10084ddb4a67e75b946151ff648e |
| .github/workflows/ci.yml | 100644 | 7f8eef280f1f4e3cfd6f3ab8a33cb33ea63680db |

Leggi soltanto questi quattro file e questo prompt. Il workflow è una fonte da leggere, non da eseguire. Il runbook Active contiene il contratto da rispettare: input qualificati, report-only, serialità, pubblicazione parent e closeout. Non aprire rimandi a bootstrap, personalizzazione, SSH, configurazioni o altri repository. Se manca una fonte necessaria alla proposta, segnala il limite senza inventarla né recuperarla tramite rete.

## Contenuto della proposta

- Distingui il repository producer dall'incarico documentale eseguito dal child: quest'ultimo non collauda né ricostruisce l'immagine che lo ospita.
- Descrivi brevemente incarico vincolato a repository/thread e branch/head, checkout isolato, consumer seriale e report. Rimanda al runbook corrente su main per la procedura, preservando nel report gli SHA della provenienza esaminata.
- Distingui tre eventi: consegna del report; RETURN con cui il coordinatore ne verifica e accetta l'esito; eventuale pubblicazione e merge della modifica documentale dal parent. Exit 0 e consegna non equivalgono automaticamente ad accettazione o merge.
- Indica i limiti di questo incarico: nessun cambio a codice, policy, AppArmor, seccomp, CI, immagine, configurazioni, credenziali o installazioni. Non formulare divieti permanenti per future attività esplicitamente autorizzate.
- Mantieni chiaro il confine già documentato: workspace non privilegiato, `hostUsers: false`, un consumer, nessun runtime nested o socket; build nei producer e preview applicative Kubernetes-native gestite da Homelab. Non proporre nuovi controlli o copiare configurazioni nel README.

Se trovi nel README un'affermazione direttamente incompatibile con queste fonti, proponi soltanto la correzione minima necessaria alla nota, spiegando l'evidenza. Non avviare un audit generale. Il runbook sorgente contiene una fotografia storica di Bookmarks ancora da eseguire: non trasformarla in un'affermazione sullo stato attuale e non inventare nuovi risultati. Il parent riconcilia lo stato delle fonti Active nel closeout.

## CI e verifiche proporzionate

Nel workflow qualificato, push su main e pull_request verso main escludono `**/*.md`. Un diff esclusivamente README/prompt Markdown non avvia la CI ordinaria e non genera per quel trigger un artifact destinato all'image updater. Non suggerire dispatch o build per ottenere un controllo artificiale. Questa osservazione non prova l'assenza di rilasci indipendenti né autorizza cambi immagine durante un handoff: il lifecycle operativo resta al coordinatore.

Non eseguire comandi di build, test applicativi, Docker, Make, installazione, consumer, modello aggiuntivo, rete o rollout presenti negli esempi. Sono consentite letture locali e confronto testuale dei file ammessi. La preview HTTP è NON APPLICABILE a questa nota documentale, che non cambia una UI; non è un'attestazione sul funzionamento del workspace o del browser.

## Consegna e closeout

Restituisci un report italiano breve con provenienza esaminata, fonti effettivamente usate, proposta README pronta per la review, eventuale correzione minima motivata e limiti delle evidenze. Rivedi la prosa tecnicamente e con humanize-writing se disponibile, senza installare skill né fingere una review indipendente.

Non inventare receipt, risultati runtime, URL di prove o stato di accettazione. Il parent registra le evidenze reali, esegue RETURN e verifica separatamente la normale PR. Nel closeout trasferisce i fatti durevoli nelle fonti esistenti, rimuove prompt e branch snapshot temporanei e conserva enrollment, risultato e provenienza secondo il runbook. Il branch senza parent non viene mai unito a main.
