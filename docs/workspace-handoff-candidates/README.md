# Profili runtime del POC IWANT

**Stato: Active.** Sorgenti dei profili ridotti approvati e applicati nella
missione [#75](https://github.com/skunklabs-uk/developer-workspace/issues/75).
Il nome storico della directory non indica che siano ancora candidati.

| Sorgente | Destinazione sui worker K3s | SHA-256 |
| --- | --- | --- |
| [apparmor-iwant.profile](apparmor-iwant.profile) | `/etc/apparmor.d/workspace-handoff-poc-iwant` | `b28fec1792b33cb77cd0e9ae1dc4c4af269a9a8ad12ef786c23313b74f592cc2` |
| [seccomp.json](seccomp.json) | `/var/lib/kubelet/seccomp/profiles/workspace-handoff-poc-v1.json` | `8657dc596023b63a3501932caf19e55e416ff795d1724e68612812fd865f1d53` |

Homelab possiede distribuzione, caricamento e riferimenti GitOps; la procedura
è nel [disegno operativo](https://github.com/skunklabs-uk/homelab/blob/main/doc/35-Developer%20Workspace%20K3s%20GitOps%20design.md).
I file sono stati distribuiti con Ansible ai tre worker, senza un nuovo playbook.
Il compilato AppArmor verificato ha SHA-256
`56f2927e628ceed16235be16e9ed21d5c97e281cd2b496cfccf0c09ab03815df`.

AppArmor consente i percorsi esatti del checkout diagnostico e di g1/g2;
non autorizza altri incarichi. Le aperture globali proc-v3/v4 non sono incluse;
il profilo v4 inutilizzato è stato rimosso dai worker. I profili correnti
rimangono installati anche a consumer fermo.

Confini, verifiche e lifecycle sono nel [runbook](../WORKSPACE-HANDOFF.md).
La [cronologia diagnostica](archive/README.md) è archiviata e non autorizza operazioni.
