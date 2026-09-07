# Candidati runtime per WORKSPACE-HANDOFF-POC

**Stato: Draft.** Missione [#75](https://github.com/skunklabs-uk/developer-workspace/issues/75).
Candidati completi come file di policy, derivati dalla baseline di
`f712903f5fac019058a4cd59d8314468a66c28e5`. Compilati offline; applicati e poi rimossi nel collaudo del 7 settembre 2026.
**Proposta congiunta:** i due profili richiedono anche il diff nativo handoff
preparato sotto per affrontare i due finding. Non applicare i soli profili
al POC invariato. Non sono un profilo
predefinito per altri repository, versioni o comandi interattivi.

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

**Decisione residua:** accettare per questo POC il ramo nativo senza proc come
criterio di compatibilità, mantenendo i dinieghi filesystem/rete e verificando
separatamente exec/helper/tool; oppure mantenere l'obbligo di proc e autorizzare
la sola diagnosi del nuovo EPERM. La prima alternativa evita ulteriori aperture
di sicurezza, ma non viene adottata implicitamente. Nessun incarico IWANT,
riattivazione del consumer o collaudo LLM è autorizzato da questa documentazione.
Review indipendente delle evidenze completata; closeout della missione ancora
aperto finché mancano i due giri e le riletture ChatGPT.

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
