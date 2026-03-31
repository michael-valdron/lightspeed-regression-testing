#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
LIGHTSPEED_STACK_PATH="${REPO_ROOT}/compose/lightspeed-core-configs/lightspeed-stack.yaml"

sync_file() {
  local url="$1"
  local destination="$2"
  local destination_dir
  local tmp_file

  destination_dir="$(dirname "${destination}")"
  mkdir -p "${destination_dir}"

  tmp_file="$(mktemp "${destination}.tmp.XXXXXX")"
  curl --fail --silent --show-error --location "${url}" --output "${tmp_file}"
  mv "${tmp_file}" "${destination}"
  chmod 0644 "${destination}"

  printf "Synced %s\n" "${destination}"
}

ensure_lightspeed_mcp_server() {
  local destination="$1"

  if grep -q 'name: test-mcp-server' "${destination}"; then
    printf "Retained local MCP server override in %s\n" "${destination}"
    return
  fi

  cat <<'EOF' >> "${destination}"
mcp_servers:
  - name: test-mcp-server
    provider_id: "model-context-protocol"
    url: "http://test-mcp-server:8888/mcp"
    authorization_headers:
      Authorization: "client"
EOF

  printf "Reapplied local MCP server override in %s\n" "${destination}"
}

sync_file \
  "https://raw.githubusercontent.com/redhat-ai-dev/lightspeed-configs/main/llama-stack-configs/config.yaml" \
  "${REPO_ROOT}/compose/llama-stack-configs/config.yaml"

sync_file \
  "https://raw.githubusercontent.com/redhat-ai-dev/lightspeed-configs/main/lightspeed-core-configs/lightspeed-stack.yaml" \
  "${LIGHTSPEED_STACK_PATH}"

ensure_lightspeed_mcp_server "${LIGHTSPEED_STACK_PATH}"

sync_file \
  "https://raw.githubusercontent.com/redhat-ai-dev/lightspeed-configs/main/lightspeed-core-configs/rhdh-profile.py" \
  "${REPO_ROOT}/compose/lightspeed-core-configs/rhdh-profile.py"

sync_file \
  "https://raw.githubusercontent.com/redhat-ai-dev/lightspeed-configs/main/env/default-values.env" \
  "${REPO_ROOT}/compose/env/default-values.env"

printf "Upstream config sync complete.\n"
