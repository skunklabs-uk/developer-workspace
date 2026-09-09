# Profili runtime del POC IWANT

**Stato: Active.** Sorgenti dei profili ridotti approvati e applicati nella
missione [#75](https://github.com/skunklabs-uk/developer-workspace/issues/75),
con il delta della continuazione [#79](https://github.com/skunklabs-uk/developer-workspace/issues/79) distribuito e ricaricato il 9 settembre 2026.
Il nome storico della directory non indica che siano ancora candidati.

| Sorgente | Destinazione sui worker K3s | SHA-256 |
| --- | --- | --- |
| [apparmor-iwant.profile](apparmor-iwant.profile) | `/etc/apparmor.d/workspace-handoff-poc-iwant` | `4581088a082c031dfea806127b1fcbcb926da6f740c0ccbd97ea35658538b672` |
| [seccomp.json](seccomp.json) | `/var/lib/kubelet/seccomp/profiles/workspace-handoff-poc-v1.json` | `8657dc596023b63a3501932caf19e55e416ff795d1724e68612812fd865f1d53` |

Homelab possiede distribuzione, caricamento e riferimenti GitOps; la procedura
è nel [disegno operativo](https://github.com/skunklabs-uk/homelab/blob/main/doc/35-Developer%20Workspace%20K3s%20GitOps%20design.md).
Il profilo #79 è distribuito e ricaricato su `k3s-worker1`, `k3s-worker2` e
`k3s-worker3`: la sorgente su ciascun worker ha SHA-256
`4581088a082c031dfea806127b1fcbcb926da6f740c0ccbd97ea35658538b672`, il
profilo è in enforce e il compilato sui worker ha SHA-256
`f04f6adf97faecd1883144701c46e4bc043ba62f804d262540428e30a87f162d`.
Il raw compilato offline con `apparmor_parser -Q -K -S` resta
`9a0f79b5f61f7c0ca480238f7dc84d3f5ab6f76cc43f5054466ab98402d42873`: è
un'evidenza distinta dal compilato osservato sui worker.

AppArmor consente il checkout diagnostico e i checkout in
`runs/<sha256>/checkout`, tramite `@{hex64}`; non autorizza altri percorsi dello
stato o della home. La variabile ammette 64 caratteri esadecimali, anche
maiuscoli, e non lega i pattern sorgente e destinazione. Nel lifecycle corrente
bubblewrap espone al comando soltanto il checkout selezionato: il profilo non è
un'autenticazione dei job e non autorizza da solo un incarico. Le aperture
globali proc-v3/v4 non sono incluse; il profilo v4 inutilizzato è stato rimosso
dai worker. Il consumer resta fermo e il Pod non è stato ricreato; il codice
write non è rilasciato né collaudato nel Pod.

Il rollback del delta #79 resta di competenza Homelab. I backup della sorgente
baseline `b28fec1792b33cb77cd0e9ae1dc4c4af269a9a8ad12ef786c23313b74f592cc2`
sono conservati; per il rollback ripristinare tale sorgente, il raw offline
`56f2927e628ceed16235be16e9ed21d5c97e281cd2b496cfccf0c09ab03815df` e
ricaricare sui worker.

Confini, verifiche e lifecycle sono nel [runbook](../WORKSPACE-HANDOFF.md).
La [cronologia diagnostica](archive/README.md) è archiviata e non autorizza operazioni.
