#!/usr/bin/env bash
set -euo pipefail

image=${1:?usage: test-init-reaping.sh IMAGE}
container=

cleanup() {
  if [[ -n ${container:-} ]]; then
    docker rm -f "$container" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

count_pid1_zombies() {
  docker exec "$container" bash -c '
    set -euo pipefail
    count=0
    for stat in /proc/[0-9]*/stat; do
      [[ -r $stat ]] || continue
      line=$(<"$stat")
      rest=${line#*) }
      state=${rest%% *}
      rest=${rest#* }
      ppid=${rest%% *}
      if [[ $state == Z && $ppid == 1 ]]; then
        count=$((count + 1))
      fi
    done
    printf "%s\n" "$count"
  '
}

container=$(docker run -d --rm \
  -e WORKSPACE_BOOTSTRAP=false \
  "$image")

ready=false
for _ in {1..50}; do
  if docker exec "$container" true >/dev/null 2>&1; then
    ready=true
    break
  fi
  sleep 0.1
done

if [[ $ready != true ]]; then
  echo "container did not become available for exec" >&2
  docker logs "$container" >&2 || true
  exit 1
fi

before=$(count_pid1_zombies)

docker exec "$container" bash -c '
  set -euo pipefail
  for _ in {1..12}; do
    bash -c "sleep 0.5 & exit 0"
  done
'

sleep 1
after=$(count_pid1_zombies)

if ((after > before)); then
  echo "orphan zombie leak detected under PID 1: before=$before after=$after" >&2
  exit 1
fi

printf "PID 1 reaped orphaned children: before=%s after=%s\n" "$before" "$after"
