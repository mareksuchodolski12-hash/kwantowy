# Helm

`infra/helm/quantum-control-plane` provides a baseline chart for API, worker, and web deployments.

```bash
helm upgrade --install qcp infra/helm/quantum-control-plane \
  --set image.api=ghcr.io/<org>/qcp-api:<tag> \
  --set image.worker=ghcr.io/<org>/qcp-worker:<tag> \
  --set image.web=ghcr.io/<org>/qcp-web:<tag>
```
