# Helm

`infra/helm/quantum-control-plane` provides baseline chart for API, worker, and web deployments.

## Image tagging strategy

Set repository+tag explicitly (recommended tag format: `sha-<gitsha>`):

```bash
helm upgrade --install qcp infra/helm/quantum-control-plane \
  --set image.api.repository=ghcr.io/<org>/qcp-api \
  --set image.api.tag=sha-<gitsha> \
  --set image.worker.repository=ghcr.io/<org>/qcp-worker \
  --set image.worker.tag=sha-<gitsha> \
  --set image.web.repository=ghcr.io/<org>/qcp-web \
  --set image.web.tag=sha-<gitsha>
```
