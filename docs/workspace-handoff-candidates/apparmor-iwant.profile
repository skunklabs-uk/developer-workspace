
abi <abi/3.0>,

##included <tunables/global>

@{hex32}=@{h}@{h}@{h}@{h}@{h}@{h}@{h}@{h}@{h}@{h}@{h}@{h}@{h}@{h}@{h}@{h}@{h}@{h}@{h}@{h}@{h}@{h}@{h}@{h}@{h}@{h}@{h}@{h}@{h}@{h}@{h}@{h}
@{hex64}=@{hex32}@{hex32}
@{handoff_state}=iwant{,-[0-9]*}

profile workspace-handoff-poc-iwant flags=(attach_disconnected,mediate_deleted) {
  ##include <abstractions/base>

  network,
  capability,
  file,
  umount,
  signal (receive) peer=unconfined,
  signal (receive) peer=runc,
  signal (receive) peer=crun,
  signal (send,receive) peer=workspace-handoff-poc-iwant,

  deny @{PROC}/* w,
  deny @{PROC}/{[^1-9],[^1-9][^0-9],[^1-9s][^0-9y][^0-9s],[^1-9][^0-9][^0-9][^0-9]*}/** w,
  deny @{PROC}/sys/[^k]** w,
  deny @{PROC}/sys/kernel/{?,??,[^s][^h][^m]**} w,
  deny @{PROC}/sysrq-trigger rwklx,
  deny @{PROC}/mem rwklx,
  deny @{PROC}/kmem rwklx,
  deny @{PROC}/kcore rwklx,

  deny /{,oldroot/,newroot/}proc/{asound,acpi,scsi}{,/**} mrwklx,
  deny /{,oldroot/,newroot/}proc/{interrupts,kcore,keys,latency_stats,timer_list,timer_stats,sched_debug} mrwklx,
  deny /{,oldroot/}sys/{firmware,devices/virtual/powercap}{,/**} mrwklx,
  deny /{,oldroot/,newroot/}proc/{bus,fs,irq,sys}{,/**} w,
  deny /{,oldroot/,newroot/}proc/sysrq-trigger w,

  mount options=(rw,silent,make-rslave) /,
  mount options=(rw,silent,make-rprivate) /oldroot/,
  mount fstype=tmpfs options=(rw,nosuid,nodev) tmpfs -> /tmp/,
  mount options=(rw,rbind) /tmp/newroot/ -> /tmp/newroot/,
  pivot_root oldroot=/tmp/oldroot/ /tmp/,
  pivot_root oldroot=/newroot/ /newroot/,

  mount fstype=tmpfs options=(rw,nosuid,nodev) tmpfs -> /newroot/,
  mount fstype=tmpfs options=(rw,nosuid,nodev) tmpfs -> /newroot/dev/,
  mount fstype=devpts options=(rw,nosuid,noexec) devpts -> /newroot/dev/pts/,
  mount fstype=proc options=(rw,nosuid,nodev,noexec) proc -> /newroot/proc/,
  mount options=(rw,rbind) /oldroot/dev/null -> /newroot/dev/null,
  mount options=(rw,rbind) /oldroot/dev/zero -> /newroot/dev/zero,
  mount options=(rw,rbind) /oldroot/dev/full -> /newroot/dev/full,
  mount options=(rw,rbind) /oldroot/dev/random -> /newroot/dev/random,
  mount options=(rw,rbind) /oldroot/dev/urandom -> /newroot/dev/urandom,
  mount options=(rw,rbind) /oldroot/dev/tty -> /newroot/dev/tty,

  mount options=(rw,rbind) /oldroot/usr/bin/ -> /newroot/bin/,
  mount options=(rw,rbind) /oldroot/etc/ -> /newroot/etc/,
  mount options=(rw,rbind) /oldroot/home/coder/.codex/packages/standalone/releases/0.153.4-x86_64-unknown-linux-musl/codex-resources/zsh/bin/zsh -> /newroot/home/coder/.codex/packages/standalone/releases/0.153.4-x86_64-unknown-linux-musl/codex-resources/zsh/bin/zsh,
  mount options=(rw,rbind) /oldroot/usr/lib/ -> /newroot/lib/,
  mount options=(rw,rbind) /oldroot/usr/lib64/ -> /newroot/lib64/,
  mount options=(rw,rbind) /oldroot/usr/sbin/ -> /newroot/sbin/,
  mount options=(rw,rbind) /oldroot/usr/ -> /newroot/usr/,
  mount options=(rw,rbind) /oldroot/workspaces/developer-workspace/.worktrees/handoff-75/ -> /newroot/workspaces/developer-workspace/.worktrees/handoff-75/,
  mount options=(rw,rbind) /oldroot/home/coder/.local/state/workspace-handoff/@{handoff_state}/runs/@{hex64}/checkout/ -> /newroot/home/coder/.local/state/workspace-handoff/@{handoff_state}/runs/@{hex64}/checkout/,

  remount options=(ro,bind,nosuid,nodev,relatime,silent) /newroot/bin/,
  remount options=(ro,bind,nosuid,nodev,relatime,silent) /newroot/etc/,
  remount options=(ro,bind,nosuid,nodev,relatime,silent) /newroot/home/coder/.codex/packages/standalone/releases/0.153.4-x86_64-unknown-linux-musl/codex-resources/zsh/bin/zsh,
  remount options=(ro,bind,nosuid,nodev,relatime,silent) /newroot/lib/,
  remount options=(ro,bind,nosuid,nodev,relatime,silent) /newroot/lib64/,
  remount options=(ro,bind,nosuid,nodev,relatime,silent) /newroot/sbin/,
  remount options=(ro,bind,nosuid,nodev,relatime,silent) /newroot/usr/,
  remount options=(ro,bind,nosuid,nodev,relatime,silent) /newroot/workspaces/developer-workspace/.worktrees/handoff-75/,
  remount options=(ro,bind,nosuid,nodev,relatime,silent) /newroot/home/coder/.local/state/workspace-handoff/@{handoff_state}/runs/@{hex64}/checkout/,
  remount options=(rw,bind,nosuid,nodev,relatime,silent) /newroot/home/coder/.local/state/workspace-handoff/@{handoff_state}/runs/@{hex64}/checkout/,
  remount options=(ro,bind,nosuid,nodev,relatime,silent) /newroot/etc/hosts,
  remount options=(ro,bind,nosuid,nodev,relatime,silent) /newroot/etc/hostname,
  remount options=(ro,bind,nosuid,nodev,relatime,silent) /newroot/etc/resolv.conf,
  remount options=(ro,bind,nosuid,nodev,relatime,silent) /newroot/etc/developer-workspace/kubeconfig/,
  remount options=(ro,bind,nosuid,nodev,relatime,silent) /newroot/etc/developer-workspace/proxmox/,

  mount options=(rw,rbind) /oldroot/home/coder/.codex/tmp/arg0/codex-arg0*/ -> /newroot/home/coder/.codex/tmp/arg0/codex-arg0*/,
  remount options=(ro,bind,nosuid,nodev,relatime,silent) /newroot/home/coder/.codex/tmp/arg0/codex-arg0*/,

  mount options=(rw,rbind) /oldroot/home/coder/.codex/packages/standalone/releases/0.153.4-x86_64-unknown-linux-musl/bin/codex -> /newroot/home/coder/.codex/packages/standalone/releases/0.153.4-x86_64-unknown-linux-musl/bin/codex,
  remount options=(ro,bind,nosuid,nodev,relatime,silent) /newroot/home/coder/.codex/packages/standalone/releases/0.153.4-x86_64-unknown-linux-musl/bin/codex,
  mount fstype=tmpfs options=(rw,nosuid,nodev) tmpfs -> /newroot/etc/developer-workspace/,
}
