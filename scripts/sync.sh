#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

sync_file() {
  local url="$1"
  local destination="$2"
  local destination_dir
  local tmp_file

  destination_dir="$(dirname "${destination}")"
  mkdir -p "${destination_dir}"

  tmp_file="$(mktemp "${destination}.tmp.XXX")"
  curl --fail --silent --show-error --location "${url}" --output "${tmp_file}"
  mv "${tmp_file}" "${destination}"

  printf "Synced %s\n" "${destination}"
}

sync_file \
  "https://raw.githubusercontent.com/redhat-ai-dev/lightspeed-configs/main/llama-stack-configs/config.yaml" \
  "${REPO_ROOT}/compose/llama-stack-configs/config.yaml"

sync_file \
  "https://raw.githubusercontent.com/redhat-ai-dev/lightspeed-configs/main/lightspeed-core-configs/lightspeed-stack.yaml" \
  "${REPO_ROOT}/compose/lightspeed-core-configs/lightspeed-stack.yaml"

sync_file \
  "https://raw.githubusercontent.com/redhat-ai-dev/lightspeed-configs/main/lightspeed-core-configs/rhdh-profile.py" \
  "${REPO_ROOT}/compose/lightspeed-core-configs/rhdh-profile.py"

sync_file \
  "https://raw.githubusercontent.com/redhat-ai-dev/lightspeed-configs/main/env/default-values.env" \
  "${REPO_ROOT}/compose/env/default-values.env"

printf "Upstream config sync complete.\n"
