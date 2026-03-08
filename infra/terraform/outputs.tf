output "namespace" {
  value = kubernetes_namespace.qcp.metadata[0].name
}
