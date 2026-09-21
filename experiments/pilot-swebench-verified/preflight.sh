#!/usr/bin/env bash
set -euo pipefail

fail=0

check_cmd() {
  if command -v "$1" >/dev/null 2>&1; then
    printf "OK   %-12s %s\n" "$1" "$(command -v "$1")"
  else
    printf "FAIL %-12s missing\n" "$1"
    fail=1
  fi
}

check_cmd python
check_cmd harbor

if [[ "${CAEP_ENV:-docker}" == "docker" ]]; then
  check_cmd docker
  if command -v docker >/dev/null 2>&1; then
    if docker info >/dev/null 2>&1; then
      echo "OK   docker-daemon running"
    else
      echo "FAIL docker-daemon not reachable"
      fail=1
    fi
  fi
fi

if [[ -n "${CAEP_MODEL:-}" ]]; then
  echo "OK   CAEP_MODEL   $CAEP_MODEL"
else
  echo "FAIL CAEP_MODEL   unset"
  fail=1
fi

if [[ -n "${OPENAI_API_KEY:-}" || -n "${CODEX_AUTH_JSON:-}" ]]; then
  echo "OK   codex-auth   credential present in environment (value not printed)"
else
  echo "WARN codex-auth   OPENAI_API_KEY/CODEX_AUTH_JSON not detected; local Codex subscription auth may still work"
fi

exit "$fail"
