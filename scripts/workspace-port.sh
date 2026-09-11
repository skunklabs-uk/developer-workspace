#!/usr/bin/env bash
set -euo pipefail

state_dir=${WORKSPACE_PORT_STATE_DIR:-${XDG_STATE_HOME:-${HOME:-/home/coder}/.local/state}/developer-workspace}
state_file="$state_dir/project-ports.tsv"
lock_file="$state_dir/project-ports.lock"
port_min=${WORKSPACE_PORT_MIN:-3000}
port_max=${WORKSPACE_PORT_MAX:-3999}
preview_base=${WORKSPACE_PORT_PREVIEW_BASE:-https://dev.skunklabs.uk/proxy}

usage() {
  cat <<'USAGE'
Usage: workspace-port <allocate|list|check|forget> [project]

Without [project], allocate/check/forget discover the project from the current
Git repository (origin basename, falling back to the repository directory).
USAGE
}

die() {
  printf 'workspace-port: %s\n' "$*" >&2
  exit 2
}

validate_config() {
  [[ $port_min =~ ^[0-9]+$ && $port_max =~ ^[0-9]+$ ]] || die 'port range must be numeric'
  ((port_min >= 1 && port_max <= 65535 && port_min <= port_max)) || die 'invalid port range'
}

validate_project() {
  local project=$1
  [[ $project =~ ^[A-Za-z0-9._-]+$ ]] || die "invalid project name: $project"
}

discover_project() {
  local root remote name
  root=$(git rev-parse --show-toplevel 2>/dev/null) || die 'not inside a Git repository; pass a project name explicitly'
  remote=$(git -C "$root" remote get-url origin 2>/dev/null || true)
  if [[ -n $remote ]]; then
    name=${remote##*/}
    name=${name%.git}
  else
    name=${root##*/}
  fi
  validate_project "$name"
  printf '%s\n' "$name"
}

resolve_project() {
  if [[ $# -gt 0 && -n $1 ]]; then
    validate_project "$1"
    printf '%s\n' "$1"
  else
    discover_project
  fi
}

ensure_state() {
  mkdir -p "$state_dir"
  chmod 700 "$state_dir"
  touch "$state_file" "$lock_file"
  chmod 600 "$state_file" "$lock_file"
}

find_port() {
  local project=$1 line_project line_port
  [[ -f $state_file ]] || return 1
  while IFS=$'\t' read -r line_project line_port; do
    [[ $line_project == "$project" ]] || continue
    printf '%s\n' "$line_port"
    return 0
  done < "$state_file"
  return 1
}

port_reserved() {
  local wanted=$1 line_project line_port
  [[ -f $state_file ]] || return 1
  while IFS=$'\t' read -r line_project line_port; do
    [[ $line_port == "$wanted" ]] && return 0
  done < "$state_file"
  return 1
}

port_busy() {
  local port=$1 hex table local_address state
  printf -v hex '%04X' "$port"
  for table in /proc/net/tcp /proc/net/tcp6; do
    [[ -r $table ]] || continue
    while read -r _ local_address _ state _; do
      [[ $state == 0A && ${local_address##*:} == "$hex" ]] && return 0
    done < "$table"
  done
  return 1
}

status_for_port() {
  if port_busy "$1"; then
    printf 'listening'
  else
    printf 'stopped'
  fi
}

preview_url() {
  printf '%s/%s/' "${preview_base%/}" "$1"
}

print_assignment() {
  local project=$1 port=$2
  printf 'Project: %s\n' "$project"
  printf 'Port:    %s\n' "$port"
  printf 'Preview: %s\n' "$(preview_url "$port")"
}

allocate() {
  local project=$1 existing port
  ensure_state
  exec 9>"$lock_file"
  flock 9

  if existing=$(find_port "$project"); then
    print_assignment "$project" "$existing"
    return 0
  fi

  for ((port=port_min; port<=port_max; port++)); do
    port_reserved "$port" && continue
    port_busy "$port" && continue
    printf '%s\t%s\n' "$project" "$port" >> "$state_file"
    print_assignment "$project" "$port"
    return 0
  done

  die "no available port in range $port_min-$port_max"
}

list_assignments() {
  local project port
  ensure_state
  printf 'PROJECT\tPORT\tSTATUS\tPREVIEW\n'
  while IFS=$'\t' read -r project port; do
    [[ -n ${project:-} && -n ${port:-} ]] || continue
    printf '%s\t%s\t%s\t%s\n' "$project" "$port" "$(status_for_port "$port")" "$(preview_url "$port")"
  done < "$state_file"
}

check_assignment() {
  local project=$1 port
  ensure_state
  if ! port=$(find_port "$project"); then
    die "project has no assigned port: $project"
  fi
  printf 'Project: %s\n' "$project"
  printf 'Port:    %s\n' "$port"
  printf 'Status:  %s\n' "$(status_for_port "$port")"
  printf 'Preview: %s\n' "$(preview_url "$port")"
}

forget_assignment() {
  local project=$1 current line_project line_port tmp found=false
  ensure_state
  exec 9>"$lock_file"
  flock 9
  current=$(find_port "$project" || true)
  [[ -n $current ]] || die "project has no assigned port: $project"

  tmp="$state_file.tmp.$$"
  : > "$tmp"
  while IFS=$'\t' read -r line_project line_port; do
    if [[ $line_project == "$project" ]]; then
      found=true
      continue
    fi
    [[ -n ${line_project:-} && -n ${line_port:-} ]] && printf '%s\t%s\n' "$line_project" "$line_port" >> "$tmp"
  done < "$state_file"
  chmod 600 "$tmp"
  mv "$tmp" "$state_file"
  [[ $found == true ]] || die "project has no assigned port: $project"
  printf 'Forgot: %s (%s)\n' "$project" "$current"
}

main() {
  validate_config
  local command=${1:-}
  case $command in
    allocate)
      shift
      [[ $# -le 1 ]] || die 'allocate accepts at most one project argument'
      allocate "$(resolve_project "${1:-}")"
      ;;
    list)
      [[ $# -eq 1 ]] || die 'list does not accept a project argument'
      list_assignments
      ;;
    check)
      shift
      [[ $# -le 1 ]] || die 'check accepts at most one project argument'
      check_assignment "$(resolve_project "${1:-}")"
      ;;
    forget)
      shift
      [[ $# -le 1 ]] || die 'forget accepts at most one project argument'
      forget_assignment "$(resolve_project "${1:-}")"
      ;;
    -h|--help|help)
      usage
      ;;
    *)
      usage >&2
      exit 2
      ;;
  esac
}

main "$@"
