# Lightspeed Regression Testing Hub

## Sync Upstream Configs

This repository mirrors selected upstream configuration files from
[github.com/redhat-ai-dev/lightspeed-configs](https://github.com/redhat-ai-dev/lightspeed-configs/tree/main) for regression testing. Run the sync script
to overwrite local copies with the exact upstream versions:

```bash
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
`values.env` is gitignored so local secrets stay out of version control.

```bash
cp compose/env/default-values.env compose/env/values.env
```
