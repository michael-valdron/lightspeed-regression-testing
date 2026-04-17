from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SUPPORTED_PROVIDER_MODES = {"both", "openai_only", "vllm_only"}
REPO_ROOT = Path(__file__).resolve().parents[2]
LOCAL_VALUES_ENV_PATH = REPO_ROOT / "compose" / "env" / "values.env"


@dataclass(frozen=True)
class ProviderConfig:
    provider: str
    model: str


@dataclass(frozen=True)
class SuiteConfig:
    base_url: str
    provider_mode: str
    enable_validation: bool
    openai_model: str
    vllm_model: str
    user_id_prefix: str
    feedback_storage_path: str
    results_dir: str
    timeout_seconds: int
    rag_query: str
    standard_query: str
    mcp_server_name: str
    mcp_valid_auth_header: str
    mcp_invalid_auth_header: str

    @property
    def provider_matrix(self) -> list[ProviderConfig]:
        if self.provider_mode == "openai_only":
            return [ProviderConfig(provider="openai", model=self.openai_model)]
        if self.provider_mode == "vllm_only":
            return [ProviderConfig(provider="vllm", model=self.vllm_model)]
        return [
            ProviderConfig(provider="openai", model=self.openai_model),
            ProviderConfig(provider="vllm", model=self.vllm_model),
        ]

    @property
    def mcp_valid_headers(self) -> dict[str, Any]:
        return {self.mcp_server_name: {"Authorization": self.mcp_valid_auth_header}}

    @property
    def mcp_invalid_headers(self) -> dict[str, Any]:
        return {self.mcp_server_name: {"Authorization": self.mcp_invalid_auth_header}}


def get_env(
    key: str,
    default: str | int | None = None,
    convert_to_int: bool = False,
) -> str | int:
    raw = os.getenv(key)
    if raw is None or not raw.strip():
        if default is None:
            raise RuntimeError(f"Missing required environment variable: {key}")
        value: str | int = default
    else:
        value = raw.strip()

    if not convert_to_int:
        return value

    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"Environment variable {key} must be an integer") from exc


def load_env_file_defaults(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition("=")
        if not sep:
            continue
        os.environ.setdefault(key.strip(), value.strip())


def get_env_nonempty_flag(key: str, default: bool = False) -> bool:
    raw = os.getenv(key)
    if raw is None or not raw.strip():
        return default

    return True


def load_config() -> SuiteConfig:
    load_env_file_defaults(LOCAL_VALUES_ENV_PATH)
    base_url = str(get_env("LS_BASE_URL", "http://localhost:8080")).rstrip("/")
    provider_mode = str(get_env("PROVIDER_MODE", "both")).lower()
    if provider_mode not in SUPPORTED_PROVIDER_MODES:
        raise RuntimeError(
            f"Invalid PROVIDER_MODE={provider_mode!r}. "
            f"Expected one of: {sorted(SUPPORTED_PROVIDER_MODES)}"
        )

    config = SuiteConfig(
        base_url=base_url,
        provider_mode=provider_mode,
        enable_validation=get_env_nonempty_flag("ENABLE_VALIDATION", default=False),
        openai_model=str(get_env("OPENAI_MODEL", "gpt-4o-mini")),
        vllm_model=str(get_env("VLLM_MODEL", "redhataillama-31-8b-instruct")),
        user_id_prefix=str(get_env("TEST_USER_ID_PREFIX", "test-user")),
        feedback_storage_path=str(get_env("FEEDBACK_STORAGE_PATH")),
        results_dir=str(get_env("RESULTS_DIR", "./results")),
        timeout_seconds=int(get_env("REQUEST_TIMEOUT_SECONDS", 120, convert_to_int=True)),
        rag_query=str(
            get_env(
            "RAG_QUERY",
            "How do I configure Developer Lightspeed in Red Hat Developer Hub? I am looking for the yaml snippets to assist me.",
            )
        ),
        standard_query=str(
            get_env(
            "STANDARD_QUERY",
            "Explain what Red Hat Developer Lightspeed is in one paragraph.",
            )
        ),
        mcp_server_name=str(get_env("MCP_SERVER_NAME", "test-mcp-server")),
        mcp_valid_auth_header=str(get_env("MCP_VALID_AUTH_HEADER", "test-secret-token")),
        mcp_invalid_auth_header=str(
            get_env("MCP_INVALID_AUTH_HEADER", "Bearer test-secret-token")
        ),
    )

    # Validate MCP headers encode cleanly because they are sent as JSON in one header.
    json.dumps(config.mcp_valid_headers)
    json.dumps(config.mcp_invalid_headers)
    return config
