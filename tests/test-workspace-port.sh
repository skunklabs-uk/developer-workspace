#!/usr/bin/env bash
set -euo pipefail

script=${WORKSPACE_PORT_SCRIPT:-$(cd "$(dirname "$0")/.." && pwd)/scripts/workspace-port.sh}
tmp=$(mktemp -d)
server_pid=
cleanup() {
  if [[ -n ${server_pid:-} ]]; then kill "$server_pid" 2>/dev/null || true; fi
  rm -rf "$tmp"
}
trap cleanup EXIT

fail() { echo "FAIL: $*" >&2; exit 1; }
assert_contains() { [[ $1 == *"$2"* ]] || fail "expected <$1> to contain <$2>"; }
workspace_port() { bash "$script" "$@"; }

export HOME="$tmp/home"
export WORKSPACE_PORT_STATE_DIR="$tmp/state"
export WORKSPACE_PORT_MIN=3000
export WORKSPACE_PORT_MAX=3005
mkdir -p "$HOME" "$tmp/repos"

make_repo() {
  local name=$1
  local dir="$tmp/repos/$name"
  mkdir -p "$dir"
  git -C "$dir" init -q
  git -C "$dir" remote add origin "git@github.com:skunklabs-uk/${name}.git"
  printf '%s' "$dir"
}

baialupo=$(make_repo baialupo.com)
iwant=$(make_repo iwant)
aeris=$(make_repo aeris)

out=$(cd "$baialupo" && workspace_port allocate)
assert_contains "$out" "Project: baialupo.com"
assert_contains "$out" "Port:    3000"
assert_contains "$out" "Preview: https://dev.skunklabs.uk/proxy/3000/"

out=$(cd "$baialupo" && workspace_port allocate)
assert_contains "$out" "Port:    3000"

out=$(cd "$iwant" && workspace_port allocate)
assert_contains "$out" "Port:    3001"

out=$(workspace_port list)
assert_contains "$out" $'baialupo.com\t3000\tstopped'
assert_contains "$out" $'iwant\t3001\tstopped'

python3 -m http.server 3002 --bind 127.0.0.1 --directory "$tmp" >/dev/null 2>&1 &
server_pid=$!
for _ in $(seq 1 50); do
  if (exec 3<>/dev/tcp/127.0.0.1/3002) 2>/dev/null; then
    exec 3>&- 3<&-
    break
  fi
  sleep 0.02
done
out=$(cd "$aeris" && workspace_port allocate)
assert_contains "$out" "Port:    3003"

out=$(cd "$aeris" && workspace_port check)
assert_contains "$out" "Status:  stopped"

(cd "$iwant" && workspace_port forget) >/dev/null
out=$(cd "$iwant" && workspace_port allocate)
assert_contains "$out" "Port:    3001"

out=$(cd "$tmp" && workspace_port check baialupo.com)
assert_contains "$out" "Project: baialupo.com"
assert_contains "$out" "Port:    3000"

echo "workspace-port tests passed"
