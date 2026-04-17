# Lightspeed Regression Testing Hub

## Sync Upstream Configs

This repository mirrors selected upstream configuration files from
[github.com/redhat-ai-dev/lightspeed-configs](https://github.com/redhat-ai-dev/lightspeed-configs/tree/main) for regression testing. Run the sync script
to overwrite local copies with the exact upstream versions:

```bash
./scripts/sync.sh
```

To overwrite local copies with versions from your personal forks:

```bash
export LIGHTSPEED_CONFIGS_REPO='<your-user>/<fork-repo-name>'
export LIGHTSPEED_CONFIGS_REPO_BRANCH='<your-branch>'
./scripts/sync.sh
```

The sync process updates these tracked files:

- `compose/llama-stack-configs/config.yaml`
- `compose/lightspeed-core-configs/lightspeed-stack.yaml`
- `compose/lightspeed-core-configs/rhdh-profile.py`
- `compose/env/default-values.env`

The script intentionally overwrites those files every run.

## Environment Secrets

`compose/env/default-values.env` is the committed template synced from upstream.
Create your own local `values.env` for secret or environment-specific values.

```bash
cp compose/env/default-values.env compose/env/values.env
```

For both local compose and OCP, `compose/env/values.env` is the single toggle for
validation:

- Set `ENABLE_VALIDATION=true` to enable validation and run the problematic-query test.
- Leave `ENABLE_VALIDATION` empty to disable validation and skip that test.

The local test suite auto-loads `compose/env/values.env`, and the OCP manifests
inject the same settings through `llama-stack-secrets`.

If you already have an older local `values.env`, remove any legacy
`ENABLE_SAFETY` or `SAFETY_*` entries.

`compose/compose.yaml` still pins the local validation defaults when validation is
enabled:

- `ENABLE_VLLM=true`
- `VALIDATION_PROVIDER=vllm`
- `VALIDATION_MODEL_NAME=redhataillama-31-8b-instruct`

## Lightspeed API Regression Test Suite

### Provider Modes

Use `PROVIDER_MODE` to choose which inference providers run:

- `both` (default)
- `openai_only`
- `vllm_only`

Example run:
```
PROVIDER_MODE=vllm_only pytest test-suite/tests -q
```

### Test Environment Variables

`FEEDBACK_STORAGE_PATH` behavior depends on how you run the suite:

- `lightspeed-core` now writes feedback to a host bind mount at `./feedback-data`
  (mounted into the container at `/tmp/data/feedback`).
- `make compose-up` prepares `./feedback-data` with writable permissions for the container.

Optional overrides:

- `LS_BASE_URL` (default `http://localhost:8080`)
- `OPENAI_MODEL` (default `gpt-4o-mini`)
- `VLLM_MODEL` (default `redhataillama-31-8b-instruct`) --> team cluster
- `RESULTS_DIR` (default `./results` locally; compose test container sets `/results`)

### Run Commands

Logs are written as structured `.txt` case files under `results/run_<timestamp>/`.

Example local run (outside container):

```bash
mkdir -p ./compose/feedback-data results
FEEDBACK_STORAGE_PATH=./compose/feedback-data PROVIDER_MODE=vllm_only pytest test-suite/tests -q
```

### Testing in Cluster

There is a set of `.yaml` files used with `Kustomize` to deploy the resources to
OCP for testing. The following are deployed as part of one deployment:

- Lightspeed Core with validation enabled
- Test MCP Server

The testing suite is run as a Job, and communicates with Lightspeed Core via an internal Service.

There is no separate Ollama sidecar in the OCP deployment anymore; question
validation now runs inside `lightspeed-core` using the configured inference
provider.

You can easily edit the image tags by updating `images.newTag` in [ocp/kustomization.yaml](./ocp/kustomization.yaml).

The testing requires the following secrets to be set in your `values.env` file:
- ENABLE_VLLM
- ENABLE_OPENAI
- VLLM_URL
- VLLM_API_KEY
- OPENAI_API_KEY

The deployment and test job both read `ENABLE_VALIDATION` from the generated
`llama-stack-secrets` secret, which comes from `compose/env/values.env`. That
means the validation shield and the problematic-query test now toggle on or off
together in both local and OCP runs. `ocp/deployment.yaml` still pins
`VALIDATION_PROVIDER=vllm` and
`VALIDATION_MODEL_NAME=redhataillama-31-8b-instruct` when validation is enabled,
so no Ollama-specific safety settings are required.

> [!NOTE]
> 
> You can run with just `openai` or just `vllm` by editing the `PROVIDER_MODE` in [ocp/job.yaml](./ocp/job.yaml). You can omit `ENABLE_VLLM/ENABLE_OPENAI` depending on your choice.
> 
> See [provider-modes](#provider-modes) for more.

To deploy:
```
make deploy-ocp
```

To tear down:
```
make remove-ocp
```

The logs of the Job will outline any testing failures. Due to the Job container shutting down after completion, the results are written to a Persistent Volume that is accessible via the Lightspeed Core container at `/tmp/results`.