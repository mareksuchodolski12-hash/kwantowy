package kubernetes.security

deny[msg] {
  input.kind == "Deployment"
  container := input.spec.template.spec.containers[_]
  not container.resources
  msg := sprintf("deployment %s missing resource requests/limits", [input.metadata.name])
}
